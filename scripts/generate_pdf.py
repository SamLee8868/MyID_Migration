#!/usr/bin/env python3
"""
============================================================
MyID Migration Dashboard PDF Generator
============================================================
PURPOSE: Converts the HTML print report to a PDF file
USAGE: python3 scripts/generate_pdf.py
OUTPUT: Creates PDF in reports/ folder
METHOD: Uses macOS Safari to generate PDF (no additional tools needed)
============================================================
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path
import time

# ============================================================
# SECTION: File Paths
# TO UPDATE: Change these paths if you move files around
# ============================================================
# Get the project root directory (parent of scripts/)
PROJECT_ROOT = Path(__file__).parent.parent

# Input HTML file (the print-optimized version)
HTML_FILE = PROJECT_ROOT / "reports" / "MyID_Migration_Report_Print.html"

# Output PDF file
OUTPUT_PDF = PROJECT_ROOT / "reports" / "MyID_Migration_Report.pdf"

# ============================================================
# SECTION: PDF Generation using macOS tools
# PURPOSE: Converts HTML to PDF using Safari/Chrome print
# ============================================================
def generate_pdf_with_browser():
    """
    Converts the print-optimized HTML report to PDF format using browser
    """
    print("=" * 60)
    print("MyID Migration Dashboard - PDF Generator")
    print("=" * 60)
    
    # Check if HTML file exists
    if not HTML_FILE.exists():
        print(f"❌ Error: HTML file not found at {HTML_FILE}")
        print("   Please run generate_dashboard.py first to create the HTML report.")
        return False
    
    print(f"📄 Reading HTML from: {HTML_FILE}")
    print("🔄 Opening in browser...")
    
    # Get absolute path for the HTML file
    html_path = HTML_FILE.absolute()
    pdf_path = OUTPUT_PDF.absolute()
    
    # AppleScript to open in Safari and save as PDF
    applescript = f'''
    tell application "Safari"
        activate
        open location "file://{html_path}"
        delay 2
        
        tell application "System Events"
            keystroke "p" using {{command down}}
            delay 1
            keystroke "p" using {{command down}}
            delay 0.5
            keystroke "{pdf_path}"
            delay 0.5
            keystroke return
            delay 1
        end tell
        
        quit
    end tell
    '''
    
    try:
        # Method 1: Try using cupsfilter (built into macOS)
        print("🔄 Attempting to convert using cupsfilter...")
        result = subprocess.run(
            ['cupsfilter', str(html_path)],
            capture_output=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # Write the PDF output
            with open(pdf_path, 'wb') as f:
                f.write(result.stdout)
            
            # Get file size for display
            pdf_size = OUTPUT_PDF.stat().st_size
            pdf_size_kb = pdf_size / 1024
            
            print("=" * 60)
            print("✅ PDF Generated Successfully!")
            print("=" * 60)
            print(f"📍 Location: {OUTPUT_PDF}")
            print(f"📊 File Size: {pdf_size_kb:.1f} KB")
            print(f"🕐 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)
            print("\n💡 Tip: You can now share this PDF with your team!")
            return True
        else:
            raise Exception("cupsfilter failed")
            
    except Exception as e:
        print(f"⚠️  Automated conversion not available: {str(e)}")
        print("\n" + "=" * 60)
        print("📋 Manual PDF Generation Instructions")
        print("=" * 60)
        print("\nPlease follow these steps to create the PDF:\n")
        print("1. Open the file in your browser:")
        print(f"   {HTML_FILE}")
        print("\n2. Press Cmd+P (or File → Print)")
        print("\n3. In the print dialog:")
        print("   - Click the 'PDF' dropdown in the bottom-left")
        print("   - Select 'Save as PDF'")
        print(f"   - Save as: {OUTPUT_PDF}")
        print("\n4. Click 'Save'")
        print("\n" + "=" * 60)
        print("\n💡 The HTML file is already optimized for PDF printing!")
        
        # Open the HTML file in the default browser
        print("\n🌐 Opening the HTML file in your browser now...")
        subprocess.run(['open', str(HTML_FILE)])
        
        return False


# ============================================================
# SECTION: Main Execution
# ============================================================
if __name__ == "__main__":
    success = generate_pdf_with_browser()
    exit(0 if success else 1)
