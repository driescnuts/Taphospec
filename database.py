"""
Database module for TaphoSpec v2.1
Handles all Supabase PostgreSQL interactions
Includes v2.0 base functions + v2.1 spectral library features
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import streamlit as st
import numpy as np

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


class TaphoSpecDB:
    """Database connection and operations for TaphoSpec v2.1"""
    
    def __init__(self):
        """Initialize database connection"""
        if not SUPABASE_AVAILABLE:
            raise ImportError("Supabase not available. Install with: pip install supabase")
        
        # Get credentials from Streamlit secrets or environment variables
        try:
            url = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
            key = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY")
        except:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError(
                "Supabase credentials not found. Please set SUPABASE_URL and SUPABASE_KEY "
                "in Streamlit secrets or environment variables."
            )
        
        self.client: Client = create_client(url, key)
    
    # ==================== PROJECT OPERATIONS (v2.0) ====================
    
    def create_project(self, project_name: str, description: str = None, 
                      principal_investigator: str = None, institution: str = None,
                      is_public: bool = False, user_id: str = None) -> Dict:
        """Create a new project"""
        data = {
            "project_name": project_name,
            "description": description,
            "principal_investigator": principal_investigator,
            "institution": institution,
            "is_public": is_public
        }
        
        # Add user_id if provided (required for RLS)
        if user_id:
            data["user_id"] = user_id
        
        result = self.client.table("projects").insert(data).execute()
        return result.data[0] if result.data else None
    
    def get_projects(self, is_public: Optional[bool] = None) -> List[Dict]:
        """Get all projects, optionally filtered by public status"""
        query = self.client.table("projects").select("*")
        
        if is_public is not None:
            query = query.eq("is_public", is_public)
        
        result = query.order("created_at", desc=True).execute()
        return result.data if result.data else []
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """Get a specific project by ID"""
        result = self.client.table("projects").select("*").eq("project_id", project_id).execute()
        return result.data[0] if result.data else None
    
    def update_project(self, project_id: str, updates: Dict) -> Dict:
        """Update a project"""
        updates["updated_at"] = datetime.utcnow().isoformat()
        result = self.client.table("projects").update(updates).eq("project_id", project_id).execute()
        return result.data[0] if result.data else None
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project (cascade deletes all related data)"""
        result = self.client.table("projects").delete().eq("project_id", project_id).execute()
        return len(result.data) > 0
    
    # ==================== SITE OPERATIONS (v2.0) ====================
    
    def create_site(self, project_id: str, site_name: str, country: str = None,
                   latitude: float = None, longitude: float = None, 
                   site_type: str = None, excavation_year: int = None,
                   context_type: str = None, stratigraphy: str = None,
                   sediment_type: str = None, site_description: str = None) -> Dict:
        """Create a new archaeological site"""
        data = {
            "project_id": project_id,
            "site_name": site_name,
            "country": country,
            "latitude": latitude,
            "longitude": longitude,
            "site_type": site_type,
            "excavation_year": excavation_year,
            "context_type": context_type,
            "stratigraphy": stratigraphy,
            "sediment_type": sediment_type,
            "site_description": site_description
        }
        
        result = self.client.table("sites").insert(data).execute()
        return result.data[0] if result.data else None
    
    def get_sites(self, project_id: str = None) -> List[Dict]:
        """Get all sites, optionally filtered by project"""
        query = self.client.table("sites").select("*")
        
        if project_id:
            query = query.eq("project_id", project_id)
        
        result = query.order("site_name").execute()
        return result.data if result.data else []
    
    def get_site(self, site_id: str) -> Optional[Dict]:
        """Get a specific site by ID"""
        result = self.client.table("sites").select("*").eq("site_id", site_id).execute()
        return result.data[0] if result.data else None
    
    def update_site(self, site_id: str, updates: Dict) -> Dict:
        """Update a site"""
        updates["updated_at"] = datetime.utcnow().isoformat()
        result = self.client.table("sites").update(updates).eq("site_id", site_id).execute()
        return result.data[0] if result.data else None
    
    def delete_site(self, site_id: str) -> bool:
        """Delete a site (cascade deletes all related data)"""
        result = self.client.table("sites").delete().eq("site_id", site_id).execute()
        return len(result.data) > 0
    
    # ==================== SAMPLE OPERATIONS (v2.0) ====================
    
    def create_sample(self, site_id: str, sample_code: str, 
                     tool_type: str = None, raw_material: str = None,
                     location_on_tool: str = None, preservation_status: str = None,
                     # Visual attributes integrated in same table
                     visual_color: str = None, visual_texture: str = None,
                     visual_transparency: str = None, visual_luster: str = None,
                     visual_morphology: str = None, visual_description: str = None,
                     sample_notes: str = None) -> Dict:
        """Create a new sample with visual attributes integrated"""
        data = {
            "site_id": site_id,
            "sample_code": sample_code,
            "tool_type": tool_type,
            "raw_material": raw_material,
            "location_on_tool": location_on_tool,
            "preservation_status": preservation_status,
            # Visual attributes
            "visual_color": visual_color,
            "visual_texture": visual_texture,
            "visual_transparency": visual_transparency,
            "visual_luster": visual_luster,
            "visual_morphology": visual_morphology,
            "visual_description": visual_description,
            "sample_notes": sample_notes
        }
        
        result = self.client.table("samples").insert(data).execute()
        return result.data[0] if result.data else None
    
    def get_samples(self, site_id: str = None, project_id: str = None) -> List[Dict]:
        """Get all samples, optionally filtered by site or project"""
        if project_id:
            # Get samples through site-project relationship
            query = self.client.table("samples").select(
                "*, sites!inner(site_id, site_name, project_id)"
            ).eq("sites.project_id", project_id)
        elif site_id:
            query = self.client.table("samples").select("*").eq("site_id", site_id)
        else:
            query = self.client.table("samples").select("*")
        
        result = query.order("sample_code").execute()
        return result.data if result.data else []
    
    def get_sample(self, sample_id: str) -> Optional[Dict]:
        """Get a specific sample by ID with all visual attributes"""
        result = self.client.table("samples").select("*").eq("sample_id", sample_id).execute()
        return result.data[0] if result.data else None
    
    def update_sample(self, sample_id: str, updates: Dict) -> Dict:
        """Update a sample"""
        updates["updated_at"] = datetime.utcnow().isoformat()
        result = self.client.table("samples").update(updates).eq("sample_id", sample_id).execute()
        return result.data[0] if result.data else None
    
    def delete_sample(self, sample_id: str) -> bool:
        """Delete a sample (cascade deletes all related analyses)"""
        result = self.client.table("samples").delete().eq("sample_id", sample_id).execute()
        return len(result.data) > 0
    
    # ==================== EDS ANALYSIS OPERATIONS (v2.0) ====================
    
    def create_eds_analysis(self, sample_id: str, elemental_data: Dict,
                           analysis_metadata: Dict = None) -> Dict:
        """
        Create a new EDS analysis
        
        elemental_data: Dict with elements as lowercase keys (c, p, ca, etc.)
        analysis_metadata: Optional dict with acquisition parameters
        """
        data = {
            "sample_id": sample_id,
            # Elemental composition (lowercase column names in database)
            "c": elemental_data.get("C") or elemental_data.get("c"),
            "n": elemental_data.get("N") or elemental_data.get("n"),
            "o": elemental_data.get("O") or elemental_data.get("o"),
            "p": elemental_data.get("P") or elemental_data.get("p"),
            "ca": elemental_data.get("Ca") or elemental_data.get("ca"),
            "k": elemental_data.get("K") or elemental_data.get("k"),
            "al": elemental_data.get("Al") or elemental_data.get("al"),
            "mn": elemental_data.get("Mn") or elemental_data.get("mn"),
            "fe": elemental_data.get("Fe") or elemental_data.get("fe"),
            "si": elemental_data.get("Si") or elemental_data.get("si"),
            "mg": elemental_data.get("Mg") or elemental_data.get("mg"),
            "na": elemental_data.get("Na") or elemental_data.get("na"),
            "s": elemental_data.get("S") or elemental_data.get("s"),
            "cl": elemental_data.get("Cl") or elemental_data.get("cl"),
            "ti": elemental_data.get("Ti") or elemental_data.get("ti"),
            "zn": elemental_data.get("Zn") or elemental_data.get("zn"),
        }
        
        # Add metadata if provided
        if analysis_metadata:
            data.update({
                "analysis_date": analysis_metadata.get("analysis_date"),
                "analyst": analysis_metadata.get("analyst"),
                "instrument": analysis_metadata.get("instrument"),
                "accelerating_voltage_kv": analysis_metadata.get("accelerating_voltage_kv"),
                "beam_current_na": analysis_metadata.get("beam_current_na"),
                "analysis_point_number": analysis_metadata.get("analysis_point_number"),
                "analysis_notes": analysis_metadata.get("analysis_notes")
            })
        
        # Calculate Ca/P ratio if both present
        if data.get("ca") and data.get("p"):
            data["ca_p_ratio"] = data["ca"] / data["p"]
        
        result = self.client.table("eds_analyses").insert(data).execute()
        return result.data[0] if result.data else None
    
    def get_eds_analyses(self, sample_id: str = None, site_id: str = None) -> List[Dict]:
        """Get EDS analyses, optionally filtered by sample or site"""
        if site_id:
            query = self.client.table("eds_analyses").select(
                "*, samples!inner(sample_id, sample_code, site_id)"
            ).eq("samples.site_id", site_id)
        elif sample_id:
            query = self.client.table("eds_analyses").select("*").eq("sample_id", sample_id)
        else:
            query = self.client.table("eds_analyses").select("*")
        
        result = query.order("created_at", desc=True).execute()
        return result.data if result.data else []
    
    def update_eds_analysis(self, analysis_id: str, updates: Dict) -> Dict:
        """Update an EDS analysis (e.g., add classification results)"""
        updates["updated_at"] = datetime.utcnow().isoformat()
        result = self.client.table("eds_analyses").update(updates).eq("analysis_id", analysis_id).execute()
        return result.data[0] if result.data else None
    
    # ==================== STATISTICS & AGGREGATIONS (v2.0) ====================
    
    def get_site_statistics(self, site_id: str = None) -> List[Dict]:
        """Get pre-computed site statistics"""
        query = self.client.table("site_statistics").select("*")
        
        if site_id:
            query = query.eq("site_id", site_id)
        
        result = query.execute()
        return result.data if result.data else []
    
    def get_project_summary(self, project_id: str = None) -> List[Dict]:
        """Get pre-computed project summaries"""
        query = self.client.table("project_summary").select("*")
        
        if project_id:
            query = query.eq("project_id", project_id)
        
        result = query.execute()
        return result.data if result.data else []
    
    # ==================== BULK OPERATIONS (v2.0) ====================
    
    def bulk_create_samples(self, samples_data: List[Dict]) -> List[Dict]:
        """Create multiple samples at once"""
        result = self.client.table("samples").insert(samples_data).execute()
        return result.data if result.data else []
    
    def bulk_create_eds_analyses(self, analyses_data: List[Dict]) -> List[Dict]:
        """Create multiple EDS analyses at once"""
        result = self.client.table("eds_analyses").insert(analyses_data).execute()
        return result.data if result.data else []
    
    # ==================== SPECTRAL LIBRARY OPERATIONS (v2.1) ====================
    
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
        query = self.client.table("spectral_library").select("*")
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
    
    # ==================== MULTI-MODAL ANALYSIS OPERATIONS (v2.1) ====================
    
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
    
    # ==================== EXPERIMENTAL SAMPLES OPERATIONS (v2.1) ====================
    
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
    
    # ==================== LIBRARY SEARCH OPERATIONS (v2.1) ====================
    
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


