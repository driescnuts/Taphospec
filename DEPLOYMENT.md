# Deploying TaphoSpec to Streamlit Cloud

## 📋 Prerequisites

1. GitHub account
2. Streamlit Cloud account (free - sign up at [share.streamlit.io](https://share.streamlit.io))
3. Your TaphoSpec repository on GitHub

## 🚀 Step-by-Step Deployment

### Step 1: Push to GitHub

```bash
# Navigate to your project directory
cd taphospec-app

# Initialize git repository (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: TaphoSpec v1.0 Phase 1"

# Add remote (replace with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/taphospec.git

# Push to GitHub
git push -u origin main
```

### Step 2: Connect to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "Sign up" or "Sign in" with GitHub
3. Authorize Streamlit to access your GitHub repositories

### Step 3: Deploy the App

1. Click "New app" button
2. Select your repository: `YOUR_USERNAME/taphospec`
3. Set branch: `main` (or `master` if that's your default)
4. Set main file path: `app.py`
5. Click "Deploy!"

### Step 4: Configure (Optional)

**Custom URL:**
- Go to app settings
- Under "General" → "App URL"
- Choose: `your-custom-name.streamlit.app`

**Secrets Management:**
If you need to add API keys or sensitive data later:
- Go to app settings
- Click "Secrets"
- Add key-value pairs in TOML format

### Step 5: Test Your Deployment

1. Wait for deployment to complete (~2-3 minutes)
2. Visit your app URL: `https://your-app-name.streamlit.app`
3. Test all features:
   - Upload the sample data
   - Navigate through all tabs
   - Check all visualizations
   - Export results

## 🔧 Troubleshooting

### Deployment Failed

**Check requirements.txt:**
```bash
# Ensure all package versions are compatible
pip install -r requirements.txt
streamlit run app.py  # Test locally first
```

**Common issues:**
- Missing package in requirements.txt
- Version conflicts
- Syntax errors in app.py

### App Crashes on Upload

- Check file size limits (Streamlit Cloud: 200MB)
- Verify CSV/Excel format compatibility
- Test with sample data first

### Slow Performance

- Reduce data processing complexity
- Add `@st.cache_data` decorators for expensive computations
- Consider pagination for large datasets

## 🔄 Updating Your App

Any push to your GitHub repository will automatically trigger a redeployment:

```bash
# Make changes to your code
git add .
git commit -m "Description of changes"
git push origin main
```

Streamlit Cloud will detect the changes and redeploy automatically.

## 🎨 Customization

### Change Theme Colors

Edit `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#d97706"      # Accent color
backgroundColor = "#fffbeb"    # Main background
secondaryBackgroundColor = "#fef3c7"  # Sidebar background
textColor = "#1e293b"         # Text color
```

### Add Custom Domain

1. Go to app settings → "General"
2. Click "Custom domain"
3. Follow DNS configuration instructions
4. Point your domain to Streamlit Cloud

## 📊 Monitoring

**View Logs:**
- Click on app settings
- Select "Logs" tab
- View real-time application logs

**Analytics:**
- Streamlit Cloud provides basic usage analytics
- View visitor statistics in app dashboard

## 💰 Pricing

**Free Tier:**
- 1 private app
- Unlimited public apps
- Community support
- 1GB RAM per app

**Team/Enterprise:**
- More resources
- Priority support
- Advanced features

For research/academic use, the free tier is usually sufficient.

## 🔒 Security Best Practices

1. **Don't commit sensitive data:**
   - Use `.gitignore` for data files
   - Add secrets via Streamlit Cloud interface

2. **Use environment variables:**
   ```python
   import os
   api_key = os.environ.get('API_KEY')
   ```

3. **Keep dependencies updated:**
   ```bash
   pip list --outdated
   pip install --upgrade package_name
   ```

## 🌐 Making Your App Public

By default, your app is public. To make it private:

1. Upgrade to Streamlit Team plan
2. Configure access controls in app settings
3. Share with specific email addresses

## 📱 Mobile Optimization

Streamlit apps are automatically mobile-responsive, but test on:
- iOS Safari
- Android Chrome
- Different screen sizes

## 🎓 Advanced Features

### Add Authentication

```python
import streamlit as st

def check_password():
    """Returns `True` if user had correct password."""
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", 
                     on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password", type="password",
                     on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        return True

if check_password():
    # Your app code here
    st.write("Welcome to TaphoSpec!")
```

### Enable Caching for Better Performance

```python
@st.cache_data
def load_data(file):
    return pd.read_csv(file)

@st.cache_data
def calculate_correlations(df):
    # Expensive computation
    return correlations
```

## 📚 Resources

- [Streamlit Documentation](https://docs.streamlit.io)
- [Streamlit Community Forum](https://discuss.streamlit.io)
- [Streamlit Gallery](https://streamlit.io/gallery) - For inspiration

## 🐛 Getting Help

**Issues with deployment:**
1. Check [Streamlit Community Forum](https://discuss.streamlit.io)
2. Review [Streamlit Docs](https://docs.streamlit.io)
3. Create issue on GitHub repository

**Issues with TaphoSpec:**
- Open issue on GitHub: [github.com/YOUR_USERNAME/taphospec/issues](https://github.com/YOUR_USERNAME/taphospec/issues)
- Email: dries.cnuts@uliege.be

---

## ✅ Deployment Checklist

- [ ] Code tested locally
- [ ] All dependencies in requirements.txt
- [ ] Sample data included
- [ ] README.md completed
- [ ] .gitignore configured
- [ ] Pushed to GitHub
- [ ] Connected to Streamlit Cloud
- [ ] App deployed successfully
- [ ] All features tested online
- [ ] Custom URL configured (optional)
- [ ] Documentation reviewed

**Your app is now live! 🎉**

Share the link with colleagues and collaborators.

---

**Need help?** Contact dries.cnuts@uliege.be
