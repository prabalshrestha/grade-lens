import pandas as pd
import os
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class CSVManager:
    """Handles CSV operations for storing grading results"""

    def __init__(self, output_file: str):
        self.output_file = output_file
        self.results: List[Dict] = []

    def add_grading_result(
        self, student_name: str, filename: str, grading_result: Dict, total_score: float
    ):
        """Add a grading result to the collection"""
        # Extract student ID from filename (2nd part after splitting by underscore)
        student_id = self._extract_student_id(filename)
        canvas_url = f"https://boisestatecanvas.instructure.com/courses/42497/gradebook/speed_grader?assignment_id=1479096&student_id={student_id}"

        result_entry = {
            "student_name": student_name,
            "filename": filename,
            "student_id": student_id,
            "url": canvas_url,
            "total_score": total_score,
            "grading_details": grading_result,
        }
        self.results.append(result_entry)
        logger.info(f"Added grading result for {student_name}: {total_score} points")

    def save_to_csv(self):
        """Save all results to CSV file"""
        try:
            # Create a flattened version for CSV
            csv_data = []

            for result in self.results:
                row = {
                    "student_name": result["student_name"],
                    "filename": result["filename"],
                    "student_id": result["student_id"],
                    "url": result["url"],
                    "total_score": result["total_score"],
                }

                # Add individual question scores
                grading_details = result["grading_details"]
                for question, details in grading_details.items():
                    if isinstance(details, dict):
                        row[f"{question}_score"] = details.get("score", 0)
                        row[f"{question}_reasoning"] = details.get("reasoning", "")
                    else:
                        row[f"{question}_score"] = 0
                        row[f"{question}_reasoning"] = "Error in grading"

                csv_data.append(row)

            # Create DataFrame and save to CSV
            df = pd.DataFrame(csv_data)
            df.to_csv(self.output_file, index=False)
            logger.info(f"Results saved to {self.output_file}")

            # Also save detailed results as JSON for reference
            json_file = self.output_file.replace(".csv", "_detailed.json")
            import json

            with open(json_file, "w") as f:
                json.dump(self.results, f, indent=2)
            logger.info(f"Detailed results saved to {json_file}")

        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")
            raise

    def get_summary_stats(self) -> Dict:
        """Get summary statistics of grading results"""
        if not self.results:
            return {}

        total_students = len(self.results)
        scores = [result["total_score"] for result in self.results]

        stats = {
            "total_students": total_students,
            "average_score": sum(scores) / len(scores) if scores else 0,
            "highest_score": max(scores) if scores else 0,
            "lowest_score": min(scores) if scores else 0,
            "students_with_zero": sum(1 for score in scores if score == 0),
            "students_with_full_marks": sum(1 for score in scores if score >= 1.0),
        }

        return stats

    def _extract_student_id(self, filename: str) -> str:
        """Extract student ID from filename (2nd part, or 3rd if 2nd is 'LATE')"""
        try:
            # Remove file extension first
            name_without_ext = filename.split(".")[0]
            # Split by underscore
            parts = name_without_ext.split("_")

            if len(parts) >= 2:
                # Check if 2nd part is 'LATE', then use 3rd part as student ID
                if parts[1] == "LATE" and len(parts) >= 3:
                    return parts[2]  # 3rd part is the student ID for LATE submissions
                else:
                    return parts[
                        1
                    ]  # 2nd part is the student ID for regular submissions
            else:
                logger.warning(
                    f"Could not extract student ID from filename: {filename}"
                )
                return "unknown"
        except Exception as e:
            logger.error(f"Error extracting student ID from {filename}: {str(e)}")
            return "unknown"
