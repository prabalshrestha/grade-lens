#!/usr/bin/env python3
"""
Test the grading agent on Kaggle's Automatic Short Answer Grading Dataset
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
from src.models.grading_result import AssignmentGrade

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_kaggle_dataset():
    """Load the Kaggle dataset"""
    try:
        import kagglehub
        import pandas as pd
        
        logger.info("Downloading Kaggle dataset...")
        
        # Download the dataset (returns path to downloaded files)
        path = kagglehub.dataset_download("mubeenfurqanahmed/automatic-short-answer-grading-dataset")
        
        logger.info(f"Dataset downloaded to: {path}")
        
        # List files in the dataset
        import os
        files = os.listdir(path)
        logger.info(f"Files in dataset: {files}")
        
        # Find CSV file
        csv_files = [f for f in files if f.endswith('.csv')]
        if not csv_files:
            logger.error("No CSV files found in dataset")
            return None
        
        # Load the first CSV file
        csv_path = os.path.join(path, csv_files[0])
        logger.info(f"Loading: {csv_path}")
        
        df = pd.read_csv(csv_path)
        
        logger.info(f"Dataset loaded: {len(df)} records")
        logger.info(f"Columns: {list(df.columns)}")
        
        return df
    
    except ImportError:
        logger.error("kagglehub or pandas not installed. Install with: pip install kagglehub pandas")
        return None
    except Exception as e:
        logger.error(f"Error loading dataset: {str(e)}", exc_info=True)
        return None


def create_assignment_config_from_dataset(df, num_records=25):
    """
    Create an AssignmentConfig from the dataset
    
    The dataset typically has columns like:
    - question: The question text
    - student_answer: Student's answer
    - reference_answer: Model/correct answer
    - score: Ground truth score
    """
    
    # Inspect the first few rows
    logger.info("\nFirst 5 records:")
    logger.info(df.head())
    
    # Get unique questions (assuming the dataset has multiple answers per question)
    questions = []
    
    # Take first num_records
    subset = df.head(num_records)
    
    # Group by question if there are multiple questions
    if 'question' in df.columns:
        unique_questions = subset['question'].unique()
        logger.info(f"\nFound {len(unique_questions)} unique questions in first {num_records} records")
        
        for i, q_text in enumerate(unique_questions[:5], 1):  # Limit to 5 questions max
            # Get reference answer if available
            q_data = subset[subset['question'] == q_text].iloc[0]
            reference_answer = q_data.get('reference_answer', None) if 'reference_answer' in q_data else None
            
            question = QuestionConfig(
                id=f"question_{i}",
                text=q_text,
                points=10.0,
                answer_key=reference_answer,
                question_type="short_answer",
                rubric=RubricConfig(
                    no_submission=0.0,
                    attempted=5.0,
                    mostly_correct=8.0,
                    correct=10.0,
                    criteria=[
                        "Correctness of answer",
                        "Completeness of explanation",
                        "Use of proper terminology"
                    ],
                    instructions="Compare student answer to reference answer. Award full credit for correct and complete answers."
                )
            )
            questions.append(question)
    else:
        # If no question column, create a generic question
        logger.warning("No 'question' column found. Creating generic question.")
        questions.append(
            QuestionConfig(
                id="question_1",
                text="Short answer question",
                points=10.0,
                answer_key=None,
                question_type="short_answer",
                rubric=RubricConfig(
                    no_submission=0.0,
                    attempted=5.0,
                    mostly_correct=8.0,
                    correct=10.0,
                )
            )
        )
    
    # Create assignment config
    config = AssignmentConfig(
        assignment_id="kaggle_short_answer",
        assignment_name="Kaggle Short Answer Grading Dataset Test",
        course_code="TEST",
        term="2025",
        questions=questions,
        grading_instructions="Grade based on correctness and completeness compared to reference answer.",
        allow_partial_credit=True,
        created_by="Kaggle Dataset Test Script",
        version="1.0"
    )
    
    return config, subset


def grade_dataset_records(df, config, grading_mode="full", num_records=25):
    """
    Grade the dataset records using the grading agent
    """
    
    # Initialize grading agent
    logger.info(f"\nInitializing grading agent (mode: {grading_mode})...")
    agent = QAGradingAgent(OPENAI_API_KEY, model=OPENAI_MODEL, grading_mode=grading_mode)
    
    results = []
    subset = df.head(num_records)
    
    logger.info(f"\nGrading {len(subset)} records...")
    logger.info("=" * 80)
    
    for idx, row in subset.iterrows():
        try:
            # Extract student answer
            if 'student_answer' in row:
                submission_text = row['student_answer']
            elif 'answer' in row:
                submission_text = row['answer']
            else:
                # Try to find any column that might contain the answer
                answer_cols = [col for col in row.index if 'answer' in col.lower()]
                if answer_cols:
                    submission_text = row[answer_cols[0]]
                else:
                    logger.warning(f"No answer column found for record {idx}")
                    continue
            
            # Get ground truth score if available
            ground_truth_score = None
            if 'score' in row:
                ground_truth_score = row['score']
            elif 'grade' in row:
                ground_truth_score = row['grade']
            
            # Get student ID/name
            student_id = f"student_{idx}"
            student_name = row.get('student_id', f"Student {idx}")
            
            logger.info(f"\n[{idx + 1}/{len(subset)}] Grading: {student_name}")
            if ground_truth_score is not None:
                logger.info(f"  Ground truth score: {ground_truth_score}")
            
            # Grade the submission
            grade = agent.grade_submission(
                config,
                student_name=student_name,
                submission_text=str(submission_text),
                student_id=student_id,
                submission_file=None
            )
            
            if grade:
                logger.info(f"  AI Score: {grade.total_score}/{grade.max_score} ({grade.get_percentage():.1f}%)")
                
                result = {
                    'record_id': idx,
                    'student_name': student_name,
                    'submission': submission_text,
                    'ai_score': grade.total_score,
                    'max_score': grade.max_score,
                    'ai_percentage': grade.get_percentage(),
                    'ground_truth_score': ground_truth_score,
                    'questions': [
                        {
                            'question_id': q.question_id,
                            'score': q.score,
                            'max_score': q.max_score,
                            'reasoning': q.reasoning,
                            'feedback': q.feedback
                        }
                        for q in grade.questions
                    ]
                }
                results.append(result)
            else:
                logger.error(f"  Failed to grade record {idx}")
        
        except Exception as e:
            logger.error(f"Error grading record {idx}: {str(e)}", exc_info=True)
            continue
    
    logger.info("\n" + "=" * 80)
    logger.info(f"Completed grading {len(results)} records")
    
    return results


def save_results(results, grading_mode):
    """Save results to file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = "output/kaggle_dataset"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save detailed results
    output_file = os.path.join(output_dir, f"kaggle_results_{grading_mode}_{timestamp}.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\nResults saved to: {output_file}")
    
    # Calculate statistics
    if results:
        ai_scores = [r['ai_score'] for r in results]
        ground_truth_scores = [r['ground_truth_score'] for r in results if r['ground_truth_score'] is not None]
        
        stats = {
            'total_records': len(results),
            'ai_mean_score': sum(ai_scores) / len(ai_scores),
            'ai_min_score': min(ai_scores),
            'ai_max_score': max(ai_scores),
        }
        
        if ground_truth_scores:
            stats['ground_truth_mean'] = sum(ground_truth_scores) / len(ground_truth_scores)
            stats['ground_truth_min'] = min(ground_truth_scores)
            stats['ground_truth_max'] = max(ground_truth_scores)
            
            # Calculate correlation if both exist
            if len(ground_truth_scores) == len(ai_scores):
                # Simple correlation
                import numpy as np
                correlation = np.corrcoef(ai_scores, ground_truth_scores)[0, 1]
                stats['correlation'] = float(correlation)
        
        logger.info("\nStatistics:")
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")
        
        # Save stats
        stats_file = os.path.join(output_dir, f"kaggle_stats_{grading_mode}_{timestamp}.json")
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Statistics saved to: {stats_file}")
    
    return output_file


def main():
    """Main function"""
    
    logger.info("=" * 80)
    logger.info("KAGGLE DATASET GRADING TEST")
    logger.info("=" * 80)
    
    # Check API key
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not found. Please set it in your .env file")
        return 1
    
    # Load dataset
    df = load_kaggle_dataset()
    if df is None:
        return 1
    
    # Create assignment config
    config, subset = create_assignment_config_from_dataset(df, num_records=25)
    logger.info(f"\nCreated assignment config with {len(config.questions)} questions")
    
    # Test with different grading modes
    modes = ["basic", "standard", "full"]
    
    for mode in modes:
        logger.info("\n" + "=" * 80)
        logger.info(f"TESTING GRADING MODE: {mode.upper()}")
        logger.info("=" * 80)
        
        results = grade_dataset_records(subset, config, grading_mode=mode, num_records=25)
        
        if results:
            save_results(results, mode)
        
        logger.info(f"\nCompleted {mode} mode")
    
    logger.info("\n" + "=" * 80)
    logger.info("ALL TESTS COMPLETED")
    logger.info("=" * 80)
    logger.info("\nResults saved to: output/kaggle_dataset/")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

