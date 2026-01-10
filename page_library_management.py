"""
Library Management Page - TaphoSpec v2.1
Add, edit, and verify reference spectra in the library
"""

import streamlit as st
import pandas as pd
from datetime import date

def render_library_management_page(db):
    """Main library management page"""
    
    st.markdown('<p class="main-header">📚 Library Management</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Manage reference spectra in the spectral library</p>', unsafe_allow_html=True)
    
    # Tabs for different operations
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 View Library",
        "➕ Add Entry", 
        "✏️ Edit Entry",
        "📈 Statistics"
    ])
    
    with tab1:
        view_library_tab(db)
    
    with tab2:
        add_library_entry_tab(db)
    
    with tab3:
        edit_library_entry_tab(db)
    
    with tab4:
        library_statistics_tab(db)


def view_library_tab(db):
    """View all library entries"""
    
    st.subheader("📊 Library Contents")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        filter_type = st.selectbox(
            "Type",
            options=['All', 'archaeological', 'experimental']
        )
    
    with col2:
        filter_material = st.selectbox(
            "Material",
            options=['All', 'organic_adhesive', 'bone', 'ochre', 'resin', 'mineral']
        )
    
    with col3:
        filter_verified = st.checkbox("Verified only")
    
    with col4:
        filter_multimodal = st.checkbox("Multi-modal only")
    
    # Get entries
    entries = db.get_library_entries(
        spectrum_type=None if filter_type == 'All' else filter_type,
        material_type=None if filter_material == 'All' else filter_material,
        verified_only=filter_verified,
        multimodal_only=filter_multimodal
    )
    
    if not entries:
        st.info("No entries match the current filters.")
        return
    
    st.write(f"**Found {len(entries)} entries**")
    
    # Display as dataframe
    display_df = pd.DataFrame([{
        'Name': e.get('spectrum_name'),
        'Code': e.get('spectrum_code', 'N/A'),
        'Type': e.get('spectrum_type'),
        'Material': e.get('material_type'),
        'Source': e.get('source_type', 'N/A'),
        'EDS': '✓' if e.get('has_eds') else '✗',
        'FTIR': '✓' if e.get('has_ftir') else '✗',
        'Verified': '✓' if e.get('verified') else '✗',
        'Keywords': ', '.join(e.get('keywords', [])) if e.get('keywords') else 'None'
    } for e in entries])
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Detailed view
    st.markdown("---")
    st.subheader("🔍 Detailed View")
    
    entry_names = {e.get('spectrum_name'): e for e in entries}
    selected_name = st.selectbox("Select entry to view", options=list(entry_names.keys()))
    
    if selected_name:
        entry = entry_names[selected_name]
        display_library_entry_details(entry)


