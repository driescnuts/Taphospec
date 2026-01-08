# TaphoSpec v2.0 - Nieuwe Structuur

## 🎯 Overzicht Verbeteringen

### **1. Gebruiksvriendelijke Navigatie**

De app is nu georganiseerd volgens de natuurlijke onderzoeksworkflow:

```
🏠 Home Dashboard
   └─ Quick stats, recent projects, quick actions

📊 Data Management
   ├─ 📥 Import Data (met database integratie)
   ├─ 📝 View & Edit Data
   └─ 📍 Projects & Sites (met GPS coordinates)

🔬 Analysis
   ├─ ✓ Residue Authentication (Karkanas & Weiner)
   ├─ 📊 Spectral Analysis (FTIR/Raman matching)
   ├─ 📈 Statistical Analysis (PCA, HCA, correlations)
   └─ 🧮 Specialized Tools (Ca/P calculator, etc.)

📈 Results & Visualization
   ├─ 🗺️ Site Maps (geografische visualisatie)
   └─ 📊 Statistics Dashboard

⚙️ Settings & Help
```

### **2. Database Integratie - Opgeloste Problemen**

#### ✅ **Visuele Attributen Geïntegreerd in Samples Tabel**

**Probleem opgelost:** Visuele observaties (kleur, textuur, transparantie, etc.) zijn nu direct geïntegreerd in de `samples` tabel in plaats van in een aparte tabel.

**Nieuwe samples tabel structuur:**
```sql
CREATE TABLE samples (
    sample_id UUID PRIMARY KEY,
    site_id UUID REFERENCES sites,
    sample_code TEXT NOT NULL,
    
    -- Archaeological context
    tool_type TEXT,
    raw_material TEXT,
    location_on_tool TEXT,
    preservation_status TEXT,
    
    -- INTEGRATED visual attributes (Karkanas & Weiner)
    visual_color TEXT,
    visual_texture TEXT,
    visual_transparency TEXT,
    visual_luster TEXT,
    visual_morphology TEXT,
    visual_description TEXT,
    
    sample_notes TEXT,
    ...
);
```

**Voordelen:**
- Eén record per sample met alle metadata
- Geen complexe joins nodig
- Eenvoudigere data import
- Directe koppeling met sample_id

#### ✅ **Import Data Volledig Afgestemd**

De Import Data module is volledig aangepast aan de nieuwe database structuur:

