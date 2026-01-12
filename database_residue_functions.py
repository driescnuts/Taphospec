# ================================================
# RESIDUE FUNCTIONS - Add to database.py v2.2
# ================================================
# Insert these functions in the TaphoSpecDB class

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


def update_residue(self, residue_id: str, updates: Dict) -> Dict:
    """Update residue information"""
    
    # Add updated_at timestamp
    updates['updated_at'] = 'now()'
    
    result = self.client.table("residues").update(updates).eq("residue_id", residue_id).execute()
    return result.data[0] if result.data else None


def delete_residue(self, residue_id: str) -> bool:
    """Delete residue (cascades to EDS analyses)"""
    
    result = self.client.table("residues").delete().eq("residue_id", residue_id).execute()
    return True


def get_residue_summary(self, sample_id: str = None) -> List[Dict]:
    """Get residue summary with EDS point counts"""
    
    query = self.client.table("residue_summary").select("*")
    
    if sample_id:
        query = query.eq("sample_id", sample_id)
    
    result = query.order("sample_code", desc=False).order("residue_number", desc=False).execute()
    return result.data if result.data else []


def get_next_residue_number(self, sample_id: str) -> int:
    """Get next available residue number for a sample"""
    
    result = self.client.table("residues").select("residue_number").eq("sample_id", sample_id).order("residue_number", desc=True).limit(1).execute()
    
    if result.data:
        return result.data[0]['residue_number'] + 1
    return 1


def link_eds_to_residue(self, analysis_id: str, residue_id: str) -> bool:
    """Link an EDS analysis to a residue"""
    
    result = self.client.table("eds_analyses").update({
        "residue_id": residue_id
    }).eq("analysis_id", analysis_id).execute()
    
    return True


def get_eds_by_residue(self, residue_id: str) -> List[Dict]:
    """Get all EDS analyses for a specific residue"""
    
    result = self.client.table("eds_analyses").select("*").eq("residue_id", residue_id).order("analysis_point_number").execute()
    
    return result.data if result.data else []


def create_residue_with_eds(self, sample_id: str, residue_data: Dict, eds_analyses: List[str]) -> Dict:
    """Create residue and link multiple EDS analyses to it"""
    
    # Create residue
    residue = self.create_residue(
        sample_id=sample_id,
        residue_number=residue_data.get('residue_number'),
        location_on_tool=residue_data.get('location_on_tool'),
        location_description=residue_data.get('location_description'),
        visual_color=residue_data.get('visual_color'),
        visual_texture=residue_data.get('visual_texture'),
        visual_transparency=residue_data.get('visual_transparency'),
        visual_luster=residue_data.get('visual_luster'),
        visual_morphology=residue_data.get('visual_morphology'),
        visual_distribution=residue_data.get('visual_distribution'),
        visual_preservation=residue_data.get('visual_preservation'),
        residue_photo=residue_data.get('residue_photo'),
        visual_notes=residue_data.get('visual_notes')
    )
    
    if not residue:
        return None
    
    residue_id = residue['residue_id']
    
    # Link EDS analyses
    for analysis_id in eds_analyses:
        self.link_eds_to_residue(analysis_id, residue_id)
    
    return self.get_residue_with_analyses(residue_id)


def get_residues_for_site(self, site_id: str) -> List[Dict]:
    """Get all residues for a site (across all samples)"""
    
    # Get samples for this site
    samples = self.get_samples(site_id=site_id)
    sample_ids = [s['sample_id'] for s in samples]
    
    if not sample_ids:
        return []
    
    # Get residues for these samples
    result = self.client.table("residue_summary").select("*").in_("sample_id", sample_ids).execute()
    
    return result.data if result.data else []


# ================================================
# UPDATED: EDS Analysis Functions
# ================================================
# These need to be UPDATED in existing database.py

def create_eds_analysis(self, residue_id: str, analysis_point_number: int,
                       c: float = None, n: float = None, o: float = None,
                       p: float = None, ca: float = None, k: float = None,
                       al: float = None, mn: float = None, fe: float = None,
                       si: float = None, mg: float = None, na: float = None,
                       s: float = None, cl: float = None, ti: float = None,
                       zn: float = None, ba: float = None, sr: float = None,
                       classification: str = None, ca_p_ratio: float = None,
                       analysis_date: str = None, analyst: str = None) -> Dict:
    """
    Create new EDS analysis linked to a residue
    NOTE: Now takes residue_id instead of sample_id!
    """
    
    data = {
        "residue_id": residue_id,  # Changed from sample_id!
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
    """
    Get EDS analyses, optionally filtered
    NOTE: Now supports filtering by residue_id!
    """
    
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


# ================================================
# HELPER FUNCTIONS
# ================================================

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


def import_residue_data(self, sample_id: str, data_rows: List[Dict]) -> Dict:
    """
    Import multiple EDS analyses grouped by residue
    
    Expected format:
    [
        {
            'residue': 1,
            'point': 1,
            'location': 'edge',
            'color': 'black',
            'c': 45.2,
            'p': 1.8,
            ...
        },
        ...
    ]
    """
    
    # Group by residue number
    residues_data = {}
    
    for row in data_rows:
        residue_num = row.get('residue', 1)
        
        if residue_num not in residues_data:
            residues_data[residue_num] = {
                'residue_number': residue_num,
                'location_on_tool': row.get('location'),
                'visual_color': row.get('color'),
                'visual_texture': row.get('texture'),
                'visual_notes': row.get('visual_notes'),
                'eds_points': []
            }
        
        residues_data[residue_num]['eds_points'].append(row)
    
    # Create residues and link EDS
    created_residues = []
    
    for residue_num, residue_info in residues_data.items():
        # Create residue
        residue = self.create_residue(
            sample_id=sample_id,
            residue_number=residue_num,
            location_on_tool=residue_info.get('location_on_tool'),
            visual_color=residue_info.get('visual_color'),
            visual_texture=residue_info.get('visual_texture'),
            visual_notes=residue_info.get('visual_notes')
        )
        
        if not residue:
            continue
        
        residue_id = residue['residue_id']
        
        # Create EDS analyses
        for point_data in residue_info['eds_points']:
            self.create_eds_analysis(
                residue_id=residue_id,
                analysis_point_number=point_data.get('point', 1),
                c=point_data.get('c'),
                n=point_data.get('n'),
                o=point_data.get('o'),
                p=point_data.get('p'),
                ca=point_data.get('ca'),
                k=point_data.get('k'),
                al=point_data.get('al'),
                mn=point_data.get('mn'),
                fe=point_data.get('fe'),
                si=point_data.get('si'),
                mg=point_data.get('mg'),
                na=point_data.get('na'),
                s=point_data.get('s'),
                cl=point_data.get('cl')
            )
        
        created_residues.append(residue)
    
    return {
        'sample_id': sample_id,
        'residues_created': len(created_residues),
        'residues': created_residues
    }
