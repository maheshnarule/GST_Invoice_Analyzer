
import os
import streamlit as st
import sqlite3
import hashlib
import time
import random
from streamlit_lottie import st_lottie
import requests
import json

# ==================== ADVANCED STYLING & ANIMATIONS ====================
def load_lottie_url(url: str):
    """Load Lottie animation from URL"""
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

def apply_advanced_styling():
    """Apply advanced CSS styling and animations"""
    st.markdown("""
    <style>
    /* Global Styles - WHITE BACKGROUND */
    .stApp {
        background: white !important;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }
    
    /* Main Container */
    .main-container {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
    
    /* Landing Page Styles */
    .landing-hero {
        text-align: center;
        padding: 4rem 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        color: white;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    
    .landing-hero::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000"><polygon fill="rgba(255,255,255,0.05)" points="0,1000 1000,0 1000,1000"/></svg>');
    }
    
    .hero-title {
        font-size: 4rem;
        font-weight: 800;
        margin-bottom: 1rem;
        background: linear-gradient(45deg, #fff, #f0f0f0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .hero-subtitle {
        font-size: 1.5rem;
        opacity: 0.9;
        margin-bottom: 2rem;
        font-weight: 300;
        color: white;
    }
    
    /* Feature Cards - 3 in a row */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 2rem;
        margin: 3rem 0;
    }
    
    .feature-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        color: white !important;
        transition: all 0.3s ease;
        cursor: pointer;
        min-height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
    }
    
    .feature-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 20px 40px rgba(102, 126, 234, 0.4);
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        color: white !important;
    }
    
    .feature-title {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: white !important;
    }
    
    .feature-description {
        font-size: 1rem;
        opacity: 0.9;
        line-height: 1.5;
        color: white !important;
    }
    
    /* Ensure all text in feature cards is white */
    .feature-card * {
        color: white !important;
    }
    
    /* Auth Container */
    .auth-container {
        max-width: 500px;
        margin: 2rem auto;
        background: white;
        border-radius: 20px;
        padding: 3rem;
        box-shadow: 0 20px 60px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
    
    /* Button Styles */
    .stButton > button {
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        border: none !important;
    }
    
    .primary-btn {
        background: linear-gradient(45deg, #667eea, #764ba2) !important;
        color: white !important;
    }
    
    .primary-btn:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3) !important;
    }
    
    /* Input Styles */
    .stTextInput > div > div > input {
        border-radius: 12px !important;
        border: 2px solid #e0e0e0 !important;
        padding: 12px 16px !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }
    
    /* Sidebar Styles */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2c3e50 0%, #3498db 100%) !important;
    }
    
    .sidebar-content {
        padding: 2rem 1rem;
    }
    
    .user-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: white;
    }
    
    /* Navigation Cards */
    .nav-card {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: white;
        cursor: pointer;
        transition: all 0.3s ease;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .nav-card:hover {
        background: rgba(255, 255, 255, 0.2);
        transform: translateX(5px);
    }
    
    .nav-card.active {
        background: rgba(255, 255, 255, 0.25);
        border-left: 4px solid #e74c3c;
    }
    
    /* Progress Bar */
    .progress-container {
        width: 100%;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        overflow: hidden;
        margin: 1rem 0;
    }
    
    .progress-bar {
        height: 6px;
        background: linear-gradient(45deg, #667eea, #764ba2);
        border-radius: 10px;
        transition: width 0.3s ease;
    }
    
    /* Notification Badge */
    .notification-badge {
        background: #e74c3c;
        color: white;
        border-radius: 50%;
        width: 20px;
        height: 20px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        margin-left: 8px;
    }
    
    /* Floating Elements */
    .floating {
        animation: float 6s ease-in-out infinite;
    }
    
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-20px); }
        100% { transform: translateY(0px); }
    }
    
    /* Gradient Text */
    .gradient-text {
        background: linear-gradient(45deg, #667eea, #764ba2, #e74c3c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-size: 300% 300%;
        animation: gradient 3s ease infinite;
    }
    
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Header with sidebar gradient */
    .sidebar-gradient-header {
        background: linear-gradient(180deg, #2c3e50 0%, #3498db 100%);
        color: white;
        padding: 3rem 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    /* Fix for white background */
    [data-testid="stAppViewContainer"] {
        background: white !important;
    }
    
    .main-header {
        background: white !important;
        color: #2c3e50 !important;
        padding: 2rem 0;
        margin-bottom: 2rem;
        border-bottom: 2px solid #e0e0e0;
    }
    </style>
    """, unsafe_allow_html=True)

