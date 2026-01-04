# TaphoSpec

**Multi-Modal Spectroscopic Analysis Platform for Archaeological Residue Authentication**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-url.streamlit.app)

TaphoSpec is a comprehensive analytical platform for authenticating archaeological residues using multi-modal spectroscopy, with specific focus on distinguishing preserved organic adhesives from authigenic mineral mimics in cave and rockshelter contexts.

## 🎯 Overview

Archaeological residues on stone tools can provide critical evidence for past human behavior, but diagenetic processes—particularly in phosphate-rich environments—can create mineral deposits that closely mimic organic residues. TaphoSpec provides systematic protocols for:

- **Elemental correlation analysis** to identify diagenetic processes
- **Automated authentication** based on diagnostic elemental criteria
- **Multi-criteria decision support** integrating chemical, optical, and morphological evidence
- **Taphonomic context interpretation** for robust scientific conclusions

## 🔬 Scientific Background

Based on research at Sibudu Cave (South Africa) documenting hafting adhesive preservation in guano-rich rockshelters. The platform implements methodologies from:

- Weiner et al. (2002) - Diagenetic mineral detection through elemental correlations
- Karkanas et al. (2000, 2002) - K-Al phosphate formation under acidic conditions  
- Shahack-Gross et al. (2004) - Organic carbon replacement patterns
- Mentzer et al. (2014) - Authigenic mineral assemblages in rockshelters

## ✨ Features

### Phase 1 (Current Release)

#### 1. **Correlation Analysis Module**
Diagnostic elemental correlations for identifying diagenetic pathways:
- **P-Ca correlation**: Calcium phosphate mineralisation (guano diagenesis)
- **K-Al correlation**: K-Al phosphate formation (acidic conditions, pH <5)
- **C-P anticorrelation**: Organic carbon replacement by phosphates
- **C-Mn anticorrelation**: Organic carbon replacement by Mn-bearing phases

#### 2. **Automated Authentication Workflow**
Classification based on diagnostic cut-off values:

**Organic Adhesives:**
- C > 25%, Mn < 1%, P < 3%
- C > 20%, Fe > 5%, Mn < 1%, P < 5% (ochre-loaded)

**Mineral Mimics:**
- Mn > 5% → Mn-phosphate (DIAGNOSTIC)
- P > 10%, Ca/P = 1.5-1.8, C < 10% → Apatite
- K > 2%, Al > 2%, P > 5% → K-Al phosphates

#### 3. **Ca/P Ratio Calculator**
Automatic calculation and interpretation:
- Brushite: ~1.0
- Hydroxyapatite/Dahllite: 1.6-1.7
- Biogenic phosphate identification

#### 4. **Confidence Scoring System**
High/Medium/Low confidence with detailed reasoning and recommendations for each analysis point.

#### 5. **Visual Attributes Documentation**
Structured recording of:
- Optical microscopy observations (color, texture, location, boundaries)
- SEM morphology (500-2000× magnification)
- Multi-criteria authentication framework

## 🚀 Getting Started

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/taphospec.git
cd taphospec

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

### Data Format

Upload SEM-EDS data as CSV or Excel with the following structure:

**Required columns:**
- `C` - Carbon (mass %)
- `P` - Phosphorus (mass %)
- `Ca` - Calcium (mass %)
- `Mn` - Manganese (mass %)

**Optional columns:**
- `N`, `O`, `K`, `Al`, `Fe`, `Si`, `Mg`, `Na`, `S`, `Cl`, `Ti`, `Zn`

**Example:**
```csv
C,P,Ca,Mn,Fe,K,Al,Si
45.6,0.8,2.1,0.1,0.4,0.3,0.2,0.2
38.2,2.9,4.2,0.2,0.8,0.4,0.3,0.1
6.8,9.1,7.2,24.3,3.1,1.2,0.8,4.1
```

### Sample Data

A test sample dataset is provided in `/sample_data/sample_sibudu_data.csv` for testing.

## 📊 Usage Workflow

1. **Data Import**: Upload your SEM-EDS elemental composition data
2. **Correlation Analysis**: Examine diagenetic signatures
3. **Authentication**: View automated classifications with confidence scores
4. **Visual Attributes**: Document optical and SEM morphological observations
5. **Report**: Generate comprehensive taphonomic analysis summary

## 🛠️ Technical Stack

- **Frontend**: Streamlit
- **Data Processing**: Pandas, NumPy
- **Statistics**: SciPy
- **Visualization**: Plotly
- **Export**: OpenPyXL

## 📖 Documentation

### Authentication Decision Tree

```
IF Mn > 5%
  → Mn-Phosphate Mineral Mimic (High Confidence)
  → EXCLUDE from organic residue analysis

ELIF P > 10% AND Ca/P = 1.5-1.8 AND C < 10%
  → Apatite/Hydroxyapatite (High Confidence)
  → EXCLUDE from organic residue analysis

ELIF K > 2% AND Al > 2% AND P > 5%
  → K-Al Phosphate (High Confidence)
  → Acidic diagenesis indicator
  → EXCLUDE from organic residue analysis

ELIF C > 25% AND Mn < 1% AND P < 3%
  → Organic Adhesive (High Confidence)
  → PROCEED to FTIR/GC-MS

ELIF C > 20% AND Fe > 5% AND Mn < 1% AND P < 5%
  → Ochre-Loaded Compound Adhesive (High Confidence)
  → PROCEED to FTIR/GC-MS

ELIF 15 ≤ C ≤ 25 AND 1 ≤ Mn ≤ 5 AND 3 ≤ P ≤ 8
  → Partially Mineralized Organic (Medium Confidence)
  → CAUTION: Detailed SEM morphology assessment needed

ELSE
  → Ambiguous (Low Confidence)
  → Additional analyses required
```

### Correlation Interpretation

| Correlation | Threshold | Sign | Interpretation |
|------------|-----------|------|----------------|
| P-Ca | \|r\| > 0.7 | + | Calcium phosphate mineralisation (guano) |
| K-Al | \|r\| > 0.6 | + | K-Al phosphate formation (pH <5) |
| K-P | \|r\| > 0.6 | + | K incorporation into phosphates |
| C-P | r < -0.3 | - | Phosphate replaces organic carbon |
| C-Mn | r < -0.2 | - | Mn oxides/phosphates replace carbon |

## 🗺️ Roadmap

### Phase 2 (Planned)
- Spatial aggregation by excavation unit/stratigraphic layer
- Raw material substrate effects tracking
- Preservation landscape mapping
- Batch processing capabilities

### Phase 3 (Future)
- FTIR spectral library integration
- Machine learning for SEM morphology classification
- Experimental taphonomy trajectory visualization
- Multi-site comparison tools

## 📚 Citation

If you use TaphoSpec in your research, please cite:

```
TaphoSpec: Multi-Modal Spectroscopic Analysis Platform for Archaeological Residue Authentication
Cnuts, D. et al. (2024)
TraceoLab, University of Liège
https://github.com/yourusername/taphospec
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Dries Cnuts** - TraceoLab, University of Liège
- Developed in collaboration with Claude (Anthropic)

## 🙏 Acknowledgments

- University of Liège, TraceoLab


## 📧 Contact

For questions or collaboration inquiries:
- Email: dries.cnuts@uliege.be
- Lab: [TraceoLab](https://www.traceolab.be/)

---

**TraceoLab · University of Liège · v1.0 Phase 1**
