import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from scipy.stats import pearsonr
from io import BytesIO

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

# Authentication functions
def authenticate_residue(row):
    """
    Authenticate residue based on elemental criteria from Sibudu manuscript.
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
with st.sidebar:
    st.header("📊 Navigation")
    
    page = st.radio(
        "Select Analysis",
        ["Data Import", "Correlation Analysis", "Authentication", "Visual Attributes", "Report"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    st.markdown("""
    ### About TaphoSpec
    
    Platform for authenticating archaeological residues using multi-modal spectroscopy.
    
    **Based on:**  
    Hafting Adhesive Preservation in Guano-Rich Rockshelters (Sibudu Cave study)
    
    **Methods:**
    - SEM-EDS elemental analysis
    - Correlation-based diagenesis detection
    - Multi-criteria authentication
    """)

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'authenticated_data' not in st.session_state:
    st.session_state.authenticated_data = None

# Page: Data Import
if page == "Data Import":
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
            st.markdown(f"""
            **Classification:** {point_auth['classification']}  
            **Confidence:** {point_auth['confidence']}
            
            **Elemental Data:**
            - C: {point_data.get('C', 'N/A'):.1f}%
            - Mn: {point_data.get('Mn', 'N/A'):.2f}%
            - P: {point_data.get('P', 'N/A'):.1f}%
            - Ca/P: {point_auth['ca_p_ratio']:.2f if point_auth['ca_p_ratio'] else 'N/A'}
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

st.markdown("---")
st.caption("TaphoSpec v1.0 Phase 1 | TraceoLab, University of Liège | Based on Sibudu Cave hafting adhesives manuscript")
