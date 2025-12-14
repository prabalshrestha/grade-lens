#!/bin/bash
# Script to run grading comparison across all three modes
# Usage: ./run_grading_comparison.sh <assignment_id>

if [ -z "$1" ]; then
    echo "Usage: ./run_grading_comparison.sh <assignment_id>"
    echo "Example: ./run_grading_comparison.sh cs361_hw7"
    exit 1
fi

ASSIGNMENT="$1"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=========================================================================="
echo "GRADING MODE COMPARISON EXPERIMENT"
echo "=========================================================================="
echo "Assignment: $ASSIGNMENT"
echo "Timestamp: $TIMESTAMP"
echo ""
echo "This script will run grading in three modes:"
echo "  1. BASIC - Rubric only (no criteria, instructions, or answer key)"
echo "  2. STANDARD - Rubric + criteria + instructions (no answer key)"
echo "  3. FULL - Everything including answer key"
echo ""
echo "=========================================================================="
echo ""

# Run basic mode
echo "=========================================================================="
echo "[1/3] Running BASIC mode..."
echo "=========================================================================="
python main.py --assignment "$ASSIGNMENT" --grading-mode basic
if [ $? -eq 0 ]; then
    echo "✓ Basic mode completed successfully"
else
    echo "✗ Basic mode failed"
fi
echo ""

# Run standard mode
echo "=========================================================================="
echo "[2/3] Running STANDARD mode..."
echo "=========================================================================="
python main.py --assignment "$ASSIGNMENT" --grading-mode standard
if [ $? -eq 0 ]; then
    echo "✓ Standard mode completed successfully"
else
    echo "✗ Standard mode failed"
fi
echo ""

# Run full mode
echo "=========================================================================="
echo "[3/3] Running FULL mode..."
echo "=========================================================================="
python main.py --assignment "$ASSIGNMENT" --grading-mode full
if [ $? -eq 0 ]; then
    echo "✓ Full mode completed successfully"
else
    echo "✗ Full mode failed"
fi
echo ""

# Summary
echo "=========================================================================="
echo "COMPARISON COMPLETE"
echo "=========================================================================="
echo ""
echo "Results saved to:"
echo "  Basic mode:    output/${ASSIGNMENT}_basic/"
echo "  Standard mode: output/${ASSIGNMENT}_standard/"
echo "  Full mode:     output/${ASSIGNMENT}/"
echo ""
echo "Compare the following files:"
echo "  - grading_results_latest.csv  (scores and grades)"
echo "  - grading_summary_*.json      (statistics)"
echo "  - grading_results_detailed_*.json (detailed feedback)"
echo ""
echo "To analyze results:"
echo "  1. Open the CSV files in a spreadsheet application"
echo "  2. Compare score distributions across modes"
echo "  3. Review detailed JSON for feedback quality differences"
echo "  4. Check summary JSON for statistics (mean, std dev, etc.)"
echo ""
echo "=========================================================================="

