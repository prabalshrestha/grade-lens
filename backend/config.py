"""
Global configuration for Grade Lens grading system
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Get the project root directory (parent of backend)
PROJECT_ROOT = Path(__file__).parent.parent

# Load environment variables from backend directory (where .env now lives)
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# ============================================================================
# OpenAI Configuration
# ============================================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not OPENAI_API_KEY:
    import warnings
    warnings.warn(
        "OPENAI_API_KEY not found in environment variables. "
        "Please set it in your .env file or environment."
    )

# ============================================================================
# Directory Paths
# ============================================================================
# Base directories (relative to project root)
ASSIGNMENTS_BASE_DIR = os.path.join(PROJECT_ROOT, os.getenv("ASSIGNMENTS_BASE_DIR", "assignments"))
SUBMISSIONS_BASE_DIR = os.path.join(PROJECT_ROOT, os.getenv("SUBMISSIONS_BASE_DIR", "submissions"))
OUTPUT_BASE_DIR = os.path.join(PROJECT_ROOT, os.getenv("OUTPUT_BASE_DIR", "output"))

# ============================================================================
# Logging Configuration
# ============================================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ============================================================================
# LLM Parameters
# ============================================================================
# Temperature for LLM (lower = more consistent grading)
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))

# Maximum retries for API calls
MAX_API_RETRIES = int(os.getenv("MAX_API_RETRIES", "3"))

# ============================================================================
# Grading Configuration
# ============================================================================
# Default letter grade scale (percentage thresholds)
DEFAULT_GRADE_SCALE = {
    "A": 90.0,
    "B": 80.0,
    "C": 70.0,
    "D": 60.0,
    "F": 0.0,
}

# ============================================================================
# Output Configuration
# ============================================================================
# Include timestamp in output filenames
INCLUDE_TIMESTAMP = os.getenv("INCLUDE_TIMESTAMP", "true").lower() == "true"

# Save detailed JSON by default
SAVE_DETAILED_JSON = os.getenv("SAVE_DETAILED_JSON", "true").lower() == "true"

# Save CSV by default
SAVE_CSV = os.getenv("SAVE_CSV", "true").lower() == "true"

# Save summary JSON by default
SAVE_SUMMARY_JSON = os.getenv("SAVE_SUMMARY_JSON", "true").lower() == "true"

# ============================================================================
# File Processing Configuration
# ============================================================================
# Supported file extensions for submissions
SUPPORTED_EXTENSIONS = [".pdf", ".docx", ".txt"]

# Maximum file size in MB (for safety)
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
