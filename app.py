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
        font-size: 2.5rem;
        font-weight: bold;
        color: #78350f;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #64748b;
        margin-bottom: 0.25rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #fbbf24;
    }
    .interpretation-box {
        background-color: #f0f9ff;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3b82f6;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fef3c7;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f59e0b;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d1fae5;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #10b981;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #fee2e2;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ef4444;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================
# AUTHENTICATION & DATABASE CONNECTION
# ==============================================

# Initialize authentication
if AUTH_AVAILABLE:
    init_auth_session_state()
    
    # Initialize database connection FIRST (needed for auth_manager)
    if DATABASE_AVAILABLE:
        try:
            db = get_db_connection()
            # Initialize auth manager BEFORE authentication check
            if 'auth_manager' not in st.session_state:
                st.session_state.auth_manager = AuthManager(db.client)
            init_session_state_db()
            database_enabled = True
        except Exception as e:
            database_enabled = False
            st.error(f"⚠️ Database connection failed: {str(e)}")
            st.info("Please check your Supabase credentials in Streamlit secrets.")
            st.stop()
    else:
        st.error("⚠️ Database module not available. Please install dependencies.")
        st.stop()
    
    # NOW check authentication (auth_manager is initialized)
    if not check_authentication():
        st.stop()  # Stop execution if not authenticated
        
else:
    # No authentication - original behavior
    if DATABASE_AVAILABLE:
        try:
            db = get_db_connection()
            init_session_state_db()
            database_enabled = True
        except Exception as e:
            database_enabled = False
            st.sidebar.warning("⚠️ Database not configured. Running in standalone mode.")
    else:
        database_enabled = False

# Authentication functions
def authenticate_residue(row):
    """
    Authenticate residue based on diagnostic elemental criteria.
    """
    # Convert to float, handle non-numeric values
    def safe_float(value):
        try:
            return float(value) if pd.notna(value) else 0.0
        except (ValueError, TypeError):
            return 0.0
    
    C = safe_float(row.get('C', 0))
    Mn = safe_float(row.get('Mn', 0))
    P = safe_float(row.get('P', 0))
    Ca = safe_float(row.get('Ca', 0))
    K = safe_float(row.get('K', 0))
    Al = safe_float(row.get('Al', 0))
    Fe = safe_float(row.get('Fe', 0))
    
    ca_p_ratio = Ca / P if P > 0 else None
    
    # Diagnostic criteria
    criteria = {
        'organic_adhesive': C > 25 and Mn < 1 and P < 3,
        'organic_adhesive_ochre': C > 20 and Fe > 5 and Mn < 1 and P < 5,
        'mn_phosphate': Mn > 5,
        'apatite': P > 10 and ca_p_ratio and 1.5 <= ca_p_ratio <= 1.8 and C < 10,
        'k_al_phosphate': K > 2 and Al > 2 and P > 5,
        'partially_mineralized': 15 <= C <= 25 and 1 <= Mn <= 5 and 3 <= P <= 8
    }
    
    # Classification logic
    if criteria['mn_phosphate']:
        return {
            'classification': 'Mn-Phosphate Mineral Mimic',
            'confidence': 'High',
            'color': '#ef4444',
            'reasoning': [f"Mn > 5% ({Mn:.1f}%) is diagnostic for Mn-bearing phosphates"],
            'recommendation': '✗ Exclude from organic residue analysis',
            'ca_p_ratio': ca_p_ratio
        }
    elif criteria['apatite']:
        return {
            'classification': 'Apatite (Biogenic)',
            'confidence': 'High',
            'color': '#f97316',
            'reasoning': [
                f"P > 10% ({P:.1f}%) with Ca/P ratio {ca_p_ratio:.2f}",
                f"Low carbon ({C:.1f}%) confirms mineral phase"
            ],
            'recommendation': '✗ Exclude from organic residue analysis',
            'ca_p_ratio': ca_p_ratio
        }
    elif criteria['k_al_phosphate']:
        return {
            'classification': 'K-Al Phosphate (Acidic Diagenesis)',
            'confidence': 'High',
            'color': '#f59e0b',
            'reasoning': [f"K > 2%, Al > 2%, P > 5% indicates taranakite/leucophosphite"],
            'recommendation': '✗ Exclude from organic residue analysis',
            'ca_p_ratio': ca_p_ratio
        }
    elif criteria['organic_adhesive']:
        return {
            'classification': 'Organic Adhesive',
            'confidence': 'High',
            'color': '#10b981',
            'reasoning': [
                f"C > 25% ({C:.1f}%) indicates preserved organic material",
                f"Mn < 1% ({Mn:.2f}%) excludes Mn-bearing phases",
                f"P < 3% ({P:.1f}%) indicates minimal mineralization"
            ],
            'recommendation': '✓ Proceed with FTIR/GC-MS',
            'ca_p_ratio': ca_p_ratio
        }
    elif criteria['organic_adhesive_ochre']:
        return {
            'classification': 'Ochre-Loaded Compound Adhesive',
            'confidence': 'High',
            'color': '#059669',
            'reasoning': [
                f"C > 20% ({C:.1f}%) with Fe > 5% ({Fe:.1f}%)",
                f"Mn < 1% excludes Mn-bearing mineral mimics"
            ],
            'recommendation': '✓ Proceed with FTIR/GC-MS',
            'ca_p_ratio': ca_p_ratio
        }
    elif criteria['partially_mineralized']:
        return {
            'classification': 'Partially Mineralized Organic',
            'confidence': 'Medium',
            'color': '#eab308',
            'reasoning': [
                f"Moderate C ({C:.1f}%), Mn ({Mn:.1f}%), P ({P:.1f}%)",
                "Suggests organic material undergoing mineralization"
            ],
            'recommendation': '⚠ Caution: Detailed SEM morphology assessment needed',
            'ca_p_ratio': ca_p_ratio
        }
    elif C > 15 and Mn < 1 and P < 5:
        return {
            'classification': 'Possible Organic Material',
            'confidence': 'Medium',
            'color': '#84cc16',
            'reasoning': [
                f"C > 15% ({C:.1f}%) but below organic threshold",
                "Consider molecular confirmation"
            ],
            'recommendation': '? Additional analyses needed',
            'ca_p_ratio': ca_p_ratio
        }
    else:
        return {
            'classification': 'Ambiguous',
            'confidence': 'Low',
            'color': '#94a3b8',
            'reasoning': ["Mixed elemental signature"],
            'recommendation': '? Additional analyses needed',
            'ca_p_ratio': ca_p_ratio
        }

def calculate_correlations(df):
    """Calculate diagnostic elemental correlations."""
    correlations = []
    
    correlation_pairs = [
        {
            'x': 'P', 'y': 'Ca', 'name': 'P-Ca',
            'interpretation': 'Calcium phosphate mineralisation (guano diagenesis)',
            'context': 'Phosphoric acid from guano decomposition combines with calcium from bones, shells, or ash to form calcium phosphate minerals',
            'threshold': 0.7,
            'expected': 'positive',
            'reference': 'Weiner et al. 2002'
        },
        {
            'x': 'K', 'y': 'Al', 'name': 'K-Al',
            'interpretation': 'K-Al phosphate formation (acidic conditions)',
            'context': 'Under strongly acidic conditions (pH <5), K and Al combine with phosphate to form taranakite and leucophosphite',
            'threshold': 0.6,
            'expected': 'positive',
            'reference': 'Karkanas et al. 2002; Mentzer et al. 2014'
        },
        {
            'x': 'K', 'y': 'P', 'name': 'K-P',
            'interpretation': 'K incorporation into phosphate structures',
            'context': 'Potassium incorporation indicates acidic diagenetic conditions',
            'threshold': 0.6,
            'expected': 'positive',
            'reference': 'Karkanas et al. 2002'
        },
        {
            'x': 'C', 'y': 'P', 'name': 'C-P',
            'interpretation': 'Organic carbon replacement by phosphates',
            'context': 'Negative correlation shows phosphate mineralisation systematically replaces organic carbon',
            'threshold': -0.3,
            'expected': 'negative',
            'reference': 'Shahack-Gross et al. 2004'
        },
        {
            'x': 'C', 'y': 'Mn', 'name': 'C-Mn',
            'interpretation': 'Organic carbon replacement by Mn oxides/phosphates',
            'context': 'Manganese mobilised under reducing conditions replaces organic carbon',
            'threshold': -0.2,
            'expected': 'negative',
            'reference': 'Weiner et al. 2002'
        },
        {
            'x': 'Fe', 'y': 'P', 'name': 'Fe-P',
            'interpretation': 'Iron phosphate vs. iron oxide formation',
            'context': 'Helps distinguish iron phosphates from ochre (iron oxides)',
            'threshold': 0.5,
            'expected': 'positive',
            'reference': 'This study'
        }
    ]
    
    for pair in correlation_pairs:
        if pair['x'] in df.columns and pair['y'] in df.columns:
            # Filter valid data
            valid_data = df[[pair['x'], pair['y']]].dropna()
            valid_data = valid_data[(valid_data > 0).all(axis=1)]
            
            if len(valid_data) >= 3:
                r, p_value = pearsonr(valid_data[pair['x']], valid_data[pair['y']])
                
                significant = (
                    (pair['expected'] == 'positive' and r > abs(pair['threshold'])) or
                    (pair['expected'] == 'negative' and r < pair['threshold'])
                )
                
                correlations.append({
                    **pair,
                    'r': r,
                    'p_value': p_value,
                    'n': len(valid_data),
                    'significant': significant,
                    'x_data': valid_data[pair['x']].values,
                    'y_data': valid_data[pair['y']].values
                })
    
    return correlations

# Header
st.markdown('<div class="main-header">🔬 TaphoSpec</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Multi-Modal Spectroscopic Analysis Platform for Archaeological Residue Authentication</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header" style="font-size: 0.8rem; margin-bottom: 2rem;">TraceoLab · University of Liège · v1.0 Phase 1</div>', unsafe_allow_html=True)

# Sidebar

# ==============================================
# NAVIGATION - v2.2 COLLAPSIBLE STRUCTURE
# ==============================================

# Initialize session state for page navigation
if 'page' not in st.session_state:
    st.session_state.page = "Home"

with st.sidebar:
    st.header("🔬 TaphoSpec v2.2")
    
    # Quick Access Buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏠 Home", use_container_width=True, key="quick_home"):
            st.session_state.page = "Home"
    with col2:
        if st.button("🔍 Identify", use_container_width=True, key="quick_identify"):
            st.session_state.page = "Library Search"
    
    st.markdown("---")
    
    # ARCHAEOLOGICAL DATA Section
    with st.expander("🏛️ ARCHAEOLOGICAL DATA", expanded=True):
        if st.button("📁 Sites", use_container_width=True, key="nav_sites"):
            st.session_state.page = "Project Management"
        if st.button("📥 Import Analyses", use_container_width=True, key="nav_import"):
            st.session_state.page = "Data Import"
        if database_enabled:
            if st.button("📊 Dataset Statistics", use_container_width=True, key="nav_stats"):
                st.session_state.page = "Statistics"
    
    # IDENTIFICATION Section  
    if database_enabled and LIBRARY_PAGES_AVAILABLE:
        with st.expander("🔍 IDENTIFICATION", expanded=False):
            if st.button("🔍 Identify Unknown", use_container_width=True, key="nav_identify"):
                st.session_state.page = "Library Search"
    
    # SITE ANALYSIS Section
    with st.expander("📉 SITE ANALYSIS", expanded=False):
        if st.button("🎯 Bulk Authentication", use_container_width=True, key="nav_auth"):
            st.session_state.page = "Authentication"
        if st.button("📊 Correlations", use_container_width=True, key="nav_corr"):
            st.session_state.page = "Correlation Analysis"
        if database_enabled:
            if st.button("🗺️ Spatial Patterns", use_container_width=True, key="nav_map"):
                st.session_state.page = "Site Map"
        if st.button("📋 Reports", use_container_width=True, key="nav_report"):
            st.session_state.page = "Report"
        if st.button("👁️ Visual Attributes", use_container_width=True, key="nav_visual"):
            st.session_state.page = "Visual Attributes"
    
    # REFERENCE LIBRARY Section
    if database_enabled and LIBRARY_PAGES_AVAILABLE:
        with st.expander("📚 REFERENCE LIBRARY", expanded=False):
            if st.button("📖 Browse & Search", use_container_width=True, key="nav_browse"):
                st.session_state.page = "Library Search"
            if st.button("➕ Manage Entries", use_container_width=True, key="nav_manage"):
                st.session_state.page = "Library Management"
    
    # SETTINGS Section (Admin only)
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
    st.caption("TaphoSpec v2.2 with Residues")
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
    st.markdown('<div class="main-header">🔬 TaphoSpec v2.2</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Archaeological Residue Authentication Platform</div>', unsafe_allow_html=True)
    
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
            st.session_state.page = "Project Management"
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
elif page == "Project Management" and database_enabled:
    st.header("📁 Project Management")
    
    tab1, tab2, tab3 = st.tabs(["Projects", "Sites", "Data Import"])
    
    with tab1:
        st.subheader("Your Projects")
        
        # Create new project
        with st.expander("➕ Create New Project"):
            with st.form("new_project"):
                col1, col2 = st.columns(2)
                
                with col1:
                    proj_name = st.text_input("Project Name*", placeholder="e.g., Krapina Analysis 2024")
                    pi_name = st.text_input("Principal Investigator", placeholder="Your name")
                
                with col2:
                    institution = st.text_input("Institution", placeholder="University of Liège")
                    is_public = st.checkbox("Make public (visible to all users)", value=False)
                
                description = st.text_area("Description", placeholder="Brief project description...")
                
                submitted = st.form_submit_button("Create Project")
                
                if submitted and proj_name:
                    try:
                        project = db.create_project(
                            project_name=proj_name,
                            description=description,
                            principal_investigator=pi_name,
                            institution=institution,
                            is_public=is_public
                        )
                        st.success(f"✅ Created project: {proj_name}")
                        st.session_state.current_project_id = project['project_id']
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating project: {str(e)}")
        
        # List existing projects
        try:
            projects_df = db.get_projects()
            
            if len(projects_df) > 0:
                for _, project in projects_df.iterrows():
                    with st.container():
                        col1, col2, col3 = st.columns([3, 2, 1])
                        
                        with col1:
                            st.markdown(f"### {project['project_name']}")
                            if project.get('description'):
                                st.caption(project['description'])
                        
                        with col2:
                            if project.get('principal_investigator'):
                                st.write(f"👤 {project['principal_investigator']}")
                            if project.get('institution'):
                                st.caption(project['institution'])
                        
                        with col3:
                            if st.button("Select", key=f"proj_{project['project_id']}"):
                                st.session_state.current_project_id = project['project_id']
                                st.rerun()
                        
                        st.markdown("---")
            else:
                st.info("No projects yet. Create your first project above!")
                
        except Exception as e:
            st.error(f"Error loading projects: {str(e)}")
    
    with tab2:
        st.subheader("Sites")
        
        if not st.session_state.current_project_id:
            st.warning("⚠️ Please select a project first (Projects tab)")
        else:
            # Create new site
            with st.expander("➕ Register New Site"):
                with st.form("new_site"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        site_name = st.text_input("Site Name*", placeholder="e.g., Krapina Cave")
                        country = st.text_input("Country", placeholder="e.g., Croatia")
                        latitude = st.number_input("Latitude*", min_value=-90.0, max_value=90.0, value=0.0, format="%.6f")
                        longitude = st.number_input("Longitude*", min_value=-180.0, max_value=180.0, value=0.0, format="%.6f")
                    
                    with col2:
                        context_type = st.selectbox(
                            "Taphonomic Context",
                            ["cave_guano", "cave_carbonate", "rockshelter", "open_air_sand", 
                             "open_air_clay", "peat_bog", "volcanic_ash", "other"]
                        )
                        sediment_type = st.text_input("Sediment Type", placeholder="e.g., guano-rich")
                        time_period = st.text_input("Time Period", placeholder="e.g., Middle Palaeolithic")
                        excavation_year = st.number_input("Excavation Year", min_value=1800, max_value=2026, value=2024)
                    
                    site_notes = st.text_area("Notes", placeholder="Additional site information...")
                    
                    submitted = st.form_submit_button("Register Site")
                    
                    if submitted and site_name and latitude != 0.0 and longitude != 0.0:
                        try:
                            site = db.create_site(
                                project_id=st.session_state.current_project_id,
                                site_name=site_name,
                                latitude=latitude,
                                longitude=longitude,
                                country=country,
                                context_type=context_type,
                                sediment_type=sediment_type,
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
                sites_df = db.get_sites(st.session_state.current_project_id)
                
                if len(sites_df) > 0:
                    for _, site in sites_df.iterrows():
                        with st.container():
                            col1, col2, col3 = st.columns([3, 2, 1])
                            
                            with col1:
                                st.markdown(f"### 📍 {site['site_name']}")
                                if site.get('country'):
                                    st.caption(f"{site['country']}")
                            
                            with col2:
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
    
    with tab3:
        st.subheader("💾 Save Current Data to Database")
        
        if not st.session_state.current_site_id:
            st.warning("⚠️ Please select a site first (Sites tab)")
        elif st.session_state.data is None:
            st.warning("⚠️ No data loaded. Please import data first (Data Import page)")
        else:
            st.info(f"Ready to save {len(st.session_state.data)} analyses to database")
            
            sample_prefix = st.text_input("Sample Prefix", value="AUTO", help="Prefix for auto-generated sample codes")
            
            if st.button("💾 Save to Database", type="primary"):
                try:
                    with st.spinner("Saving to database..."):
                        n_samples, n_analyses = db.import_eds_data_from_dataframe(
                            df=st.session_state.data,
                            site_id=st.session_state.current_site_id,
                            sample_prefix=sample_prefix
                        )
                    
                    st.success(f"✅ Saved {n_samples} samples with {n_analyses} analyses!")
                    
                except Exception as e:
                    st.error(f"Error saving to database: {str(e)}")

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

