# ================================================
# ENHANCED SITE REGISTRATION FORM
# Add this to your Sites page in app.py
# ================================================

def render_enhanced_site_form(db):
    """Enhanced site registration form with full taphonomic context"""
    
    with st.expander("➕ Register New Site with Context", expanded=False):
        with st.form("new_site_context"):
            st.markdown("### Basic Site Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                site_name = st.text_input(
                    "Site Name*", 
                    placeholder="e.g., Spy Cave",
                    help="Official site name"
                )
                country = st.text_input(
                    "Country*", 
                    placeholder="e.g., Belgium"
                )
                region = st.text_input(
                    "Region/Province",
                    placeholder="e.g., Wallonia, Namur"
                )
            
            with col2:
                latitude = st.number_input(
                    "Latitude*", 
                    min_value=-90.0, 
                    max_value=90.0, 
                    value=50.48, 
                    format="%.6f",
                    help="Decimal degrees"
                )
                longitude = st.number_input(
                    "Longitude*", 
                    min_value=-180.0, 
                    max_value=180.0, 
                    value=4.72, 
                    format="%.6f",
                    help="Decimal degrees"
                )
                elevation = st.number_input(
                    "Elevation (m a.s.l.)",
                    min_value=-500,
                    max_value=9000,
                    value=200,
                    help="Meters above sea level"
                )
            
            st.markdown("---")
            st.markdown("### 🌍 Geographic & Climatic Context")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                climate_zone = st.selectbox(
                    "Climate Zone*",
                    [
                        "Tropical",
                        "Subtropical", 
                        "Temperate",
                        "Mediterranean",
                        "Arid/Semi-arid",
                        "Arctic/Sub-arctic"
                    ],
                    help="Affects preservation potential"
                )
            
            with col2:
                rainfall_regime = st.selectbox(
                    "Rainfall Regime",
                    [
                        "Humid (>1000mm/yr)",
                        "Moderate (500-1000mm/yr)",
                        "Dry (<500mm/yr)",
                        "Variable/Seasonal",
                        "Unknown"
                    ]
                )
            
            with col3:
                temperature_regime = st.selectbox(
                    "Temperature Regime",
                    [
                        "Tropical (>25°C mean)",
                        "Warm temperate (15-25°C)",
                        "Cool temperate (5-15°C)",
                        "Cold (<5°C mean)",
                        "Variable/Seasonal"
                    ]
                )
            
            st.markdown("---")
            st.markdown("### 🏛️ Depositional Context")
            st.info("⚠️ This determines which authentication criteria will be applied!")
            
            col1, col2 = st.columns(2)
            
            with col1:
                context_type = st.selectbox(
                    "Primary Depositional Context*",
                    [
                        "cave_guano",
                        "cave_carbonate",
                        "cave_other",
                        "rockshelter",
                        "open_air_sand",
                        "open_air_clay",
                        "open_air_loess",
                        "peat_bog",
                        "volcanic_ash",
                        "other"
                    ],
                    format_func=lambda x: {
                        "cave_guano": "🦇 Cave (Guano-Rich)",
                        "cave_carbonate": "🪨 Cave (Carbonate-Rich)",
                        "cave_other": "🕳️ Cave (Other)",
                        "rockshelter": "🏔️ Rockshelter",
                        "open_air_sand": "🏖️ Open-Air (Sand/Sandstone)",
                        "open_air_clay": "🧱 Open-Air (Clay/Silt)",
                        "open_air_loess": "🌾 Open-Air (Loess)",
                        "peat_bog": "🌿 Peat Bog",
                        "volcanic_ash": "🌋 Volcanic Ash",
                        "other": "❓ Other"
                    }.get(x, x),
                    help="Select the depositional environment"
                )
                
                # Show expected signatures based on selection
                if context_type in ["cave_guano", "cave_carbonate", "open_air_sand", "peat_bog"]:
                    st.caption(f"ℹ️ Expected: {get_context_description(context_type)}")
            
            with col2:
                context_description = st.text_area(
                    "Detailed Context Description",
                    placeholder="e.g., Guano-rich chamber with active bat colony...",
                    height=100
                )
            
            st.markdown("---")
            st.markdown("### 🧪 Taphonomic Factors")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                ph_condition = st.selectbox(
                    "pH Conditions",
                    [
                        "Strongly Acidic (pH <4)",
                        "Acidic (pH 4-6)",
                        "Neutral (pH 6-8)",
                        "Alkaline (pH 8-10)",
                        "Strongly Alkaline (pH >10)",
                        "Variable",
                        "Unknown"
                    ],
                    help="Affects mineral/organic preservation"
                )
            
            with col2:
                water_table = st.selectbox(
                    "Water Regime",
                    [
                        "Permanently Saturated",
                        "Seasonally Saturated",
                        "Seasonally Wet",
                        "Well-Drained",
                        "Arid/Dry",
                        "Unknown"
                    ],
                    help="Waterlogging affects preservation"
                )
            
            with col3:
                microbial_activity = st.selectbox(
                    "Microbial Activity",
                    [
                        "Very High",
                        "High",
                        "Moderate",
                        "Low",
                        "Very Low/Sterile",
                        "Unknown"
                    ],
                    help="Affects organic decay rates"
                )
            
            # Special conditions
            col1, col2 = st.columns(2)
            
            with col1:
                guano_presence = st.checkbox(
                    "🦇 Bat/Bird Guano Present",
                    help="Guano affects P chemistry significantly"
                )
                
                if guano_presence:
                    st.warning("⚠️ Guano-specific corrections will be applied")
            
            with col2:
                fire_evidence = st.checkbox(
                    "🔥 Evidence of Fire/Hearths",
                    help="Affects organic preservation & chemistry"
                )
            
            st.markdown("---")
            st.markdown("### 📊 Expected Preservation Potential")
            st.caption("Based on site context, what preservation do you expect?")
            
            col1, col2 = st.columns(2)
            
            with col1:
                organic_preservation = st.select_slider(
                    "Organic Preservation Potential",
                    options=["Very Poor", "Poor", "Fair", "Good", "Excellent"],
                    value="Fair",
                    help="Expected preservation of organic residues"
                )
            
            with col2:
                mineral_preservation = st.select_slider(
                    "Mineral Preservation Potential",
                    options=["Very Poor", "Poor", "Fair", "Good", "Excellent"],
                    value="Fair",
                    help="Expected preservation of mineral residues"
                )
            
            st.markdown("---")
            st.markdown("### 📚 Geoarchaeological References")
            
            site_references = st.text_area(
                "Key Publications for This Site",
                placeholder="e.g., Goldberg et al. (2009). Site formation at...\nKarkanas & Berna (2015). Taphonomy of...",
                help="Relevant geoarchaeological studies",
                height=80
            )
            
            geoarch_studies = st.text_area(
                "Relevant Regional Studies",
                placeholder="e.g., General studies on cave preservation in this region...",
                help="Broader regional geoarchaeology",
                height=60
            )
            
            st.markdown("---")
            st.markdown("### 📝 Additional Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                time_period = st.text_input(
                    "Time Period",
                    placeholder="e.g., Middle Palaeolithic"
                )
                excavation_year = st.number_input(
                    "Excavation Year",
                    min_value=1800,
                    max_value=2026,
                    value=2024
                )
            
            with col2:
                context_confidence = st.selectbox(
                    "Context Characterization Confidence",
                    ["High", "Medium", "Low"],
                    help="How well is the site context understood?"
                )
            
            taphonomic_notes = st.text_area(
                "Taphonomic Notes",
                placeholder="Any additional taphonomic observations, exceptional conditions, diagenetic processes...",
                height=80
            )
            
            st.markdown("---")
            
            # Submit button
            submitted = st.form_submit_button("✅ Register Site with Full Context", type="primary")
            
            if submitted and site_name and country:
                try:
                    # Create default project if needed
                    projects = db.get_projects()
                    if not projects or len(projects) == 0:
                        default_project = db.create_project(
                            project_name="Default Project",
                            description="Auto-created"
                        )
                        project_id = default_project['project_id']
                    else:
                        project_id = projects[0]['project_id']
                    
                    # Create site with full context
                    site = db.create_site_with_context(
                        project_id=project_id,
                        site_name=site_name,
                        country=country,
                        region=region,
                        latitude=latitude,
                        longitude=longitude,
                        elevation=elevation,
                        climate_zone=climate_zone,
                        rainfall_regime=rainfall_regime,
                        temperature_regime=temperature_regime,
                        context_type=context_type,
                        context_description=context_description,
                        ph_condition=ph_condition,
                        water_table=water_table,
                        microbial_activity=microbial_activity,
                        guano_presence=guano_presence,
                        organic_preservation=organic_preservation,
                        mineral_preservation=mineral_preservation,
                        site_references=site_references,
                        geoarch_studies=geoarch_studies,
                        time_period=time_period,
                        excavation_year=excavation_year,
                        context_confidence=context_confidence,
                        taphonomic_notes=taphonomic_notes
                    )
                    
                    st.success(f"✅ Registered site: {site_name} with full context!")
                    st.session_state.current_site_id = site['site_id']
                    
                    # Show context summary
                    st.info(f"""
                    **Context Summary:**
                    - Type: {context_type}
                    - Climate: {climate_zone}
                    - Preservation: Organic={organic_preservation}, Mineral={mineral_preservation}
                    - Authentication method will use context-specific criteria!
                    """)
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error creating site: {str(e)}")
                    st.exception(e)

