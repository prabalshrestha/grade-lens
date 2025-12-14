"""
Code Evaluation Agent - Evaluates code quality and correctness
Hybrid approach: AI analysis + optional test execution
"""

import os
import sys
import re
import subprocess
import logging
import tempfile
import signal
from typing import List, Dict, Any, Optional
import json

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class CodeEvaluationAgent:
    """Evaluates code submissions with hybrid AI + testing approach"""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.2,
        enable_execution: bool = False,
    ):
        """
        Initialize the code evaluation agent

        Args:
            api_key: OpenAI API key
            model: Model name
            temperature: Temperature for generation
            enable_execution: Whether to allow code execution (default: False for safety)
        """
        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=temperature,
        )
        self.model_name = model
        self.enable_execution = enable_execution

    def evaluate_code(
        self,
        code_submission: dict,
        assignment_config: "AssignmentConfig",
        test_cases: Optional[List[dict]] = None,
    ) -> dict:
        """
        Hybrid evaluation: AI + optional tests

        Args:
            code_submission: Code submission dictionary from CodeExtractionAgent
            assignment_config: Assignment configuration
            test_cases: Optional test cases

        Returns:
            Dictionary with evaluation results
        """
        logger.info("Evaluating code submission")

        try:
            results = {
                "ai_evaluation": {},
                "test_results": None,
                "overall_assessment": "",
                "score_breakdown": {},
            }

            # AI Evaluation
            ai_eval = self.ai_evaluate_code(
                code_submission["combined_code"],
                code_submission.get("files", []),
                assignment_config,
            )
            results["ai_evaluation"] = ai_eval

            # Test Execution (if enabled and test cases provided)
            if self.enable_execution and test_cases:
                logger.info(f"Running {len(test_cases)} test cases")
                test_results = self.run_test_cases(
                    code_submission["combined_code"],
                    code_submission.get("files", []),
                    test_cases,
                )
                results["test_results"] = test_results
            elif test_cases and not self.enable_execution:
                logger.info("Test cases provided but execution disabled")
                results["test_results"] = {
                    "status": "skipped",
                    "message": "Code execution disabled",
                }

            # Generate overall assessment
            results["overall_assessment"] = self._generate_overall_assessment(
                ai_eval, results.get("test_results")
            )

            return results

        except Exception as e:
            logger.error(f"Error evaluating code: {str(e)}", exc_info=True)
            return {
                "ai_evaluation": {},
                "test_results": None,
                "overall_assessment": f"Error during evaluation: {str(e)}",
                "score_breakdown": {},
            }

    def ai_evaluate_code(
        self,
        combined_code: str,
        files: List[dict],
        assignment_config: "AssignmentConfig",
    ) -> dict:
        """
        Let LLM evaluate code against rubric

        Args:
            combined_code: Combined code string
            files: List of file dictionaries
            assignment_config: Assignment configuration

        Returns:
            Dictionary with AI evaluation
        """
        try:
            # Build evaluation prompt
            system_prompt = self._build_code_evaluation_system_prompt(assignment_config)
            user_prompt = self._build_code_evaluation_user_prompt(
                combined_code, files, assignment_config
            )

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            response = self.llm.invoke(messages)
            evaluation_text = response.content

            # Try to parse JSON response
            evaluation_data = self._parse_evaluation_response(evaluation_text)

            return evaluation_data

        except Exception as e:
            logger.error(f"Error in AI evaluation: {str(e)}")
            return {
                "correctness": "Error during evaluation",
                "style": "Could not evaluate",
                "efficiency": "Could not evaluate",
                "error": str(e),
            }

    def run_test_cases(
        self, combined_code: str, files: List[dict], test_cases: List[dict]
    ) -> dict:
        """
        Execute code with test cases (sandboxed)

        Args:
            combined_code: Combined code string
            files: List of file dictionaries
            test_cases: List of test case dictionaries

        Returns:
            Dictionary with test results
        """
        if not files:
            return {
                "status": "error",
                "message": "No code files to test",
                "passed": 0,
                "failed": 0,
                "details": [],
            }

        # Determine primary language
        language = files[0].get("language", "python")

        if language == "python":
            return self._run_python_tests(files, test_cases)
        elif language == "java":
            return self._run_java_tests(files, test_cases)
        else:
            return {
                "status": "unsupported",
                "message": f"Testing not supported for {language}",
                "passed": 0,
                "failed": 0,
                "details": [],
            }

    def _run_python_tests(self, files: List[dict], test_cases: List[dict]) -> dict:
        """Run Python test cases with timeout and sandboxing"""
        results = {"status": "completed", "passed": 0, "failed": 0, "details": []}

        try:
            # Create temporary file with code
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, encoding="utf-8"
            ) as f:
                # Write all Python code
                for file_data in files:
                    if file_data.get("language") == "python":
                        f.write(file_data["content"])
                        f.write("\n\n")

                temp_file = f.name

            # Run each test case
            for i, test_case in enumerate(test_cases):
                test_result = self._execute_python_test(
                    temp_file, test_case, timeout=5  # 5 second timeout
                )

                results["details"].append(test_result)

                if test_result["passed"]:
                    results["passed"] += 1
                else:
                    results["failed"] += 1

            # Clean up
            try:
                os.unlink(temp_file)
            except:
                pass

        except Exception as e:
            logger.error(f"Error running Python tests: {str(e)}")
            results["status"] = "error"
            results["message"] = str(e)

        return results

    def _execute_python_test(
        self, code_file: str, test_case: dict, timeout: int = 5
    ) -> dict:
        """
        Execute a single Python test case with sandboxing

        Security measures:
        - Timeout limit (default: 5 seconds)
        - Subprocess isolation
        - No dangerous imports allowed
        - Memory and CPU limits via subprocess
        """
        test_result = {
            "description": test_case.get("description", "Test"),
            "input": test_case.get("input"),
            "expected_output": test_case.get("expected_output"),
            "actual_output": None,
            "passed": False,
            "error": None,
            "timeout": timeout,
        }

        try:
            # Security check: scan for dangerous imports
            with open(code_file, "r") as f:
                code_content = f.read()

            dangerous_patterns = [
                r"import\s+os",
                r"import\s+subprocess",
                r"import\s+sys",
                r"from\s+os\s+import",
                r"from\s+subprocess\s+import",
                r"__import__",
                r"eval\s*\(",
                r"exec\s*\(",
                r"compile\s*\(",
            ]

            for pattern in dangerous_patterns:
                if re.search(pattern, code_content):
                    test_result["error"] = (
                        f"Security: Dangerous code pattern detected: {pattern}"
                    )
                    test_result["passed"] = False
                    logger.warning(f"Blocked execution: {pattern} found in code")
                    return test_result

            # Prepare test input
            test_input = test_case.get("input", "")

            # Run code in subprocess with resource limits
            process = subprocess.Popen(
                [sys.executable, code_file],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                # Resource limits (Unix-like systems)
                preexec_fn=self._set_resource_limits if os.name != "nt" else None,
            )

            try:
                stdout, stderr = process.communicate(input=test_input, timeout=timeout)

                actual_output = stdout.strip()
                test_result["actual_output"] = actual_output

                # Check if output matches expected
                expected = str(test_case.get("expected_output", "")).strip()
                test_result["passed"] = actual_output == expected

                if stderr:
                    test_result["error"] = stderr

            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()  # Clean up zombie process
                test_result["error"] = f"Timeout exceeded ({timeout}s)"
                test_result["passed"] = False
                logger.warning(f"Test timeout after {timeout}s")

        except Exception as e:
            test_result["error"] = str(e)
            test_result["passed"] = False
            logger.error(f"Test execution error: {str(e)}")

        return test_result

    def _set_resource_limits(self):
        """Set resource limits for subprocess (Unix-like systems only)"""
        try:
            import resource

            # Limit CPU time to 10 seconds
            resource.setrlimit(resource.RLIMIT_CPU, (10, 10))

            # Limit memory to 256MB
            resource.setrlimit(
                resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024)
            )

            # Limit file size to 1MB
            resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))

        except ImportError:
            # resource module not available (Windows)
            pass
        except Exception as e:
            logger.warning(f"Could not set resource limits: {str(e)}")

    def _run_java_tests(self, files: List[dict], test_cases: List[dict]) -> dict:
        """Run Java test cases (basic implementation)"""
        # Java testing would require compilation
        # For now, return unsupported
        return {
            "status": "unsupported",
            "message": "Java test execution not yet implemented",
            "passed": 0,
            "failed": 0,
            "details": [],
        }

    def _build_code_evaluation_system_prompt(
        self, assignment_config: "AssignmentConfig"
    ) -> str:
        """Build system prompt for code evaluation"""
        prompt_parts = []

        prompt_parts.append(
            "You are an expert code reviewer and instructor. "
            "Evaluate student code submissions based on the provided rubric and requirements."
        )

        prompt_parts.append(f"\n\nAssignment: {assignment_config.assignment_name}")

        # Add rubric information
        if assignment_config.general_rubric:
            rubric = assignment_config.general_rubric
            prompt_parts.append("\n\nGrading Criteria:")
            if rubric.criteria:
                for criterion in rubric.criteria:
                    prompt_parts.append(f"- {criterion}")

        prompt_parts.append(
            "\n\nEvaluate the code on these dimensions:\n"
            "1. Correctness: Does it solve the problem correctly?\n"
            "2. Code Quality: Is it well-structured, readable, and maintainable?\n"
            "3. Efficiency: Is the algorithm/approach efficient?\n"
            "4. Style: Does it follow good coding practices?\n"
            "\nReturn your evaluation in JSON format:\n"
            "{\n"
            '  "correctness": "detailed analysis",\n'
            '  "code_quality": "detailed analysis",\n'
            '  "efficiency": "detailed analysis",\n'
            '  "style": "detailed analysis",\n'
            '  "strengths": ["strength 1", "strength 2"],\n'
            '  "improvements": ["improvement 1", "improvement 2"]\n'
            "}"
        )

        return "\n".join(prompt_parts)

    def _build_code_evaluation_user_prompt(
        self,
        combined_code: str,
        files: List[dict],
        assignment_config: "AssignmentConfig",
    ) -> str:
        """Build user prompt for code evaluation"""
        prompt_parts = []

        prompt_parts.append("Student Code Submission:\n")
        prompt_parts.append("=" * 70)

        # Add file information
        if len(files) > 1:
            prompt_parts.append(f"\nSubmitted {len(files)} files:")
            for file_data in files:
                prompt_parts.append(
                    f"- {file_data['filename']} ({file_data['language']})"
                )
            prompt_parts.append("")

        # Add code (limit length if too long)
        if len(combined_code) > 10000:
            prompt_parts.append(combined_code[:10000])
            prompt_parts.append("\n\n[... code truncated for length ...]")
        else:
            prompt_parts.append(combined_code)

        prompt_parts.append("\n" + "=" * 70)
        prompt_parts.append(
            "\nPlease evaluate this code submission and return your analysis in JSON format."
        )

        return "\n".join(prompt_parts)

    def _parse_evaluation_response(self, response_text: str) -> dict:
        """Parse LLM evaluation response"""
        try:
            # Try to extract JSON from response
            import re

            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)

            if json_match:
                evaluation = json.loads(json_match.group(0))
                return evaluation
            else:
                # Return response as plain text if not JSON
                return {
                    "evaluation": response_text,
                    "correctness": "See evaluation",
                    "code_quality": "See evaluation",
                    "efficiency": "See evaluation",
                    "style": "See evaluation",
                }
        except Exception as e:
            logger.warning(f"Could not parse evaluation response: {str(e)}")
            return {"evaluation": response_text, "parse_error": str(e)}

    def _generate_overall_assessment(
        self, ai_evaluation: dict, test_results: Optional[dict]
    ) -> str:
        """Generate overall assessment from AI eval and test results"""
        parts = []

        # AI Evaluation summary
        if ai_evaluation.get("correctness"):
            parts.append(f"Correctness: {ai_evaluation['correctness'][:200]}")

        # Test results summary
        if test_results and test_results.get("status") == "completed":
            passed = test_results.get("passed", 0)
            failed = test_results.get("failed", 0)
            total = passed + failed

            parts.append(
                f"\n\nTest Results: {passed}/{total} tests passed "
                f"({passed/total*100:.0f}%)"
                if total > 0
                else ""
            )

        # Strengths
        if ai_evaluation.get("strengths"):
            parts.append("\n\nStrengths:")
            for strength in ai_evaluation["strengths"][:3]:
                parts.append(f"- {strength}")

        # Improvements
        if ai_evaluation.get("improvements"):
            parts.append("\n\nAreas for Improvement:")
            for improvement in ai_evaluation["improvements"][:3]:
                parts.append(f"- {improvement}")

        return "\n".join(parts) if parts else "Code evaluation completed"
