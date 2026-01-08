"""
Database module for TaphoSpec
Handles all Supabase PostgreSQL interactions
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import streamlit as st

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


class TaphoSpecDB:
    """Database connection and operations for TaphoSpec"""
    
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
    
    # ==================== PROJECT OPERATIONS ====================
    
    def create_project(self, project_name: str, description: str = None, 
                      principal_investigator: str = None, institution: str = None,
                      is_public: bool = False) -> Dict:
        """Create a new project"""
        data = {
            "project_name": project_name,
            "description": description,
            "principal_investigator": principal_investigator,
            "institution": institution,
            "is_public": is_public
        }
        
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
    
    # ==================== SITE OPERATIONS ====================
    
    def create_site(self, project_id: str, site_name: str, country: str = None,
                   latitude: float = None, longitude: float = None, 
                   site_type: str = None, excavation_year: int = None,
                   context_type: str = None, stratigraphy: str = None,
                   site_description: str = None) -> Dict:
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
    
    # ==================== SAMPLE OPERATIONS ====================
    
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
    
    # ==================== EDS ANALYSIS OPERATIONS ====================
    
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
    
    # ==================== STATISTICS & AGGREGATIONS ====================
    
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
    
    # ==================== BULK OPERATIONS ====================
    
    def bulk_create_samples(self, samples_data: List[Dict]) -> List[Dict]:
        """Create multiple samples at once"""
        result = self.client.table("samples").insert(samples_data).execute()
        return result.data if result.data else []
    
    def bulk_create_eds_analyses(self, analyses_data: List[Dict]) -> List[Dict]:
        """Create multiple EDS analyses at once"""
        result = self.client.table("eds_analyses").insert(analyses_data).execute()
        return result.data if result.data else []


# Convenience function for getting database connection
def get_db_connection() -> TaphoSpecDB:
    """Get or create database connection from session state"""
    if 'db' not in st.session_state or st.session_state.db is None:
        st.session_state.db = TaphoSpecDB()
    return st.session_state.db
