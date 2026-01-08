"""
Authentication Module for TaphoSpec
Handles user login, registration, and session management
"""

import streamlit as st
from typing import Optional, Dict
import hashlib
import re

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


class AuthManager:
    """Manages user authentication using Supabase"""
    
    def __init__(self, supabase_client: Client):
        """Initialize with Supabase client"""
        self.client = supabase_client
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password: str) -> tuple[bool, str]:
        """
        Validate password strength
        Returns (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"
        
        return True, ""
    
    def register_user(self, email: str, password: str, full_name: str, 
                     institution: str = None) -> tuple[bool, str]:
        """
        Register a new user
        Returns (success, message)
        """
        # Validate email
        if not self.validate_email(email):
            return False, "Invalid email format"
        
        # Validate password
        is_valid, error_msg = self.validate_password(password)
        if not is_valid:
            return False, error_msg
        
        # Check if user already exists
        try:
            result = self.client.table('users').select('email').eq('email', email).execute()
            if len(result.data) > 0:
                return False, "Email already registered"
        except Exception as e:
            return False, f"Database error: {str(e)}"
        
        # Create user
        try:
            hashed_password = self.hash_password(password)
            
            user_data = {
                'email': email,
                'password_hash': hashed_password,
                'full_name': full_name,
                'institution': institution,
                'is_active': True,
                'is_admin': False
            }
            
            result = self.client.table('users').insert(user_data).execute()
            
            if result.data:
                return True, "Registration successful! Please log in."
            else:
                return False, "Registration failed"
                
        except Exception as e:
            return False, f"Registration error: {str(e)}"
    
    def login(self, email: str, password: str) -> tuple[bool, Optional[Dict], str]:
        """
        Authenticate user
        Returns (success, user_data, message)
        """
        if not email or not password:
            return False, None, "Please enter email and password"
        
        try:
            # Get user from database
            result = self.client.table('users').select('*').eq('email', email).execute()
            
            if len(result.data) == 0:
                return False, None, "Invalid email or password"
            
            user = result.data[0]
            
            # Check if user is active
            if not user.get('is_active', False):
                return False, None, "Account is deactivated. Please contact admin."
            
            # Verify password
            hashed_password = self.hash_password(password)
            if user['password_hash'] != hashed_password:
                return False, None, "Invalid email or password"
            
            # Update last login
            self.client.table('users').update({
                'last_login': 'now()'
            }).eq('user_id', user['user_id']).execute()
            
            # Remove password hash from returned data
            user.pop('password_hash', None)
            
            return True, user, "Login successful!"
            
        except Exception as e:
            return False, None, f"Login error: {str(e)}"
    
    def logout(self):
        """Clear session state for logout"""
        keys_to_clear = ['authenticated', 'user', 'user_id', 'user_email', 
                        'user_name', 'is_admin']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    def change_password(self, user_id: str, old_password: str, 
                       new_password: str) -> tuple[bool, str]:
        """
        Change user password
        Returns (success, message)
        """
        # Validate new password
        is_valid, error_msg = self.validate_password(new_password)
        if not is_valid:
            return False, error_msg
        
        try:
            # Get user
            result = self.client.table('users').select('password_hash').eq(
                'user_id', user_id
            ).execute()
            
            if len(result.data) == 0:
                return False, "User not found"
            
            # Verify old password
            old_hash = self.hash_password(old_password)
            if result.data[0]['password_hash'] != old_hash:
                return False, "Current password is incorrect"
            
            # Update password
            new_hash = self.hash_password(new_password)
            self.client.table('users').update({
                'password_hash': new_hash
            }).eq('user_id', user_id).execute()
            
            return True, "Password changed successfully!"
            
        except Exception as e:
            return False, f"Error changing password: {str(e)}"


def init_auth_session_state():
    """Initialize authentication-related session state"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
    
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False


