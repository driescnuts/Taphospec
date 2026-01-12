# ================================================
# APP.PY v2.2 - NAVIGATION UPDATE
# ================================================
# Replace the navigation section (lines ~350-360) with this:

# NEW NAVIGATION STRUCTURE - COLLAPSIBLE SECTIONS
# ================================================

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
    
    # Initialize page in session state if not exists
    if 'page' not in st.session_state:
        st.session_state.page = "Home"
    
    # ================================================
    # ARCHAEOLOGICAL DATA Section
    # ================================================
    with st.expander("🏛️ ARCHAEOLOGICAL DATA", expanded=True):
        if st.button("📁 Sites", use_container_width=True, key="nav_sites"):
            st.session_state.page = "Project Management"
        if st.button("📥 Import Analyses", use_container_width=True, key="nav_import"):
            st.session_state.page = "Data Import"
        if st.button("📊 Dataset Statistics", use_container_width=True, key="nav_stats"):
            st.session_state.page = "Statistics"
    
    # ================================================
    # IDENTIFICATION Section  
    # ================================================
    with st.expander("🔍 IDENTIFICATION", expanded=False):
        if st.button("🔍 Identify Unknown", use_container_width=True, key="nav_identify"):
            st.session_state.page = "Library Search"
    
    # ================================================
    # SITE ANALYSIS Section
    # ================================================
    with st.expander("📉 SITE ANALYSIS", expanded=False):
        if st.button("🎯 Bulk Authentication", use_container_width=True, key="nav_auth"):
            st.session_state.page = "Authentication"
        if st.button("📊 Correlations", use_container_width=True, key="nav_corr"):
            st.session_state.page = "Correlation Analysis"
        if st.button("🗺️ Spatial Patterns", use_container_width=True, key="nav_map"):
            st.session_state.page = "Site Map"
        if st.button("📋 Reports", use_container_width=True, key="nav_report"):
            st.session_state.page = "Report"
    
    # ================================================
    # REFERENCE LIBRARY Section
    # ================================================
    if database_enabled and LIBRARY_PAGES_AVAILABLE:
        with st.expander("📚 REFERENCE LIBRARY", expanded=False):
            if st.button("📖 Browse References", use_container_width=True, key="nav_browse"):
                st.session_state.page = "Library Search"
            if st.button("➕ Manage Entries", use_container_width=True, key="nav_manage"):
                st.session_state.page = "Library Management"
    
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
        if st.session_state.current_project_id:
            st.info(f"📁 Active Project")
        if st.session_state.current_site_id:
            st.info(f"📍 Active Site")
    else:
        st.warning("🗄️ Standalone Mode")
    
    st.markdown("---")
    
    # Version info
    st.caption("TaphoSpec v2.2")
    st.caption("TraceoLab - ULiège")

# ================================================
# PAGE ROUTING - Update to use session_state.page
# ================================================

# Replace your current page routing section with:

page = st.session_state.get('page', 'Home')

