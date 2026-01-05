"""
TaphoSpec Database Module
Supabase/PostgreSQL integration for archaeological residue data
"""

import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd
from supabase import create_client, Client
import streamlit as st

class TaphoSpecDB:
    """
    Database interface for TaphoSpec application.
    Handles all CRUD operations with Supabase backend.
    """
    
    def __init__(self):
        """Initialize Supabase client"""
        # Get credentials from Streamlit secrets or environment
        try:
            supabase_url = st.secrets["SUPABASE_URL"]
            supabase_key = st.secrets["SUPABASE_KEY"]
        except:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("Supabase credentials not found. Please configure in .streamlit/secrets.toml")
        
        self.client: Client = create_client(supabase_url, supabase_key)
    
    # ==========================================
    # PROJECT OPERATIONS
    # ==========================================
    
    def create_project(self, 
                      project_name: str,
                      description: str = None,
                      principal_investigator: str = None,
                      institution: str = None,
                      is_public: bool = False) -> Dict:
        """Create a new project"""
        data = {
            "project_name": project_name,
            "description": description,
            "principal_investigator": principal_investigator,
            "institution": institution,
            "is_public": is_public
        }
        
        response = self.client.table("projects").insert(data).execute()
        return response.data[0] if response.data else None
    
    def get_projects(self, user_only: bool = False) -> pd.DataFrame:
        """Get all accessible projects"""
        response = self.client.table("projects").select("*").execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    
    def get_project(self, project_id: str) -> Dict:
        """Get single project by ID"""
        response = self.client.table("projects").select("*").eq("project_id", project_id).execute()
        return response.data[0] if response.data else None
    
    def update_project(self, project_id: str, updates: Dict) -> Dict:
        """Update project information"""
        response = self.client.table("projects").update(updates).eq("project_id", project_id).execute()
        return response.data[0] if response.data else None
    
    def delete_project(self, project_id: str) -> bool:
        """Delete project (cascade deletes sites, samples, analyses)"""
        response = self.client.table("projects").delete().eq("project_id", project_id).execute()
        return len(response.data) > 0
    
    # ==========================================
    # SITE OPERATIONS
    # ==========================================
    
    def create_site(self,
                   project_id: str,
                   site_name: str,
                   latitude: float,
                   longitude: float,
                   country: str = None,
                   context_type: str = None,
                   **kwargs) -> Dict:
        """Create a new site"""
        data = {
            "project_id": project_id,
            "site_name": site_name,
            "latitude": latitude,
            "longitude": longitude,
            "country": country,
            "context_type": context_type,
            **kwargs
        }
        
        response = self.client.table("sites").insert(data).execute()
        return response.data[0] if response.data else None
    
    def get_sites(self, project_id: str = None) -> pd.DataFrame:
        """Get sites, optionally filtered by project"""
        query = self.client.table("sites").select("*")
        
        if project_id:
            query = query.eq("project_id", project_id)
        
        response = query.execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    
    def get_site(self, site_id: str) -> Dict:
        """Get single site by ID"""
        response = self.client.table("sites").select("*").eq("site_id", site_id).execute()
        return response.data[0] if response.data else None
    
    def get_site_statistics(self) -> pd.DataFrame:
        """Get pre-computed site statistics from view"""
        response = self.client.table("site_statistics").select("*").execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    
    def update_site(self, site_id: str, updates: Dict) -> Dict:
        """Update site information"""
        response = self.client.table("sites").update(updates).eq("site_id", site_id).execute()
        return response.data[0] if response.data else None
    
    # ==========================================
    # SAMPLE OPERATIONS
    # ==========================================
    
    def create_sample(self,
                     site_id: str,
                     sample_code: str,
                     artifact_type: str = None,
                     raw_material: str = None,
                     **kwargs) -> Dict:
        """Create a new sample"""
        data = {
            "site_id": site_id,
            "sample_code": sample_code,
            "artifact_type": artifact_type,
            "raw_material": raw_material,
            **kwargs
        }
        
        response = self.client.table("samples").insert(data).execute()
        return response.data[0] if response.data else None
    
    def get_samples(self, site_id: str = None) -> pd.DataFrame:
        """Get samples, optionally filtered by site"""
        query = self.client.table("samples").select("*")
        
        if site_id:
            query = query.eq("site_id", site_id)
        
        response = query.execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    
    def get_sample(self, sample_id: str) -> Dict:
        """Get single sample by ID"""
        response = self.client.table("samples").select("*").eq("sample_id", sample_id).execute()
        return response.data[0] if response.data else None
    
    def update_sample(self, sample_id: str, updates: Dict) -> Dict:
        """Update sample information"""
        response = self.client.table("samples").update(updates).eq("sample_id", sample_id).execute()
        return response.data[0] if response.data else None
    
    # ==========================================
    # EDS ANALYSIS OPERATIONS
    # ==========================================
    
    def create_eds_analysis(self,
                           sample_id: str,
                           elemental_data: Dict,
                           authentication: Dict,
                           **kwargs) -> Dict:
        """Create a new EDS analysis"""
        data = {
            "sample_id": sample_id,
            **elemental_data,  # C, P, Ca, Mn, Fe, etc.
            "classification": authentication.get('classification'),
            "confidence": authentication.get('confidence'),
            "reasoning": authentication.get('reasoning'),
            "recommendation": authentication.get('recommendation'),
            "ca_p_ratio": authentication.get('ca_p_ratio'),
            **kwargs
        }
        
        response = self.client.table("eds_analyses").insert(data).execute()
        return response.data[0] if response.data else None
    
    def bulk_create_eds_analyses(self, analyses: List[Dict]) -> List[Dict]:
        """Bulk insert multiple EDS analyses"""
        response = self.client.table("eds_analyses").insert(analyses).execute()
        return response.data if response.data else []
    
    def get_eds_analyses(self, sample_id: str = None, site_id: str = None) -> pd.DataFrame:
        """Get EDS analyses, optionally filtered"""
        query = self.client.table("eds_analyses").select("*, samples(site_id, sample_code)")
        
        if sample_id:
            query = query.eq("sample_id", sample_id)
        
        response = query.execute()
        df = pd.DataFrame(response.data) if response.data else pd.DataFrame()
        
        # Filter by site if needed (after join)
        if site_id and not df.empty:
            df = df[df['samples'].apply(lambda x: x['site_id'] == site_id if x else False)]
        
        return df
    
    def update_eds_analysis(self, analysis_id: str, updates: Dict) -> Dict:
        """Update EDS analysis"""
        response = self.client.table("eds_analyses").update(updates).eq("analysis_id", analysis_id).execute()
        return response.data[0] if response.data else None
    
    # ==========================================
    # BATCH IMPORT FROM CSV/EXCEL
    # ==========================================
    
    def import_eds_data_from_dataframe(self, 
                                       df: pd.DataFrame, 
                                       site_id: str,
                                       sample_prefix: str = "AUTO") -> Tuple[int, int]:
        """
        Import EDS data from DataFrame (from CSV upload).
        Creates samples automatically if needed.
        
        Returns: (n_samples_created, n_analyses_created)
        """
        n_samples = 0
        n_analyses = 0
        
        for idx, row in df.iterrows():
            # Create sample
            sample_code = f"{sample_prefix}_{idx+1:03d}"
            
            sample = self.create_sample(
                site_id=site_id,
                sample_code=sample_code,
                sample_notes=f"Auto-imported from batch upload"
            )
            
            if sample:
                n_samples += 1
                sample_id = sample['sample_id']
                
                # Extract elemental data
                elemental_cols = ['C', 'N', 'O', 'P', 'Ca', 'K', 'Al', 'Mn', 'Fe', 'Si', 
                                'Mg', 'Na', 'S', 'Cl', 'Ti', 'Zn']
                elemental_data = {}
                
                for col in elemental_cols:
                    if col in row and pd.notna(row[col]):
                        elemental_data[col] = float(row[col])
                
                # Authentication would happen here (imported from app.py)
                # For now, store raw data
                
                analysis = self.create_eds_analysis(
                    sample_id=sample_id,
                    elemental_data=elemental_data,
                    authentication={},  # To be filled by authentication function
                    analysis_notes="Auto-imported from batch upload"
                )
                
                if analysis:
                    n_analyses += 1
        
        return n_samples, n_analyses
    
    # ==========================================
    # EXPORT FUNCTIONS
    # ==========================================
    
    def export_project_to_csv(self, project_id: str) -> pd.DataFrame:
        """Export all project data to DataFrame for CSV export"""
        # Get all data with joins
        query = """
        SELECT 
            p.project_name,
            s.site_name,
            s.latitude,
            s.longitude,
            s.context_type,
            sam.sample_code,
            sam.artifact_type,
            sam.raw_material,
            eds.*
        FROM projects p
        JOIN sites s ON p.project_id = s.project_id
        JOIN samples sam ON s.site_id = sam.site_id
        JOIN eds_analyses eds ON sam.sample_id = eds.sample_id
        WHERE p.project_id = %s
        """
        
        # Supabase doesn't support raw SQL easily, so we'll do it with multiple queries
        sites = self.get_sites(project_id)
        
        all_data = []
        for _, site in sites.iterrows():
            samples = self.get_samples(site['site_id'])
            
            for _, sample in samples.iterrows():
                analyses = self.get_eds_analyses(sample['sample_id'])
                
                for _, analysis in analyses.iterrows():
                    row = {
                        **site.to_dict(),
                        **sample.to_dict(),
                        **analysis.to_dict()
                    }
                    all_data.append(row)
        
        return pd.DataFrame(all_data)
    
    # ==========================================
    # SEARCH & FILTER
    # ==========================================
    
    def search_samples(self, 
                      search_term: str = None,
                      context_type: str = None,
                      raw_material: str = None,
                      classification: str = None) -> pd.DataFrame:
        """
        Search samples with various filters
        """
        # Complex query with joins - would need to be built step by step
        query = self.client.table("samples").select("""
            *,
            sites(*),
            eds_analyses(*)
        """)
        
        # Add filters as needed
        response = query.execute()
        
        df = pd.DataFrame(response.data) if response.data else pd.DataFrame()
        
        # Apply additional filters in pandas
        if context_type and not df.empty:
            df = df[df['sites'].apply(lambda x: x.get('context_type') == context_type if x else False)]
        
        if raw_material and not df.empty:
            df = df[df['raw_material'] == raw_material]
        
        return df


# ==========================================
# HELPER FUNCTIONS FOR STREAMLIT
# ==========================================

@st.cache_resource
def get_db_connection():
    """
    Cached database connection for Streamlit.
    Use this in your app.py:
    
    db = get_db_connection()
    """
    return TaphoSpecDB()


def init_session_state_db():
    """Initialize database-related session state"""
    if 'current_project_id' not in st.session_state:
        st.session_state.current_project_id = None
    
    if 'current_site_id' not in st.session_state:
        st.session_state.current_site_id = None
    
    if 'current_sample_id' not in st.session_state:
        st.session_state.current_sample_id = None