def get_context_description(context_type):
    """Get brief description of expected signatures"""
    descriptions = {
        "cave_guano": "High P (3-20%), Mn indicator for bat guano",
        "cave_carbonate": "High Ca, moderate P (0.5-3%)",
        "open_air_sand": "Low P (<2%), Si contamination",
        "peat_bog": "Very low P, excellent organic preservation"
    }
    return descriptions.get(context_type, "See literature for expected signatures")


# ================================================
# DATABASE FUNCTION TO ADD
# ================================================

def create_site_with_context(self, project_id, site_name, **context_params):
    """
    Create site with full taphonomic context
    Add this to database.py TaphoSpecDB class
    """
    
    data = {
        "project_id": project_id,
        "site_name": site_name,
        "country": context_params.get('country'),
        "region": context_params.get('region'),
        "latitude": context_params.get('latitude'),
        "longitude": context_params.get('longitude'),
        "elevation": context_params.get('elevation'),
        "climate_zone": context_params.get('climate_zone'),
        "rainfall_regime": context_params.get('rainfall_regime'),
        "temperature_regime": context_params.get('temperature_regime'),
        "context_type": context_params.get('context_type'),
        "context_type_detailed": context_params.get('context_description'),
        "ph_condition": context_params.get('ph_condition'),
        "water_table": context_params.get('water_table'),
        "microbial_activity": context_params.get('microbial_activity'),
        "guano_presence": context_params.get('guano_presence', False),
        "organic_preservation": context_params.get('organic_preservation'),
        "mineral_preservation": context_params.get('mineral_preservation'),
        "site_references": context_params.get('site_references'),
        "geoarch_studies": context_params.get('geoarch_studies'),
        "time_period": context_params.get('time_period'),
        "excavation_year": context_params.get('excavation_year'),
        "context_confidence": context_params.get('context_confidence'),
        "taphonomic_notes": context_params.get('taphonomic_notes')
    }
    
    # Remove None values
    data = {k: v for k, v in data.items() if v is not None}
    
    result = self.client.table("sites").insert(data).execute()
    return result.data[0] if result.data else None