if page == "Home" or page not in [
    "Data Import", "Correlation Analysis", "Authentication", 
    "Visual Attributes", "Report", "Project Management", 
    "Site Map", "Statistics", "Library Search", 
    "Library Management", "Admin Panel"
]:
    # HOME PAGE
    st.markdown('<div class="main-header">🔬 TaphoSpec v2.2</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Archaeological Residue Authentication Platform</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🏛️ Archaeological Data")
        st.markdown("""
        Manage your excavation data:
        - Organize sites and samples
        - Import EDS analyses with residues
        - Dataset statistics and overview
        """)
        if st.button("→ Go to Sites", key="home_sites"):
            st.session_state.page = "Project Management"
            st.rerun()
    
    with col2:
        st.markdown("### 🔍 Identification")
        st.markdown("""
        Identify unknown residues:
        - Search library for matches
        - Select specific analysis points
        - Accept/reject identifications
        """)
        if st.button("→ Identify Unknown", key="home_identify"):
            st.session_state.page = "Library Search"
            st.rerun()
    
    with col3:
        st.markdown("### 📉 Site Analysis")
        st.markdown("""
        Analyze your dataset:
        - Bulk authentication
        - Element correlations
        - Spatial patterns
        - Generate reports
        """)
        if st.button("→ Start Analysis", key="home_analysis"):
            st.session_state.page = "Correlation Analysis"
            st.rerun()
    
    st.markdown("---")
    
    if database_enabled and LIBRARY_PAGES_AVAILABLE:
        st.markdown("### 📚 Reference Library")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Browse references:**
            - View all library entries
            - Search by material type
            - Check availability
            """)
            if st.button("→ Browse Library", key="home_browse"):
                st.session_state.page = "Library Search"
                st.rerun()
        
        with col2:
            st.markdown("""
            **Manage entries:**
            - Add new references
            - Edit existing entries
            - Quality verification
            """)
            if st.button("→ Manage Library", key="home_manage"):
                st.session_state.page = "Library Management"
                st.rerun()
    
    st.markdown("---")
    
    # Quick stats if database enabled
    if database_enabled:
        st.markdown("### 📊 Quick Statistics")
        
        try:
            db = get_db_connection()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                projects = db.get_projects()
                st.metric("Projects", len(projects))
            
            with col2:
                sites = db.get_sites()
                st.metric("Sites", len(sites))
            
            with col3:
                samples = db.get_samples()
                st.metric("Samples", len(samples))
            
            with col4:
                analyses = db.get_eds_analyses()
                st.metric("EDS Analyses", len(analyses))
            
            if LIBRARY_PAGES_AVAILABLE:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    library = db.get_library_entries()
                    st.metric("Library Entries", len(library))
                
                with col2:
                    verified = len([e for e in library if e.get('verified', False)])
                    st.metric("Verified", verified)
                
                with col3:
                    searches = db.get_library_searches()
                    st.metric("Searches", len(searches))
        
        except Exception as e:
            st.info("Connect database to see statistics")

elif page == "Data Import":
    # Keep existing Data Import page code
    pass

elif page == "Correlation Analysis":
    # Keep existing Correlation Analysis page code
    pass

elif page == "Authentication":
    # Keep existing Authentication page code
    pass

elif page == "Visual Attributes":
    # Keep existing Visual Attributes page code
    pass

elif page == "Report":
    # Keep existing Report page code
    pass

elif page == "Project Management":
    # Keep existing Project Management page code
    pass

elif page == "Site Map":
    # Keep existing Site Map page code
    pass

elif page == "Statistics":
    # Keep existing Statistics page code
    pass

elif page == "Library Search":
    if database_enabled and LIBRARY_PAGES_AVAILABLE:
        render_library_search_page()
    else:
        st.error("Library features not available")

elif page == "Library Management":
    if database_enabled and LIBRARY_PAGES_AVAILABLE:
        render_library_management_page()
    else:
        st.error("Library features not available")

elif page == "Admin Panel":
    if AUTH_AVAILABLE and is_admin():
        render_admin_panel()
    else:
        st.error("Access denied")

# ================================================
# NOTES FOR IMPLEMENTATION
# ================================================

"""
CHANGES MADE:
1. ✅ Collapsible sections with st.expander()
2. ✅ Quick access buttons (Home, Identify)
3. ✅ Page state in st.session_state.page
4. ✅ 4 main categories:
   - Archaeological Data
   - Identification
   - Site Analysis
   - Reference Library
5. ✅ Home page with overview and quick links
6. ✅ Button-based navigation (not radio)
7. ✅ use_container_width for consistent styling

TO IMPLEMENT:
1. Replace navigation section (lines 350-360) with code above
2. Replace page routing section with new routing
3. Add Home page code
4. Keep all existing page implementations
5. Test thoroughly!

BENEFITS:
- ✅ Clear logical grouping
- ✅ Less clutter (collapsible)
- ✅ Quick access to most-used features
- ✅ Better UX for complex workflows
- ✅ Room to grow (Taphonomy section ready)
"""
