# ================================================
# TAPHOSPEC v2.4 - CONTEXT-AWARE AUTHENTICATION
# ================================================
# Add these functions to your database.py or create context_analysis.py

import pandas as pd
import numpy as np

# ================================================
# CONTEXT REFERENCE DATABASE
# ================================================

CONTEXT_REFERENCES = {
    "cave_guano": {
        "name": "Cave (Guano-Rich)",
        "key_papers": [
            "Karkanas, P., Bar-Yosef, O., Goldberg, P., & Weiner, S. (2000). Diagenesis in prehistoric caves: the use of minerals that form in situ to assess the completeness of the archaeological record. Journal of Archaeological Science, 27(10), 915-929.",
            "Weiner, S. (2010). Microarchaeology: Beyond the Visible Archaeological Record. Cambridge University Press.",
            "Goldberg, P., Miller, C. E., & Mentzer, S. M. (2017). Recognizing fire in the Paleolithic archaeological record. Current Anthropology, 58(S16), S175-S190."
        ],
        "expected_signatures": {
            "P_min": 3.0,
            "P_max": 20.0,
            "C_baseline": 10.0,  # Guano contribution
            "Ca_P_ratio": (1.2, 2.5),
            "Mn_indicator": 0.5  # Bat guano marker
        },
        "corrections": {
            "C_adjustment": True,
            "P_baseline": 5.0  # Subtract guano background
        },
        "interpretation": """
        Guano-rich caves present unique taphonomic challenges:
        - Elevated phosphorus (P) from bat/bird guano is EXPECTED, not contamination
        - Carbon (C) enrichment from guano organics requires correction
        - Manganese (Mn) >0.5% is diagnostic of bat guano (Karkanas 2000)
        - Alkaline pH from guano promotes carbonate preservation
        - Ca/P ratios affected by guano apatite formation
        
        Authentication must distinguish residue organics from guano organics.
        """,
        "method": "Karkanas (2000) guano-cave criteria with corrections"
    },
    
    "cave_carbonate": {
        "name": "Cave (Carbonate-Rich)",
        "key_papers": [
            "Karkanas, P., & Goldberg, P. (2019). Reconstructing Archaeological Sites: Understanding the Geoarchaeological Matrix. Wiley-Blackwell.",
            "Shahack-Gross, R. (2011). Herbivorous livestock dung: formation, taphonomy, methods for identification, and archaeological significance. Journal of Archaeological Science, 38(2), 205-218."
        ],
        "expected_signatures": {
            "P_min": 0.5,
            "P_max": 3.0,
            "Ca_high": True,
            "carbonate_presence": True
        },
        "interpretation": """
        Carbonate-rich caves provide moderate preservation:
        - Alkaline pH (typically 8-9) promotes carbonate formation
        - Calcium (Ca) enrichment from speleothem formation
        - Moderate organic preservation
        - Mineral residues well-preserved
        """,
        "method": "Standard Karkanas & Weiner (2010) with carbonate consideration"
    },
    
    "open_air_sand": {
        "name": "Open-Air (Sand/Sandstone)",
        "key_papers": [
            "Goldberg, P., & Berna, F. (2010). Micromorphology and context. Quaternary International, 214(1-2), 56-62.",
            "Miller, C. E., Goldberg, P., & Berna, F. (2013). Geoarchaeological investigations at Diepkloof Rock Shelter, Western Cape, South Africa. Journal of Archaeological Science, 40(9), 3432-3452.",
            "Karkanas, P., Shahack-Gross, R., Ayalon, A., Bar-Matthews, M., Barkai, R., Frumkin, A., Gopher, A., & Stiner, M. C. (2007). Evidence for habitual use of fire at the end of the Lower Paleolithic: Site-formation processes at Qesem Cave, Israel. Journal of Human Evolution, 53(2), 197-212."
        ],
        "expected_signatures": {
            "P_min": 0.1,
            "P_max": 2.0,
            "C_max": 15.0,  # Higher C suspicious
            "Si_high": True  # Sand contamination
        },
        "corrections": {
            "Si_adjustment": True,  # Subtract sediment background
            "leaching_factor": 0.5  # P depletion expected
        },
        "interpretation": """
        Open-air sites present POOR preservation conditions:
        - Phosphorus (P) depletion due to leaching (Goldberg & Berna 2010)
        - Rapid oxidation destroys organics
        - Silicon (Si) enrichment from sand/sandstone matrix
        - Surviving organics indicate EXCEPTIONAL preservation or recent deposition
        - UV degradation, temperature fluctuations accelerate decay
        
        Any identified organic residues in these contexts are significant findings.
        """,
        "method": "Goldberg & Berna (2010) open-air criteria with leaching correction"
    },
    
    "open_air_clay": {
        "name": "Open-Air (Clay/Silt)",
        "key_papers": [
            "Goldberg, P., & Berna, F. (2010). Micromorphology and context. Quaternary International, 214(1-2), 56-62.",
            "Macphail, R. I., & Goldberg, P. (2018). Applied Soils and Micromorphology in Archaeology. Cambridge University Press."
        ],
        "expected_signatures": {
            "P_min": 0.2,
            "P_max": 3.0,
            "Al_high": True,  # Clay minerals
            "Fe_moderate": True
        },
        "interpretation": """
        Clay-rich open-air sites offer better preservation than sand:
        - Clay minerals can sequester and protect organics
        - Aluminum (Al) and Iron (Fe) enrichment from clay
        - Moderate P retention (better than sand)
        - Moisture retention affects preservation
        """,
        "method": "Modified Karkanas & Weiner for clay contexts"
    },
    
    "rockshelter": {
        "name": "Rockshelter",
        "key_papers": [
            "Karkanas, P., Shahack-Gross, R., Ayalon, A., Bar-Matthews, M., Barkai, R., Frumkin, A., Gopher, A., & Stiner, M. C. (2007). Evidence for habitual use of fire at the end of the Lower Paleolithic. Journal of Human Evolution, 53(2), 197-212.",
            "Goldberg, P., Miller, C. E., Schiegl, S., Ligouis, B., Berna, F., Conard, N. J., & Wadley, L. (2009). Bedding, hearths, and site maintenance in the Middle Stone Age of Sibudu Cave, KwaZulu-Natal, South Africa. Archaeological and Anthropological Sciences, 1(2), 95-122."
        ],
        "expected_signatures": {
            "P_min": 0.5,
            "P_max": 5.0,
            "variable_preservation": True
        },
        "interpretation": """
        Rockshelters offer GOOD intermediate preservation:
        - Protection from direct weathering
        - Variable pH depending on bedrock geology
        - Moderate to good organic preservation
        - Ash deposition from hearths can affect chemistry
        """,
        "method": "Standard Karkanas & Weiner (2010) criteria"
    },
    
    "peat_bog": {
        "name": "Peat Bog",
        "key_papers": [
            "van Geel, B. (2001). Non-pollen palynomorphs. In J. P. Smol, H. J. B. Birks, & W. M. Last (Eds.), Tracking Environmental Change Using Lake Sediments (pp. 99-119). Springer.",
            "Harrault, L., Milek, K., Jardé, E., Jeanneau, L., Derrien, M., & Anderson, D. G. (2019). Faecal biomarkers can distinguish specific mammalian species in modern and past environments. PLoS ONE, 14(2), e0211119."
        ],
        "expected_signatures": {
            "P_min": 0.0,
            "P_max": 0.5,
            "C_high": True,
            "organic_excellent": True,
            "mineral_absent": True
        },
        "corrections": {
            "ignore_ca_p": True  # Meaningless in acidic conditions
        },
        "interpretation": """
        Peat bogs provide EXCEPTIONAL organic preservation:
        - Acidic conditions (pH 3-5) destroy mineral residues
        - Waterlogged anaerobic environment preserves organics
        - Very low phosphorus (acidic dissolution)
        - Ca/P ratios are MEANINGLESS - ignore mineral indicators
        - Focus exclusively on organic chemical signatures
        
        Wood tar, plant resins excellently preserved. Bone, shell dissolved.
        """,
        "method": "Bog-specific organic-only analysis (ignore mineral criteria)"
    }
}