def add_library_entry_tab(db):
    """Add new library entry"""
    
    st.subheader("➕ Add New Library Entry")
    
    st.info("💡 Link an existing EDS analysis to the library as a reference spectrum")
    
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
    
    with st.form("add_library_entry"):
        st.markdown("**Step 1: Select EDS Spectrum**")
        
        analysis_options = {
            f"{a.get('sample_id', 'Unknown')[:8]} - Point {a.get('analysis_point_number', 'N/A')} - {a.get('classification', 'Unclassified')}": a
            for a in available_analyses
        }
        
        selected_option = st.selectbox("Select EDS analysis", options=list(analysis_options.keys()))
        selected_analysis = analysis_options[selected_option]
        
        # Show preview
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("C", f"{selected_analysis.get('c', 0):.1f}%")
        with col2:
            st.metric("P", f"{selected_analysis.get('p', 0):.1f}%")
        with col3:
            st.metric("Ca", f"{selected_analysis.get('ca', 0):.1f}%")
        
        st.markdown("---")
        st.markdown("**Step 2: Library Entry Details**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            spectrum_name = st.text_input(
                "Spectrum Name*",
                placeholder="e.g., Birch Tar Reference - Sweden",
                help="Descriptive name for this reference spectrum"
            )
            
            spectrum_code = st.text_input(
                "Spectrum Code",
                placeholder="e.g., REF-ORG-001",
                help="Unique identifier (optional)"
            )
            
            spectrum_type = st.selectbox(
                "Spectrum Type*",
                options=['archaeological', 'experimental'],
                help="Is this from archaeological or experimental context?"
            )
            
            material_type = st.selectbox(
                "Material Type*",
                options=['organic_adhesive', 'bone', 'ochre', 'resin', 'mineral', 'other']
            )
            
            material_subtype = st.text_input(
                "Material Subtype",
                placeholder="e.g., birch_tar, pine_resin",
                help="More specific material identification"
            )
        
        with col2:
            source_type = st.selectbox(
                "Source Type",
                options=['literature', 'experimental', 'reference_collection', 'museum', 'field']
            )
            
            source_reference = st.text_input(
                "Source Reference",
                placeholder="e.g., DOI, citation, lab notebook",
                help="Citation or reference for this spectrum"
            )
            
            source_institution = st.text_input(
                "Institution",
                placeholder="e.g., TraceoLab, ULiège"
            )
            
            quality_score = st.slider(
                "Quality Score",
                min_value=1,
                max_value=5,
                value=3,
                help="Quality assessment (1=poor, 5=excellent)"
            )
            
            contamination_level = st.selectbox(
                "Contamination Level",
                options=['none', 'low', 'medium', 'high']
            )
        
        # Keywords
        keywords_input = st.text_input(
            "Keywords (comma-separated)",
            placeholder="e.g., birch, tar, adhesive, organic, sweden",
            help="Keywords for search optimization"
        )
        
        # Description
        description = st.text_area(
            "Description",
            placeholder="Additional notes about this reference spectrum...",
            height=100
        )
        
        # Submit
        submitted = st.form_submit_button("➕ Add to Library", type="primary", use_container_width=True)
        
        if submitted:
            if not spectrum_name or not spectrum_type or not material_type:
                st.error("Please fill in all required fields (*)")
            else:
                # Parse keywords
                keywords = [kw.strip() for kw in keywords_input.split(',')] if keywords_input else []
                
                # Create library entry
                try:
                    entry = db.create_library_entry(
                        spectrum_name=spectrum_name,
                        spectrum_code=spectrum_code if spectrum_code else None,
                        spectrum_type=spectrum_type,
                        material_type=material_type,
                        material_subtype=material_subtype if material_subtype else None,
                        source_type=source_type,
                        source_reference=source_reference if source_reference else None,
                        source_institution=source_institution if source_institution else None,
                        has_eds=True,
                        has_ftir=False,
                        eds_spectrum_id=selected_analysis['analysis_id'],
                        quality_score=quality_score,
                        contamination_level=contamination_level,
                        keywords=keywords,
                        description=description if description else None,
                        created_by=st.session_state.get('user_id')
                    )
                    
                    st.success(f"✓ Added to library: {spectrum_name}")
                    st.balloons()
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error adding to library: {str(e)}")