# ==================== AUTHENTICATION FUNCTIONS ====================
def init_db():
    """Initialize database connection"""
    return sqlite3.connect("database.db", check_same_thread=False)

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(name, email, aadhaar_number, password, user_type="CA"):
    """Create new user in database"""
    try:
        conn = init_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM users WHERE email = ? OR aadhaar_number = ?", 
                      (email, aadhaar_number))
        if cursor.fetchone():
            return False, "User with this email or Aadhaar number already exists"
        
        hashed_pw = hash_password(password)
        cursor.execute(
            "INSERT INTO users (name, email, aadhaar_number, password, user_type) VALUES (?, ?, ?, ?, ?)",
            (name, email, aadhaar_number, hashed_pw, user_type)
        )
        conn.commit()
        conn.close()
        return True, "User created successfully"
    except Exception as e:
        return False, f"Error creating user: {str(e)}"

def verify_user(email, password):
    """Verify user credentials"""
    try:
        conn = init_db()
        cursor = conn.cursor()
        hashed_pw = hash_password(password)
        
        cursor.execute(
            "SELECT id, name, email, aadhaar_number, user_type FROM users WHERE email = ? AND password = ?",
            (email, hashed_pw)
        )
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return True, {
                'id': user[0],
                'name': user[1],
                'email': user[2],
                'aadhaar_number': user[3],
                'user_type': user[4]
            }
        else:
            return False, "Invalid email or password"
    except Exception as e:
        return False, f"Error verifying user: {str(e)}"

# ==================== ENHANCED AUTHENTICATION PAGES ====================
def landing_page():
    """Enhanced landing page with advanced styling"""
    apply_advanced_styling()
    
    # Hero Section
    st.markdown("""
    <div class="landing-hero" style="background: linear-gradient(180deg, #2c3e50 0%, #3498db 100%);">
        <div class="floating">
            <h1 class="hero-title">🧾 GST INVOICE ANALYZER</h1>
        </div>
        <p class="hero-subtitle">AI-Powered Invoice Processing Platform for Modern Businesses</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main Content Container
    with st.container():
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        
        # CTA Section
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 LAUNCH APPLICATION", use_container_width=True, type="primary", key="launch_btn"):
                st.session_state.current_page = "auth"
                st.rerun()
        
        # Features Grid - 3 cards in one row
        st.markdown("""
        <div class="feature-grid">
            <div class="feature-card" style="background: linear-gradient(180deg, #2c3e50 0%, #3498db 100%);">
                <div class="feature-icon">🤖</div>
                <div class="feature-title">AI-Powered Extraction</div>
                <div class="feature-description">Advanced machine learning for accurate data extraction from invoices</div>
            </div>
            <div class="feature-card" style="background: linear-gradient(180deg, #2c3e50 0%, #3498db 100%);">
                <div class="feature-icon">📊</div>
                <div class="feature-title">Smart Analytics</div>
                <div class="feature-description">Comprehensive insights and reporting for better decision making</div>
            </div>
            <div class="feature-card" style="background: linear-gradient(180deg, #2c3e50 0%, #3498db 100%);">
                <div class="feature-icon">⚡</div>
                <div class="feature-title">Lightning Fast</div>
                <div class="feature-description">Process hundreds of invoices in seconds with our optimized engine</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)


