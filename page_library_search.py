"""
Library Search Page - TaphoSpec v2.1
Search unknown EDS spectra against reference library
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from database import calculate_distance

def render_library_search_page(db):
    """Main library search page"""
    
    st.markdown('<p class="main-header">📚 Spectral Library Search</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Match unknown spectra against reference library</p>', unsafe_allow_html=True)
    
    # Check if library has entries
    library_stats = db.get_library_statistics()
    
    if not library_stats or library_stats.get('total_entries', 0) == 0:
        st.warning("⚠️ Library is empty! Add reference spectra first.")
        st.info("💡 Go to 'Library Management' to add reference spectra.")
        
        with st.expander("📖 How to use Library Search"):
            st.markdown("""
            **Library Search allows you to:**
            1. Match unknown EDS spectra against known references
            2. Find similar materials using distance metrics
            3. Compare elemental compositions visually
            4. Accept/reject matches and provide feedback
            
            **To get started:**
            - Add reference spectra to the library
            - Select an unknown spectrum to search
            - Choose distance metric and filters
            - Review matches and accept best match
            """)
        return
    
    # Show library stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📚 Total Entries", library_stats.get('total_entries', 0))
    with col2:
        st.metric("🏛️ Archaeological", library_stats.get('archaeological_count', 0))
    with col3:
        st.metric("🧪 Experimental", library_stats.get('experimental_count', 0))
    with col4:
        st.metric("🔗 Multi-modal", library_stats.get('multimodal_count', 0))
    
    st.markdown("---")
    
    # Search configuration
    st.subheader("🔍 Search Configuration")
    
    # Step 1: Select query spectrum
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**Step 1: Select Unknown Spectrum**")
        
        # Get available EDS analyses
        all_analyses = db.get_eds_analyses()
        
        if not all_analyses:
            st.warning("No EDS analyses available. Import data first.")
            return
        
        # Filter out analyses already in library
        library_entries = db.get_library_entries()
        library_analysis_ids = {e.get('eds_spectrum_id') for e in library_entries if e.get('eds_spectrum_id')}
        
        available_analyses = [a for a in all_analyses if a.get('analysis_id') not in library_analysis_ids]
        
        if not available_analyses:
            st.warning("All EDS analyses are already in the library.")
            return
        
        # Create selection options
        analysis_options = {
            f"{a.get('sample_id', 'Unknown')[:8]} - Point {a.get('analysis_point_number', 'N/A')} - {a.get('classification', 'Unclassified')}": a
            for a in available_analyses
        }
        
        selected_option = st.selectbox(
            "Select spectrum to search",
            options=list(analysis_options.keys())
        )
        
        query_spectrum = analysis_options[selected_option]
    
    with col2:
        st.markdown("**Query Spectrum Info:**")
        if query_spectrum:
            st.write(f"**ID:** {query_spectrum.get('analysis_id', 'N/A')[:8]}...")
            st.write(f"**Point:** {query_spectrum.get('analysis_point_number', 'N/A')}")
            
            # Show key elements
            c_val = query_spectrum.get('c', 0)
            p_val = query_spectrum.get('p', 0)
            ca_val = query_spectrum.get('ca', 0)
            
            st.write(f"**C:** {c_val:.1f}%" if c_val else "**C:** N/A")
            st.write(f"**P:** {p_val:.1f}%" if p_val else "**P:** N/A")
            st.write(f"**Ca:** {ca_val:.1f}%" if ca_val else "**Ca:** N/A")
    
    # Step 2: Search parameters
    st.markdown("**Step 2: Configure Search Parameters**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        distance_metric = st.selectbox(
            "Distance Metric",
            options=['euclidean', 'cosine', 'manhattan', 'chi_square'],
            help="""
            - Euclidean: Standard geometric distance
            - Cosine: Angular similarity (good for normalized data)
            - Manhattan: Sum of absolute differences
            - Chi-square: Statistical comparison
            """
        )
    
    with col2:
        # Elements to include
        all_elements = ['C', 'N', 'P', 'Ca', 'K', 'Al', 'Mn', 'Fe', 'Si', 'Mg', 'Na', 'S', 'Cl', 'Ti', 'Zn']
        default_elements = ['C', 'P', 'Ca', 'Mn', 'K', 'Al', 'Fe', 'Si']
        
        selected_elements = st.multiselect(
            "Elements to Compare",
            options=all_elements,
            default=default_elements,
            help="Select which elements to include in distance calculation"
        )
    
    with col3:
        top_n = st.slider(
            "Number of Matches",
            min_value=1,
            max_value=20,
            value=5,
            help="How many top matches to return"
        )
    
    # Step 3: Filters
    with st.expander("🔧 Advanced Filters"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_types = st.multiselect(
                "Spectrum Type",
                options=['archaeological', 'experimental'],
                default=['archaeological', 'experimental']
            )
        
        with col2:
            materials = ['organic_adhesive', 'bone', 'ochre', 'resin', 'mineral', 'other']
            filter_materials = st.multiselect(
                "Material Type",
                options=materials,
                default=[]
            )
        
        with col3:
            verified_only = st.checkbox("Verified entries only", value=False)
            multimodal_only = st.checkbox("Multi-modal only (EDS + FTIR)", value=False)
    
    # Search button
    if st.button("🔍 Search Library", type="primary", use_container_width=True):
        if not selected_elements:
            st.error("Please select at least one element to compare!")
            return
        
        with st.spinner("Searching library..."):
            # Perform search
            matches = perform_library_search(
                db,
                query_spectrum,
                selected_elements,
                distance_metric,
                top_n,
                filter_types,
                filter_materials,
                verified_only,
                multimodal_only
            )
            
            if not matches:
                st.warning("No matches found with current filters. Try adjusting search parameters.")
                return
            
            # Store in session state
            st.session_state.search_results = matches
            st.session_state.query_spectrum = query_spectrum
            st.session_state.search_params = {
                'elements': selected_elements,
                'metric': distance_metric,
                'top_n': top_n
            }
    
    # Display results
    if 'search_results' in st.session_state and st.session_state.search_results:
        st.markdown("---")
        display_search_results(
            db,
            st.session_state.search_results,
            st.session_state.query_spectrum,
            st.session_state.search_params
        )


def perform_library_search(db, query_spectrum, elements, metric, top_n, 
                          filter_types, filter_materials, verified_only, multimodal_only):
    """
    Perform library search with filters
    """
    # Get library entries with filters
    library_entries = db.get_library_entries(
        verified_only=verified_only,
        multimodal_only=multimodal_only
    )
    
    # Apply type filter
    if filter_types:
        library_entries = [e for e in library_entries if e.get('spectrum_type') in filter_types]
    
    # Apply material filter
    if filter_materials:
        library_entries = [e for e in library_entries if e.get('material_type') in filter_materials]
    
    # Only entries with EDS data
    library_entries = [e for e in library_entries if e.get('has_eds')]
    
    if not library_entries:
        return []
    
    # Calculate distances
    matches = []
    
    for lib_entry in library_entries:
        # Get elemental data (already in library_complete view)
        distance = calculate_distance(
            query_spectrum,
            lib_entry,
            elements,
            metric
        )
        
        # Convert distance to similarity score (0-1, higher is better)
        similarity_score = 1 / (1 + distance)
        
        matches.append({
            'library_id': lib_entry.get('library_id'),
            'spectrum_name': lib_entry.get('spectrum_name'),
            'spectrum_type': lib_entry.get('spectrum_type'),
            'material_type': lib_entry.get('material_type'),
            'source_type': lib_entry.get('source_type'),
            'verified': lib_entry.get('verified', False),
            'has_ftir': lib_entry.get('has_ftir', False),
            'distance': distance,
            'similarity_score': similarity_score,
            'elemental_data': lib_entry
        })
    
    # Sort by similarity (highest first)
    matches.sort(key=lambda x: x['similarity_score'], reverse=True)
    
    return matches[:top_n]


def display_search_results(db, matches, query_spectrum, search_params):
    """Display search results with visualizations"""
    
    st.subheader("🎯 Search Results")
    
    st.success(f"✓ Found {len(matches)} matches using {search_params['metric']} distance")
    
    # Results table
    results_df = pd.DataFrame([{
        'Rank': i+1,
        'Spectrum Name': m['spectrum_name'],
        'Type': m['spectrum_type'],
        'Material': m['material_type'],
        'Similarity': f"{m['similarity_score']:.3f}",
        'Distance': f"{m['distance']:.3f}",
        'Verified': '✓' if m['verified'] else '✗',
        'Multi-modal': '✓' if m['has_ftir'] else '✗'
    } for i, m in enumerate(matches)])
    
    st.dataframe(results_df, use_container_width=True, hide_index=True)
    
    # Detailed match comparison
    st.markdown("---")
    st.subheader("📊 Detailed Match Comparison")
    
    for i, match in enumerate(matches):
        with st.expander(f"#{i+1}: {match['spectrum_name']} - Similarity: {match['similarity_score']:.3f}", expanded=(i==0)):
            display_match_details(db, match, query_spectrum, search_params['elements'])
    
    # Accept/Reject section
    st.markdown("---")
    st.subheader("✅ Accept Match")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_match_idx = st.selectbox(
            "Select match to accept",
            options=range(len(matches)),
            format_func=lambda i: f"#{i+1}: {matches[i]['spectrum_name']} ({matches[i]['similarity_score']:.3f})"
        )
    
    with col2:
        feedback = st.text_area("Feedback (optional)", placeholder="Notes about this match...")
    
    if st.button("✓ Accept This Match", type="primary"):
        # Log search with user feedback
        search_id = db.log_library_search(
            query_spectrum_id=query_spectrum['analysis_id'],
            query_type='eds',
            search_params=search_params,
            results=[{k: v for k, v in m.items() if k != 'elemental_data'} for m in matches],
            user_id=st.session_state.get('user_id')
        )
        
        # Update with acceptance
        db.update_search_feedback(
            search_id=search_id['search_id'],
            accepted=True,
            selected_id=matches[selected_match_idx]['library_id'],
            feedback=feedback if feedback else None
        )
        
        st.success(f"✓ Match accepted: {matches[selected_match_idx]['spectrum_name']}")
        st.info("💡 This feedback helps improve the library matching algorithm!")


def display_match_details(db, match, query_spectrum, elements):
    """Display detailed comparison for a single match"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Query Spectrum**")
        st.write(f"**Sample ID:** {query_spectrum.get('sample_id', 'N/A')[:8]}...")
        st.write(f"**Point:** {query_spectrum.get('analysis_point_number', 'N/A')}")
        st.write(f"**Classification:** {query_spectrum.get('classification', 'Unclassified')}")
    
    with col2:
        st.markdown(f"**Library Match: {match['spectrum_name']}**")
        st.write(f"**Type:** {match['spectrum_type']}")
        st.write(f"**Material:** {match['material_type']}")
        st.write(f"**Source:** {match['source_type']}")
        
        if match['verified']:
            st.success("✓ Verified")
        
        if match['has_ftir']:
            st.info("🔗 Has FTIR data")
    
    # Elemental comparison table
    st.markdown("**Elemental Composition Comparison:**")
    
    comparison_data = []
    for element in elements:
        query_val = query_spectrum.get(element.lower(), 0)
        match_val = match['elemental_data'].get(f'eds_{element.lower()}', 0) or 0
        diff = abs(query_val - match_val)
        
        comparison_data.append({
            'Element': element,
            'Query (%)': f"{query_val:.2f}",
            'Match (%)': f"{match_val:.2f}",
            'Difference': f"{diff:.2f}",
            'Rel. Diff (%)': f"{(diff/max(query_val, 0.01)*100):.1f}"
        })
    
    comp_df = pd.DataFrame(comparison_data)
    st.dataframe(comp_df, use_container_width=True, hide_index=True)
    
    # Visualization
    fig = plot_spectrum_comparison(query_spectrum, match, elements)
    st.plotly_chart(fig, use_container_width=True)


def plot_spectrum_comparison(query, match, elements):
    """Create comparison bar chart"""
    
    query_values = [query.get(e.lower(), 0) for e in elements]
    match_values = [match['elemental_data'].get(f'eds_{e.lower()}', 0) or 0 for e in elements]
    
    fig = go.Figure()
    
    # Query spectrum
    fig.add_trace(go.Bar(
        name='Query (Unknown)',
        x=elements,
        y=query_values,
        marker_color='lightblue',
        text=[f'{v:.1f}%' for v in query_values],
        textposition='outside'
    ))
    
    # Match spectrum
    fig.add_trace(go.Bar(
        name=f"Match: {match['spectrum_name']}",
        x=elements,
        y=match_values,
        marker_color='coral',
        text=[f'{v:.1f}%' for v in match_values],
        textposition='outside'
    ))
    
    fig.update_layout(
        title=f"Spectrum Comparison - Similarity: {match['similarity_score']:.3f}",
        xaxis_title='Element',
        yaxis_title='Weight %',
        barmode='group',
        height=400,
        showlegend=True,
        hovermode='x unified'
    )
    
    return fig