def edit_library_entry_tab(db):
    """Edit existing library entry"""
    
    st.subheader("✏️ Edit Library Entry")
    
    # Get all entries
    entries = db.get_library_entries()
    
    if not entries:
        st.info("Library is empty. Add entries first.")
        return
    
    # Select entry to edit
    entry_options = {e.get('spectrum_name'): e for e in entries}
    selected_name = st.selectbox("Select entry to edit", options=list(entry_options.keys()))
    
    entry = entry_options[selected_name]
    
    # Edit form
    with st.form("edit_library_entry"):
        col1, col2 = st.columns(2)
        
        with col1:
            spectrum_name = st.text_input("Spectrum Name", value=entry.get('spectrum_name', ''))
            spectrum_type = st.selectbox(
                "Spectrum Type",
                options=['archaeological', 'experimental'],
                index=0 if entry.get('spectrum_type') == 'archaeological' else 1
            )
            material_type = st.text_input("Material Type", value=entry.get('material_type', ''))
            source_reference = st.text_input("Source Reference", value=entry.get('source_reference', ''))
        
        with col2:
            quality_score = st.slider(
                "Quality Score",
                min_value=1,
                max_value=5,
                value=entry.get('quality_score', 3) or 3
            )
            
            contamination_level = st.selectbox(
                "Contamination Level",
                options=['none', 'low', 'medium', 'high'],
                index=['none', 'low', 'medium', 'high'].index(entry.get('contamination_level', 'none'))
            )
            
            verified = st.checkbox("Verified", value=entry.get('verified', False))
        
        keywords_input = st.text_input(
            "Keywords (comma-separated)",
            value=', '.join(entry.get('keywords', [])) if entry.get('keywords') else ''
        )
        
        description = st.text_area(
            "Description",
            value=entry.get('description', ''),
            height=100
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            update_submitted = st.form_submit_button("💾 Update Entry", type="primary", use_container_width=True)
        
        with col2:
            delete_submitted = st.form_submit_button("🗑️ Delete Entry", use_container_width=True)
        
        if update_submitted:
            keywords = [kw.strip() for kw in keywords_input.split(',')] if keywords_input else []
            
            updates = {
                'spectrum_name': spectrum_name,
                'spectrum_type': spectrum_type,
                'material_type': material_type,
                'source_reference': source_reference if source_reference else None,
                'quality_score': quality_score,
                'contamination_level': contamination_level,
                'verified': verified,
                'keywords': keywords,
                'description': description if description else None
            }
            
            if verified and not entry.get('verified'):
                updates['verified_by'] = st.session_state.get('user_id')
                updates['verified_date'] = date.today().isoformat()
            
            try:
                db.update_library_entry(entry['library_id'], updates)
                st.success("✓ Entry updated successfully")
                st.rerun()
            except Exception as e:
                st.error(f"Error updating entry: {str(e)}")
        
        if delete_submitted:
            try:
                db.delete_library_entry(entry['library_id'])
                st.success("✓ Entry deleted")
                st.rerun()
            except Exception as e:
                st.error(f"Error deleting entry: {str(e)}")


def library_statistics_tab(db):
    """Show library statistics"""
    
    st.subheader("📈 Library Statistics")
    
    stats = db.get_library_statistics()
    
    # Overall metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📚 Total Entries", stats.get('total_entries', 0))
    with col2:
        st.metric("✓ Verified", stats.get('verified_count', 0))
    with col3:
        st.metric("📊 Material Types", stats.get('material_types_count', 0))
    with col4:
        st.metric("🔗 Multi-modal", stats.get('multimodal_count', 0))
    
    st.markdown("---")
    
    # Type breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Spectrum Types:**")
        st.metric("🏛️ Archaeological", stats.get('archaeological_count', 0))
        st.metric("🧪 Experimental", stats.get('experimental_count', 0))
    
    with col2:
        st.markdown("**Analysis Types:**")
        st.metric("⚛️ EDS", stats.get('eds_count', 0))
        st.metric("📈 FTIR", stats.get('ftir_count', 0))
        st.metric("🔗 Both (Multi-modal)", stats.get('multimodal_count', 0))
    
    # Detailed breakdown
    st.markdown("---")
    st.markdown("**Library Contents by Category:**")
    
    entries = db.get_library_entries()
    
    if entries:
        # By material type
        material_counts = {}
        for e in entries:
            mat = e.get('material_type', 'unknown')
            material_counts[mat] = material_counts.get(mat, 0) + 1
        
        mat_df = pd.DataFrame([
            {'Material Type': k, 'Count': v}
            for k, v in sorted(material_counts.items(), key=lambda x: x[1], reverse=True)
        ])
        
        st.dataframe(mat_df, use_container_width=True, hide_index=True)


def display_library_entry_details(entry):
    """Display detailed information about a library entry"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Basic Information:**")
        st.write(f"**Name:** {entry.get('spectrum_name')}")
        st.write(f"**Code:** {entry.get('spectrum_code', 'N/A')}")
        st.write(f"**Type:** {entry.get('spectrum_type')}")
        st.write(f"**Material:** {entry.get('material_type')}")
        if entry.get('material_subtype'):
            st.write(f"**Subtype:** {entry.get('material_subtype')}")
        
        if entry.get('verified'):
            st.success("✓ Verified Entry")
        else:
            st.warning("⚠️ Unverified")
    
    with col2:
        st.markdown("**Source Information:**")
        st.write(f"**Source Type:** {entry.get('source_type', 'N/A')}")
        if entry.get('source_reference'):
            st.write(f"**Reference:** {entry.get('source_reference')}")
        if entry.get('source_institution'):
            st.write(f"**Institution:** {entry.get('source_institution')}")
        
        st.markdown("**Data Availability:**")
        st.write(f"**EDS:** {'✓ Yes' if entry.get('has_eds') else '✗ No'}")
        st.write(f"**FTIR:** {'✓ Yes' if entry.get('has_ftir') else '✗ No'}")
    
    if entry.get('keywords'):
        st.markdown("**Keywords:**")
        st.write(', '.join(entry.get('keywords')))
    
    if entry.get('description'):
        st.markdown("**Description:**")
        st.info(entry.get('description'))
    
    # EDS data preview
    if entry.get('has_eds'):
        st.markdown("**EDS Elemental Composition:**")
        
        elements = ['C', 'N', 'P', 'Ca', 'K', 'Al', 'Mn', 'Fe', 'Si', 'Mg']
        eds_data = []
        
        for elem in elements:
            val = entry.get(f'eds_{elem.lower()}', 0)
            if val and val > 0:
                eds_data.append({'Element': elem, 'Weight %': f'{val:.2f}'})
        
        if eds_data:
            eds_df = pd.DataFrame(eds_data)
            st.dataframe(eds_df, use_container_width=True, hide_index=True)
