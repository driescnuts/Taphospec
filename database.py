"""
Database operations for Spectral Library features (v2.1)
Extension of database.py with library, multimodal, and experimental functions
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import numpy as np


class SpectralLibraryDB:
    """
    Extension class for spectral library operations
    Mix this into TaphoSpecDB class
    """
    
    # ==================== SPECTRAL LIBRARY OPERATIONS ====================
    
    def create_library_entry(self, spectrum_name: str, spectrum_type: str,
                            material_type: str, **kwargs) -> Dict:
        """
        Create a new spectral library entry
        
        Args:
            spectrum_name: Name/title of the spectrum
            spectrum_type: 'archaeological' or 'experimental'
            material_type: Type of material (e.g., 'organic_adhesive')
            **kwargs: Additional optional fields
        """
        data = {
            "spectrum_name": spectrum_name,
            "spectrum_type": spectrum_type,
            "material_type": material_type,
            **kwargs
        }
        
        result = self.client.table("spectral_library").insert(data).execute()
        return result.data[0] if result.data else None
    
    def get_library_entries(self, spectrum_type: str = None, 
                           material_type: str = None,
                           verified_only: bool = False,
                           multimodal_only: bool = False) -> List[Dict]:
        """
        Get library entries with optional filters
        """
        query = self.client.table("library_complete").select("*")
        
        if spectrum_type:
            query = query.eq("spectrum_type", spectrum_type)
        
        if material_type:
            query = query.eq("material_type", material_type)
        
        if verified_only:
            query = query.eq("verified", True)
        
        if multimodal_only:
            query = query.eq("has_eds", True).eq("has_ftir", True)
        
        result = query.execute()
        return result.data if result.data else []
    
    def update_library_entry(self, library_id: str, updates: Dict) -> Dict:
        """Update a library entry"""
        updates["updated_at"] = datetime.utcnow().isoformat()
        result = self.client.table("spectral_library").update(updates).eq("library_id", library_id).execute()
        return result.data[0] if result.data else None
    
    def delete_library_entry(self, library_id: str) -> bool:
        """Delete a library entry"""
        result = self.client.table("spectral_library").delete().eq("library_id", library_id).execute()
        return len(result.data) > 0
    
    def verify_library_entry(self, library_id: str, user_id: str) -> Dict:
        """Mark a library entry as verified"""
        return self.update_library_entry(library_id, {
            "verified": True,
            "verified_by": user_id,
            "verified_date": datetime.utcnow().date().isoformat()
        })
    
    def search_library_by_keywords(self, keywords: List[str]) -> List[Dict]:
        """Search library by keywords"""
        # Note: PostgreSQL array contains operator
        query = self.client.table("spectral_library").select("*")
        
        # Filter by keywords (requires custom RPC or multiple queries)
        result = query.execute()
        
        # Filter in Python (for simplicity)
        filtered = []
        for entry in result.data:
            entry_keywords = entry.get('keywords', []) or []
            if any(kw.lower() in [k.lower() for k in entry_keywords] for kw in keywords):
                filtered.append(entry)
        
        return filtered
    
    def get_library_statistics(self) -> Dict:
        """Get library statistics"""
        result = self.client.table("library_statistics").select("*").execute()
        return result.data[0] if result.data else {}
    
    # ==================== MULTI-MODAL ANALYSIS OPERATIONS ====================
    
    def create_multimodal_link(self, sample_id: str, analysis_point_number: int,
                               eds_analysis_id: str = None, ftir_analysis_id: str = None,
                               **kwargs) -> Dict:
        """
        Link EDS and FTIR analyses from the same point
        """
        data = {
            "sample_id": sample_id,
            "analysis_point_number": analysis_point_number,
            "eds_analysis_id": eds_analysis_id,
            "ftir_analysis_id": ftir_analysis_id,
            **kwargs
        }
        
        result = self.client.table("multimodal_analyses").insert(data).execute()
        return result.data[0] if result.data else None
    
    def get_multimodal_links(self, sample_id: str = None) -> List[Dict]:
        """Get multimodal analysis links"""
        query = self.client.table("multimodal_summary").select("*")
        
        if sample_id:
            query = query.eq("sample_id", sample_id)
        
        result = query.order("analysis_point_number").execute()
        return result.data if result.data else []
    
    def update_multimodal_link(self, link_id: str, updates: Dict) -> Dict:
        """Update a multimodal link"""
        updates["updated_at"] = datetime.utcnow().isoformat()
        result = self.client.table("multimodal_analyses").update(updates).eq("link_id", link_id).execute()
        return result.data[0] if result.data else None
    
    def set_multimodal_classification(self, link_id: str, classification: str,
                                     confidence_score: float, agreement_level: str,
                                     reasoning: Dict = None) -> Dict:
        """
        Set the combined classification for a multimodal analysis
        """
        updates = {
            "combined_classification": classification,
            "confidence_score": confidence_score,
            "agreement_level": agreement_level
        }
        
        if reasoning:
            updates["reasoning"] = reasoning
        
        # Set agreement flag
        updates["all_techniques_agree"] = (agreement_level == 'full')
        updates["requires_review"] = (agreement_level == 'conflict')
        
        return self.update_multimodal_link(link_id, updates)
    
    def get_conflicting_multimodal_analyses(self) -> List[Dict]:
        """Get analyses where EDS and FTIR disagree"""
        query = self.client.table("multimodal_summary").select("*")
        query = query.eq("agreement_level", "conflict")
        result = query.execute()
        return result.data if result.data else []
    
    # ==================== EXPERIMENTAL SAMPLES OPERATIONS ====================
    
    def create_experimental_sample(self, experiment_name: str, researcher: str,
                                   base_material: str, preparation_protocol: str,
                                   **kwargs) -> Dict:
        """
        Create a new experimental sample
        """
        data = {
            "experiment_name": experiment_name,
            "researcher": researcher,
            "base_material": base_material,
            "preparation_protocol": preparation_protocol,
            **kwargs
        }
        
        result = self.client.table("experimental_samples").insert(data).execute()
        return result.data[0] if result.data else None
    
    def get_experimental_samples(self, experiment_type: str = None,
                                base_material: str = None,
                                researcher: str = None) -> List[Dict]:
        """Get experimental samples with optional filters"""
        query = self.client.table("experimental_samples").select("*")
        
        if experiment_type:
            query = query.eq("experiment_type", experiment_type)
        
        if base_material:
            query = query.eq("base_material", base_material)
        
        if researcher:
            query = query.eq("researcher", researcher)
        
        result = query.order("experiment_date", desc=True).execute()
        return result.data if result.data else []
    
    def get_experimental_sample(self, experiment_id: str) -> Optional[Dict]:
        """Get a specific experimental sample"""
        result = self.client.table("experimental_samples").select("*").eq("experiment_id", experiment_id).execute()
        return result.data[0] if result.data else None
    
    def update_experimental_sample(self, experiment_id: str, updates: Dict) -> Dict:
        """Update an experimental sample"""
        updates["updated_at"] = datetime.utcnow().isoformat()
        result = self.client.table("experimental_samples").update(updates).eq("experiment_id", experiment_id).execute()
        return result.data[0] if result.data else None
    
    def create_sequential_experiment(self, parent_id: str, new_treatment: str,
                                    treatment_description: str, **kwargs) -> Dict:
        """
        Create a new experiment in a degradation sequence
        """
        # Get parent experiment
        parent = self.get_experimental_sample(parent_id)
        
        if not parent:
            raise ValueError(f"Parent experiment {parent_id} not found")
        
        # Build cumulative treatment history
        cumulative = parent.get('cumulative_treatments', []) or []
        cumulative.append(new_treatment)
        
        # Create new experiment
        data = {
            "experiment_name": f"{parent['experiment_name']} + {new_treatment}",
            "parent_experiment_id": parent_id,
            "treatment_sequence": parent.get('treatment_sequence', 0) + 1,
            "researcher": parent['researcher'],
            "base_material": parent['base_material'],
            "preparation_protocol": parent['preparation_protocol'],
            "degradation_type": new_treatment,
            "treatment_description": treatment_description,
            "cumulative_treatments": cumulative,
            **kwargs
        }
        
        return self.create_experimental_sample(**data)
    
    def get_degradation_series(self, base_experiment_id: str) -> List[Dict]:
        """
        Get all experiments in a degradation sequence
        """
        result = self.client.table("experimental_series").select("*").execute()
        
        # Filter for the specific series
        series = []
        for exp in result.data:
            if base_experiment_id in exp.get('path', []):
                series.append(exp)
        
        # Sort by treatment sequence
        series.sort(key=lambda x: x.get('treatment_sequence', 0))
        
        return series
    
    def add_experimental_to_library(self, experiment_id: str) -> Dict:
        """
        Add an experimental sample to the spectral library
        Uses the database function for atomic operation
        """
        result = self.client.rpc('add_experiment_to_library', {'exp_id': experiment_id}).execute()
        return result.data[0] if result.data else None
    
    # ==================== LIBRARY SEARCH OPERATIONS ====================
    
    def log_library_search(self, query_spectrum_id: str, query_type: str,
                          search_params: Dict, results: List[Dict],
                          user_id: str = None) -> Dict:
        """
        Log a library search for analytics
        """
        data = {
            "query_spectrum_id": query_spectrum_id,
            "query_type": query_type,
            "distance_metric": search_params.get('distance_metric'),
            "elements_used": search_params.get('elements_used'),
            "top_n": search_params.get('top_n'),
            "filter_spectrum_type": search_params.get('filter_spectrum_type'),
            "filter_material_type": search_params.get('filter_material_type'),
            "only_verified": search_params.get('only_verified', False),
            "only_multimodal": search_params.get('only_multimodal', False),
            "results": results,
            "best_match_id": results[0]['library_id'] if results else None,
            "best_match_score": results[0]['similarity_score'] if results else None,
            "user_id": user_id
        }
        
        result = self.client.table("library_searches").insert(data).execute()
        return result.data[0] if result.data else None
    
    def update_search_feedback(self, search_id: str, accepted: bool,
                               selected_id: str = None, feedback: str = None) -> Dict:
        """
        Update search with user feedback
        """
        updates = {
            "user_accepted_match": accepted,
            "user_selected_id": selected_id,
            "user_feedback": feedback
        }
        
        result = self.client.table("library_searches").update(updates).eq("search_id", search_id).execute()
        return result.data[0] if result.data else None
    
    def get_search_history(self, user_id: str = None, limit: int = 50) -> List[Dict]:
        """Get search history"""
        query = self.client.table("library_searches").select("*")
        
        if user_id:
            query = query.eq("user_id", user_id)
        
        result = query.order("search_date", desc=True).limit(limit).execute()
        return result.data if result.data else []


# ==================== DISTANCE CALCULATION FUNCTIONS ====================

def calculate_euclidean_distance(spectrum1: Dict, spectrum2: Dict, elements: List[str]) -> float:
    """
    Calculate Euclidean distance between two spectra
    """
    vec1 = np.array([spectrum1.get(e, 0) for e in elements])
    vec2 = np.array([spectrum2.get(e, 0) for e in elements])
    
    return np.linalg.norm(vec1 - vec2)


def calculate_cosine_similarity(spectrum1: Dict, spectrum2: Dict, elements: List[str]) -> float:
    """
    Calculate cosine similarity between two spectra
    Returns similarity (0-1, higher is more similar)
    """
    vec1 = np.array([spectrum1.get(e, 0) for e in elements])
    vec2 = np.array([spectrum2.get(e, 0) for e in elements])
    
    # Avoid division by zero
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return np.dot(vec1, vec2) / (norm1 * norm2)


def calculate_manhattan_distance(spectrum1: Dict, spectrum2: Dict, elements: List[str]) -> float:
    """
    Calculate Manhattan distance between two spectra
    """
    vec1 = np.array([spectrum1.get(e, 0) for e in elements])
    vec2 = np.array([spectrum2.get(e, 0) for e in elements])
    
    return np.sum(np.abs(vec1 - vec2))


def calculate_chi_square_distance(spectrum1: Dict, spectrum2: Dict, elements: List[str]) -> float:
    """
    Calculate Chi-square distance between two spectra
    """
    vec1 = np.array([spectrum1.get(e, 0) + 1e-10 for e in elements])  # Avoid division by zero
    vec2 = np.array([spectrum2.get(e, 0) + 1e-10 for e in elements])
    
    return np.sum(((vec1 - vec2) ** 2) / (vec1 + vec2))


def calculate_distance(spectrum1: Dict, spectrum2: Dict, elements: List[str], 
                      metric: str = 'euclidean') -> float:
    """
    Calculate distance between two spectra using specified metric
    """
    if metric == 'euclidean':
        return calculate_euclidean_distance(spectrum1, spectrum2, elements)
    elif metric == 'cosine':
        # Convert similarity to distance
        similarity = calculate_cosine_similarity(spectrum1, spectrum2, elements)
        return 1 - similarity
    elif metric == 'manhattan':
        return calculate_manhattan_distance(spectrum1, spectrum2, elements)
    elif metric == 'chi_square':
        return calculate_chi_square_distance(spectrum1, spectrum2, elements)
    else:
        raise ValueError(f"Unknown distance metric: {metric}")
