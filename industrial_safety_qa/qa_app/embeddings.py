from sentence_transformers import SentenceTransformer
import numpy as np
import chromadb
from django.conf import settings
from .models import DocumentChunk
import re

# Initialize the embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize ChromaDB client with the new configuration
try:
    chroma_client = chromadb.PersistentClient(path=str(settings.CHROMA_DB_PATH))
    
    # Create or get collection
    collection = chroma_client.get_or_create_collection(
        name="safety_documents",
        metadata={"hnsw:space": "cosine"}  # Use cosine similarity
    )
except Exception as e:
    print(f"Error initializing ChromaDB: {e}")
    collection = None

def clean_chunk_text(text):
    """Clean chunk text by removing extra whitespace and noise"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove page numbers and headers/footers
    text = re.sub(r'\bPage\s+\d+\b', '', text)
    text = re.sub(r'\b\d+\s+of\s+\d+\b', '', text)
    
    return text

def generate_embeddings():
    """Generate embeddings for all chunks and store in ChromaDB"""
    if not collection:
        print("ChromaDB collection not available")
        return
    
    chunks = DocumentChunk.objects.all()
    
    print(f"Generating embeddings for {chunks.count()} chunks")
    
    ids = []
    documents = []
    embeddings = []
    metadatas = []
    
    for chunk in chunks:
        # Clean the text before embedding
        clean_text = clean_chunk_text(chunk.chunk_text)
        if not clean_text or len(clean_text.split()) < 5:  # Skip very short chunks
            continue
            
        # Generate embedding
        embedding = model.encode(clean_text)
        
        # Prepare data for ChromaDB
        chunk_id = f"{chunk.document.id}_{chunk.chunk_index}"
        ids.append(chunk_id)
        documents.append(clean_text)
        embeddings.append(embedding.tolist())
        metadatas.append({
            "document_id": chunk.document.id,
            "chunk_index": chunk.chunk_index,
            "document_title": chunk.document.title,
            "document_url": chunk.document.url,
            "original_text": chunk.chunk_text  # Keep original for display
        })
    
    # Clear existing data
    try:
        collection.delete(where={})
    except:
        pass  # Ignore if collection doesn't exist yet
    
    # Add to ChromaDB in batches to avoid large requests
    batch_size = 50  # Smaller batch size for reliability
    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i+batch_size]
        batch_embeddings = embeddings[i:i+batch_size]
        batch_metadatas = metadatas[i:i+batch_size]
        batch_documents = documents[i:i+batch_size]
        
        try:
            collection.add(
                ids=batch_ids,
                embeddings=batch_embeddings,
                metadatas=batch_metadatas,
                documents=batch_documents
            )
            print(f"Added batch {i//batch_size + 1}/{(len(ids)-1)//batch_size + 1}")
        except Exception as e:
            print(f"Error adding batch {i//batch_size + 1}: {e}")
    
    print(f"Generated embeddings for {len(ids)} chunks")

def search_embeddings(query, k=10):
    """Search for similar chunks using embeddings"""
    if not collection:
        return []
    
    # Clean the query
    clean_query = clean_chunk_text(query)
    
    # Generate query embedding
    query_embedding = model.encode(clean_query).tolist()
    
    try:
        # Search in ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=k * 2  # Get more results for better reranking
        )
        
        # Format results
        formatted_results = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                # Use original text for display, cleaned text for scoring
                formatted_results.append({
                    'chunk_text': results['metadatas'][0][i]['original_text'],
                    'cleaned_text': results['documents'][0][i],
                    'document_title': results['metadatas'][0][i]['document_title'],
                    'document_url': results['metadatas'][0][i]['document_url'],
                    'chunk_index': results['metadatas'][0][i]['chunk_index'],
                    'score': 1 - results['distances'][0][i] if results['distances'] and results['distances'][0] else 1.0
                })
        
        return formatted_results
    except Exception as e:
        print(f"Error searching embeddings: {e}")
        return []