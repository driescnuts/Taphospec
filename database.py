"""
TaphoSpec Database Module v2.4
Handles all database operations using Supabase
Includes residue-based data model with context-aware features
"""

import os
from supabase import create_client, Client
import streamlit as st
from datetime import datetime
from typing import Optional, Dict, List, Any


class TaphoSpecDB:
    """Database handler for TaphoSpec using Supabase"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        """Initialize database connection"""
        self.client: Client = create_client(supabase_url, supabase_key)
    
    # ================================================
    # PROJECT MANAGEMENT
    # ================================================
    
    def create_project(self, project_name: str, description: str = None) -> Dict:
        """Create a new project"""
        data = {
            "project_name": project_name,
            "description": description,
            "created_at": datetime.utcnow().isoformat()
        }
        result = self.client.table("projects").insert(data).execute()
        return result.data[0] if result.data else None
    
    def get_projects(self) -> List[Dict]:
        """Get all projects"""
        result = self.client.table("projects").select("*").execute()
        return result.data if result.data else []
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """Get a specific project"""
        result = self.client.table("projects").select("*").eq("project_id", project_id).execute()
        return result.data[0] if result.data else None
    
    # ================================================
    # SITE MANAGEMENT
    # ================================================
    
    def create_site(self, project_id: str, site_name: str, **kwargs) -> Dict:
        """Create a new site"""
        data = {
            "project_id": project_id,
            "site_name": site_name,
            "country": kwargs.get('country'),
            "region": kwargs.get('region'),
            "latitude": kwargs.get('latitude'),
            "longitude": kwargs.get('longitude'),
            "elevation": kwargs.get('elevation'),
            "context_type": kwargs.get('context_type'),
            "time_period": kwargs.get('time_period'),
            "excavation_year": kwargs.get('excavation_year'),
            "created_at": datetime.utcnow().isoformat()
        }
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        
        result = self.client.table("sites").insert(data).execute()
        return result.data[0] if result.data else None
    
    def get_sites(self, project_id: str = None) -> List[Dict]:
        """Get all sites"""
        query = self.client.table("sites").select("*")
        if project_id:
            query = query.eq("project_id", project_id)
        result = query.execute()
        return result.data if result.data else []
    
    def get_site(self, site_id: str) -> Optional[Dict]:
        """Get a specific site"""
        result = self.client.table("sites").select("*").eq("site_id", site_id).execute()
        return result.data[0] if result.data else None
    
    # ================================================
    # SAMPLE MANAGEMENT
    # ================================================
    
    def create_sample(self, site_id: str, sample_code: str, **kwargs) -> Dict:
        """Create a new sample"""
        data = {
            "site_id": site_id,
            "sample_code": sample_code,
            "tool_type": kwargs.get('tool_type'),
            "material": kwargs.get('material'),
            "context": kwargs.get('context'),
            "created_at": datetime.utcnow().isoformat()
        }
        data = {k: v for k, v in data.items() if v is not None}
        result = self.client.table("samples").insert(data).execute()
        return result.data[0] if result.data else None
    
    def get_samples(self, site_id: str = None) -> List[Dict]:
        """Get all samples"""
        query = self.client.table("samples").select("*")
        if site_id:
            query = query.eq("site_id", site_id)
        result = query.execute()
        return result.data if result.data else []
    
    def get_sample(self, sample_id: str) -> Optional[Dict]:
        """Get a specific sample"""
        result = self.client.table("samples").select("*").eq("sample_id", sample_id).execute()
        return result.data[0] if result.data else None
    
    # ================================================
    # RESIDUE MANAGEMENT (v2.2+)
    # ================================================
    
    def create_residue(self, sample_id: str, residue_number: int, 
                      location_on_tool: str = None, location_description: str = None,
                      visual_color: str = None, visual_texture: str = None,
                      visual_transparency: str = None, visual_luster: str = None,
                      visual_morphology: str = None, visual_distribution: str = None,
                      visual_preservation: str = None, residue_photo: str = None,
                      visual_notes: str = None) -> Dict:
        """Create new residue on a sample"""
        
        data = {
            "sample_id": sample_id,
            "residue_number": residue_number,
            "location_on_tool": location_on_tool,
            "location_description": location_description,
            "visual_color": visual_color,
            "visual_texture": visual_texture,
            "visual_transparency": visual_transparency,
            "visual_luster": visual_luster,
            "visual_morphology": visual_morphology,
            "visual_distribution": visual_distribution,
            "visual_preservation": visual_preservation,
            "residue_photo": residue_photo,
            "visual_notes": visual_notes
        }
        
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        
        result = self.client.table("residues").insert(data).execute()
        return result.data[0] if result.data else None
    
    def get_residues(self, sample_id: str = None, residue_id: str = None) -> List[Dict]:
        """Get residues, optionally filtered"""
        
        query = self.client.table("residues").select("*")
        
        if residue_id:
            query = query.eq("residue_id", residue_id)
        elif sample_id:
            query = query.eq("sample_id", sample_id)
        
        result = query.order("residue_number", desc=False).execute()
        return result.data if result.data else []
    
    def get_residue_with_analyses(self, residue_id: str) -> Dict:
        """Get residue with all its EDS analyses"""
        
        # Get residue info
        residue_result = self.client.table("residues").select("*").eq("residue_id", residue_id).execute()
        
        if not residue_result.data:
            return None
        
        residue = residue_result.data[0]
        
        # Get all EDS analyses for this residue
        eds_result = self.client.table("eds_analyses").select("*").eq("residue_id", residue_id).order("analysis_point_number").execute()
        
        residue['eds_analyses'] = eds_result.data if eds_result.data else []
        
        return residue
    
    def get_sample_with_residues(self, sample_id: str) -> Dict:
        """Get sample with all residues and their EDS analyses"""
        
        # Get sample
        sample_result = self.client.table("samples").select("*").eq("sample_id", sample_id).execute()
        
        if not sample_result.data:
            return None
        
        sample = sample_result.data[0]
        
        # Get residues
        residues = self.get_residues(sample_id=sample_id)
        
        # Get EDS analyses for each residue
        for residue in residues:
            residue['eds_analyses'] = self.get_eds_by_residue(residue['residue_id'])
        
        sample['residues'] = residues
        
        return sample
    
    # ================================================
    # EDS ANALYSIS (Updated for residue model)
    # ================================================
    
    def create_eds_analysis(self, residue_id: str, analysis_point_number: int,
                           c: float = None, n: float = None, o: float = None,
                           p: float = None, ca: float = None, k: float = None,
                           al: float = None, mn: float = None, fe: float = None,
                           si: float = None, mg: float = None, na: float = None,
                           s: float = None, cl: float = None, ti: float = None,
                           zn: float = None, ba: float = None, sr: float = None,
                           classification: str = None, ca_p_ratio: float = None,
                           analysis_date: str = None, analyst: str = None) -> Dict:
        """Create new EDS analysis linked to a residue"""
        
        data = {
            "residue_id": residue_id,
            "analysis_point_number": analysis_point_number,
            "c": c, "n": n, "o": o, "p": p, "ca": ca, "k": k,
            "al": al, "mn": mn, "fe": fe, "si": si, "mg": mg,
            "na": na, "s": s, "cl": cl, "ti": ti, "zn": zn,
            "ba": ba, "sr": sr,
            "classification": classification,
            "ca_p_ratio": ca_p_ratio,
            "analysis_date": analysis_date,
            "analyst": analyst
        }
        
        # Calculate Ca/P ratio if both present
        if ca is not None and p is not None and p > 0:
            data['ca_p_ratio'] = ca / p
        
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        
        result = self.client.table("eds_analyses").insert(data).execute()
        return result.data[0] if result.data else None
    
    def get_eds_analyses(self, residue_id: str = None, sample_id: str = None, 
                        site_id: str = None) -> List[Dict]:
        """Get EDS analyses, optionally filtered"""
        
        if residue_id:
            # Direct query by residue
            query = self.client.table("eds_analyses").select("*").eq("residue_id", residue_id)
        elif site_id:
            # Use view for site filtering
            query = self.client.table("eds_complete").select("*").eq("site_id", site_id)
        elif sample_id:
            # Get via residues
            residues = self.get_residues(sample_id=sample_id)
            residue_ids = [r['residue_id'] for r in residues]
            
            if not residue_ids:
                return []
            
            query = self.client.table("eds_analyses").select("*").in_("residue_id", residue_ids)
        else:
            # Get all
            query = self.client.table("eds_analyses").select("*")
        
        result = query.order("created_at", desc=True).execute()
        return result.data if result.data else []
    
    def get_eds_by_residue(self, residue_id: str) -> List[Dict]:
        """Get all EDS analyses for a specific residue"""
        
        result = self.client.table("eds_analyses").select("*").eq("residue_id", residue_id).order("analysis_point_number").execute()
        
        return result.data if result.data else []


# ================================================
# CONNECTION HELPER
# ================================================

@st.cache_resource
def get_db_connection():
    """Get database connection (cached)"""
    supabase_url = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("Supabase credentials not found. Set SUPABASE_URL and SUPABASE_KEY in secrets.")
    
    return TaphoSpecDB(supabase_url, supabase_key)


def init_session_state_db():
    """Initialize database-related session state"""
    if 'db' not in st.session_state:
        try:
            st.session_state.db = get_db_connection()
        except Exception as e:
            st.error(f"Database connection failed: {str(e)}")
            st.session_state.db = None
