#!/bin/bash
# ============================================================
# MyID Migration Dashboard PDF Generator (Shell Script)
# ============================================================
# PURPOSE: Converts the HTML print report to a PDF file using Chrome
# USAGE: bash scripts/generate_pdf.sh
# OUTPUT: Creates PDF in reports/ folder
# ============================================================

# Get the script's directory (works with symlinks)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Define paths
HTML_FILE="$PROJECT_ROOT/reports/MyID_Migration_Report_Print.html"
OUTPUT_PDF="$PROJECT_ROOT/reports/MyID_Migration_Report.pdf"
CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

echo "============================================================"
echo "MyID Migration Dashboard - PDF Generator"
echo "============================================================"

# Check if HTML file exists
if [ ! -f "$HTML_FILE" ]; then
    echo "❌ Error: HTML file not found at $HTML_FILE"
    echo "   Please run generate_dashboard.py first to create the HTML report."
    exit 1
fi

echo "📄 Reading HTML from: $HTML_FILE"

# Check if Chrome is installed
if [ ! -f "$CHROME_PATH" ]; then
    echo "❌ Error: Google Chrome not found at $CHROME_PATH"
    echo "   Please install Google Chrome or use the manual method."
    exit 1
fi

# Generate PDF using Chrome headless
echo "🔄 Converting HTML to PDF using Chrome..."

"$CHROME_PATH" --headless --disable-gpu --print-to-pdf="$OUTPUT_PDF" --no-pdf-header-footer --print-to-pdf-no-header "file://$HTML_FILE" 2>/dev/null

# Check if PDF was created
if [ -f "$OUTPUT_PDF" ]; then
    # Get file size
    FILE_SIZE=$(du -k "$OUTPUT_PDF" | cut -f1)
    
    echo "============================================================"
    echo "✅ PDF Generated Successfully!"
    echo "============================================================"
    echo "📍 Location: $OUTPUT_PDF"
    echo "📊 File Size: ${FILE_SIZE} KB"
    echo "🕐 Generated: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "============================================================"
    echo ""
    echo "💡 Tip: You can now share this PDF with your team!"
    exit 0
else
    echo "❌ Error: PDF generation failed"
    echo ""
    echo "============================================================"
    echo "📋 Manual PDF Generation Instructions"
    echo "============================================================"
    echo ""
    echo "Please follow these steps to create the PDF:"
    echo ""
    echo "1. Open the file in your browser:"
    echo "   $HTML_FILE"
    echo ""
    echo "2. Press Cmd+P (or File → Print)"
    echo ""
    echo "3. In the print dialog:"
    echo "   - Click the 'PDF' dropdown in the bottom-left"
    echo "   - Select 'Save as PDF'"
    echo "   - Save as: $OUTPUT_PDF"
    echo ""
    echo "4. Click 'Save'"
    echo ""
    echo "============================================================"
    exit 1
fi