# ==================== DISTANCE CALCULATION FUNCTIONS (v2.1) ====================

def calculate_euclidean_distance(spectrum1: Dict, spectrum2: Dict, elements: List[str]) -> float:
    """Calculate Euclidean distance between two spectra"""
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
    """Calculate Manhattan distance between two spectra"""
    vec1 = np.array([spectrum1.get(e, 0) for e in elements])
    vec2 = np.array([spectrum2.get(e, 0) for e in elements])
    
    return np.sum(np.abs(vec1 - vec2))


def calculate_chi_square_distance(spectrum1: Dict, spectrum2: Dict, elements: List[str]) -> float:
    """Calculate Chi-square distance between two spectra"""
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


# ==================== CONNECTION HELPER FUNCTIONS ====================

def get_db_connection() -> TaphoSpecDB:
    """Get or create database connection from session state"""
    if 'db' not in st.session_state or st.session_state.db is None:
        st.session_state.db = TaphoSpecDB()
    return st.session_state.db


def init_session_state_db():
    """Initialize database-related session state variables"""
    if 'current_project_id' not in st.session_state:
        st.session_state.current_project_id = None
    
    if 'current_site_id' not in st.session_state:
        st.session_state.current_site_id = None
    
    if 'current_sample_id' not in st.session_state:
        st.session_state.current_sample_id = None
    
    if 'db' not in st.session_state:
        st.session_state.db = None
