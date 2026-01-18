import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from scipy.stats import pearsonr
from io import BytesIO

# Database integration
try:
    from database import get_db_connection, init_session_state_db
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

# Authentication integration
try:
    from auth import (
        AuthManager, 
        check_authentication, 
        render_user_menu,
        init_auth_session_state,
        is_admin,
        render_admin_panel
    )
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False

# Phase 2: Library features
try:
    from page_library_search import render_library_search_page
    from page_library_management import render_library_management_page
    LIBRARY_PAGES_AVAILABLE = True
except ImportError:
    LIBRARY_PAGES_AVAILABLE = False

# Initialize database connection
database_enabled = False
db = None
if DATABASE_AVAILABLE:
    try:
        db = get_db_connection()
        database_enabled = True
    except Exception as e:
        database_enabled = False
        print(f"Database connection failed: {e}")

# Initialize authentication
if AUTH_AVAILABLE:
    try:
        init_auth_session_state()
    except Exception as e:
        print(f"Auth initialization failed: {e}")


# Page configuration
st.set_page_config(
    page_title="TaphoSpec - Archaeological Residue Analysis",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #2E7D32;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2E7D32;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# ================================================
# CONTEXT-AWARE AUTHENTICATION (v2.4)
# ================================================

# Context reference database with geoarchaeological citations
CONTEXT_REFERENCES = {
    "cave_guano": {
        "name": "Cave (Guano-Rich)",
        "key_papers": [
            "Karkanas, P., Bar-Yosef, O., Goldberg, P., & Weiner, S. (2000). Diagenesis in prehistoric caves. Journal of Archaeological Science, 27(10), 915-929.",
            "Weiner, S. (2010). Microarchaeology: Beyond the Visible Archaeological Record. Cambridge University Press.",
            "Goldberg, P., Miller, C. E., & Mentzer, S. M. (2017). Recognizing fire in the Paleolithic archaeological record. Current Anthropology, 58(S16), S175-S190."
        ],
        "expected_signatures": {
            "P_min": 3.0,
            "P_max": 20.0,
            "C_baseline": 10.0,
            "Mn_indicator": 0.5
        },
        "corrections": {
            "C_adjustment": True,
            "P_baseline": 5.0
        },
        "interpretation": """
        Guano-rich caves present unique taphonomic challenges:
        - Elevated phosphorus (P) from bat/bird guano is EXPECTED, not contamination
        - Carbon (C) enrichment from guano organics requires correction
        - Manganese (Mn) >0.5% is diagnostic of bat guano (Karkanas 2000)
        - Alkaline pH from guano promotes carbonate preservation
        """,
        "method": "Karkanas (2000) guano-cave criteria with corrections"
    },
    
    "cave_carbonate": {
        "name": "Cave (Carbonate-Rich)",
        "key_papers": [
            "Karkanas, P., & Goldberg, P. (2019). Reconstructing Archaeological Sites. Wiley-Blackwell.",
            "Shahack-Gross, R. (2011). Herbivorous livestock dung. Journal of Archaeological Science, 38(2), 205-218."
        ],
        "expected_signatures": {
            "P_min": 0.5,
            "P_max": 3.0
        },
        "interpretation": """
        Carbonate-rich caves provide moderate preservation:
        - Alkaline pH (typically 8-9) promotes carbonate formation
        - Calcium (Ca) enrichment from speleothem formation
        - Moderate organic preservation
        """,
        "method": "Standard Karkanas & Weiner (2010) with carbonate consideration"
    },
    
    "open_air_sand": {
        "name": "Open-Air (Sand/Sandstone)",
        "key_papers": [
            "Goldberg, P., & Berna, F. (2010). Micromorphology and context. Quaternary International, 214(1-2), 56-62.",
            "Miller, C. E., Goldberg, P., & Berna, F. (2013). Geoarchaeological investigations at Diepkloof. Journal of Archaeological Science, 40(9), 3432-3452."
        ],
        "expected_signatures": {
            "P_min": 0.1,
            "P_max": 2.0,
            "C_max": 15.0
        },
        "corrections": {
            "leaching_factor": 0.5
        },
        "interpretation": """
        Open-air sites present POOR preservation conditions:
        - Phosphorus (P) depletion due to leaching (Goldberg & Berna 2010)
        - Rapid oxidation destroys organics
        - Silicon (Si) enrichment from sand/sandstone matrix
        - Surviving organics indicate EXCEPTIONAL preservation
        """,
        "method": "Goldberg & Berna (2010) open-air criteria with leaching correction"
    },
    
    "open_air_clay": {
        "name": "Open-Air (Clay/Silt)",
        "key_papers": [
            "Goldberg, P., & Berna, F. (2010). Micromorphology and context.",
            "Macphail, R. I., & Goldberg, P. (2018). Applied Soils and Micromorphology. Cambridge."
        ],
        "expected_signatures": {
            "P_min": 0.2,
            "P_max": 3.0
        },
        "interpretation": """
        Clay-rich open-air sites offer better preservation than sand:
        - Clay minerals can sequester and protect organics
        - Moderate P retention
        """,
        "method": "Modified Karkanas & Weiner for clay contexts"
    },
    
    "rockshelter": {
        "name": "Rockshelter",
        "key_papers": [
            "Karkanas, P., et al. (2007). Evidence for habitual use of fire. Journal of Human Evolution, 53(2), 197-212.",
            "Goldberg, P., et al. (2009). Bedding, hearths at Sibudu Cave. Archaeological Sciences, 1(2), 95-122."
        ],
        "expected_signatures": {
            "P_min": 0.5,
            "P_max": 5.0
        },
        "interpretation": """
        Rockshelters offer GOOD intermediate preservation:
        - Protection from direct weathering
        - Variable pH depending on bedrock geology
        """,
        "method": "Standard Karkanas & Weiner (2010) criteria"
    },
    
    "peat_bog": {
        "name": "Peat Bog",
        "key_papers": [
            "van Geel, B. (2001). Non-pollen palynomorphs. Tracking Environmental Change. Springer.",
            "Harrault, L., et al. (2019). Faecal biomarkers distinguish species. PLoS ONE, 14(2)."
        ],
        "expected_signatures": {
            "P_min": 0.0,
            "P_max": 0.5
        },
        "corrections": {
            "ignore_ca_p": True
        },
        "interpretation": """
        Peat bogs provide EXCEPTIONAL organic preservation:
        - Acidic conditions (pH 3-5) destroy mineral residues
        - Waterlogged anaerobic environment preserves organics
        - Ca/P ratios are MEANINGLESS - ignore mineral indicators
        """,
        "method": "Bog-specific organic-only analysis"
    }
}

def authenticate_with_context(data, site_context):
    """Apply context-specific authentication criteria"""
    
    context_type = site_context.get('context_type', 'unknown')
    
    if context_type in CONTEXT_REFERENCES:
        context_params = CONTEXT_REFERENCES[context_type]
    else:
        return authenticate_standard(data)
    
    results = data.copy()
    
    # Apply context-specific logic
    if context_type == "cave_guano":
        results = authenticate_guano_cave(results, context_params, site_context)
    elif "open_air" in context_type:
        results = authenticate_open_air(results, context_params, site_context)
    elif context_type == "peat_bog":
        results = authenticate_peat_bog(results, context_params)
    else:
        results = authenticate_standard(results)
    
    return {
        'results': results,
        'methodology': context_params['method'],
        'references': context_params['key_papers'],
        'interpretation': context_params['interpretation']
    }

def authenticate_guano_cave(data, context_params, site_context):
    """Apply guano-cave specific authentication"""
    
    results = data.copy()
    guano_baseline_P = context_params['corrections']['P_baseline']
    
    for idx, row in results.iterrows():
        C = row.get('c', 0)
        P = row.get('p', 0)
        Mn = row.get('mn', 0)
        Ca = row.get('ca', 0)
        
        corrected_P = max(0, P - guano_baseline_P)
        
        if Mn > context_params['expected_signatures']['Mn_indicator']:
            results.at[idx, 'guano_indicator'] = f"Bat guano (Mn={Mn:.2f}%)"
        
        if C > 10 and P > 5:
            guano_C_contribution = (P / guano_baseline_P) * context_params['expected_signatures']['C_baseline']
            corrected_C = max(0, C - guano_C_contribution)
            results.at[idx, 'corrected_c'] = corrected_C
        else:
            results.at[idx, 'corrected_c'] = C
        
        corrected_C_val = results.at[idx, 'corrected_c']
        
        if corrected_C_val > 20:
            classification = "Organic"
            confidence = "High" if corrected_P < 2 else "Medium"
        elif corrected_P > 10 and Ca/P < 2.0 if P > 0 else False:
            classification = "Apatite"
            confidence = "Medium"
        elif corrected_C_val < 5 and corrected_P < 2:
            classification = "Mimic"
            confidence = "High"
        else:
            classification = "Mixed/Uncertain"
            confidence = "Low"
        
        results.at[idx, 'context_adjusted_classification'] = classification
        results.at[idx, 'confidence_level'] = confidence
    
    return results

def authenticate_open_air(data, context_params, site_context):
    """Apply open-air specific authentication"""
    
    results = data.copy()
    
    for idx, row in results.iterrows():
        C = row.get('c', 0)
        P = row.get('p', 0)
        Si = row.get('si', 0)
        
        if Si > 20:
            results.at[idx, 'contamination_note'] = f"High Si ({Si:.1f}%) - sediment contamination"
        
        if C > 20:
            results.at[idx, 'context_adjusted_classification'] = "Organic (Exceptional!)"
            results.at[idx, 'confidence_level'] = "High"
        elif P > context_params['expected_signatures']['P_max']:
            results.at[idx, 'context_adjusted_classification'] = "Apatite (Unexpected)"
            results.at[idx, 'confidence_level'] = "Low"
        elif C < 10 and P < 1:
            results.at[idx, 'context_adjusted_classification'] = "Mimic (Expected)"
            results.at[idx, 'confidence_level'] = "High"
        else:
            results.at[idx, 'context_adjusted_classification'] = "Mixed/Degraded"
            results.at[idx, 'confidence_level'] = "Medium"
    
    return results

def authenticate_peat_bog(data, context_params):
    """Apply peat bog specific authentication"""
    
    results = data.copy()
    
    for idx, row in results.iterrows():
        C = row.get('c', 0)
        P = row.get('p', 0)
        
        if C > 30:
            results.at[idx, 'context_adjusted_classification'] = "Organic (Well-Preserved)"
            results.at[idx, 'confidence_level'] = "High"
        elif C > 15:
            results.at[idx, 'context_adjusted_classification'] = "Organic (Moderate)"
            results.at[idx, 'confidence_level'] = "Medium"
        elif P > 1:
            results.at[idx, 'context_adjusted_classification'] = "Anomalous (mineral in bog)"
            results.at[idx, 'confidence_level'] = "Low"
        else:
            results.at[idx, 'context_adjusted_classification'] = "Uncertain"
            results.at[idx, 'confidence_level'] = "Low"
    
    return results

def authenticate_standard(data):
    """Standard Karkanas & Weiner (2010) criteria"""
    
    results = data.copy()
    
    for idx, row in results.iterrows():
        C = row.get('c', 0)
        P = row.get('p', 0)
        Ca = row.get('ca', 0)
        Ca_P = Ca/P if P > 0 else 0
        
        if C > 20 and P < 3:
            classification = "Organic"
            confidence = "High"
        elif P > 10 and 1.2 < Ca_P < 2.2:
            classification = "Apatite"
            confidence = "High"
        elif C < 10 and P < 3:
            classification = "Mimic"
            confidence = "High"
        else:
            classification = "Mixed/Uncertain"
            confidence = "Medium"
        
        results.at[idx, 'context_adjusted_classification'] = classification
        results.at[idx, 'confidence_level'] = confidence
    
    return results



# ================================================
# HELPER FUNCTIONS FOR ENHANCED SITE FORM
# ================================================

def get_context_description(context_type):
    '''Get brief description of expected signatures'''
    descriptions = {
        "cave_guano": "High P (3-20%), Mn indicator for bat guano",
        "cave_carbonate": "High Ca, moderate P (0.5-3%)",
        "open_air_sand": "Low P (<2%), Si contamination",
        "peat_bog": "Very low P, excellent organic preservation"
    }
    return descriptions.get(context_type, "See literature for expected signatures")

def render_enhanced_site_form(db):
    '''Enhanced site registration form with full taphonomic context'''
    
    with st.expander("➕ Register New Site with Full Context", expanded=False):
        with st.form("new_site_context"):
            st.markdown("### Basic Site Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                site_name = st.text_input("Site Name*", placeholder="e.g., Spy Cave")
                country = st.text_input("Country*", placeholder="e.g., Belgium")
                region = st.text_input("Region", placeholder="e.g., Wallonia")
            
            with col2:
                latitude = st.number_input("Latitude*", min_value=-90.0, max_value=90.0, value=50.48, format="%.6f")
                longitude = st.number_input("Longitude*", min_value=-180.0, max_value=180.0, value=4.72, format="%.6f")
                elevation = st.number_input("Elevation (m)", value=200)
            
            st.markdown("---")
            st.markdown("### 🌍 Geographic Context")
            
            col1, col2 = st.columns(2)
            
            with col1:
                climate_zone = st.selectbox("Climate Zone*", [
                    "Tropical", "Subtropical", "Temperate",
                    "Mediterranean", "Arid/Semi-arid", "Arctic"
                ])
            
            with col2:
                rainfall = st.selectbox("Rainfall", [
                    "Humid (>1000mm)", "Moderate (500-1000mm)",
                    "Dry (<500mm)", "Variable"
                ])
            
            st.markdown("---")
            st.markdown("### 🏛️ Depositional Context")
            st.info("⚠️ This determines authentication criteria!")
            
            context_type = st.selectbox("Primary Context*", [
                "cave_guano", "cave_carbonate", "cave_other",
                "rockshelter", "open_air_sand", "open_air_clay",
                "open_air_loess", "peat_bog", "volcanic_ash", "other"
            ], format_func=lambda x: {
                "cave_guano": "🦇 Cave (Guano-Rich)",
                "cave_carbonate": "🪨 Cave (Carbonate)",
                "cave_other": "🕳️ Cave (Other)",
                "rockshelter": "🏔️ Rockshelter",
                "open_air_sand": "🏖️ Open-Air (Sand)",
                "open_air_clay": "🧱 Open-Air (Clay)",
                "open_air_loess": "🌾 Open-Air (Loess)",
                "peat_bog": "🌿 Peat Bog",
                "volcanic_ash": "🌋 Volcanic Ash",
                "other": "❓ Other"
            }.get(x, x))
            
            if context_type in ["cave_guano", "open_air_sand", "peat_bog"]:
                st.caption(f"ℹ️ {get_context_description(context_type)}")
            
            st.markdown("---")
            st.markdown("### 🧪 Taphonomic Factors")
            
            col1, col2 = st.columns(2)
            
            with col1:
                ph_condition = st.selectbox("pH Conditions", [
                    "Acidic (pH <6)", "Neutral (pH 6-8)",
                    "Alkaline (pH >8)", "Unknown"
                ])
            
            with col2:
                water_table = st.selectbox("Water Regime", [
                    "Saturated", "Seasonal", "Well-Drained", "Unknown"
                ])
            
            guano_presence = st.checkbox("🦇 Bat/Bird Guano Present")
            
            st.markdown("---")
            st.markdown("### 📊 Expected Preservation")
            
            col1, col2 = st.columns(2)
            
            with col1:
                organic_preservation = st.select_slider(
                    "Organic Preservation",
                    options=["Very Poor", "Poor", "Fair", "Good", "Excellent"],
                    value="Fair"
                )
            
            with col2:
                mineral_preservation = st.select_slider(
                    "Mineral Preservation",
                    options=["Very Poor", "Poor", "Fair", "Good", "Excellent"],
                    value="Fair"
                )
            
            st.markdown("---")
            st.markdown("### 📚 References")
            
            site_references = st.text_area(
                "Key Publications",
                placeholder="e.g., Goldberg et al. (2009)...",
                height=80
            )
            
            taphonomic_notes = st.text_area(
                "Taphonomic Notes",
                placeholder="Additional observations...",
                height=80
            )
            
            st.markdown("---")
            
            submitted = st.form_submit_button("✅ Register Site", type="primary")
            
            if submitted and site_name and country:
                try:
                    # Get or create project
                    projects = db.get_projects()
                    if not projects or len(projects) == 0:
                        default_project = db.create_project(
                            project_name="Default Project",
                            description="Auto-created"
                        )
                        project_id = default_project['project_id']
                    else:
                        project_id = projects[0]['project_id']
                    
                    # Create site
                    site_data = {
                        "project_id": project_id,
                        "site_name": site_name,
                        "country": country,
                        "latitude": latitude,
                        "longitude": longitude,
                        "elevation": elevation,
                        "climate_zone": climate_zone,
                        "context_type": context_type,
                        "ph_condition": ph_condition,
                        "water_table": water_table,
                        "guano_presence": guano_presence,
                        "organic_preservation": organic_preservation,
                        "site_references": site_references,
                        "taphonomic_notes": taphonomic_notes
                    }
                    
                    site = db.client.table("sites").insert(site_data).execute()
                    
                    if site.data:
                        st.success(f"✅ Registered: {site_name} with context!")
                        st.session_state.current_site_id = site.data[0]['site_id']
                        st.rerun()
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    st.exception(e)

# NAVIGATION - v2.3 CLEAN STRUCTURE
# ==============================================

# Initialize session state for page navigation
if 'page' not in st.session_state:
    st.session_state.page = "Home"

with st.sidebar:
    st.header("🔬 TaphoSpec v2.3")
    
    # Quick Access Buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏠 Home", use_container_width=True, key="quick_home"):
            st.session_state.page = "Home"
    with col2:
        if st.button("🔍 Identify", use_container_width=True, key="quick_identify"):
            st.session_state.page = "Library Search"
    
    st.markdown("---")
    
    # ================================================
    # ARCHAEOLOGICAL DATA Section
    # ================================================
    with st.expander("🏛️ ARCHAEOLOGICAL DATA", expanded=True):
        if st.button("📁 Sites", use_container_width=True, key="nav_sites"):
            st.session_state.page = "Sites"
        if st.button("📥 Import Analyses", use_container_width=True, key="nav_import"):
            st.session_state.page = "Data Import"
        if database_enabled:
            if st.button("📊 Dataset Statistics", use_container_width=True, key="nav_stats"):
                st.session_state.page = "Statistics"
    
    # ================================================
    # IDENTIFICATION Section  
    # ================================================
    if database_enabled and LIBRARY_PAGES_AVAILABLE:
        with st.expander("🔍 IDENTIFICATION", expanded=False):
            if st.button("🔍 Identify Unknown", use_container_width=True, key="nav_identify"):
                st.session_state.page = "Library Search"
    
    # ================================================
    # TAPHONOMIC ANALYSIS Section
    # ================================================
    with st.expander("🧪 TAPHONOMIC ANALYSIS", expanded=False):
        if st.button("🎯 Bulk Authentication", use_container_width=True, key="nav_auth"):
            st.session_state.page = "Authentication"
        if st.button("📊 Correlations", use_container_width=True, key="nav_corr"):
            st.session_state.page = "Correlation Analysis"
    
    # ================================================
    # REPORTS Section
    # ================================================
    with st.expander("📋 REPORTS", expanded=False):
        if st.button("📋 Site Reports", use_container_width=True, key="nav_report"):
            st.session_state.page = "Report"
    
    # ================================================
    # REFERENCE LIBRARY Section
    # ================================================
    if database_enabled and LIBRARY_PAGES_AVAILABLE:
        with st.expander("📚 REFERENCE LIBRARY", expanded=False):
            if st.button("➕ Manage Entries", use_container_width=True, key="nav_manage"):
                st.session_state.page = "Library Management"
            if st.button("🗺️ Reference Origins", use_container_width=True, key="nav_origins"):
                st.session_state.page = "Reference Origins"
            if st.button("📊 Library Statistics", use_container_width=True, key="nav_libstats"):
                st.session_state.page = "Library Statistics"
    
    # ================================================
    # SETTINGS Section (Admin only)
    # ================================================
    if AUTH_AVAILABLE and is_admin():
        st.markdown("---")
        if st.button("⚙️ Admin Panel", use_container_width=True, key="nav_admin"):
            st.session_state.page = "Admin Panel"
    
    st.markdown("---")
    
    # User menu (if authentication is enabled)
    if AUTH_AVAILABLE:
        render_user_menu()
    
    # Database status indicator
    if database_enabled:
        st.success("🗄️ Database: Connected")
        if 'current_project_id' in st.session_state and st.session_state.current_project_id:
            st.info(f"📁 Active Project")
        if 'current_site_id' in st.session_state and st.session_state.current_site_id:
            st.info(f"📍 Active Site")
    else:
        st.warning("🗄️ Standalone Mode")
    
    st.markdown("---")
    
    # Version info
    st.caption("TaphoSpec v2.3 - Clean Structure")
    st.caption("TraceoLab - ULiège")

if 'data' not in st.session_state:
    st.session_state.data = None
if 'authenticated_data' not in st.session_state:
    st.session_state.authenticated_data = None

# Database-related session state
if database_enabled:
    if 'current_project_id' not in st.session_state:
        st.session_state.current_project_id = None
    if 'current_site_id' not in st.session_state:
        st.session_state.current_site_id = None
    if 'current_sample_id' not in st.session_state:
        st.session_state.current_sample_id = None


# Get current page from session state
page = st.session_state.get('page', 'Home')

# ==============================================
# HOME PAGE
# ==============================================
if page == "Home":
    # Don't add another title - Streamlit shows page_title already
    st.markdown("---")
    
    # Quick overview cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🏛️ Archaeological Data")
        st.markdown("""
        - Organize sites with residues
        - Import EDS analyses  
        - Dataset statistics
        """)
        if st.button("→ Sites", key="home_sites"):
            st.session_state.page = "Sites"
            st.rerun()
    
    with col2:
        st.markdown("### 🔍 Identification")
        st.markdown("""
        - Search library
        - Select analysis points
        - Identify residues
        """)
        if database_enabled and LIBRARY_PAGES_AVAILABLE:
            if st.button("→ Identify", key="home_identify"):
                st.session_state.page = "Library Search"
                st.rerun()
    
    with col3:
        st.markdown("### 📉 Analysis")
        st.markdown("""
        - Bulk authentication
        - Correlations
        - Reports
        """)
        if st.button("→ Analyze", key="home_analysis"):
            st.session_state.page = "Correlation Analysis"
            st.rerun()

# Page: Data Import
elif page == "Data Import":
    st.header("📁 Data Import")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        Upload your SEM-EDS data file (CSV, Excel, or Tab-delimited format).
        
        **Required columns:** C, P, Ca, Mn  
        **Optional columns:** N, O, K, Al, Fe, Si, Mg, Na, S, Cl, Ti, Zn
        """)
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['csv', 'xlsx', 'xls', 'txt'],
            help="Upload CSV or Excel file with elemental composition data (mass %)"
        )
        
        if uploaded_file is not None:
            try:
                # Read file
                if uploaded_file.name.endswith('.csv') or uploaded_file.name.endswith('.txt'):
                    # Try reading with comma as decimal first (European)
                    try:
                        df = pd.read_csv(uploaded_file, decimal=',')
                    except:
                        # If that fails, try with period as decimal (US)
                        uploaded_file.seek(0)
                        df = pd.read_csv(uploaded_file, decimal='.')
                else:
                    df = pd.read_excel(uploaded_file)
                
                # Convert numeric columns to float
                numeric_cols = ['C', 'N', 'O', 'P', 'Ca', 'K', 'Al', 'Mn', 'Fe', 'Si', 'Mg', 'Na', 'S', 'Cl', 'Ti', 'Zn']
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Check required columns
                required_cols = ['C', 'P', 'Ca', 'Mn']
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
                else:
                    st.session_state.data = df
                    
                    # Authenticate all points
                    auth_results = []
                    for idx, row in df.iterrows():
                        auth = authenticate_residue(row)
                        auth_results.append(auth)
                    
                    st.session_state.authenticated_data = pd.DataFrame(auth_results)
                    
                    st.success(f"✅ Successfully loaded {len(df)} analysis points!")
                    
                    st.markdown("### Data Preview")
                    st.dataframe(df.head(10), use_container_width=True)
                    
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")
    
    with col2:
        st.markdown("""
        ### 📋 Data Format
        
        **Example structure:**
        ```
        C,P,Ca,Mn,Fe,...
        45.6,0.8,2.1,0.1,0.4
        38.2,2.9,4.2,0.2,0.8
        6.8,9.1,7.2,24.3,3.1
        ```
        
        **Tips:**
        - Use comma or semicolon as separator
        - European decimal notation (,) supported
        - First row must be headers
        - Mass percentages (%)
        """)

# Page: Correlation Analysis
elif page == "Correlation Analysis":
    if st.session_state.data is None:
        st.warning("⚠️ Please upload data first in the Data Import section.")
    else:
        st.header("📈 Elemental Correlation Analysis")
        
        st.markdown("""
        <div class="interpretation-box">
        <strong>Methodological Approach:</strong> Different diagenetic pathways produce characteristic patterns 
        of elemental co-occurrence. Strong correlations quantitatively identify dominant geochemical processes 
        affecting preservation.
        </div>
        """, unsafe_allow_html=True)
        
        correlations = calculate_correlations(st.session_state.data)
        
        # Display correlations in grid
        cols = st.columns(2)
        
        for idx, corr in enumerate(correlations):
            with cols[idx % 2]:
                st.markdown(f"### {corr['name']}")
                
                # Scatter plot
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=corr['x_data'],
                    y=corr['y_data'],
                    mode='markers',
                    marker=dict(
                        size=8,
                        color='#10b981' if corr['significant'] and corr['r'] > 0 else '#ef4444' if corr['significant'] else '#94a3b8',
                        opacity=0.6
                    ),
                    name='Data points'
                ))
                
                # Add trend line if significant
                if corr['significant']:
                    z = np.polyfit(corr['x_data'], corr['y_data'], 1)
                    p = np.poly1d(z)
                    x_line = np.linspace(corr['x_data'].min(), corr['x_data'].max(), 100)
                    
                    fig.add_trace(go.Scatter(
                        x=x_line,
                        y=p(x_line),
                        mode='lines',
                        line=dict(
                            color='#10b981' if corr['r'] > 0 else '#ef4444',
                            width=2,
                            dash='dash'
                        ),
                        name='Trend line',
                        opacity=0.4
                    ))
                
                fig.update_layout(
                    xaxis_title=f"{corr['x']} (mass %)",
                    yaxis_title=f"{corr['y']} (mass %)",
                    showlegend=False,
                    height=300,
                    margin=dict(l=10, r=10, t=30, b=10)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Statistics
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Correlation (r)", f"{corr['r']:.3f}")
                with col_b:
                    st.metric("Sample size (n)", corr['n'])
                
                st.caption(f"**{corr['interpretation']}**")
                
                if corr['significant']:
                    strength = "Strong" if abs(corr['r']) > 0.7 else "Moderate"
                    direction = "positive" if corr['r'] > 0 else "negative"
                    
                    if corr['r'] > 0:
                        st.markdown(f"""
                        <div class="success-box">
                        <strong>{strength} {direction} correlation</strong><br>
                        {corr['context']}<br>
                        <em style="font-size: 0.85rem;">Reference: {corr['reference']}</em>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="error-box">
                        <strong>{strength} {direction} correlation</strong><br>
                        {corr['context']}<br>
                        <em style="font-size: 0.85rem;">Reference: {corr['reference']}</em>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("---")
        
        # Interpretation summary
        st.markdown("## 📊 Interpretation Summary")
        
        significant_corrs = [c for c in correlations if c['significant']]
        
        if significant_corrs:
            for corr in significant_corrs:
                st.markdown(f"""
                - **{corr['name']}** (r = {corr['r']:.3f}, n = {corr['n']}): {corr['context']}
                """)
        else:
            st.info("""
            No strong correlations detected. This may indicate:
            - Limited diagenetic alteration in this assemblage
            - High spatial/temporal heterogeneity in preservation
            - Sample size insufficient to detect patterns (n < 20)
            """)

# Page: Authentication
elif page == "Authentication":
    if st.session_state.data is None:
        st.warning("⚠️ Please upload data first in the Data Import section.")
    else:
        st.header("🔍 Residue Authentication")
        
        df = st.session_state.data
        auth_df = st.session_state.authenticated_data
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Points", len(df))
        
        with col2:
            organic_count = sum(auth_df['classification'].str.contains('Organic', na=False))
            st.metric("Organic Residues", organic_count, delta=None, delta_color="normal")
        
        with col3:
            mineral_count = sum(
                auth_df['classification'].str.contains('Mineral|Phosphate', na=False, regex=True)
            )
            st.metric("Mineral Mimics", mineral_count, delta=None, delta_color="inverse")
        
        with col4:
            ca_p_ratios = [r for r in auth_df['ca_p_ratio'] if r is not None]
            avg_ratio = np.mean(ca_p_ratios) if ca_p_ratios else None
            st.metric("Avg Ca/P Ratio", f"{avg_ratio:.2f}" if avg_ratio else "N/A")
        
        # Ca/P Ratio interpretation
        if avg_ratio and 1.5 <= avg_ratio <= 1.8:
            st.markdown(f"""
            <div class="warning-box">
            <strong>Ca/P Ratio Interpretation:</strong> Average ratio {avg_ratio:.2f} is consistent with 
            hydroxyapatite/dahllite - indicates biogenic phosphate from vertebrate-derived material (guano)
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Classification breakdown
        st.markdown("## 📊 Classification Breakdown")
        
        classification_counts = auth_df['classification'].value_counts()
        
        fig = px.bar(
            x=classification_counts.values,
            y=classification_counts.index,
            orientation='h',
            color=classification_counts.index,
            color_discrete_map={
                'Organic Adhesive': '#10b981',
                'Ochre-Loaded Compound Adhesive': '#059669',
                'Mn-Phosphate Mineral Mimic': '#ef4444',
                'Apatite (Biogenic)': '#f97316',
                'K-Al Phosphate (Acidic Diagenesis)': '#f59e0b',
                'Partially Mineralized Organic': '#eab308',
                'Possible Organic Material': '#84cc16',
                'Ambiguous': '#94a3b8'
            }
        )
        
        fig.update_layout(
            showlegend=False,
            xaxis_title="Count",
            yaxis_title="",
            height=300,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Data table with authentication results
        st.markdown("## 📋 Detailed Results")
        
        # Combine data
        display_df = df.copy()
        display_df['Classification'] = auth_df['classification']
        display_df['Confidence'] = auth_df['confidence']
        display_df['Ca/P'] = auth_df['ca_p_ratio'].apply(lambda x: f"{x:.2f}" if x else "N/A")
        
        # Add color coding
        def color_classification(val):
            colors = {
                'Organic Adhesive': 'background-color: #d1fae5',
                'Ochre-Loaded Compound Adhesive': 'background-color: #d1fae5',
                'Mn-Phosphate Mineral Mimic': 'background-color: #fee2e2',
                'Apatite (Biogenic)': 'background-color: #fed7aa',
                'K-Al Phosphate (Acidic Diagenesis)': 'background-color: #fef3c7',
                'Partially Mineralized Organic': 'background-color: #fef9c3',
                'Possible Organic Material': 'background-color: #ecfccb',
                'Ambiguous': 'background-color: #f1f5f9'
            }
            return colors.get(val, '')
        
        styled_df = display_df.style.applymap(
            color_classification,
            subset=['Classification']
        )
        
        st.dataframe(styled_df, use_container_width=True)
        
        # Download results
        st.markdown("---")
        st.markdown("## 💾 Export Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name="taphospec_authentication_results.csv",
                mime="text/csv"
            )
        
        with col2:
            # Excel export
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                display_df.to_excel(writer, sheet_name='Authentication', index=False)
            
            st.download_button(
                label="📥 Download as Excel",
                data=buffer.getvalue(),
                file_name="taphospec_authentication_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# Page: Visual Attributes
elif page == "Visual Attributes":
    if st.session_state.data is None:
        st.warning("⚠️ Please upload data first in the Data Import section.")
    else:
        st.header("👁️ Visual & Morphological Attributes")
        
        st.markdown("""
        <div class="interpretation-box">
        <strong>Multi-Criteria Authentication Framework:</strong> Integrate optical microscopy and SEM observations 
        with elemental data for robust authentication.
        </div>
        """, unsafe_allow_html=True)
        
        # Framework explanation
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **1. Optical Criteria**
            - Amorphous appearance
            - Brown-black color
            - Location in hafting zones
            - Conforming boundaries
            """)
        
        with col2:
            st.markdown("""
            **2. SEM Morphology (500-2000×)**
            - Truly amorphous vs microcrystalline
            - Smooth surfaces vs botryoidal
            - Flow features vs replacement textures
            """)
        
        with col3:
            st.markdown("""
            **3. Elemental Signature**
            - C > 25%, Mn < 1%, P < 3%
            - Ca/P ratios
            - K-Al-P combinations
            """)
        
        st.markdown("---")
        
        # Point selection
        df = st.session_state.data
        auth_df = st.session_state.authenticated_data
        
        point_id = st.selectbox(
            "Select analysis point to document:",
            options=range(1, len(df) + 1),
            format_func=lambda x: f"Point {x} - {auth_df.iloc[x-1]['classification']}"
        )
        
        point_idx = point_id - 1
        point_data = df.iloc[point_idx]
        point_auth = auth_df.iloc[point_idx]
        
        st.markdown(f"### Point {point_id}")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Get elemental data safely
            c_val = point_data.get('C', None)
            mn_val = point_data.get('Mn', None)
            p_val = point_data.get('P', None)
            ca_p = point_auth.get('ca_p_ratio', None)
            
            # Format values safely
            c_str = f"{c_val:.1f}%" if c_val is not None and isinstance(c_val, (int, float)) else 'N/A'
            mn_str = f"{mn_val:.2f}%" if mn_val is not None and isinstance(mn_val, (int, float)) else 'N/A'
            p_str = f"{p_val:.1f}%" if p_val is not None and isinstance(p_val, (int, float)) else 'N/A'
            ca_p_str = f"{ca_p:.2f}" if ca_p is not None and isinstance(ca_p, (int, float)) else 'N/A'
            
            st.markdown(f"""
            **Classification:** {point_auth['classification']}  
            **Confidence:** {point_auth['confidence']}
            
            **Elemental Data:**
            - C: {c_str}
            - Mn: {mn_str}
            - P: {p_str}
            - Ca/P: {ca_p_str}
            """)
        
        with col2:
            st.markdown("**Diagnostic Reasoning:**")
            for reason in point_auth['reasoning']:
                st.markdown(f"- {reason}")
            
            st.markdown(f"**Recommendation:** {point_auth['recommendation']}")
        
        st.markdown("---")
        
        # Visual attributes form
        st.markdown("## 🔬 Optical Microscopy Observations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            color = st.selectbox(
                "Color",
                ["", "Brown", "Dark Brown", "Black", "Brown-Black", "Red-Brown (ochre)", "Yellow-Brown"]
            )
            
            texture = st.selectbox(
                "Texture",
                ["", "Amorphous", "Smooth", "Slightly Granular", "Crystalline", "Botryoidal"]
            )
        
        with col2:
            location = st.selectbox(
                "Location",
                ["", "Backed Edge", "Proximal End", "Ventral Surface", "Dorsal Surface", "Scattered/Random"]
            )
            
            boundaries = st.selectbox(
                "Boundaries",
                ["", "Sharp/Defined", "Conforming to Surface", "Gradational", "Irregular"]
            )
        
        st.markdown("**Additional Features:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            flow_features = st.checkbox("Flow features / plastic deformation visible")
        with col2:
            multiple_apps = st.checkbox("Multiple application episodes")
        with col3:
            sediment_distinct = st.checkbox("Clearly distinct from adhering sediment")
        
        st.markdown("---")
        
        # SEM morphology
        st.markdown("## 🔬 SEM Morphology (500-2000× magnification)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            morphology = st.selectbox(
                "Morphology at High Magnification",
                ["", "Truly Amorphous (no crystallinity)", "Microcrystalline Aggregates (0.5-5 µm)", 
                 "Botryoidal Microtopography", "Radiating Growth Patterns"]
            )
        
        with col2:
            surface = st.selectbox(
                "Surface Characteristics",
                ["", "Smooth, Massive", "Subtle Flow Features", 
                 "Replacement Textures (pseudomorphs)", "Mineral Growth Patterns"]
            )
        
        st.markdown("""
        <div class="interpretation-box">
        <strong>Diagnostic Criteria:</strong><br>
        ✓ <strong>Organic:</strong> Truly amorphous, smooth massive surfaces, sharp boundaries, subtle flow features<br>
        ✗ <strong>Mineral:</strong> Microcrystalline aggregates, botryoidal surfaces, replacement textures, radiating growth
        </div>
        """, unsafe_allow_html=True)
        
        # Save button
        if st.button("💾 Save Visual Attributes", type="primary"):
            st.success("✅ Visual attributes saved for Point " + str(point_id))
            st.info("Note: In full version, these would be saved to a database or exported with the report.")

# Page: Report
elif page == "Report":
    if st.session_state.data is None:
        st.warning("⚠️ Please upload data first in the Data Import section.")
    else:
        st.header("📄 Analysis Report")
        
        df = st.session_state.data
        auth_df = st.session_state.authenticated_data
        correlations = calculate_correlations(df)
        
        # Executive Summary
        st.markdown("## Executive Summary")
        
        st.markdown(f"""
        Analysis of **{len(df)} EDS point analyses** reveals:
        """)
        
        significant_corrs = [c for c in correlations if c['significant']]
        
        for corr in significant_corrs:
            if corr['name'] == 'P-Ca' and corr['r'] > 0.7:
                st.markdown(f"""
                <div class="success-box">
                ✓ <strong>Strong P-Ca correlation (r = {corr['r']:.3f})</strong> indicates widespread 
                calcium phosphate mineralisation - hallmark of guano-driven diagenesis
                </div>
                """, unsafe_allow_html=True)
            
            elif corr['name'] == 'K-Al' and corr['r'] > 0.6:
                st.markdown(f"""
                <div class="warning-box">
                ⚠ <strong>Strong K-Al correlation (r = {corr['r']:.3f})</strong> diagnostic of K-Al phosphate 
                formation under strongly acidic conditions (pH &lt;5)
                </div>
                """, unsafe_allow_html=True)
            
            elif corr['name'] == 'C-P' and corr['r'] < -0.3:
                st.markdown(f"""
                <div class="error-box">
                ✗ <strong>Negative C-P correlation (r = {corr['r']:.3f})</strong> demonstrates phosphate 
                mineralisation systematically replaces organic carbon
                </div>
                """, unsafe_allow_html=True)
        
        ca_p_ratios = [r for r in auth_df['ca_p_ratio'] if r is not None]
        if ca_p_ratios:
            avg_ratio = np.mean(ca_p_ratios)
            if 1.5 <= avg_ratio <= 1.8:
                st.markdown(f"""
                <div class="warning-box">
                📊 <strong>Mean Ca/P ratio: {avg_ratio:.3f}</strong> - consistent with stoichiometric 
                hydroxyapatite/dahllite (biogenic phosphate)
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Classification Breakdown
        st.markdown("## Classification Breakdown")
        
        classification_counts = auth_df['classification'].value_counts()
        total = len(auth_df)
        
        for classification, count in classification_counts.items():
            percentage = (count / total) * 100
            st.markdown(f"- **{classification}**: {count} ({percentage:.1f}%)")
        
        st.markdown("---")
        
        # Recommendations
        st.markdown("## Recommendations")
        
        organic_count = sum(auth_df['classification'].str.contains('Organic', na=False))
        mineral_count = sum(auth_df['classification'].str.contains('Mineral|Phosphate', na=False, regex=True))
        ambiguous_count = sum(auth_df['confidence'].isin(['Medium', 'Low']))
        
        if organic_count > 0:
            st.markdown(f"""
            <div class="success-box">
            ✓ <strong>Organic adhesive candidates:</strong> {organic_count} points show elemental signatures 
            consistent with preserved organic material. Proceed with FTIR spectroscopy and/or GC-MS for 
            molecular confirmation.
            </div>
            """, unsafe_allow_html=True)
        
        if mineral_count > 0:
            st.markdown(f"""
            <div class="error-box">
            ✗ <strong>Mineral mimics identified:</strong> {mineral_count} points show elemental compositions 
            diagnostic of authigenic mineral formation. Exclude from organic residue analysis.
            </div>
            """, unsafe_allow_html=True)
        
        if ambiguous_count > 0:
            st.markdown(f"""
            <div class="warning-box">
            ⚠ <strong>Ambiguous cases:</strong> {ambiguous_count} points require additional analysis. 
            High-magnification SEM morphological assessment (500-2000×) recommended to distinguish 
            microcrystalline textures from truly amorphous organic material.
            </div>
            """, unsafe_allow_html=True)
        
        if any(c['significant'] for c in correlations if c['name'] == 'P-Ca'):
            st.markdown("""
            <div class="warning-box">
            📍 <strong>Taphonomic context:</strong> Strong elemental correlations indicate this assemblage 
            experienced intense guano-driven diagenesis. Preservation likely varies dramatically across 
            spatial/stratigraphic contexts. Consider pilot taphonomic characterisation across excavation 
            units before interpreting behavioural patterns.
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Export button
        if st.button("📥 Download PDF Report", type="primary"):
            st.info("PDF export functionality will be available in future version. Use CSV/Excel export from Authentication page.")

# ==============================================
# NEW DATABASE-ENABLED PAGES
# ==============================================

# Page: Project Management
elif page == "Sites" and database_enabled:
    st.header("📁 Sites")
    st.markdown("### Manage Your Archaeological Sites")
    
    tab1, tab2 = st.tabs(["Sites", "Samples"])
    
    with tab1:
        st.subheader("Your Sites")
        
        # Create new site
        with st.expander("➕ Register New Site"):
            with st.form("new_site"):
                col1, col2 = st.columns(2)
                
                with col1:
                    site_name = st.text_input("Site Name*", placeholder="e.g., Spy Cave")
                    country = st.text_input("Country", placeholder="e.g., Belgium")
                    latitude = st.number_input("Latitude", min_value=-90.0, max_value=90.0, value=50.48, format="%.6f")
                    longitude = st.number_input("Longitude", min_value=-180.0, max_value=180.0, value=4.72, format="%.6f")
                
                with col2:
                    context_type = st.selectbox(
                        "Taphonomic Context",
                        ["cave", "rockshelter", "open_air", "other"]
                    )
                    time_period = st.text_input("Time Period", placeholder="e.g., Middle Palaeolithic")
                    excavation_year = st.number_input("Excavation Year", min_value=1800, max_value=2026, value=2024)
                
                site_notes = st.text_area("Notes", placeholder="Additional site information...")
                
                submitted = st.form_submit_button("Register Site")
                
                if submitted and site_name:
                    try:
                        # Create a default project if none exists
                        projects = db.get_projects()
                        if not projects or len(projects) == 0:
                            # Create default project
                            default_project = db.create_project(
                                project_name="Default Project",
                                description="Auto-created default project"
                            )
                            project_id = default_project['project_id']
                        else:
                            # Use first project
                            project_id = projects[0]['project_id']
                        
                        site = db.create_site(
                            project_id=project_id,
                            site_name=site_name,
                            latitude=latitude,
                            longitude=longitude,
                            country=country,
                            context_type=context_type,
                            time_period=time_period,
                            excavation_year=excavation_year,
                            site_notes=site_notes
                        )
                        st.success(f"✅ Registered site: {site_name}")
                        st.session_state.current_site_id = site['site_id']
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating site: {str(e)}")
        
        # List sites
        try:
            sites = db.get_sites()
            
            if sites and len(sites) > 0:
                for site in sites:
                    with st.container():
                        col1, col2, col3 = st.columns([3, 2, 1])
                        
                        with col1:
                            st.markdown(f"### 📍 {site['site_name']}")
                            if site.get('country'):
                                st.caption(f"{site['country']}")
                        
                        with col2:
                            if site.get('latitude') and site.get('longitude'):
                                st.write(f"🗺️ {site['latitude']:.4f}, {site['longitude']:.4f}")
                            if site.get('context_type'):
                                st.caption(f"Context: {site['context_type']}")
                        
                        with col3:
                            if st.button("Select", key=f"site_{site['site_id']}"):
                                st.session_state.current_site_id = site['site_id']
                                st.rerun()
                        
                        st.markdown("---")
            else:
                st.info("No sites registered yet. Add your first site above!")
                
        except Exception as e:
            st.error(f"Error loading sites: {str(e)}")
    
    with tab2:
        st.subheader("Samples & Residues")
        
        if not st.session_state.current_site_id:
            st.warning("⚠️ Please select a site first (Sites tab)")
        else:
            try:
                # Get selected site info
                sites = db.get_sites()
                current_site = next((s for s in sites if s['site_id'] == st.session_state.current_site_id), None)
                
                if current_site:
                    st.info(f"📍 Selected site: **{current_site['site_name']}**")
                
                # Get samples for this site
                samples = db.get_samples(site_id=st.session_state.current_site_id)
                
                if samples and len(samples) > 0:
                    st.success(f"Found {len(samples)} samples")
                    
                    for sample in samples:
                        with st.expander(f"🔬 {sample['sample_code']}"):
                            # Show sample info
                            if sample.get('tool_type'):
                                st.write(f"**Tool Type:** {sample['tool_type']}")
                            if sample.get('raw_material'):
                                st.write(f"**Raw Material:** {sample['raw_material']}")
                            
                            # Get residues for this sample
                            if hasattr(db, 'get_residues'):
                                residues = db.get_residues(sample_id=sample['sample_id'])
                                
                                if residues and len(residues) > 0:
                                    st.markdown("**Residues:**")
                                    for residue in residues:
                                        st.write(f"- Residue #{residue['residue_number']}: {residue.get('location_on_tool', 'Unknown location')}")
                                        
                                        # Get EDS analyses for this residue
                                        eds_analyses = db.get_eds_analyses(residue_id=residue['residue_id'])
                                        if eds_analyses:
                                            st.caption(f"  └─ {len(eds_analyses)} EDS analysis points")
                                else:
                                    st.caption("No residues recorded")
                            else:
                                # Fallback if residues not available
                                eds_analyses = db.get_eds_analyses(sample_id=sample['sample_id'])
                                if eds_analyses:
                                    st.caption(f"{len(eds_analyses)} EDS analyses")
                else:
                    st.info("No samples yet. Import data to add samples.")
                    
            except Exception as e:
                st.error(f"Error loading samples: {str(e)}")

# Page: Site Map
elif page == "Site Map" and database_enabled:
    st.header("🗺️ Geographic Distribution")
    
    try:
        # Get site statistics
        map_data = db.get_site_statistics()
        
        if len(map_data) == 0:
            st.info("📍 No sites registered yet. Go to Project Management → Sites to add your first site!")
        else:
            # Create map
            fig = px.scatter_mapbox(
                map_data,
                lat='latitude',
                lon='longitude',
                hover_name='site_name',
                hover_data={
                    'n_analyses': True,
                    'n_organic': True,
                    'preservation_rate': ':.1f',
                    'context_type': True,
                    'latitude': False,
                    'longitude': False
                },
                color='preservation_rate',
                color_continuous_scale='RdYlGn',
                size='n_analyses',
                size_max=20,
                zoom=2,
                height=600,
                labels={
                    'preservation_rate': 'Preservation %',
                    'n_analyses': '# Analyses',
                    'n_organic': '# Organic',
                    'context_type': 'Context'
                }
            )
            
            fig.update_layout(
                mapbox_style="open-street-map",
                margin={"r":0,"t":0,"l":0,"b":0}
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Statistics
            st.markdown("### 📊 Summary Statistics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Sites", len(map_data))
            with col2:
                st.metric("Total Analyses", int(map_data['n_analyses'].sum()))
            with col3:
                st.metric("Organic Residues", int(map_data['n_organic'].sum()))
            with col4:
                avg_pres = map_data['preservation_rate'].mean()
                st.metric("Avg Preservation", f"{avg_pres:.1f}%")
            
            # Context breakdown
            st.markdown("### 🏛️ By Taphonomic Context")
            context_summary = map_data.groupby('context_type').agg({
                'site_name': 'count',
                'n_analyses': 'sum',
                'preservation_rate': 'mean'
            }).round(1)
            context_summary.columns = ['Sites', 'Analyses', 'Avg Preservation %']
            st.dataframe(context_summary, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error loading map data: {str(e)}")
        st.info("Make sure you have sites registered with coordinates in Project Management.")

# Page: Statistics
elif page == "Statistics" and database_enabled:
    st.header("📈 Database Statistics")
    
    try:
        # Project summary
        st.subheader("📁 Projects Overview")
        projects = db.get_projects()
        
        if len(projects) > 0:
            # Convert list to DataFrame for easier iteration
            projects_df = pd.DataFrame(projects)
            
            for _, proj in projects_df.iterrows():
                with st.expander(f"📂 {proj['project_name']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if proj.get('principal_investigator'):
                            st.write(f"**PI:** {proj['principal_investigator']}")
                        if proj.get('institution'):
                            st.write(f"**Institution:** {proj['institution']}")
                    
                    with col2:
                        st.write(f"**Created:** {proj['created_at'][:10]}")
                        st.write(f"**Public:** {'Yes' if proj.get('is_public') else 'No'}")
                    
                    # Get project sites
                    sites = db.get_sites(proj['project_id'])
                    st.write(f"**Sites:** {len(sites)}")
        else:
            st.info("No projects yet")
        
        # Overall statistics
        st.markdown("---")
        st.subheader("📊 Overall Statistics")
        
        sites_df = db.get_sites()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Projects", len(projects))
        with col2:
            st.metric("Total Sites", len(sites_df))
        with col3:
            # Would need to count samples/analyses
            st.metric("Data Points", "-")
        
    except Exception as e:
        st.error(f"Error loading statistics: {str(e)}")

# Page: Library Search
elif page == "Library Search" and database_enabled and LIBRARY_PAGES_AVAILABLE:
    render_library_search_page(db)

# Page: Library Management  
elif page == "Library Management" and database_enabled and LIBRARY_PAGES_AVAILABLE:
    render_library_management_page(db)


# Page: Reference Origins (Geographic distribution of library references)
elif page == "Reference Origins" and database_enabled and LIBRARY_PAGES_AVAILABLE:
    st.header("🗺️ Reference Origins")
    st.markdown("### Geographic Distribution of Reference Library")
    
    try:
        db = get_db_connection()
        library_entries = db.get_library_entries()
        
        if library_entries:
            # Get unique sources/locations from library
            locations = []
            for entry in library_entries:
                source = entry.get('source', '')
                if source:
                    locations.append({
                        'name': entry.get('name', 'Unknown'),
                        'source': source,
                        'type': entry.get('type', 'unknown'),
                        'material': entry.get('material_type', 'unknown')
                    })
            
            if locations:
                st.success(f"Found {len(locations)} library entries with source information")
                
                # Group by source
                from collections import Counter
                source_counts = Counter([loc['source'] for loc in locations])
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown("#### Reference Sources")
                    for source, count in source_counts.most_common():
                        with st.expander(f"📍 {source} ({count} references)"):
                            source_entries = [loc for loc in locations if loc['source'] == source]
                            for entry in source_entries:
                                st.markdown(f"- **{entry['name']}** ({entry['type']}) - {entry['material']}")
                
                with col2:
                    st.markdown("#### Statistics")
                    st.metric("Total Sources", len(source_counts))
                    st.metric("Total References", len(locations))
                    
                    type_counts = Counter([loc['type'] for loc in locations])
                    st.markdown("**By Type:**")
                    for ref_type, count in type_counts.items():
                        st.write(f"- {ref_type}: {count}")
                
                st.markdown("---")
                st.markdown("#### Material Distribution")
                material_counts = Counter([loc['material'] for loc in locations])
                
                import plotly.express as px
                fig = px.pie(
                    values=list(material_counts.values()),
                    names=list(material_counts.keys()),
                    title="Reference Library Materials"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No source information available. Add source details when creating references.")
        else:
            st.info("No library entries yet. Add references first.")
    except Exception as e:
        st.error(f"Error: {str(e)}")

# Page: Library Statistics
elif page == "Library Statistics" and database_enabled and LIBRARY_PAGES_AVAILABLE:
    st.header("📊 Library Statistics")
    st.markdown("### Reference Library Composition and Coverage")
    
    try:
        db = get_db_connection()
        library_entries = db.get_library_entries()
        
        if library_entries:
            from collections import Counter
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Entries", len(library_entries))
            
            with col2:
                verified = len([e for e in library_entries if e.get('verified', False)])
                st.metric("Verified", verified)
            
            with col3:
                pct = (verified / len(library_entries) * 100) if library_entries else 0
                st.metric("Verified %", f"{pct:.1f}%")
            
            st.markdown("---")
            
            # Type distribution
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### By Type")
                type_counts = Counter([e.get('type', 'unknown') for e in library_entries])
                for ref_type, count in type_counts.most_common():
                    st.write(f"**{ref_type}:** {count}")
            
            with col2:
                st.markdown("#### By Material")
                material_counts = Counter([e.get('material_type', 'unknown') for e in library_entries])
                for material, count in material_counts.most_common():
                    st.write(f"**{material}:** {count}")
            
            st.markdown("---")
            
            # Visualization
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=list(material_counts.keys()),
                y=list(material_counts.values()),
                name="Materials"
            ))
            fig.update_layout(title="Library Materials Distribution")
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.info("No library entries yet.")
    except Exception as e:
        st.error(f"Error: {str(e)}")


# Page: Admin Panel
elif page == "Admin Panel" and AUTH_AVAILABLE and is_admin():
    render_admin_panel(st.session_state.auth_manager)

st.markdown("---")
st.caption("TaphoSpec v2.1 with Library Features | TraceoLab, University of Liège")

# ==================== LIBRARY PAGES (v2.1) ====================

def render_library_pages_section(database_enabled, db):
    """Handle library page routing"""
    
    # This function should be called from your main page routing logic
    # Add this to your page selection:
    
    # if selected_page == "📚 Library Search":
    #     if database_enabled and LIBRARY_PAGES_AVAILABLE:
    #         render_library_search_page(db)
    #     else:
    #         st.warning("Database required for library search")
    
    # elif selected_page == "📖 Library Management":
    #     if database_enabled and LIBRARY_PAGES_AVAILABLE:
    #         render_library_management_page(db)
    #     else:
    #         st.warning("Database required for library management")
    
    pass

