# TaphoSpec Quick Start Guide

## 🚀 Installation & Setup

### Option 1: Run Locally

```bash
# Clone the repository
git clone https://github.com/yourusername/taphospec.git
cd taphospec

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### Option 2: Use Streamlit Cloud

Visit: [https://your-app-url.streamlit.app](https://your-app-url.streamlit.app)

No installation required!

## 📊 Using TaphoSpec

### Step 1: Prepare Your Data

Export your SEM-EDS data as CSV or Excel with these columns:

**Required:**
- C (Carbon, mass %)
- P (Phosphorus, mass %)
- Ca (Calcium, mass %)
- Mn (Manganese, mass %)

**Optional but recommended:**
- Fe (Iron)
- K (Potassium)
- Al (Aluminum)
- Si (Silicon)
- O (Oxygen)

**Example CSV format:**
```csv
C,P,Ca,Mn,Fe,K,Al,Si
45.6,0.8,2.1,0.1,0.4,0.3,0.2,0.2
38.2,2.9,4.2,0.2,0.8,0.4,0.3,0.1
```

### Step 2: Upload Data

1. Go to **Data Import** page
2. Click "Choose a file"
3. Select your CSV or Excel file
4. Review the data preview

### Step 3: Analyze Correlations

1. Navigate to **Correlation Analysis**
2. Review the scatter plots for each element pair
3. Look for significant correlations (highlighted in green/red)
4. Read the interpretation boxes

**Key correlations to watch:**
- **P-Ca** (r > 0.7): Strong guano diagenesis
- **K-Al** (r > 0.6): Acidic conditions present
- **C-P** (r < -0.3): Organic carbon being replaced

### Step 4: View Authentication Results

1. Go to **Authentication** page
2. Review the summary metrics (organic vs mineral counts)
3. Check the Ca/P ratio interpretation
4. Examine the classification breakdown chart
5. Scroll to detailed results table

**Color coding:**
- 🟢 Green: Organic residues (proceed to molecular analysis)
- 🔴 Red: Mineral mimics (exclude from analysis)
- 🟡 Yellow: Ambiguous (additional testing needed)

### Step 5: Document Visual Attributes (Optional)

1. Navigate to **Visual Attributes** page
2. Select an analysis point
3. Record optical microscopy observations:
   - Color (brown, black, etc.)
   - Texture (amorphous, crystalline, etc.)
   - Location (backed edge, proximal end, etc.)
   - Boundaries (sharp, conforming, etc.)
4. Document SEM morphology at 500-2000× magnification
5. Save attributes

### Step 6: Generate Report

1. Go to **Report** page
2. Review the executive summary
3. Check classification breakdown
4. Read recommendations
5. Export results as CSV or Excel

## 🎯 Interpreting Results

### High Confidence Organic Adhesive
```
✓ Classification: Organic Adhesive
✓ C > 25%, Mn < 1%, P < 3%
→ Action: Proceed with FTIR spectroscopy and/or GC-MS
```

### High Confidence Mineral Mimic
```
✗ Classification: Mn-Phosphate Mineral Mimic
✗ Mn > 5%
→ Action: Exclude from organic residue analysis
```

### Medium/Low Confidence
```
⚠ Classification: Partially Mineralized Organic
⚠ Mixed elemental signature
→ Action: High-magnification SEM morphology assessment needed
```

## 📈 Best Practices

1. **Always check correlations first** - This tells you about the diagenetic environment
2. **Don't rely on elemental data alone** - Combine with optical and SEM observations
3. **Pay attention to Ca/P ratios** - Values of 1.5-1.8 indicate apatite formation
4. **Document ambiguous cases** - Visual attributes help resolve borderline classifications
5. **Consider spatial context** - Preservation varies across excavation units

## ⚠️ Common Pitfalls

1. **Assuming brown residues are organic** - Mn-phosphates can look identical optically
2. **Ignoring Ca/P ratios** - Essential for identifying biogenic phosphates
3. **Missing strong correlations** - These indicate systematic diagenetic processes
4. **Not documenting visual data** - Critical for multi-criteria authentication

## 🔧 Troubleshooting

### Data Upload Issues
- Ensure column names match exactly (C, P, Ca, Mn)
- Check that values are numeric (not text)
- Remove any merged cells in Excel
- Use comma or semicolon as separator

### Missing Correlations
- Need at least 3 valid data points per correlation
- Check for zeros or negative values
- Ensure both elements in pair are present

### Classification Seems Wrong
- Review the diagnostic reasoning in detailed view
- Check if visual observations conflict with elemental data
- Consider that mixed signatures are common in partially mineralized samples

## 💡 Tips for Publication

1. **Report n-values** for all correlations
2. **Include Ca/P ratio distributions** (mean, SD, range)
3. **Document classification percentages** by category
4. **Specify confidence levels** for each authenticated residue
5. **Describe taphonomic context** based on correlation patterns
6. **Acknowledge limitations** (e.g., spatial heterogeneity)

## 📚 Additional Resources

- **Methodology**: See README.md for scientific background
- **Citation**: See README.md for proper citation format
- **Source code**: Available on GitHub
- **Contact**: dries.cnuts@uliege.be

## 🎓 Training Data

Practice with the included sample dataset:
`sample_data/sample_sibudu_data.csv`

This contains 40 realistic analyses based on Sibudu Cave research.

---

**Need help?** Open an issue on GitHub or contact dries.cnuts@uliege.be
