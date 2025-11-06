"""
Output manager for handling grading results export to JSON and CSV
"""

import os
import json
import pandas as pd
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from ..models.grading_result import AssignmentGrade

logger = logging.getLogger(__name__)


class OutputManager:
    """Manages output of grading results in multiple formats"""

    def __init__(self, output_base_dir: str = "output"):
        self.output_base_dir = output_base_dir

    def save_results(
        self,
        assignment_id: str,
        grades: List[AssignmentGrade],
        include_csv: bool = True,
        include_json: bool = True,
        include_detailed_json: bool = True,
    ) -> Dict[str, str]:
        """
        Save grading results to files
        
        Args:
            assignment_id: Assignment identifier
            grades: List of AssignmentGrade objects
            include_csv: Whether to generate CSV file
            include_json: Whether to generate summary JSON
            include_detailed_json: Whether to generate detailed JSON
            
        Returns:
            Dictionary mapping format to file path
        """
        # Create assignment-specific output directory
        output_dir = os.path.join(self.output_base_dir, assignment_id)
        os.makedirs(output_dir, exist_ok=True)

        saved_files = {}

        try:
            # Generate timestamp for filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Save detailed JSON (complete data)
            if include_detailed_json:
                detailed_json_path = os.path.join(
                    output_dir, f"grading_results_detailed_{timestamp}.json"
                )
                self._save_detailed_json(grades, detailed_json_path)
                saved_files["detailed_json"] = detailed_json_path
                logger.info(f"Saved detailed JSON: {detailed_json_path}")

            # Save CSV (flattened for spreadsheet)
            if include_csv:
                csv_path = os.path.join(output_dir, f"grading_results_{timestamp}.csv")
                self._save_csv(grades, csv_path)
                saved_files["csv"] = csv_path
                logger.info(f"Saved CSV: {csv_path}")

            # Save summary JSON (aggregate statistics)
            if include_json:
                summary_json_path = os.path.join(
                    output_dir, f"grading_summary_{timestamp}.json"
                )
                self._save_summary_json(grades, summary_json_path, assignment_id)
                saved_files["summary_json"] = summary_json_path
                logger.info(f"Saved summary JSON: {summary_json_path}")

            # Also save a "latest" version without timestamp
            if include_csv:
                latest_csv = os.path.join(output_dir, "grading_results_latest.csv")
                self._save_csv(grades, latest_csv)
                saved_files["latest_csv"] = latest_csv

            logger.info(f"Successfully saved results for {len(grades)} submissions")
            return saved_files

        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            raise

    def _save_detailed_json(self, grades: List[AssignmentGrade], file_path: str):
        """Save detailed JSON with all grading data"""
        data = {
            "grading_session": {
                "timestamp": datetime.now().isoformat(),
                "total_submissions": len(grades),
            },
            "results": [grade.to_dict() for grade in grades],
        }

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

    def _save_csv(self, grades: List[AssignmentGrade], file_path: str):
        """Save CSV with flattened grading data"""
        # Convert all grades to flat dictionaries
        flat_data = [grade.to_flat_dict() for grade in grades]

        # Create DataFrame
        df = pd.DataFrame(flat_data)

        # Reorder columns for better readability
        priority_columns = [
            "student_name",
            "student_id",
            "total_score",
            "max_score",
            "percentage",
            "letter_grade",
        ]

        # Get all columns
        all_columns = df.columns.tolist()

        # Reorder: priority columns first, then the rest
        ordered_columns = [col for col in priority_columns if col in all_columns]
        ordered_columns += [col for col in all_columns if col not in ordered_columns]

        df = df[ordered_columns]

        # Save to CSV
        df.to_csv(file_path, index=False)

    def _save_summary_json(
        self, grades: List[AssignmentGrade], file_path: str, assignment_id: str
    ):
        """Save summary JSON with statistics"""
        if not grades:
            summary = {
                "assignment_id": assignment_id,
                "timestamp": datetime.now().isoformat(),
                "total_submissions": 0,
            }
        else:
            scores = [grade.total_score for grade in grades]
            max_possible = grades[0].max_score if grades else 0

            summary = {
                "assignment_id": assignment_id,
                "assignment_name": grades[0].assignment_name if grades else None,
                "timestamp": datetime.now().isoformat(),
                "statistics": {
                    "total_submissions": len(grades),
                    "max_possible_score": max_possible,
                    "average_score": sum(scores) / len(scores),
                    "median_score": sorted(scores)[len(scores) // 2],
                    "highest_score": max(scores),
                    "lowest_score": min(scores),
                    "average_percentage": (sum(scores) / len(scores) / max_possible * 100)
                    if max_possible > 0
                    else 0,
                    "students_with_zero": sum(1 for s in scores if s == 0),
                    "students_with_full_marks": sum(
                        1 for s in scores if s >= max_possible
                    ),
                },
                "grade_distribution": self._calculate_grade_distribution(grades),
                "question_statistics": self._calculate_question_statistics(grades),
                "flagged_for_review": [
                    {
                        "student_name": grade.student_name,
                        "reason": grade.review_reason,
                        "score": grade.total_score,
                    }
                    for grade in grades
                    if grade.requires_human_review
                ],
            }

        with open(file_path, "w") as f:
            json.dump(summary, f, indent=2)

    def _calculate_grade_distribution(self, grades: List[AssignmentGrade]) -> Dict[str, int]:
        """Calculate distribution of letter grades"""
        distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}

        for grade in grades:
            letter = grade.get_letter_grade()
            if letter in distribution:
                distribution[letter] += 1

        return distribution

    def _calculate_question_statistics(
        self, grades: List[AssignmentGrade]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate statistics per question"""
        if not grades:
            return {}

        question_stats = {}

        # Get all unique question IDs
        question_ids = set()
        for grade in grades:
            for q in grade.questions:
                question_ids.add(q.question_id)

        # Calculate stats for each question
        for qid in question_ids:
            scores = []
            max_score = 0

            for grade in grades:
                for q in grade.questions:
                    if q.question_id == qid:
                        scores.append(q.score)
                        max_score = q.max_score
                        break

            if scores:
                question_stats[qid] = {
                    "max_score": max_score,
                    "average_score": sum(scores) / len(scores),
                    "median_score": sorted(scores)[len(scores) // 2],
                    "highest_score": max(scores),
                    "lowest_score": min(scores),
                    "average_percentage": (sum(scores) / len(scores) / max_score * 100)
                    if max_score > 0
                    else 0,
                    "zero_scores": sum(1 for s in scores if s == 0),
                    "full_scores": sum(1 for s in scores if s >= max_score),
                }

        return question_stats

    def get_summary_stats(self, grades: List[AssignmentGrade]) -> Dict[str, Any]:
        """
        Get summary statistics (for console output)
        
        Args:
            grades: List of AssignmentGrade objects
            
        Returns:
            Dictionary with summary statistics
        """
        if not grades:
            return {
                "total_students": 0,
                "average_score": 0,
                "highest_score": 0,
                "lowest_score": 0,
                "students_with_zero": 0,
                "students_with_full_marks": 0,
            }

        scores = [grade.total_score for grade in grades]
        max_possible = grades[0].max_score

        return {
            "total_students": len(grades),
            "max_possible_score": max_possible,
            "average_score": sum(scores) / len(scores),
            "average_percentage": (sum(scores) / len(scores) / max_possible * 100)
            if max_possible > 0
            else 0,
            "highest_score": max(scores),
            "lowest_score": min(scores),
            "students_with_zero": sum(1 for s in scores if s == 0),
            "students_with_full_marks": sum(1 for s in scores if s >= max_possible),
            "requires_review": sum(1 for g in grades if g.requires_human_review),
        }

    def print_summary(self, grades: List[AssignmentGrade]):
        """Print summary statistics to console"""
        stats = self.get_summary_stats(grades)

        print("\n" + "=" * 80)
        print("GRADING SUMMARY")
        print("=" * 80)

        if stats["total_students"] == 0:
            print("No submissions graded.")
            print("=" * 80)
            return

        print(f"Total submissions graded: {stats['total_students']}")
        print(f"Maximum possible score: {stats['max_possible_score']:.1f}")
        print(f"\nScore Statistics:")
        print(f"  Average score: {stats['average_score']:.2f} ({stats['average_percentage']:.1f}%)")
        print(f"  Highest score: {stats['highest_score']:.2f}")
        print(f"  Lowest score: {stats['lowest_score']:.2f}")
        print(f"\nDistribution:")
        print(f"  Students with zero points: {stats['students_with_zero']}")
        print(f"  Students with full marks: {stats['students_with_full_marks']}")

        if stats["requires_review"] > 0:
            print(f"\nFlagged for human review: {stats['requires_review']}")

        print("=" * 80 + "\n")

    def export_for_lms(
        self, grades: List[AssignmentGrade], file_path: str, lms_format: str = "canvas"
    ):
        """
        Export grades in LMS-compatible format
        
        Args:
            grades: List of grades
            file_path: Output file path
            lms_format: LMS type ('canvas', 'blackboard', etc.)
        """
        if lms_format.lower() == "canvas":
            # Canvas CSV format
            data = []
            for grade in grades:
                data.append(
                    {
                        "Student": grade.student_name,
                        "ID": grade.student_id or "",
                        "SIS User ID": grade.student_id or "",
                        "SIS Login ID": "",
                        "Section": "",
                        "Score": grade.total_score,
                        "Comments": grade.overall_comment or "",
                    }
                )

            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False)
            logger.info(f"Exported Canvas-format CSV: {file_path}")

        else:
            logger.warning(f"LMS format '{lms_format}' not yet implemented")

