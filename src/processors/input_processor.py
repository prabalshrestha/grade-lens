"""
Input processor for parsing assignment configurations and preparing data for grading
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .document_processor import DocumentProcessor
from ..models.assignment_config import AssignmentConfig, QuestionConfig, RubricConfig

logger = logging.getLogger(__name__)


class InputProcessor:
    """Processes assignment configuration and input files into standardized format"""

    def __init__(self, assignments_base_dir: str = "assignments"):
        self.assignments_base_dir = assignments_base_dir
        self.doc_processor = DocumentProcessor()

    def load_assignment(self, assignment_id: str) -> Optional[AssignmentConfig]:
        """
        Load complete assignment configuration from assignment directory
        
        Args:
            assignment_id: Unique identifier for the assignment
            
        Returns:
            AssignmentConfig object or None if loading fails
        """
        assignment_dir = os.path.join(self.assignments_base_dir, assignment_id)

        if not os.path.exists(assignment_dir):
            logger.error(f"Assignment directory not found: {assignment_dir}")
            return None

        try:
            # Load base configuration
            config_path = os.path.join(assignment_dir, "config.json")
            if not os.path.exists(config_path):
                logger.error(f"Configuration file not found: {config_path}")
                return None

            with open(config_path, "r") as f:
                config_data = json.load(f)

            # Process questions document if specified
            if "questions_file" in config_data:
                questions_file = os.path.join(assignment_dir, config_data["questions_file"])
                if os.path.exists(questions_file):
                    questions_text = self.doc_processor.extract_text_from_file(questions_file)
                    config_data["questions_text"] = questions_text
                    logger.info(f"Loaded questions from: {questions_file}")
                else:
                    logger.warning(f"Questions file not found: {questions_file}")

            # Process answer key if specified
            if "answer_key_file" in config_data:
                answer_key_file = os.path.join(assignment_dir, config_data["answer_key_file"])
                if os.path.exists(answer_key_file):
                    answer_key_text = self.doc_processor.extract_text_from_file(answer_key_file)
                    config_data["answer_key_text"] = answer_key_text
                    logger.info(f"Loaded answer key from: {answer_key_file}")
                else:
                    logger.warning(f"Answer key file not found: {answer_key_file}")

            # Load rubric if in separate file
            if "rubric_file" in config_data:
                rubric_file = os.path.join(assignment_dir, config_data["rubric_file"])
                if os.path.exists(rubric_file):
                    with open(rubric_file, "r") as f:
                        rubric_data = json.load(f)
                    config_data["general_rubric"] = rubric_data
                    logger.info(f"Loaded rubric from: {rubric_file}")

            # Enrich question texts with extracted document content if needed
            config_data = self._enrich_questions(config_data, assignment_dir)

            # Create AssignmentConfig object
            assignment_config = AssignmentConfig.from_dict(config_data)
            logger.info(f"Successfully loaded assignment: {assignment_id}")

            return assignment_config

        except Exception as e:
            logger.error(f"Error loading assignment {assignment_id}: {str(e)}")
            return None

    def _enrich_questions(self, config_data: Dict[str, Any], assignment_dir: str) -> Dict[str, Any]:
        """
        Enrich question data with content from separate files if specified
        
        Args:
            config_data: Configuration dictionary
            assignment_dir: Path to assignment directory
            
        Returns:
            Enriched configuration data
        """
        if "questions" not in config_data:
            return config_data

        for i, question in enumerate(config_data["questions"]):
            # Load question text from file if specified
            if "question_file" in question:
                question_file = os.path.join(assignment_dir, question["question_file"])
                if os.path.exists(question_file):
                    question["text"] = self.doc_processor.extract_text_from_file(question_file)
                    logger.debug(f"Loaded text for question {question.get('id', i)}")

            # Load answer key from file if specified
            if "answer_key_file" in question:
                answer_file = os.path.join(assignment_dir, question["answer_key_file"])
                if os.path.exists(answer_file):
                    question["answer_key"] = self.doc_processor.extract_text_from_file(answer_file)
                    logger.debug(f"Loaded answer key for question {question.get('id', i)}")

        return config_data

    def get_processed_json(self, assignment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get processed assignment as JSON dictionary
        
        Args:
            assignment_id: Assignment identifier
            
        Returns:
            Dictionary with complete assignment data or None
        """
        assignment_config = self.load_assignment(assignment_id)
        if assignment_config:
            return assignment_config.to_dict()
        return None

    def list_available_assignments(self) -> list:
        """
        List all available assignments
        
        Returns:
            List of assignment IDs
        """
        if not os.path.exists(self.assignments_base_dir):
            logger.warning(f"Assignments directory not found: {self.assignments_base_dir}")
            return []

        assignments = []
        for item in os.listdir(self.assignments_base_dir):
            assignment_dir = os.path.join(self.assignments_base_dir, item)
            if os.path.isdir(assignment_dir):
                config_file = os.path.join(assignment_dir, "config.json")
                if os.path.exists(config_file):
                    assignments.append(item)

        return sorted(assignments)

    def validate_assignment(self, assignment_id: str) -> bool:
        """
        Validate that an assignment has all required files
        
        Args:
            assignment_id: Assignment identifier
            
        Returns:
            True if valid, False otherwise
        """
        assignment_dir = os.path.join(self.assignments_base_dir, assignment_id)

        # Check if directory exists
        if not os.path.exists(assignment_dir):
            logger.error(f"Assignment directory not found: {assignment_dir}")
            return False

        # Check for config.json
        config_file = os.path.join(assignment_dir, "config.json")
        if not os.path.exists(config_file):
            logger.error(f"Config file missing: {config_file}")
            return False

        # Try to load and validate
        try:
            assignment_config = self.load_assignment(assignment_id)
            if assignment_config is None:
                return False

            # Validate that assignment has at least one question
            if len(assignment_config.questions) == 0:
                logger.error(f"Assignment {assignment_id} has no questions")
                return False

            logger.info(f"Assignment {assignment_id} is valid")
            return True

        except Exception as e:
            logger.error(f"Validation error for {assignment_id}: {str(e)}")
            return False

    def create_assignment_template(self, assignment_id: str, num_questions: int = 2) -> bool:
        """
        Create a template assignment directory structure
        
        Args:
            assignment_id: New assignment identifier
            num_questions: Number of questions to create in template
            
        Returns:
            True if successful, False otherwise
        """
        assignment_dir = os.path.join(self.assignments_base_dir, assignment_id)

        try:
            # Create directory
            os.makedirs(assignment_dir, exist_ok=True)

            # Create template config
            config = {
                "assignment_id": assignment_id,
                "assignment_name": f"Template Assignment - {assignment_id}",
                "course_code": "CS XXX",
                "term": "Fall 2025",
                "questions": [],
                "general_rubric": {
                    "no_submission": 0.0,
                    "attempted": None,
                    "mostly_correct": None,
                    "correct": None,
                    "instructions": "Grade based on correctness and completeness"
                },
                "allow_partial_credit": True
            }

            # Add template questions
            for i in range(1, num_questions + 1):
                config["questions"].append({
                    "id": f"question_{i}",
                    "text": f"Question {i}: [Enter your question here]",
                    "points": 10.0,
                    "answer_key": None,
                    "question_type": "essay"
                })

            # Save config
            config_path = os.path.join(assignment_dir, "config.json")
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)

            # Create README
            readme_path = os.path.join(assignment_dir, "README.md")
            readme_content = f"""# {assignment_id}

## Assignment Configuration

This directory contains the configuration for the assignment.

### Files:

- `config.json`: Main configuration file (required)
- `questions.pdf/docx` (optional): Question document
- `answer_key.pdf/docx` (optional): Answer key document  
- `rubric.json` (optional): Separate rubric file

### Configuration Structure:

Edit `config.json` to customize:
- Assignment metadata (name, course, term)
- Questions (text, points, rubric)
- General rubric and grading instructions

### Usage:

Place student submissions in: `submissions/{assignment_id}/`
Run grading: `python main.py --assignment {assignment_id}`
"""
            with open(readme_path, "w") as f:
                f.write(readme_content)

            logger.info(f"Created assignment template: {assignment_dir}")
            return True

        except Exception as e:
            logger.error(f"Error creating template: {str(e)}")
            return False