# ================================================
# CONTEXT-AWARE AUTHENTICATION FUNCTION
# ================================================

def authenticate_with_context(data, site_context):
    """
    Apply context-specific authentication criteria
    
    Parameters:
    -----------
    data : pd.DataFrame
        EDS analysis data
    site_context : dict
        Site context information including 'context_type'
    
    Returns:
    --------
    results : pd.DataFrame
        Authenticated data with context-aware classifications
    methodology : str
        Method used for authentication
    references : list
        Key publications cited
    """
    
    context_type = site_context.get('context_type', 'unknown')
    
    # Get context parameters
    if context_type in CONTEXT_REFERENCES:
        context_params = CONTEXT_REFERENCES[context_type]
    else:
        # Default to standard K&W
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
    
    # Add confidence levels based on context
    results = add_confidence_levels(results, context_params)
    
    return {
        'results': results,
        'methodology': context_params['method'],
        'references': context_params['key_papers'],
        'interpretation': context_params['interpretation']
    }

# ================================================
# GUANO CAVE AUTHENTICATION
# ================================================

def authenticate_guano_cave(data, context_params, site_context):
    """Apply guano-cave specific authentication"""
    
    results = data.copy()
    guano_baseline_P = context_params['corrections']['P_baseline']
    
    for idx, row in results.iterrows():
        C = row.get('c', 0)
        P = row.get('p', 0)
        Mn = row.get('mn', 0)
        Ca = row.get('ca', 0)
        
        # Correct for guano contribution
        corrected_P = max(0, P - guano_baseline_P)
        
        # Manganese indicator for bat guano
        if Mn > context_params['expected_signatures']['Mn_indicator']:
            results.at[idx, 'guano_indicator'] = f"Bat guano (Mn={Mn:.2f}%)"
        
        # Correct carbon for guano organics
        if C > 10 and P > 5:
            # Estimate guano contribution
            guano_C_contribution = (P / guano_baseline_P) * context_params['expected_signatures']['C_baseline']
            corrected_C = max(0, C - guano_C_contribution)
            results.at[idx, 'corrected_c'] = corrected_C
            results.at[idx, 'correction_note'] = f"C corrected for guano ({guano_C_contribution:.1f}%)"
        else:
            results.at[idx, 'corrected_c'] = C
        
        # Classification using corrected values
        corrected_C_val = results.at[idx, 'corrected_c']
        
        if corrected_C_val > 20:
            classification = "Organic"
            confidence = "High" if corrected_P < 2 else "Medium"
        elif corrected_P > 10 and Ca/P < 2.0 if P > 0 else False:
            classification = "Apatite"
            confidence = "Medium"  # Guano complicates
        elif corrected_C_val < 5 and corrected_P < 2:
            classification = "Mimic"
            confidence = "High"
        else:
            classification = "Mixed/Uncertain"
            confidence = "Low"
        
        results.at[idx, 'context_adjusted_classification'] = classification
        results.at[idx, 'confidence_level'] = confidence
        results.at[idx, 'taphonomic_interpretation'] = f"Guano-rich cave context. {context_params['interpretation'][:100]}..."
    
    return results

