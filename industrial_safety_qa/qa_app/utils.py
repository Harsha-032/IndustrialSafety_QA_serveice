import json
import PyPDF2
import os
from pathlib import Path
from django.conf import settings
from .models import Document, DocumentChunk
import re

def load_sources():
    """Load document sources from sources.json"""
    try:
        with open(settings.SOURCES_FILE, 'r') as f:
            sources = json.load(f)
        
        print(f"Loaded {len(sources)} sources from sources.json")
        
        for source in sources:
            doc, created = Document.objects.get_or_create(
                title=source['title'],
                defaults={'url': source['url'], 'processed': False}
            )
            if not created:
                doc.url = source['url']
                doc.processed = False  # Reset processed flag
                doc.save()
        
        return Document.objects.all()
    except Exception as e:
        print(f"Error loading sources: {e}")
        return Document.objects.all()

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file with improved parsing"""
    text = ""
    try:
        print(f"Attempting to extract text from: {pdf_path}")
        
        if not pdf_path.exists():
            print(f"PDF file does not exist: {pdf_path}")
            return ""
            
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            num_pages = len(reader.pages)
            print(f"PDF has {num_pages} pages")
            
            for page_num in range(num_pages):
                try:
                    page = reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        # Clean up the text
                        page_text = re.sub(r'\s+', ' ', page_text).strip()
                        text += page_text + "\n"
                    else:
                        print(f"Page {page_num+1} has no extractable text")
                except Exception as e:
                    print(f"Error reading page {page_num+1} in {pdf_path}: {e}")
                    continue
                    
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
    
    print(f"Extracted {len(text)} characters from {pdf_path}")
    return text

def clean_text(text):
    """Clean text by removing common PDF artifacts"""
    if not text:
        return ""
    
    # Remove page numbers and headers/footers
    text = re.sub(r'\bPage\s+\d+\b', '', text)
    text = re.sub(r'\b\d+\s+of\s+\d+\b', '', text)
    text = re.sub(r'http\S+', '', text)  # Remove URLs
    text = re.sub(r'\S+@\S+', '', text)  # Remove emails
    
    # Remove common PDF artifacts
    text = re.sub(r'\.{2,}', '.', text)  # Multiple dots
    text = re.sub(r'-{2,}', '-', text)   # Multiple hyphens
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def chunk_text(text, chunk_size=300, overlap=50):
    """Split text into overlapping chunks with improved logic"""
    # Clean the text first
    text = clean_text(text)
    
    if not text or len(text.split()) < 20:  # Skip very short texts
        print("Text too short for chunking")
        return []
    
    # Split into sentences first for better chunking
    sentences = re.split(r'(?<=[.!?])\s+', text)
    print(f"Split into {len(sentences)} sentences")
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence_length = len(sentence.split())
        
        if current_length + sentence_length > chunk_size and current_chunk:
            # Save the current chunk
            chunk_text = ' '.join(current_chunk)
            chunks.append(chunk_text)
            
            # Start new chunk with overlap
            overlap_start = max(0, len(current_chunk) - overlap)
            current_chunk = current_chunk[overlap_start:]
            current_length = len(' '.join(current_chunk).split())
        
        current_chunk.append(sentence)
        current_length += sentence_length
    
    # Add the last chunk
    if current_chunk:
        chunk_text = ' '.join(current_chunk)
        chunks.append(chunk_text)
    
    print(f"Created {len(chunks)} chunks")
    return chunks

def process_documents():
    """Process all documents, extract text and create chunks"""
    documents = Document.objects.filter(processed=False)
    
    print(f"Found {documents.count()} documents to process")
    
    # First, let's see what PDF files are actually available
    pdf_files = list(settings.PDF_DIR.glob("*.pdf"))
    print(f"Available PDF files: {[f.name for f in pdf_files]}")
    
    for doc in documents:
        print(f"\nProcessing document: {doc.title}")
        
        # Find the PDF file - try multiple naming patterns
        pdf_filename_patterns = [
            f"{doc.title}.pdf",
            f"{doc.title.replace(' ', '_')}.pdf",
            f"{doc.title.replace(' ', '-')}.pdf",
            f"{doc.title.replace('/', '_')}.pdf",
            f"{doc.title.replace(':', '')}.pdf",
            f"{doc.title.replace('—', '_')}.pdf",  # Handle em dash
            f"{doc.title.replace('(', '').replace(')', '')}.pdf",  # Remove parentheses
        ]
        
        pdf_path = None
        for pattern in pdf_filename_patterns:
            potential_path = settings.PDF_DIR / pattern
            if potential_path.exists():
                pdf_path = potential_path
                print(f"Found PDF: {pdf_path.name}")
                break
        
        if not pdf_path:
            # Try to find by partial match
            print(f"PDF not found with exact patterns. Searching for partial match...")
            doc_title_lower = doc.title.lower()
            for pdf_file in pdf_files:
                if doc_title_lower in pdf_file.name.lower() or pdf_file.name.lower() in doc_title_lower:
                    pdf_path = pdf_file
                    print(f"Found PDF by partial match: {pdf_path.name}")
                    break
            
            if not pdf_path:
                print(f"PDF not found for: {doc.title}")
                continue
        
        # Extract text
        print(f"Extracting text from: {pdf_path.name}")
        text = extract_text_from_pdf(pdf_path)
        
        if not text:
            print(f"No text extracted from: {pdf_path.name}")
            continue
            
        word_count = len(text.split())
        print(f"Extracted {word_count} words from {doc.title}")
        
        if word_count < 50:  # Skip documents with too little text
            print(f"Document {doc.title} has too little text ({word_count} words), skipping")
            continue
        
        # Create chunks
        chunks = chunk_text(text)
        print(f"Created {len(chunks)} chunks from {doc.title}")
        
        for i, chunk_text_content in enumerate(chunks):
            # Skip very short chunks
            if len(chunk_text_content.split()) < 10:
                continue
                
            DocumentChunk.objects.create(
                document=doc,
                chunk_text=chunk_text_content,
                chunk_index=i
            )
        
        doc.processed = True
        doc.save()
        print(f"Successfully processed document: {doc.title}")
    
    print(f"Processing complete. Processed {documents.count()} documents")

def check_pdf_files():
    """Check what PDF files are available and match them to documents"""
    pdf_files = list(settings.PDF_DIR.glob("*.pdf"))
    documents = Document.objects.all()
    
    print("Available PDF files:")
    for pdf_file in pdf_files:
        print(f"  - {pdf_file.name}")
    
    print("\nDocument titles from sources.json:")
    for doc in documents:
        print(f"  - {doc.title}")
    
    print("\nMatching PDFs to documents:")
    for doc in documents:
        found = False
        doc_title_lower = doc.title.lower()
        
        for pdf_file in pdf_files:
            pdf_name_lower = pdf_file.name.lower()
            
            # Check if document title is in PDF filename or vice versa
            if (doc_title_lower in pdf_name_lower or 
                pdf_name_lower.replace('.pdf', '') in doc_title_lower or
                any(word in pdf_name_lower for word in doc_title_lower.split()[:3])):
                
                print(f"  ✓ {doc.title} -> {pdf_file.name}")
                found = True
                break
        
        if not found:
            print(f"  ✗ {doc.title} -> No matching PDF found")
    
    return pdf_files