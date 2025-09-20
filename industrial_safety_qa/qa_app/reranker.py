from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
import numpy as np
import re

class HybridReranker:
    def __init__(self, corpus):
        self.corpus = corpus
        self.tokenized_corpus = [self._tokenize(doc['cleaned_text']) for doc in corpus]
        self.bm25 = BM25Okapi(self.tokenized_corpus)
    
    def _tokenize(self, text):
        # Improved tokenization
        tokens = re.findall(r'\b\w+\b', text.lower())
        return [token for token in tokens if token not in ENGLISH_STOP_WORDS and len(token) > 2]
    
    def _calculate_title_match(self, query, document_title):
        """Calculate title match score"""
        query_words = set(self._tokenize(query))
        title_words = set(self._tokenize(document_title))
        
        if not query_words:
            return 0
            
        intersection = query_words.intersection(title_words)
        return len(intersection) / len(query_words)
    
    def rerank(self, query, vector_scores, alpha=0.6):
        """Rerank results using hybrid of vector similarity and BM25"""
        tokenized_query = self._tokenize(query)
        bm25_scores = self.bm25.get_scores(tokenized_query)
        
        # Normalize scores
        if len(bm25_scores) > 0 and np.max(bm25_scores) > np.min(bm25_scores):
            bm25_scores = (bm25_scores - np.min(bm25_scores)) / (np.max(bm25_scores) - np.min(bm25_scores))
        else:
            bm25_scores = np.ones_like(bm25_scores) * 0.5  # Default score if no variance
        
        if len(vector_scores) > 0 and np.max(vector_scores) > np.min(vector_scores):
            vector_scores_norm = (vector_scores - np.min(vector_scores)) / (np.max(vector_scores) - np.min(vector_scores))
        else:
            vector_scores_norm = np.ones_like(vector_scores) * 0.5  # Default score if no variance
        
        # Calculate additional features
        title_scores = np.array([self._calculate_title_match(query, doc['document_title']) for doc in self.corpus])
        length_scores = np.array([min(1.0, len(doc['cleaned_text'].split()) / 100) for doc in self.corpus])  # Prefer medium-length chunks
        
        # Combine scores with weights
        combined_scores = (
            alpha * vector_scores_norm + 
            0.3 * bm25_scores + 
            0.05 * title_scores +
            0.05 * length_scores
        )
        
        # Sort by combined scores
        sorted_indices = np.argsort(combined_scores)[::-1]
        
        # Return reranked results
        reranked_results = []
        for idx in sorted_indices:
            result = self.corpus[idx].copy()
            result['score'] = float(combined_scores[idx])
            result['vector_score'] = float(vector_scores[idx])
            result['bm25_score'] = float(bm25_scores[idx])
            result['title_score'] = float(title_scores[idx])
            reranked_results.append(result)
        
        return reranked_results