def auth_page():
    """Enhanced authentication page with previous form design"""
    apply_advanced_styling()
    
    with st.container():
        
        # Back button
        if st.button("← Back to Home", key="back_btn"):
            st.session_state.current_page = "landing"
            st.rerun()
        
        # Auth mode selector
        if 'auth_mode' not in st.session_state:
            st.session_state.auth_mode = "signin"
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔐 SIGN IN", use_container_width=True, 
                        type="primary" if st.session_state.auth_mode == "signin" else "secondary"):
                st.session_state.auth_mode = "signin"
                st.rerun()
        with col2:
            if st.button("👤 SIGN UP", use_container_width=True,
                        type="primary" if st.session_state.auth_mode == "signup" else "secondary"):
                st.session_state.auth_mode = "signup"
                st.rerun()
        
        st.markdown("---")
        
        # Sign In Form (Previous Design)
        if st.session_state.auth_mode == "signin":
            st.subheader("🔐 Sign In to Your Account")
            st.caption("Enter your credentials to access the application")
            
            with st.form("signin_form"):
                email = st.text_input("📧 Email Address", placeholder="your@email.com")
                password = st.text_input("🔒 Password", type="password", placeholder="••••••••")
                
                signin_btn = st.form_submit_button("🚀 SIGN IN", use_container_width=True)
                
                if signin_btn:
                    if not email or not password:
                        st.error("❌ Please fill in all fields")
                    else:
                        with st.spinner("🔐 Authenticating..."):
                            time.sleep(1)
                            success, result = verify_user(email, password)
                            if success:
                                st.session_state.user = result
                                st.session_state.current_page = "main_app"
                                st.session_state.authenticated = True
                                st.success(f"✅ Welcome back, {result['name']}!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ {result}")
        
        # Sign Up Form (Previous Design)
        else:
            st.subheader("👤 Create New Account")
            st.caption("Fill in your details to create an account")
            
            with st.form("signup_form"):
                name = st.text_input("👤 Full Name", placeholder="Enter your full name")
                email = st.text_input("📧 Email Address", placeholder="Enter your email")
                aadhaar_number = st.text_input("🆔 Aadhaar Number", placeholder="Enter 12-digit Aadhaar number")
                password = st.text_input("🔒 Password", type="password", placeholder="Create a strong password")
                confirm_password = st.text_input("✅ Confirm Password", type="password", placeholder="Confirm your password")
                user_type = st.selectbox("👨‍💼 User Type", ["CA", "Tax Professional", "Business Owner"])
                
                signup_btn = st.form_submit_button("✨ CREATE ACCOUNT", use_container_width=True)
                
                if signup_btn:
                    if not all([name, email, aadhaar_number, password, confirm_password]):
                        st.error("❌ Please fill in all fields")
                    elif password != confirm_password:
                        st.error("❌ Passwords do not match")
                    elif len(aadhaar_number) != 12 or not aadhaar_number.isdigit():
                        st.error("❌ Aadhaar number must be 12 digits")
                    elif len(password) < 6:
                        st.error("❌ Password must be at least 6 characters")
                    else:
                        with st.spinner("Creating your account..."):
                            time.sleep(1)
                            success, message = create_user(name, email, aadhaar_number, password, user_type)
                            if success:
                                st.success("✅ Account created successfully! Please sign in.")
                                st.session_state.auth_mode = "signin"
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
        
        st.markdown("</div></div>", unsafe_allow_html=True)


# ==================== ENHANCED MAIN APP ====================
def load_app2_functionality():
    """Import and run the main app2.py functionality"""
    try:
        import sys
        import importlib.util
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        app2_path = os.path.join(current_dir, "app2.py")
        
        spec = importlib.util.spec_from_file_location("app2_module", app2_path)
        app2_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app2_module)
        
        return app2_module
    except Exception as e:
        st.error(f"Error loading app functionality: {e}")
        return None

