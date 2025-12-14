#!/usr/bin/env python3
"""
Grade Lens CLI wrapper - Forwards commands to backend/cli.py
This allows you to run CLI commands from the project root.

Usage:
    python grade-lens-cli.py --list
    python grade-lens-cli.py --assignment cs361_hw5
    
Or directly:
    python backend/cli.py --list
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Import and run the CLI
from cli import main

if __name__ == "__main__":
    sys.exit(main())

