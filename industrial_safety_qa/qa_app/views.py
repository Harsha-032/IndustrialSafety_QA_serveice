from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import numpy as np
import re

from .models import Document, DocumentChunk
from .utils import load_sources, process_documents
from .embeddings import generate_embeddings, search_embeddings
from .reranker import HybridReranker
from .forms import QueryForm

def load_questions():
    """Load predefined questions from JSON file"""
    questions_path = settings.BASE_DIR / 'data' / 'questions.json'
    try:
        with open(questions_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def index(request):
    """Home page with query form and question suggestions"""
    form = QueryForm()
    questions_by_category = load_questions()
    return render(request, 'qa_app/index.html', {
        'form': form,
        'questions_by_category': questions_by_category
    })

@csrf_exempt
def ask_api(request):
    """API endpoint for question answering"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        query = data.get('q', '')
        k = int(data.get('k', 5))
        mode = data.get('mode', 'reranked')  # 'baseline' or 'reranked'
        
        if not query:
            return JsonResponse({'error': 'Query parameter "q" is required'}, status=400)
        
        # Baseline search with embeddings
        baseline_results = search_embeddings(query, k * 2)  # Get more for reranking
        
        if mode == 'baseline':
            results = baseline_results[:k]
            reranker_used = False
        else:
            # Apply reranker
            if baseline_results:
                reranker = HybridReranker(baseline_results)
                vector_scores = [result['score'] for result in baseline_results]
                results = reranker.rerank(query, vector_scores)[:k]
                reranker_used = True
            else:
                results = []
                reranker_used = False
        
        # Generate answer from top results
        answer = None
        contexts = []
        
        if results:
            # Lower the confidence threshold to show more answers
            confidence_threshold = 0.3
            
            # Extract answer from top results
            top_results = [r for r in results if r['score'] >= confidence_threshold]
            
            if top_results:
                # Combine top chunks to form a comprehensive answer
                answer_chunks = []
                for result in top_results[:3]:  # Use top 3 results for answer
                    answer_chunks.append(result['chunk_text'])
                
                answer = " ".join(answer_chunks)
                answer = truncate_answer(answer, 500)  # Limit answer length
                
                contexts = [{
                    'text': result['chunk_text'],
                    'score': float(result['score']),
                    'source': {
                        'title': result['document_title'],
                        'url': result['document_url'],
                        'chunk_index': result['chunk_index']
                    }
                } for result in results]
        
        response_data = {
            'answer': answer,
            'contexts': contexts,
            'reranker_used': reranker_used,
            'query': query
        }
        
        return JsonResponse(response_data)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status= 500)

def truncate_answer(text, max_length):
    """Truncate answer to maximum length while preserving sentences"""
    if len(text) <= max_length:
        return text
    
    # Find the last sentence end within the limit
    truncated = text[:max_length]
    last_period = truncated.rfind('.')
    last_exclamation = truncated.rfind('!')
    last_question = truncated.rfind('?')
    
    sentence_end = max(last_period, last_exclamation, last_question)
    
    if sentence_end > 0:
        return truncated[:sentence_end + 1] + ".."
    else:
        return truncated + "..."

def ask(request):
    """Web interface for question answering"""
    questions_by_category = load_questions()
    
    if request.method == 'POST':
        form = QueryForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data['query']
            k = form.cleaned_data['top_k']
            mode = form.cleaned_data['mode']
            
            # Call the API
            from django.test import RequestFactory
            factory = RequestFactory()
            api_request = factory.post(
                '/api/ask/', 
                data=json.dumps({'q': query, 'k': k, 'mode': mode}), 
                content_type='application/json'
            )
            
            # Get API response
            api_response = ask_api(api_request)
            response_data = json.loads(api_response.content)
            
            return render(request, 'qa_app/results.html', {
                'query': query,
                'answer': response_data.get('answer'),
                'contexts': response_data.get('contexts', []),
                'reranker_used': response_data.get('reranker_used', False),
                'mode': mode,
                'questions_by_category': questions_by_category
            })
    else:
        # Pre-fill the form if a question is passed as a parameter
        initial_query = request.GET.get('query', '')
        form = QueryForm(initial={'query': initial_query}) if initial_query else QueryForm()
    
    return render(request, 'qa_app/ask.html', {
        'form': form,
        'questions_by_category': questions_by_category
    })
def initialize_system(request):
    """Initialize the system by loading sources and processing documents"""
    if request.method == 'POST':
        try:
            # Clear existing data
            Document.objects.all().delete()
            DocumentChunk.objects.all().delete()
            
            # Load sources
            load_sources()
            
            # First check if we have PDF files
            from .utils import check_pdf_files
            pdf_files = check_pdf_files()
            
            if not pdf_files:
                return render(request, 'qa_app/initialize.html', {
                    'error': 'No PDF files found in data/pdfs/ folder. Please add PDF files and try again.'
                })
            
            # Process documents
            process_documents()
            
            # Check if any chunks were created
            chunk_count = DocumentChunk.objects.count()
            if chunk_count == 0:
                return render(request, 'qa_app/initialize.html', {
                    'error': 'No chunks were created during processing. This usually means PDF files were not found or could not be read. Check the PDF files and try again.'
                })
            
            # Generate embeddings
            generate_embeddings()
            
            return render(request, 'qa_app/index.html', {
                'form': QueryForm(),
                'message': f'System initialized successfully! Processed {chunk_count} chunks from PDF documents.'
            })
        except Exception as e:
            return render(request, 'qa_app/initialize.html', {
                'error': f'Error initializing system: {str(e)}'
            })
    
    return render(request, 'qa_app/initialize.html')

def diagnostic(request):
    """Diagnostic page to check system status"""
    documents = Document.objects.all()
    chunks = DocumentChunk.objects.all()
    chunks_with_embeddings = chunks.exclude(embedding__isnull=True)
    
    # Check if ChromaDB collection exists and has data
    try:
        from .embeddings import collection
        chroma_count = collection.count()
    except:
        chroma_count = 0
    
    return render(request, 'qa_app/diagnostic.html', {
        'document_count': documents.count(),
        'processed_document_count': documents.filter(processed=True).count(),
        'chunk_count': chunks.count(),
        'chunk_with_embedding_count': chunks_with_embeddings.count(),
        'chroma_count': chroma_count,
    })

def check_pdfs(request):
    """Check PDF files and their matching to documents"""
    from .utils import check_pdf_files
    
    pdf_files = check_pdf_files()
    
    return render(request, 'qa_app/check_pdfs.html', {
        'pdf_files': pdf_files,
        'document_count': Document.objects.count(),
    })