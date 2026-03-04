"""
TASK 4 (Part 2): FAISS Vector Database Integration
Sub-second search across massive footage
"""
import faiss
import numpy as np
import pickle
import os
from typing import List, Tuple, Dict
import json

class FAISSVectorDB:
    def __init__(self, dimension: int = 512):
        self.dimension = dimension
        self.index_path = 'static/faiss_index.bin'
        self.metadata_path = 'static/faiss_metadata.pkl'
        
        # Initialize or load index
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
        else:
            # Create IVFFlat index for accuracy-speed balance
            # IVFFlat: Better accuracy than IVF, faster than Flat
            quantizer = faiss.IndexFlatIP(dimension)  # Inner product (cosine similarity)
            
            # nlist = sqrt(N) is optimal, start with 100 and retrain as DB grows
            nlist = 100  # Number of clusters
            self.index = faiss.IndexIVFFlat(quantizer, dimension, nlist, faiss.METRIC_INNER_PRODUCT)
            self.metadata = []
        
        # Set nprobe for search (higher = more accurate but slower)
        if hasattr(self.index, 'nprobe'):
            self.index.nprobe = 10  # Search 10 clusters (good balance)
    
    def train_index(self, embeddings: np.ndarray):
        """Train FAISS index (required for IVF)"""
        if not self.index.is_trained:
            self.index.train(embeddings)
            self.save_index()
    
    def add_embedding(self, embedding: np.ndarray, case_id: int, 
                     person_profile_id: int = None) -> int:
        """
        Add embedding to FAISS index
        Returns: index position
        """
        # Normalize embedding for cosine similarity
        embedding = embedding / np.linalg.norm(embedding)
        embedding = embedding.reshape(1, -1).astype('float32')
        
        # Train if needed
        if not self.index.is_trained:
            self.train_index(embedding)
        
        # Add to index
        position = self.index.ntotal
        self.index.add(embedding)
        
        # Store metadata
        self.metadata.append({
            'position': position,
            'case_id': case_id,
            'person_profile_id': person_profile_id,
            'embedding': embedding[0].tolist()
        })
        
        self.save_index()
        return position
    
    def search(self, query_embedding: np.ndarray, k: int = 10, 
               threshold: float = 0.98) -> List[Dict]:
        """
        Search for similar embeddings
        
        Args:
            query_embedding: 512-d query vector
            k: Number of results
            threshold: Minimum similarity (0.98 = 98%)
        
        Returns:
            List of matches with case_id and similarity
        """
        # Normalize query
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        
        # Search
        similarities, indices = self.index.search(query_embedding, k)
        
        # Filter by threshold
        results = []
        for sim, idx in zip(similarities[0], indices[0]):
            if sim >= threshold and idx < len(self.metadata):
                meta = self.metadata[idx]
                results.append({
                    'case_id': meta['case_id'],
                    'person_profile_id': meta['person_profile_id'],
                    'similarity': float(sim),
                    'position': meta['position']
                })
        
        return results
    
    def batch_search(self, query_embeddings: np.ndarray, k: int = 10,
                    threshold: float = 0.98) -> List[List[Dict]]:
        """Batch search for multiple queries"""
        # Normalize all queries
        norms = np.linalg.norm(query_embeddings, axis=1, keepdims=True)
        query_embeddings = query_embeddings / norms
        query_embeddings = query_embeddings.astype('float32')
        
        # Batch search
        similarities, indices = self.index.search(query_embeddings, k)
        
        # Process results
        all_results = []
        for sim_row, idx_row in zip(similarities, indices):
            results = []
            for sim, idx in zip(sim_row, idx_row):
                if sim >= threshold and idx < len(self.metadata):
                    meta = self.metadata[idx]
                    results.append({
                        'case_id': meta['case_id'],
                        'person_profile_id': meta['person_profile_id'],
                        'similarity': float(sim),
                        'position': meta['position']
                    })
            all_results.append(results)
        
        return all_results
    
    def save_index(self):
        """Save FAISS index and metadata to disk"""
        os.makedirs('static', exist_ok=True)
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, 'wb') as f:
            pickle.dump(self.metadata, f)
    
    def get_stats(self) -> Dict:
        """Get index statistics"""
        return {
            'total_vectors': self.index.ntotal,
            'dimension': self.dimension,
            'is_trained': self.index.is_trained,
            'index_type': 'IVFFlat',
            'metadata_count': len(self.metadata)
        }

# Global instance
faiss_db = FAISSVectorDB(dimension=512)