1. **Project & Site Selection** - Stap 1 voor organisatie
2. **File Upload** - Excel/CSV met European decimal notation (komma's)
3. **Column Mapping** - Automatische detectie + manuele aanpassing
4. **Preview & Import** - Met validatie en progress tracking

**Ondersteunde kolommen:**
- Sample metadata (code, tool type, raw material, location)
- Visuele attributen (kleur, textuur, transparantie, luster, morfologie)
- Elemental data (C, N, O, P, Ca, K, Al, Mn, Fe, Si, Mg, Na, S, Cl, Ti, Zn)
- Acquisition parameters (voltage, beam current, analyst, date)

### **3. Karkanas & Weiner Methodologie**

De Residue Authentication module implementeert de volledige Karkanas & Weiner aanpak:

**Diagnostic Criteria:**
```python
Organic Adhesive:
- C > 25%
- Mn < 1%
- P < 3%

Mineral Mimic:
- Mn > 5% (diagnostic)

Biogenic Phosphate:
- 1.5 < Ca/P < 2.0
- Ca > 20%, P > 10%
```

**Output:**
- Classification (Organic Adhesive, Mineral Mimic, etc.)
- Confidence level (High, Medium, Low)
- Reasoning (array of diagnostic criteria met)
- Recommendations (follow-up analyses)

### **4. Verbeterde User Experience**

- **TraceoLab branding** met ULiège kleuren (#16a34a)
- **Context awareness** - Current project/site shown in sidebar
- **Progress tracking** - Voor lange operaties (import, authentication)
- **Validation** - Data quality checks voor import
- **Error handling** - Duidelijke foutmeldingen
- **European formats** - Comma decimals, date formats

## 🗄️ Database Setup

### **Nieuwe Schema (v2.0)**

1. **Drop oude schema** (als je die had):
```sql
DROP TABLE IF EXISTS interpretations CASCADE;
DROP TABLE IF EXISTS ftir_analyses CASCADE;
DROP TABLE IF EXISTS eds_analyses CASCADE;
DROP TABLE IF EXISTS samples CASCADE;
DROP TABLE IF EXISTS sites CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
```

2. **Run nieuwe schema:**
```bash
# In Supabase SQL Editor:
# Plak de volledige inhoud van database_schema_v2.sql
```

3. **Verify:**
```sql
-- Check samples table structure
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'samples' 
ORDER BY ordinal_position;
```

Je zou moeten zien:
- sample_id
- site_id
- sample_code
- tool_type
- raw_material
- location_on_tool
- preservation_status
- **visual_color** ← NIEUW
- **visual_texture** ← NIEUW
- **visual_transparency** ← NIEUW
- **visual_luster** ← NIEUW
- **visual_morphology** ← NIEUW
- **visual_description** ← NIEUW
- sample_notes
- created_at
- updated_at

## 📦 Deployment

### **Lokaal testen:**

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SUPABASE_URL="your-url"
export SUPABASE_KEY="your-key"

# Run app
streamlit run app.py
```

### **Streamlit Cloud:**

1. Push naar GitHub
2. Connect to Streamlit Cloud
3. Add secrets in dashboard:
```toml
SUPABASE_URL = "your-url"
SUPABASE_KEY = "your-key"
```

## 🎨 Customization

### **Kleuren aanpassen:**

In `app.py`, wijzig de CSS variabelen:
```css
:root {
    --primary-color: #16a34a;  /* TraceoLab green */
    --secondary-color: #059669;
}
```

### **Diagnostic thresholds:**

In `pages/residue_authentication.py`:
```python
c_threshold = 25  # Carbon minimum for organics
mn_max = 1        # Manganese maximum for organics
mn_mimic = 5      # Manganese diagnostic for mimics
```

## 🔬 Workflow Voorbeeld

### **Complete analyse workflow:**

1. **Create Project** (Data Management → Projects & Sites)
   - Project naam: "Guano Cave Study 2024"
   - PI: "Dries Cnuts"
   - Institution: "TraceoLab, ULiège"

2. **Register Site** (Data Management → Projects & Sites)
   - Site naam: "Blombos Cave"
   - Country: "South Africa"
   - GPS: -34.4167, 21.2167
   - Context: "guano-rich"

3. **Import Data** (Data Management → Import Data)
   - Upload Excel met EDS spectra
   - Map columns (auto-detect + manual)
   - Preview & validate
   - Import to database

4. **Authenticate** (Analysis → Residue Authentication)
   - Select data source (Current Site)
   - Adjust thresholds if needed
   - Run authentication
   - Review results
   - Save classifications

5. **Visualize** (Results → Site Maps)
   - View all sites on map
   - Color by preservation rate
   - Size by number of analyses
   - Click for details

6. **Export** (anywhere)
   - Download results as Excel
   - Generate PDF reports
   - Share with collaborators

## 📚 Belangrijke Bestanden

```
taphospec/
├── app.py                          # Main application
├── database.py                     # Database operations
├── database_schema_v2.sql          # Updated schema
├── requirements.txt                # Dependencies
├── pages/
│   ├── __init__.py
│   ├── home.py                     # Home dashboard
│   ├── import_data.py              # ✨ NIEUW - Fully integrated
│   ├── residue_authentication.py   # ✨ NIEUW - K&W methodology
│   ├── project_management.py
│   ├── site_maps.py
│   ├── statistics_dashboard.py
│   └── ...
└── README.md                       # This file
```

## ⚠️ Breaking Changes

Als je data had in de oude structuur:

1. **Backup oude data**
2. **Drop oude schema**
3. **Install nieuwe schema** (database_schema_v2.sql)
4. **Re-import data** met nieuwe Import Data module

De visuele attributen die voorheen in een aparte tabel zaten worden nu automatisch geïntegreerd tijdens import.

## 🆘 Troubleshooting

### "Database not connected"
→ Check Streamlit secrets of environment variables

### "Column 'visual_color' does not exist"
→ Update database schema met database_schema_v2.sql

### "Import fails with validation errors"
→ Check decimal notation (gebruik komma's voor Europese data)

### "Site map shows no sites"
→ Ensure sites have latitude/longitude coordinates

## 📧 Contact

**Dries Cnuts**
TraceoLab, University of Liège
dries.cnuts@uliege.be

---

**TaphoSpec v2.0** - Archaeological Residue Authentication Platform