# ================================================
# OPEN-AIR AUTHENTICATION
# ================================================

def authenticate_open_air(data, context_params, site_context):
    """Apply open-air specific authentication"""
    
    results = data.copy()
    
    for idx, row in results.iterrows():
        C = row.get('c', 0)
        P = row.get('p', 0)
        Si = row.get('si', 0)
        
        # High Si indicates sediment contamination
        if Si > 20:
            results.at[idx, 'contamination_note'] = f"High Si ({Si:.1f}%) - sediment contamination likely"
        
        # Surviving organics in open-air are exceptional
        if C > 20:
            results.at[idx, 'context_adjusted_classification'] = "Organic (Exceptional Preservation!)"
            results.at[idx, 'confidence_level'] = "High"
            results.at[idx, 'taphonomic_interpretation'] = "Organic preservation in open-air context indicates exceptional conditions or recent deposition"
        elif P > context_params['expected_signatures']['P_max']:
            # Unlikely in open-air (leaching)
            results.at[idx, 'context_adjusted_classification'] = "Apatite (Unexpected - verify)"
            results.at[idx, 'confidence_level'] = "Low"
            results.at[idx, 'taphonomic_interpretation'] = "High P unusual in open-air (leaching expected). Possible protected microenvironment"
        elif C < 10 and P < 1:
            results.at[idx, 'context_adjusted_classification'] = "Mimic (Expected)"
            results.at[idx, 'confidence_level'] = "High"
            results.at[idx, 'taphonomic_interpretation'] = "Low C and P consistent with open-air degradation"
        else:
            results.at[idx, 'context_adjusted_classification'] = "Mixed/Degraded"
            results.at[idx, 'confidence_level'] = "Medium"
    
    return results

# ================================================
# PEAT BOG AUTHENTICATION  
# ================================================

def authenticate_peat_bog(data, context_params):
    """Apply peat bog specific authentication (organic-only)"""
    
    results = data.copy()
    
    for idx, row in results.iterrows():
        C = row.get('c', 0)
        P = row.get('p', 0)
        
        # Ignore Ca/P ratios (meaningless in acidic bogs)
        results.at[idx, 'ca_p_ignored'] = True
        
        if C > 30:
            results.at[idx, 'context_adjusted_classification'] = "Organic (Well-Preserved)"
            results.at[idx, 'confidence_level'] = "High"
            results.at[idx, 'taphonomic_interpretation'] = "Exceptional organic preservation in bog environment"
        elif C > 15:
            results.at[idx, 'context_adjusted_classification'] = "Organic (Moderate)"
            results.at[idx, 'confidence_level'] = "Medium"
        elif P > 1:
            # Unexpected - minerals should dissolve
            results.at[idx, 'context_adjusted_classification'] = "Anomalous (mineral in acidic bog)"
            results.at[idx, 'confidence_level'] = "Low"
            results.at[idx, 'taphonomic_interpretation'] = "Mineral signature unexpected in acidic bog. Recent contamination?"
        else:
            results.at[idx, 'context_adjusted_classification'] = "Uncertain"
            results.at[idx, 'confidence_level'] = "Low"
    
    return results

# ================================================
# STANDARD AUTHENTICATION (fallback)
# ================================================

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
# CONFIDENCE LEVELS
# ================================================

def add_confidence_levels(data, context_params):
    """Add confidence assessment based on context appropriateness"""
    
    # Already added in context-specific functions
    return data
