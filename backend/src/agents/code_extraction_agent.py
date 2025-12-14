"""
Code Extraction Agent - Extracts and analyzes code files (Python/Java)
"""

import os
import ast
import logging
from typing import List, Dict, Any, Optional
import re

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class CodeExtractionAgent:
    """Extracts and analyzes code submissions"""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.1,
    ):
        """
        Initialize the code extraction agent

        Args:
            api_key: OpenAI API key
            model: Model name
            temperature: Temperature for generation
        """
        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=temperature,
        )
        self.model_name = model

    def extract_code_submission(
        self,
        file_paths: List[str],
        assignment_config: "AssignmentConfig",
    ) -> Dict[str, Any]:
        """
        Process multiple code files from one student

        Args:
            file_paths: List of code file paths
            assignment_config: Assignment configuration

        Returns:
            Dictionary with extracted code and analysis:
            {
                'files': [...],
                'combined_code': '...',
                'languages': ['python'],
                'analysis': '...',
                'total_lines': 150
            }
        """
        logger.info(f"Extracting code from {len(file_paths)} file(s)")

        try:
            files_data = []
            total_lines = 0
            languages_found = set()

            # Process each file
            for file_path in sorted(file_paths):  # Sort for consistent ordering
                filename = os.path.basename(file_path)
                logger.debug(f"Processing code file: {filename}")

                # Read file content
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                except UnicodeDecodeError:
                    # Try with different encoding
                    with open(file_path, "r", encoding="latin-1") as f:
                        content = f.read()

                # Detect language
                language = self._detect_language(filename)
                languages_found.add(language)

                # Analyze syntax
                syntax_analysis = self.analyze_code_syntax(content, language)

                # Extract structure
                structure = self.extract_code_structure(content, language)

                # Get AI-determined purpose (if multiple files)
                purpose = None
                if len(file_paths) > 1:
                    purpose = self._determine_file_purpose(filename, content, language)

                file_data = {
                    "filename": filename,
                    "content": content,
                    "language": language,
                    "syntax_valid": syntax_analysis["valid"],
                    "syntax_errors": syntax_analysis.get("errors", []),
                    "structure": structure,
                    "purpose": purpose,
                    "line_count": len(content.splitlines()),
                }

                files_data.append(file_data)
                total_lines += file_data["line_count"]

            # Concatenate all files
            combined_code = self.concatenate_code_files(files_data)

            # Generate overall analysis
            analysis = self._generate_submission_analysis(
                files_data, languages_found, assignment_config
            )

            return {
                "files": files_data,
                "combined_code": combined_code,
                "languages": list(languages_found),
                "analysis": analysis,
                "total_lines": total_lines,
                "file_count": len(files_data),
            }

        except Exception as e:
            logger.error(f"Error extracting code submission: {str(e)}", exc_info=True)
            # Return minimal data on error
            return {
                "files": [],
                "combined_code": "",
                "languages": [],
                "analysis": f"Error extracting code: {str(e)}",
                "total_lines": 0,
                "file_count": 0,
            }

    def concatenate_code_files(self, files: List[dict]) -> str:
        """
        Concatenate code files with clear separators

        Args:
            files: List of file dictionaries

        Returns:
            Concatenated code string
        """
        if not files:
            return ""

        parts = []

        for file_data in files:
            filename = file_data["filename"]
            content = file_data["content"]
            language = file_data["language"]

            # Add separator
            separator = f"\n{'='*70}\n"
            separator += f"File: {filename} ({language})\n"
            if file_data.get("purpose"):
                separator += f"Purpose: {file_data['purpose']}\n"
            separator += f"{'='*70}\n\n"

            parts.append(separator)
            parts.append(content)
            parts.append("\n\n")

        return "".join(parts)

    def analyze_code_syntax(self, code: str, language: str) -> dict:
        """
        Check code syntax without execution

        Args:
            code: Code string
            language: Programming language

        Returns:
            Dictionary with syntax analysis
        """
        result = {"valid": False, "errors": []}

        try:
            if language == "python":
                # Try to compile Python code
                compile(code, "<string>", "exec")
                result["valid"] = True

            elif language == "java":
                # Basic Java syntax checks (without full compilation)
                # Check for class definition
                if "class " in code or "public class " in code:
                    result["valid"] = True
                else:
                    result["errors"].append("No class definition found")

            else:
                # For other languages, just check if it's not empty
                result["valid"] = bool(code.strip())

        except SyntaxError as e:
            result["valid"] = False
            result["errors"].append(f"Syntax error at line {e.lineno}: {e.msg}")
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Error: {str(e)}")

        return result

    def extract_code_structure(self, code: str, language: str) -> dict:
        """
        Extract code structure (functions, classes, imports)

        Args:
            code: Code string
            language: Programming language

        Returns:
            Dictionary with code structure
        """
        structure = {"functions": [], "classes": [], "imports": [], "main_found": False}

        try:
            if language == "python":
                # Use AST to parse Python code
                tree = ast.parse(code)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        structure["functions"].append(node.name)
                        if node.name == "main" or node.name == "__main__":
                            structure["main_found"] = True

                    elif isinstance(node, ast.ClassDef):
                        structure["classes"].append(node.name)

                    elif isinstance(node, (ast.Import, ast.ImportFrom)):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                structure["imports"].append(alias.name)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                structure["imports"].append(node.module)

            elif language == "java":
                # Basic regex-based extraction for Java
                # Find class definitions
                class_pattern = r"class\s+(\w+)"
                structure["classes"] = re.findall(class_pattern, code)

                # Find method definitions
                method_pattern = (
                    r"(?:public|private|protected)?\s+\w+\s+(\w+)\s*\([^)]*\)"
                )
                structure["functions"] = re.findall(method_pattern, code)

                # Find imports
                import_pattern = r"import\s+([\w.]+);"
                structure["imports"] = re.findall(import_pattern, code)

                # Check for main method
                if "public static void main" in code:
                    structure["main_found"] = True

        except Exception as e:
            logger.warning(f"Error extracting structure: {str(e)}")

        return structure

    def _detect_language(self, filename: str) -> str:
        """Detect programming language from filename"""
        ext = os.path.splitext(filename)[1].lower()

        language_map = {
            ".py": "python",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".js": "javascript",
            ".ts": "typescript",
        }

        return language_map.get(ext, "unknown")

    def _determine_file_purpose(
        self, filename: str, content: str, language: str
    ) -> Optional[str]:
        """
        Use AI to determine the purpose of a code file

        Args:
            filename: Name of the file
            content: File content
            language: Programming language

        Returns:
            Brief description of file's purpose
        """
        try:
            # Limit content length for API call
            content_preview = content[:2000] if len(content) > 2000 else content

            system_prompt = """You are analyzing code submissions. 
Briefly describe the purpose of this code file in 1-2 sentences.
Focus on what the code does, not implementation details."""

            user_prompt = f"""Filename: {filename}
Language: {language}

Code:
{content_preview}

What is the purpose of this file?"""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            response = self.llm.invoke(messages)
            purpose = response.content.strip()

            return purpose[:200]  # Limit length

        except Exception as e:
            logger.warning(f"Error determining file purpose: {str(e)}")
            return None

    def _generate_submission_analysis(
        self,
        files_data: List[dict],
        languages: set,
        assignment_config: "AssignmentConfig",
    ) -> str:
        """
        Generate overall analysis of the submission

        Args:
            files_data: List of file data dictionaries
            languages: Set of languages found
            assignment_config: Assignment configuration

        Returns:
            Analysis string
        """
        parts = []

        # File count and languages
        parts.append(
            f"Student submitted {len(files_data)} file(s) "
            f"in {', '.join(sorted(languages))}."
        )

        # List files
        if len(files_data) > 1:
            file_list = [f"- {f['filename']}" for f in files_data]
            parts.append("\n\nFiles:\n" + "\n".join(file_list))

        # Syntax validation
        invalid_files = [f for f in files_data if not f["syntax_valid"]]
        if invalid_files:
            parts.append(
                f"\n\nWarning: {len(invalid_files)} file(s) have syntax errors."
            )

        # Structure summary
        total_functions = sum(len(f["structure"]["functions"]) for f in files_data)
        total_classes = sum(len(f["structure"]["classes"]) for f in files_data)

        if total_functions > 0 or total_classes > 0:
            parts.append(
                f"\n\nCode structure: {total_functions} function(s), "
                f"{total_classes} class(es)."
            )

        return "".join(parts)
