import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL", "gpt-4o-mini"
)  # Default to gpt-4o-mini if not specified

if not OPENAI_API_KEY:
    raise ValueError("Please set your OPENAI_API_KEY in the .env file")

# Grading Configuration (per question - 15 points each)
GRADING_CRITERIA = {
    "no_submission": 0,
    "attempted": 7.5,  # Half marks for attempt (50% of 15 points)
    "correct": 15.0,  # Full marks for correct solution
    "mostly_correct": 14.0,  # Deduct 1 point for mostly correct but not complete
}

# File paths
SUBMISSIONS_DIR = "submissions"
OUTPUT_DIR = "output"
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "grading_results.csv")
