#!/usr/bin/env python3
"""
Test grading agent on Kaggle dataset - 25 records with all 3 grading modes
"""

import os
import sys
import json
import logging
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from config import OPENAI_API_KEY, OPENAI_MODEL
from src.agents.qa_grading_agent import QAGradingAgent
from src.models.assignment_config import AssignmentConfig, QuestionConfig, RubricConfig

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 80)
    logger.info("KAGGLE DATASET TEST - 25 Records x 3 Grading Modes")
    logger.info("=" * 80)

    try:
        import kagglehub
        import pandas as pd
        import numpy as np

        # Load dataset
        logger.info("\nLoading dataset...")
        path = kagglehub.dataset_download(
            "mubeenfurqanahmed/automatic-short-answer-grading-dataset"
        )
        csv_path = os.path.join(
            path, [f for f in os.listdir(path) if f.endswith(".csv")][0]
        )
        df = pd.read_csv(csv_path)

        logger.info(f"Dataset: {len(df)} total records")
        logger.info(f"Columns: {list(df.columns)}")

        # Take first 25 records
        df_subset = df.head(25)
        logger.info(f"\nTesting on first {len(df_subset)} records")

        # Get question and model answer from first record
        first_row = df.iloc[0]
        question_text = first_row["questions"]
        model_answer = first_row["model_answer"]

        logger.info(f"\nQuestion: {question_text}")
        logger.info(f"Model answer: {model_answer}")

        # Create config with improved rubric for better alignment
        config = AssignmentConfig(
            assignment_id="kaggle_test",
            assignment_name="Kaggle Short Answer Grading Test",
            questions=[
                QuestionConfig(
                    id="q1",
                    text=question_text,
                    points=10.0,
                    answer_key=model_answer,
                    rubric=RubricConfig(
                        no_submission=0.0,
                        attempted=3.0,
                        mostly_correct=7.0,
                        correct=10.0,
                        criteria=[
                            "Answer demonstrates understanding of the concept",
                            "Key terms or ideas are present (even if not perfectly worded)",
                            "Explanation is relevant to the question",
                            "Partial credit for partially correct elements",
                        ],
                        instructions="""Grade generously with partial credit in mind. The model answer is a reference, not the only acceptable answer.
                        
Scoring guidelines:
- 9-10 points: Answer captures the main concept accurately, even if wording differs from model answer
- 7-8 points: Answer shows good understanding with minor gaps or imprecise terminology
- 5-6 points: Answer demonstrates partial understanding or includes some correct elements
- 3-4 points: Answer shows minimal understanding or is only tangentially related
- 1-2 points: Answer is present but mostly incorrect or off-topic
- 0 points: No answer or completely irrelevant

Focus on the student's understanding of the concept rather than exact wording. Award points for correct ideas even if expressed differently than the model answer.""",
                    ),
                )
            ],
            total_points=10.0,
            allow_partial_credit=True,
        )

        # Test all three modes
        modes = ["basic", "standard", "full"]
        all_results = {}

        for mode in modes:
            logger.info("\n" + "=" * 80)
            logger.info(f"GRADING MODE: {mode.upper()}")
            logger.info("=" * 80)

            agent = QAGradingAgent(
                OPENAI_API_KEY, model=OPENAI_MODEL, grading_mode=mode
            )
            results = []

            for idx, row in df_subset.iterrows():
                submission = str(row["student_answer"])
                teacher_score = row["teacher_marks"]
                total_marks = row["total_marks"]

                logger.info(f"\n[{idx+1}/25] Grading...")

                grade = agent.grade_submission(
                    config,
                    student_name=f"Student_{idx}",
                    submission_text=submission,
                    student_id=str(idx),
                )

                if grade:
                    # Normalize scores to 0-10 scale
                    ai_score_normalized = grade.total_score
                    teacher_score_normalized = (teacher_score / total_marks) * 10.0

                    logger.info(
                        f"  AI: {ai_score_normalized:.1f}/10, Teacher: {teacher_score_normalized:.1f}/10"
                    )

                    results.append(
                        {
                            "id": int(idx),
                            "submission": submission,
                            "ai_score": float(ai_score_normalized),
                            "teacher_score": float(teacher_score_normalized),
                            "teacher_score_raw": int(teacher_score),
                            "total_marks_raw": int(total_marks),
                            "feedback": (
                                grade.questions[0].feedback if grade.questions else None
                            ),
                        }
                    )

            all_results[mode] = results

            # Calculate statistics
            ai_scores = [r["ai_score"] for r in results]
            teacher_scores = [r["teacher_score"] for r in results]

            correlation = np.corrcoef(ai_scores, teacher_scores)[0, 1]
            mae = np.mean(np.abs(np.array(ai_scores) - np.array(teacher_scores)))

            logger.info(f"\n{mode.upper()} MODE STATISTICS:")
            logger.info(f"  AI Mean: {np.mean(ai_scores):.2f}")
            logger.info(f"  Teacher Mean: {np.mean(teacher_scores):.2f}")
            logger.info(f"  Correlation: {correlation:.3f}")
            logger.info(f"  MAE: {mae:.2f}")

        # Save results
        output_dir = "output/kaggle_dataset"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        output_file = os.path.join(output_dir, f"kaggle_25_records_{timestamp}.json")
        with open(output_file, "w") as f:
            json.dump(all_results, f, indent=2)

        logger.info(f"\n✓ Results saved to: {output_file}")

        # Create comparison summary
        summary = {
            "dataset": "Kaggle Automatic Short Answer Grading",
            "records_tested": 25,
            "question": question_text,
            "model_answer": model_answer,
            "modes": {},
        }

        for mode, results in all_results.items():
            ai_scores = [r["ai_score"] for r in results]
            teacher_scores = [r["teacher_score"] for r in results]
            correlation = np.corrcoef(ai_scores, teacher_scores)[0, 1]
            mae = np.mean(np.abs(np.array(ai_scores) - np.array(teacher_scores)))

            summary["modes"][mode] = {
                "ai_mean": float(np.mean(ai_scores)),
                "ai_std": float(np.std(ai_scores)),
                "teacher_mean": float(np.mean(teacher_scores)),
                "teacher_std": float(np.std(teacher_scores)),
                "correlation": float(correlation),
                "mae": float(mae),
            }

        summary_file = os.path.join(output_dir, f"kaggle_summary_{timestamp}.json")
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        logger.info(f"✓ Summary saved to: {summary_file}")

        # Print comparison
        logger.info("\n" + "=" * 80)
        logger.info("COMPARISON ACROSS MODES")
        logger.info("=" * 80)
        logger.info(f"{'Mode':<12} {'AI Mean':<10} {'Correlation':<12} {'MAE':<10}")
        logger.info("-" * 80)
        for mode in modes:
            stats = summary["modes"][mode]
            logger.info(
                f"{mode:<12} {stats['ai_mean']:<10.2f} {stats['correlation']:<12.3f} {stats['mae']:<10.2f}"
            )

        logger.info("\n✓ Test completed successfully!")
        return 0

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
