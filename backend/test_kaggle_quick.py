#!/usr/bin/env python3
"""
Quick test of the grading agent on Kaggle dataset (first 5 records, full mode only)
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from config import OPENAI_API_KEY, OPENAI_MODEL
from src.agents.qa_grading_agent import QAGradingAgent
from src.models.assignment_config import AssignmentConfig, QuestionConfig, RubricConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Main function"""
    
    logger.info("=" * 80)
    logger.info("QUICK KAGGLE DATASET TEST (5 records, full mode)")
    logger.info("=" * 80)
    
    try:
        import kagglehub
        import pandas as pd
        
        # Download dataset
        logger.info("\nDownloading dataset...")
        path = kagglehub.dataset_download("mubeenfurqanahmed/automatic-short-answer-grading-dataset")
        logger.info(f"Downloaded to: {path}")
        
        # Load CSV
        files = [f for f in os.listdir(path) if f.endswith('.csv')]
        if not files:
            logger.error("No CSV files found")
            return 1
        
        csv_path = os.path.join(path, files[0])
        logger.info(f"Loading: {csv_path}")
        df = pd.read_csv(csv_path)
        
        logger.info(f"\nDataset info:")
        logger.info(f"  Total records: {len(df)}")
        logger.info(f"  Columns: {list(df.columns)}")
        logger.info(f"\nFirst record:")
        logger.info(df.head(1).to_dict('records')[0])
        
        # Get first question and model answer from dataset
        first_row = df.iloc[0]
        question_text = first_row.get('questions', 'Short answer question')
        model_answer = first_row.get('model_answer', None)
        
        # Create simple config
        config = AssignmentConfig(
            assignment_id="kaggle_test",
            assignment_name="Kaggle Short Answer Test",
            questions=[
                QuestionConfig(
                    id="q1",
                    text=question_text,
                    points=10.0,
                    answer_key=model_answer,
                    rubric=RubricConfig(
                        no_submission=0.0,
                        attempted=5.0,
                        mostly_correct=8.0,
                        correct=10.0,
                        criteria=[
                            "Correctness compared to model answer",
                            "Completeness of explanation",
                            "Use of proper terminology"
                        ],
                        instructions="Compare student answer to model answer. Award points based on accuracy and completeness."
                    )
                )
            ],
            total_points=10.0,
            allow_partial_credit=True
        )
        
        # Initialize agent
        agent = QAGradingAgent(OPENAI_API_KEY, model=OPENAI_MODEL, grading_mode="full")
        
        # Grade first 5 records
        results = []
        for idx in range(min(5, len(df))):
            row = df.iloc[idx]
            
            # Find answer column
            answer_col = None
            for col in ['student_answer', 'answer', 'response', 'text']:
                if col in df.columns:
                    answer_col = col
                    break
            
            if not answer_col:
                logger.error(f"Could not find answer column. Columns: {list(df.columns)}")
                return 1
            
            submission = str(row[answer_col])
            logger.info(f"\n[{idx+1}/5] Grading record {idx}")
            logger.info(f"  Answer: {submission[:100]}...")
            
            grade = agent.grade_submission(
                config,
                student_name=f"Student_{idx}",
                submission_text=submission,
                student_id=str(idx)
            )
            
            if grade:
                logger.info(f"  Score: {grade.total_score}/{grade.max_score}")
                results.append({
                    'id': idx,
                    'score': grade.total_score,
                    'feedback': grade.questions[0].feedback if grade.questions else None
                })
        
        # Save results
        output_dir = "output/kaggle_dataset"
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "quick_test_results.json")
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"\n✓ Results saved to: {output_file}")
        logger.info(f"✓ Graded {len(results)} records successfully")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

