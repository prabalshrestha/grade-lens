"""
Submission Grouper - Groups multiple files by student based on filename patterns
Handles naming format: name_LATE_studentID_submissionID_remainder
"""

import os
import re
import logging
from typing import Dict, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class SubmissionGrouper:
    """Groups submission files by student based on filename patterns"""

    def parse_filename(self, filename: str) -> dict:
        """
        Parse filename following pattern: name_LATE_studentID_submissionID_remainder

        Examples:
            - lawfordjack_LATE_101445_22007124_HW8.py
            - nielsenconnor_192061_21988980_Problem_1.java
            - smithjohn_12345_67890_Assignment1.pdf

        Args:
            filename: The filename to parse

        Returns:
            Dictionary with parsed components:
            {
                'student_name': 'lawfordjack',
                'is_late': True,
                'student_id': '101445',
                'submission_id': '22007124',
                'remainder': 'HW8',
                'extension': '.py',
                'original_filename': 'lawfordjack_LATE_101445_22007124_HW8.py'
            }
        """
        try:
            # Store original filename
            original_filename = filename

            # Split extension
            name_without_ext, extension = os.path.splitext(filename)

            # Split by underscore
            parts = name_without_ext.split("_")

            if len(parts) < 2:
                logger.warning(f"Filename '{filename}' doesn't follow expected pattern")
                return {
                    "student_name": parts[0] if parts else "unknown",
                    "is_late": False,
                    "student_id": "unknown",
                    "submission_id": None,
                    "remainder": "",
                    "extension": extension,
                    "original_filename": original_filename,
                }

            # First part is always student name
            student_name = parts[0]
            current_index = 1

            # Check for LATE marker
            is_late = False
            if current_index < len(parts) and parts[current_index].upper() == "LATE":
                is_late = True
                current_index += 1

            # Extract student ID (first numeric part with 4+ digits)
            student_id = "unknown"
            submission_id = None
            remainder_parts = []

            found_student_id = False
            found_submission_id = False

            for i in range(current_index, len(parts)):
                part = parts[i]

                # Check if this part is numeric and has 4+ digits
                if part.isdigit() and len(part) >= 4:
                    if not found_student_id:
                        student_id = part
                        found_student_id = True
                    elif not found_submission_id:
                        submission_id = part
                        found_submission_id = True
                    else:
                        # Additional numeric parts go to remainder
                        remainder_parts.append(part)
                else:
                    # Non-numeric parts go to remainder
                    remainder_parts.append(part)

            remainder = "_".join(remainder_parts) if remainder_parts else ""

            return {
                "student_name": student_name,
                "is_late": is_late,
                "student_id": student_id,
                "submission_id": submission_id,
                "remainder": remainder,
                "extension": extension,
                "original_filename": original_filename,
            }

        except Exception as e:
            logger.error(f"Error parsing filename '{filename}': {str(e)}")
            return {
                "student_name": "unknown",
                "is_late": False,
                "student_id": "unknown",
                "submission_id": None,
                "remainder": "",
                "extension": "",
                "original_filename": filename,
            }

    def identify_student_key(self, parsed: dict) -> str:
        """
        Create unique student identifier from parsed filename

        Args:
            parsed: Parsed filename dictionary

        Returns:
            Unique key: {student_name}_{student_id}
        """
        student_name = parsed.get("student_name", "unknown")
        student_id = parsed.get("student_id", "unknown")
        return f"{student_name}_{student_id}"

    def group_files_by_student(self, file_paths: List[str]) -> Dict[str, List[str]]:
        """
        Group multiple files by student based on parsed filename

        Args:
            file_paths: List of file paths to group

        Returns:
            Dictionary mapping student_key to list of file paths:
            {
                'lawfordjack_101445': ['/path/to/file1.py', '/path/to/file2.py'],
                'nielsenconnor_192061': ['/path/to/file1.java']
            }
        """
        grouped = defaultdict(list)

        for file_path in file_paths:
            filename = os.path.basename(file_path)
            parsed = self.parse_filename(filename)
            student_key = self.identify_student_key(parsed)

            grouped[student_key].append(file_path)

            logger.debug(
                f"Grouped '{filename}' under student '{student_key}' "
                f"(late: {parsed['is_late']})"
            )

        # Log grouping summary
        logger.info(
            f"Grouped {len(file_paths)} files into {len(grouped)} student submissions"
        )
        for student_key, files in grouped.items():
            logger.info(f"  {student_key}: {len(files)} file(s)")

        return dict(grouped)

    def get_student_info(self, file_paths: List[str]) -> dict:
        """
        Extract student information from a group of files
        Uses the first file to extract info (assumes all files from same student)

        Args:
            file_paths: List of file paths from same student

        Returns:
            Dictionary with student information
        """
        if not file_paths:
            return {
                "student_name": "unknown",
                "student_id": "unknown",
                "is_late": False,
                "file_count": 0,
                "submission_id": None,
            }

        # Parse first file to get student info
        first_file = os.path.basename(file_paths[0])
        parsed = self.parse_filename(first_file)

        return {
            "student_name": parsed["student_name"],
            "student_id": parsed["student_id"],
            "is_late": parsed["is_late"],
            "file_count": len(file_paths),
            "submission_id": parsed["submission_id"],
        }

    def validate_group_consistency(self, file_paths: List[str]) -> bool:
        """
        Validate that all files in a group belong to the same student

        Args:
            file_paths: List of file paths to validate

        Returns:
            True if all files have consistent student info, False otherwise
        """
        if len(file_paths) <= 1:
            return True

        # Parse all files and check consistency
        parsed_files = [self.parse_filename(os.path.basename(f)) for f in file_paths]

        first_name = parsed_files[0]["student_name"]
        first_id = parsed_files[0]["student_id"]

        for parsed in parsed_files[1:]:
            if parsed["student_name"] != first_name or parsed["student_id"] != first_id:
                logger.warning(
                    f"Inconsistent student info in group: "
                    f"expected {first_name}/{first_id}, "
                    f"found {parsed['student_name']}/{parsed['student_id']}"
                )
                return False

        return True

    def sort_files_by_name(self, file_paths: List[str]) -> List[str]:
        """
        Sort files by filename (useful for consistent ordering)

        Args:
            file_paths: List of file paths

        Returns:
            Sorted list of file paths
        """
        return sorted(file_paths, key=lambda x: os.path.basename(x))

    def categorize_files_by_type(self, file_paths: List[str]) -> Dict[str, List[str]]:
        """
        Categorize files by their type/extension

        Args:
            file_paths: List of file paths

        Returns:
            Dictionary mapping file type to list of paths:
            {
                'code': ['.py', '.java' files],
                'document': ['.pdf', '.docx', '.txt' files],
                'other': [other files]
            }
        """
        categorized = {"code": [], "document": [], "other": []}

        code_extensions = {".py", ".java", ".cpp", ".c", ".js", ".ts"}
        doc_extensions = {".pdf", ".docx", ".txt", ".doc", ".md"}

        for file_path in file_paths:
            ext = os.path.splitext(file_path)[1].lower()

            if ext in code_extensions:
                categorized["code"].append(file_path)
            elif ext in doc_extensions:
                categorized["document"].append(file_path)
            else:
                categorized["other"].append(file_path)

        return categorized