def enhanced_sidebar():
    """Enhanced sidebar with advanced styling"""
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-content">
            <div class="user-card">
                <h3>👤 {name}</h3>
                <p>📧 {email}</p>
                <p>🎯 {role}</p>
                <div class="progress-container">
                    <div class="progress-bar" style="width: 75%;"></div>
                </div>
                <small>Profile Strength: 75%</small>
            </div>
        """.format(
            name=st.session_state.user['name'],
            email=st.session_state.user['email'],
            role=st.session_state.user['user_type']
        ), unsafe_allow_html=True)
        
        # Navigation - Only 3 main options
        st.markdown("<h3 style='color: white;'>🎯 Navigation</h3>", unsafe_allow_html=True)
        
        pages = [
            ("🧾 Multi-Invoice Extraction", "extraction"),
            ("📊 Table View & Analytics", "table"),
            ("🧾 Bill Generation", "bill")
        ]
        
        for page_name, page_key in pages:
            is_active = st.session_state.get('current_nav', 'extraction') == page_key
            active_class = "active" if is_active else ""
            st.markdown(f"""
            <div class="nav-card {active_class}">
                {page_name}
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Sign Out Button
        if st.button("🚪 Sign Out", use_container_width=True, key="signout_btn"):
            for key in list(st.session_state.keys()):
                if key not in ['current_page', 'auth_mode']:
                    del st.session_state[key]
            st.session_state.current_page = "landing"
            st.session_state.authenticated = False
            st.rerun()

def main_app_with_auth():
    """Enhanced main application with advanced styling"""
    apply_advanced_styling()
    
    # Load app2 functionality
    app2 = load_app2_functionality()
    if app2 is None:
        st.error("Failed to load application functionality. Please check if app2.py exists.")
        return
    
    # Set page config
    st.set_page_config(
        page_title="GST Invoice Analyzer Pro",
        layout="wide",
        page_icon="🧾",
        initial_sidebar_state="expanded"
    )
    
    # Enhanced Sidebar
    enhanced_sidebar()
    
    # Main Content Area - CLEAN WITH SIDEBAR GRADIENT HEADER
    with st.container():
        st.markdown("""
        <div class="main-container">
            <div class="sidebar-gradient-header">
                <h1 style="font-size: 2.5rem; margin-bottom: 1rem; color: white;">GST Invoice Analyzer Pro</h1>
                <p style="font-size: 1.2rem; color: rgba(255,255,255,0.9); margin: 0;">Welcome back, <strong>{name}</strong>! Ready to streamline your invoice processing? 🚀</p>
            </div>
        """.format(name=st.session_state.user['name']), unsafe_allow_html=True)
        
        # Navigation - Only 3 main options
        if 'current_nav' not in st.session_state:
            st.session_state.current_nav = "extraction"
        
        nav_col1, nav_col2, nav_col3 = st.columns(3)
        with nav_col1:
            if st.button("🧾 Extraction", use_container_width=True, 
                        type="primary" if st.session_state.current_nav == "extraction" else "secondary"):
                st.session_state.current_nav = "extraction"
                st.rerun()
        with nav_col2:
            if st.button("📊 Table View", use_container_width=True,
                        type="primary" if st.session_state.current_nav == "table" else "secondary"):
                st.session_state.current_nav = "table"
                st.rerun()
        with nav_col3:
            if st.button("🧾 Bill Generation", use_container_width=True,
                        type="primary" if st.session_state.current_nav == "bill" else "secondary"):
                st.session_state.current_nav = "bill"
                st.rerun()
        
        st.markdown("---")
        
        # Page content
        if st.session_state.current_nav == "extraction":
            app2.multi_invoice_extraction_page()
        elif st.session_state.current_nav == "table":
            app2.table_view_page()
        elif st.session_state.current_nav == "bill":
            app2.bill_generation_page()
        
        st.markdown("</div>", unsafe_allow_html=True)

# ==================== MAIN APPLICATION FLOW ====================
def main():
    """Main application flow with enhanced styling"""
    
    # Initialize session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "landing"
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    # Apply global styling
    apply_advanced_styling()
    
    # Page routing
    if st.session_state.current_page == "landing":
        landing_page()
    elif st.session_state.current_page == "auth":
        auth_page()
    elif st.session_state.current_page == "main_app" and st.session_state.authenticated:
        main_app_with_auth()

if __name__ == "__main__":
    main()
# [file content end]

