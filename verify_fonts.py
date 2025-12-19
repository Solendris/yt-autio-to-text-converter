import sys
import os

# Add local directory to path so we can import app
sys.path.append(os.getcwd())

try:
    from app.services.pdf_service import ensure_font_exists, register_fonts, create_pdf_summary
    print("Imports successful")
    
    print("Checking font existence...")
    ensure_font_exists()
    
    font_path = os.path.join('app', 'static', 'fonts', 'Roboto-Regular.ttf')
    if os.path.exists(font_path):
        print(f"Font found at {font_path}")
    else:
        print("Font download failed!")
        sys.exit(1)
        
    print("Registering fonts...")
    if register_fonts():
        print("Fonts registered successfully")
    else:
        print("Font registration failed")
        sys.exit(1)
        
    print("Attempting to generate test PDF...")
    pdf = create_pdf_summary("Test Title ĄĆĘŁŃÓŚŹŻ", "Test Summary ąćęłńóśźż", "http://test.url", "TEST", "NORMAL")
    if pdf:
        print("PDF generated successfully (bytes in memory)")
    else:
        print("PDF generation returned None")

except Exception as e:
    print(f"Verification failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
