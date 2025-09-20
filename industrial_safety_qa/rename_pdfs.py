import os
import json
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
SOURCES_FILE = BASE_DIR / 'data' / 'sources.json'
PDF_DIR = BASE_DIR / 'data' / 'pdfs'

def rename_pdfs_to_match_titles():
    """Rename PDF files to match document titles from sources.json"""
    # Load sources
    with open(SOURCES_FILE, 'r') as f:
        sources = json.load(f)
    
    # Get all PDF files
    pdf_files = list(PDF_DIR.glob("*.pdf"))
    
    print("Available PDF files:")
    for i, pdf_file in enumerate(pdf_files):
        print(f"{i+1}. {pdf_file.name}")
    
    print(f"\nDocument titles from sources.json:")
    for i, source in enumerate(sources):
        print(f"{i+1}. {source['title']}")
    
    # Try to match and rename
    print("\nMatching and renaning PDFs:")
    for source in sources:
        title = source['title']
        expected_filename = f"{title}.pdf".replace(" ", "_").replace("/", "_").replace(":", "").replace("—", "_")
        
        # Look for a PDF that might match this title
        for pdf_file in pdf_files:
            pdf_name = pdf_file.name.lower()
            title_lower = title.lower()
            
            # Check if this PDF might be the right one
            if (any(word in pdf_name for word in title_lower.split()[:3]) or
                pdf_name.startswith(title_lower[:10].replace(" ", "_"))):
                
                new_path = PDF_DIR / expected_filename
                if not new_path.exists():
                    try:
                        pdf_file.rename(new_path)
                        print(f"✓ Renamed '{pdf_file.name}' to '{expected_filename}'")
                    except Exception as e:
                        print(f"✗ Error renaming '{pdf_file.name}': {e}")
                else:
                    print(f"⚠ File '{expected_filename}' already exists, skipping")
                
                break
        else:
            print(f"✗ No PDF found for: {title}")

if __name__ == "__main__":
    rename_pdfs_to_match_titles()