def render_login_page():
    """Render the login/registration page"""
    
    st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <h1 style="color: #78350f; font-size: 3rem;">🔬 TaphoSpec</h1>
            <p style="font-size: 1.2rem; color: #64748b;">
                Archaeological Residue Authentication Platform
            </p>
            <p style="color: #94a3b8;">TraceoLab, University of Liège</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for login and registration
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    
    # Get auth manager from session state
    auth = st.session_state.get('auth_manager')
    
    if not auth:
        st.error("Authentication system not initialized. Please check database configuration.")
        return
    
    with tab1:
        render_login_form(auth)
    
    with tab2:
        render_registration_form(auth)
    
    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; color: #94a3b8; font-size: 0.9rem;">
            <p>For demo access, contact: traceolab@uliege.be</p>
            <p>TaphoSpec v2.0 | Secure Multi-User Platform</p>
        </div>
    """, unsafe_allow_html=True)


def render_login_form(auth: AuthManager):
    """Render login form"""
    
    st.markdown("### Sign In")
    
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="your.email@institution.edu")
        password = st.text_input("Password", type="password")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            submit = st.form_submit_button("🔐 Login", use_container_width=True)
        
        with col2:
            st.markdown("")  # Spacer
        
        if submit:
            if not email or not password:
                st.error("Please enter both email and password")
            else:
                with st.spinner("Authenticating..."):
                    success, user_data, message = auth.login(email, password)
                
                if success:
                    # Set session state
                    st.session_state.authenticated = True
                    st.session_state.user = user_data
                    st.session_state.user_id = user_data['user_id']
                    st.session_state.user_email = user_data['email']
                    st.session_state.user_name = user_data['full_name']
                    st.session_state.is_admin = user_data.get('is_admin', False)
                    
                    st.success(message)
                    st.balloons()
                    
                    # Rerun to show main app
                    st.rerun()
                else:
                    st.error(message)


def render_registration_form(auth: AuthManager):
    """Render registration form"""
    
    st.markdown("### Create Account")
    
    st.info("""
        **Registration Requirements:**
        - Valid institutional email
        - Password: min 8 chars, must include uppercase, lowercase, and digit
        - Approval required for full access
    """)
    
    with st.form("registration_form"):
        full_name = st.text_input("Full Name *", placeholder="John Doe")
        email = st.text_input("Email *", placeholder="john.doe@institution.edu")
        institution = st.text_input("Institution", placeholder="University of Liège")
        
        password = st.text_input("Password *", type="password", 
                                help="Min 8 chars, uppercase, lowercase, digit")
        password_confirm = st.text_input("Confirm Password *", type="password")
        
        st.markdown("---")
        
        agree = st.checkbox("I agree to the Terms of Use and Privacy Policy")
        
        submit = st.form_submit_button("📝 Register", use_container_width=True)
        
        if submit:
            # Validation
            if not full_name or not email or not password:
                st.error("Please fill in all required fields (marked with *)")
            elif password != password_confirm:
                st.error("Passwords do not match")
            elif not agree:
                st.error("Please agree to the Terms of Use")
            else:
                with st.spinner("Creating account..."):
                    success, message = auth.register_user(
                        email=email,
                        password=password,
                        full_name=full_name,
                        institution=institution
                    )
                
                if success:
                    st.success(message)
                    st.info("You can now log in with your credentials.")
                else:
                    st.error(message)


def render_user_menu():
    """Render user menu in sidebar"""
    
    if st.session_state.authenticated:
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"**👤 {st.session_state.user_name}**")
        st.sidebar.caption(st.session_state.user_email)
        
        if st.session_state.is_admin:
            st.sidebar.caption("🔑 Administrator")
        
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            auth = st.session_state.get('auth_manager')
            if auth:
                auth.logout()
            st.success("Logged out successfully")
            st.rerun()


def check_authentication():
    """
    Check if user is authenticated
    Returns True if authenticated, False otherwise
    Shows login page if not authenticated
    """
    init_auth_session_state()
    
    if not st.session_state.authenticated:
        render_login_page()
        return False
    
    return True


# Admin functions
def is_admin() -> bool:
    """Check if current user is admin"""
    return st.session_state.get('is_admin', False)


def render_admin_panel(auth: AuthManager):
    """Render admin panel for user management"""
    
    if not is_admin():
        st.error("Access denied. Admin privileges required.")
        return
    
    st.header("👨‍💼 Admin Panel")
    
    tab1, tab2, tab3 = st.tabs(["Users", "Activity", "Settings"])
    
    with tab1:
        st.subheader("User Management")
        
        try:
            # Get all users
            result = auth.client.table('users').select('*').execute()
            users = result.data
            
            if users:
                for user in users:
                    with st.expander(f"{user['full_name']} ({user['email']})"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**Institution:** {user.get('institution', 'N/A')}")
                            st.write(f"**Created:** {user.get('created_at', 'N/A')[:10]}")
                        
                        with col2:
                            st.write(f"**Last Login:** {user.get('last_login', 'Never')[:10] if user.get('last_login') else 'Never'}")
                            st.write(f"**Admin:** {'Yes' if user.get('is_admin') else 'No'}")
                        
                        with col3:
                            active = user.get('is_active', False)
                            st.write(f"**Status:** {'🟢 Active' if active else '🔴 Inactive'}")
                            
                            if st.button("Toggle Status", key=f"toggle_{user['user_id']}"):
                                auth.client.table('users').update({
                                    'is_active': not active
                                }).eq('user_id', user['user_id']).execute()
                                st.rerun()
            else:
                st.info("No users found")
                
        except Exception as e:
            st.error(f"Error loading users: {e}")
    
    with tab2:
        st.subheader("Recent Activity")
        st.info("Activity logging coming soon")
    
    with tab3:
        st.subheader("System Settings")
        st.info("System settings coming soon")
