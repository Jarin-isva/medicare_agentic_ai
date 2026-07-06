# MediGuide - Professional Healthcare Triage System
# Enhanced Interactive UI - Dark Mode - Production Grade
# streamlit_app.py

import os
import sys
import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any
import random
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from agents.agent_orchestrator import AgentOrchestrator
except ImportError as e:
    logger.error(f"Failed to import AgentOrchestrator: {e}")
    AgentOrchestrator = None

# ============================================
# PAGE CONFIGURATION & THEMING
# ============================================

st.set_page_config(
    page_title="MediGuide - Healthcare Triage AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/mediguide",
        "Report a bug": "https://github.com/mediguide/issues",
        "About": "MediGuide v2.0 - AI Healthcare Triage System"
    }
)

# ============================================
# DARK MODE CUSTOM CSS
# ============================================

dark_mode_css = """
<style>
    :root {
        --primary: #00D4FF;
        --primary-dark: #0098CC;
        --secondary: #FF6B6B;
        --success: #00D97E;
        --warning: #FFB800;
        --danger: #FF4757;
        --bg-dark: #0F1419;
        --bg-secondary: #1A1F26;
        --text-primary: #E4E6EB;
        --text-secondary: #A0A6B1;
        --border: #2D3139;
    }
    
    * {
        color-scheme: dark;
    }
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: var(--bg-dark) !important;
        color: var(--text-primary) !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: var(--bg-secondary) !important;
        border-right: 1px solid var(--border) !important;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        border-bottom: 2px solid var(--border);
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 0.75rem 1.5rem;
        border-radius: 8px 8px 0 0;
        background-color: var(--bg-secondary);
        border: 1px solid var(--border);
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--primary) !important;
        color: var(--bg-dark) !important;
    }
    
    .header-title {
        color: var(--primary);
        font-weight: 900;
        font-size: 2.5rem;
        margin-bottom: 1.5rem;
        text-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
        letter-spacing: 1px;
    }
    
    .subheader-title {
        color: var(--primary);
        font-weight: bold;
        font-size: 1.4rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-left: 4px solid var(--primary);
        padding-left: 1rem;
    }
    
    .emergency-banner {
        background: linear-gradient(135deg, #FF4757 0%, #FF6B7A 100%);
        border-left: 5px solid var(--danger);
        padding: 1.5rem;
        border-radius: 8px;
        color: white;
        font-weight: bold;
        font-size: 1.1rem;
        box-shadow: 0 4px 15px rgba(255, 71, 87, 0.3);
        margin: 1rem 0;
    }
    
    .urgent-banner {
        background: linear-gradient(135deg, #FFB800 0%, #FFC533 100%);
        border-left: 5px solid var(--warning);
        padding: 1.5rem;
        border-radius: 8px;
        color: #0F1419;
        font-weight: bold;
        font-size: 1.1rem;
        box-shadow: 0 4px 15px rgba(255, 184, 0, 0.3);
        margin: 1rem 0;
    }
    
    .routine-banner {
        background: linear-gradient(135deg, #00D97E 0%, #00F09B 100%);
        border-left: 5px solid var(--success);
        padding: 1.5rem;
        border-radius: 8px;
        color: #0F1419;
        font-weight: bold;
        font-size: 1.1rem;
        box-shadow: 0 4px 15px rgba(0, 217, 126, 0.3);
        margin: 1rem 0;
    }
    
    .metric-card {
        background-color: var(--bg-secondary);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid var(--border);
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0, 212, 255, 0.1);
    }
    
    .metric-card:hover {
        border-color: var(--primary);
        box-shadow: 0 6px 20px rgba(0, 212, 255, 0.2);
        transform: translateY(-2px);
    }
    
    .info-box {
        background-color: var(--bg-secondary);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid var(--primary);
        margin: 1rem 0;
    }
    
    .step-box {
        background: linear-gradient(135deg, var(--bg-secondary) 0%, rgba(0, 212, 255, 0.05) 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid var(--border);
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .step-box:hover {
        border-color: var(--primary);
        box-shadow: 0 6px 20px rgba(0, 212, 255, 0.15);
    }
    
    .stat-number {
        color: var(--primary);
        font-size: 2.5rem;
        font-weight: 900;
        margin: 0.5rem 0;
    }
    
    .stat-label {
        color: var(--text-secondary);
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .button-primary {
        background: linear-gradient(135deg, var(--primary) 0%, #00A8CC 100%);
        color: var(--bg-dark);
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 8px;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .button-primary:hover {
        box-shadow: 0 6px 20px rgba(0, 212, 255, 0.4);
        transform: translateY(-2px);
    }
    
    .diagnostic-box {
        background-color: var(--bg-secondary);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid var(--border);
        margin: 1rem 0;
        border-left: 4px solid var(--primary);
    }
    
    .progress-bar {
        background-color: var(--border);
        height: 8px;
        border-radius: 4px;
        overflow: hidden;
        margin: 1rem 0;
    }
    
    .progress-fill {
        background: linear-gradient(90deg, var(--primary) 0%, var(--secondary) 100%);
        height: 100%;
        border-radius: 4px;
        transition: width 0.3s ease;
    }
    
    input, textarea, select {
        background-color: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
    }
    
    input:focus, textarea:focus, select:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 10px rgba(0, 212, 255, 0.2) !important;
    }
    
    .stExpander {
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        background-color: var(--bg-secondary) !important;
    }
    
    .stExpander [data-testid="stExpanderDetails"] {
        background-color: rgba(0, 212, 255, 0.05) !important;
    }
    
    .stAlert {
        border-radius: 8px !important;
        margin: 1rem 0 !important;
    }
    
    .stDataFrame {
        background-color: var(--bg-secondary) !important;
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--border);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--primary);
    }
    
    /* Animation */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
    
    /* Loading animation */
    @keyframes shimmer {
        0% { background-position: -1000px 0; }
        100% { background-position: 1000px 0; }
    }
</style>
"""

st.markdown(dark_mode_css, unsafe_allow_html=True)

# ============================================
# SESSION STATE INITIALIZATION
# ============================================

def initialize_session_state():
    """Initialize all session state variables"""
    
    defaults = {
        "orchestrator": None,
        "workflow_stage": "IDLE",
        "intake_complete": False,
        "analysis_complete": False,
        "triage_complete": False,
        "coordination_complete": False,
        "patient_data": {},
        "analysis_results": {},
        "triage_results": {},
        "coordination_results": {},
        "case_history": [],
        "error_message": None,
        "success_message": None,
        "current_page": "home",
        "show_referral_letter": False,
        "intake_step": 1,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()

# ============================================
# UTILITY FUNCTIONS
# ============================================

def init_orchestrator():
    """Initialize agent orchestrator with error handling"""
    try:
        if st.session_state.orchestrator is None:
            with st.spinner("🔧 Initializing AI agents..."):
                st.session_state.orchestrator = AgentOrchestrator()
            logger.info("✅ Agent Orchestrator initialized")
        return True
    except ValueError as e:
        st.session_state.error_message = f"❌ Configuration Error: {str(e)}"
        logger.error(f"Failed to initialize orchestrator: {str(e)}")
        return False
    except Exception as e:
        st.session_state.error_message = f"❌ Unexpected Error: {str(e)}"
        logger.error(f"Unexpected error: {str(e)}")
        return False

def reset_workflow():
    """Reset workflow for new patient"""
    st.session_state.workflow_stage = "IDLE"
    st.session_state.intake_complete = False
    st.session_state.analysis_complete = False
    st.session_state.triage_complete = False
    st.session_state.coordination_complete = False
    st.session_state.patient_data = {}
    st.session_state.analysis_results = {}
    st.session_state.triage_results = {}
    st.session_state.coordination_results = {}
    st.session_state.error_message = None
    st.session_state.success_message = None
    st.session_state.intake_step = 1
    logger.info("🔄 Workflow reset for new patient")

def save_case(case_data: Dict[str, Any]):
    """Save case to history"""
    case_entry = {
        "case_id": f"CASE-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "timestamp": datetime.now().isoformat(),
        "patient_data": st.session_state.patient_data,
        "results": {
            "analysis": st.session_state.analysis_results,
            "triage": st.session_state.triage_results,
            "coordination": st.session_state.coordination_results
        }
    }
    
    st.session_state.case_history.append(case_entry)
    logger.info(f"✅ Case saved: {case_entry['case_id']}")
    return case_entry

def create_gauge_chart(value: float, title: str, max_val: float = 1.0):
    """Create interactive gauge chart"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value * max_val if max_val != 1.0 else value,
        title={'text': title},
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [0, max_val]},
            'bar': {'color': "#00D4FF"},
            'steps': [
                {'range': [0, max_val * 0.33], 'color': "rgba(0, 217, 126, 0.2)"},
                {'range': [max_val * 0.33, max_val * 0.66], 'color': "rgba(255, 184, 0, 0.2)"},
                {'range': [max_val * 0.66, max_val], 'color': "rgba(255, 71, 87, 0.2)"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': max_val * 0.9
            }
        }
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E4E6EB"),
        height=300
    )
    return fig

def create_diagnosis_chart(diagnoses):
    """Create diagnosis probability chart"""
    if not diagnoses:
        return None
    
    top_diagnoses = diagnoses[:5]
    diseases = [d.get('disease', 'Unknown') for d in top_diagnoses]
    probs = [d.get('probability', 0) * 100 for d in top_diagnoses]
    
    fig = go.Figure(data=[
        go.Bar(
            y=diseases,
            x=probs,
            orientation='h',
            marker=dict(
                color=probs,
                colorscale='Viridis',
                showscale=True
            ),
            text=[f"{p:.1f}%" for p in probs],
            textposition='auto'
        )
    ])
    
    fig.update_layout(
        title="Differential Diagnosis - Probability Distribution",
        xaxis_title="Probability (%)",
        yaxis_title="Disease",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E4E6EB"),
        height=400,
        showlegend=False
    )
    return fig

# ============================================
# PAGE: HOME
# ============================================

def page_home():
    """Home page with system overview"""
    
    st.markdown('<h1 class="header-title">🏥 MediGuide AI Healthcare Triage</h1>', 
                unsafe_allow_html=True)
    
    # Welcome section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class="step-box">
        <h2 style="color: #00D4FF; margin-top: 0;">Welcome to MediGuide</h2>
        <p style="font-size: 1.1rem; line-height: 1.8;">
        MediGuide is an advanced AI-powered healthcare triage system designed to provide 
        rapid, accurate clinical assessment and hospital referral recommendations. 
        Our multi-agent system analyzes patient symptoms, assesses emergency risk, and 
        coordinates appropriate care pathways.
        </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="info-box">
        <h3 style="color: #00D4FF; margin-top: 0;">System Stats</h3>
        <div class="stat-number">""" + str(len(st.session_state.case_history)) + """</div>
        <div class="stat-label">Cases Processed</div>
        <hr style="border-color: var(--border);">
        <div class="stat-number">""" + str(sum(1 for case in st.session_state.case_history 
                         if case.get("results", {}).get("triage", {}).get("urgency_level") == "EMERGENCY")) + """</div>
        <div class="stat-label">Emergency Cases</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Key features
    st.markdown('<h2 class="subheader-title">✨ Key Features</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
        <h3 style="color: #00D4FF;">🤖 Multi-Agent AI</h3>
        <p>4 specialized agents working together for comprehensive assessment</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
        <h3 style="color: #00D4FF;">⚡ Real-Time Analysis</h3>
        <p>Instant symptom analysis and emergency risk assessment</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
        <h3 style="color: #00D4FF;">🏥 Hospital Integration</h3>
        <p>32+ hospital network with real-time referral coordination</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Technology stack
    st.markdown('<h2 class="subheader-title">🛠️ Technology Stack</h2>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
        <h4>🧠 AI Engine</h4>
        <p>DeepSeek API<br>(Fast & Free)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
        <h4>📊 Knowledge Base</h4>
        <p>Medical KB MCP<br>(20 Diseases)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
        <h4>🚨 Emergency</h4>
        <p>Detector MCP<br>(Red Flag Detection)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
        <h4>🏥 Care Network</h4>
        <p>Hospital Registry<br>(Referral System)</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Analytics
    if st.session_state.case_history:
        st.markdown('<h2 class="subheader-title">📊 Analytics Dashboard</h2>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        total = len(st.session_state.case_history)
        emergencies = sum(1 for c in st.session_state.case_history 
                         if c.get("results", {}).get("triage", {}).get("urgency_level") == "EMERGENCY")
        urgent = sum(1 for c in st.session_state.case_history 
                    if c.get("results", {}).get("triage", {}).get("urgency_level") == "URGENT")
        
        with col1:
            st.metric("Total Cases", total, delta=None)
        
        with col2:
            st.metric("🚨 Emergency", emergencies, delta=f"{(emergencies/max(total,1))*100:.1f}%")
        
        with col3:
            st.metric("⚠️ Urgent", urgent, delta=f"{(urgent/max(total,1))*100:.1f}%")
        
        # Urgency distribution chart
        urgency_dist = {
            "EMERGENCY": emergencies,
            "URGENT": urgent,
            "ROUTINE": total - emergencies - urgent
        }
        
        fig = go.Figure(data=[
            go.Pie(
                labels=list(urgency_dist.keys()),
                values=list(urgency_dist.values()),
                marker=dict(colors=["#FF4757", "#FFB800", "#00D97E"])
            )
        ])
        
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E4E6EB"),
            height=350
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Call to action
    st.markdown('<h2 class="subheader-title">🚀 Get Started</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("▶️ Start New Patient Assessment", key="home_start", use_container_width=True):
            reset_workflow()
            st.session_state.workflow_stage = "INTAKE"
            st.session_state.current_page = "intake"
            st.success("✅ New patient session started!")
            st.balloons()
            st.rerun()

# ============================================
# PAGE: PATIENT INTAKE
# ============================================

def page_patient_intake():
    """Patient intake form page"""
    
    st.markdown('<h1 class="header-title">📋 Patient Intake & Information</h1>', 
                unsafe_allow_html=True)
    
    if st.session_state.workflow_stage == "IDLE":
        st.warning("⚠️ No active patient session. Start a new assessment from the Home page.")
        if st.button("Go to Home", key="go_home_1"):
            st.session_state.current_page = "home"
            st.rerun()
        return
    
    # Progress indicator
    st.markdown("""
    <div class="progress-bar">
        <div class="progress-fill" style="width: 25%;"></div>
    </div>
    <p style="text-align: center; color: #A0A6B1; font-size: 0.9rem;">Step 1 of 4: Patient Information Collection</p>
    """, unsafe_allow_html=True)
    
    st.markdown('<h2 class="subheader-title">👤 Demographic Information</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        age = st.number_input(
            "Age (years)",
            min_value=1, max_value=120,
            value=st.session_state.patient_data.get("age", 30),
            step=1
        )
    
    with col2:
        gender = st.selectbox(
            "Gender",
            ["M", "F", "Other"],
            index=["M", "F", "Other"].index(st.session_state.patient_data.get("gender", "M"))
        )
    
    with col3:
        location = st.selectbox(
            "Location",
            ["Chittagong", "Dhaka", "Sylhet", "Rajshahi", "Other"],
            index=0
        )
    
    st.markdown('<h2 class="subheader-title">🏥 Chief Complaint & Symptoms</h2>', unsafe_allow_html=True)
    
    chief_complaint = st.text_input(
        "Chief Complaint (main health concern)",
        value=st.session_state.patient_data.get("chief_complaint", ""),
        placeholder="e.g., Severe headache with fever, Chest pain, Difficulty breathing"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        symptom_duration = st.text_input(
            "Symptom Duration",
            value=st.session_state.patient_data.get("symptom_duration", ""),
            placeholder="e.g., 3 days, 2 weeks, Since morning"
        )
    
    with col2:
        symptom_severity = st.slider(
            "Symptom Severity",
            min_value=1, max_value=10,
            value=st.session_state.patient_data.get("symptom_severity", 5),
            format="%d"
        )
        
        if symptom_severity <= 3:
            severity_text = "🟢 Mild"
        elif symptom_severity <= 6:
            severity_text = "🟡 Moderate"
        else:
            severity_text = "🔴 Severe"
        
        st.caption(f"Current: {severity_text}")
    
    st.markdown('<h2 class="subheader-title">⚕️ Medical History</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        allergies_input = st.text_area(
            "Known Allergies (comma-separated)",
            value=", ".join(st.session_state.patient_data.get("allergies", [])),
            placeholder="e.g., Penicillin, Aspirin, Shellfish",
            height=100
        )
    
    with col2:
        medications_input = st.text_area(
            "Current Medications (comma-separated)",
            value=", ".join(st.session_state.patient_data.get("current_medications", [])),
            placeholder="e.g., Aspirin 500mg, Metformin 1000mg",
            height=100
        )
    
    medical_history_input = st.text_area(
        "Past Medical Conditions (comma-separated)",
        value=", ".join(st.session_state.patient_data.get("medical_history", [])),
        placeholder="e.g., Hypertension, Diabetes, Asthma, Heart Disease",
        height=80
    )
    
    st.markdown('<h2 class="subheader-title">👥 Additional Information</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        vital_signs_text = st.text_area(
            "Vital Signs (if available)",
            placeholder="BP: 120/80, HR: 75, Temp: 98.6°F, O2: 98%",
            height=80
        )
    
    with col2:
        additional_notes = st.text_area(
            "Additional Notes",
            placeholder="Any other relevant medical information...",
            height=80
        )
    
    # Submit button
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("✅ Submit & Proceed to Analysis", key="submit_intake", use_container_width=True):
            # Validate input
            if not chief_complaint or not age:
                st.error("❌ Please fill in Chief Complaint and Age")
                return
            
            # Update patient data
            st.session_state.patient_data = {
                "age": age,
                "gender": gender,
                "location": location,
                "chief_complaint": chief_complaint,
                "symptom_duration": symptom_duration,
                "symptom_severity": symptom_severity,
                "allergies": [a.strip() for a in allergies_input.split(",") if a.strip()],
                "current_medications": [m.strip() for m in medications_input.split(",") if m.strip()],
                "medical_history": [h.strip() for h in medical_history_input.split(",") if h.strip()],
                "vital_signs": vital_signs_text,
                "additional_notes": additional_notes
            }
            
            st.session_state.intake_complete = True
            st.session_state.workflow_stage = "ANALYSIS"
            st.success("✅ Intake complete. Analyzing symptoms...")
            st.balloons()
            st.rerun()
    
    # Summary section
    if st.session_state.patient_data:
        with st.expander("📝 Current Summary", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                <div class="diagnostic-box">
                <h4>Patient Demographics</h4>
                """ + f"<p><strong>Age:</strong> {st.session_state.patient_data.get('age')} years<br>" + 
                f"<strong>Gender:</strong> {st.session_state.patient_data.get('gender')}<br>" + 
                f"<strong>Location:</strong> {st.session_state.patient_data.get('location')}</p>" +
                """</div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                <div class="diagnostic-box">
                <h4>Chief Complaint</h4>
                """ + f"<p>{st.session_state.patient_data.get('chief_complaint')}</p>" +
                f"<p><strong>Duration:</strong> {st.session_state.patient_data.get('symptom_duration')}</p>" +
                f"<p><strong>Severity:</strong> {st.session_state.patient_data.get('symptom_severity')}/10</p>" +
                """</div>
                """, unsafe_allow_html=True)

# ============================================
# PAGE: SYMPTOM ANALYSIS
# ============================================

def page_symptom_analysis():
    """Symptom analysis and differential diagnosis page"""
    
    st.markdown('<h1 class="header-title">🔬 Symptom Analysis & Diagnosis</h1>', 
                unsafe_allow_html=True)
    
    if not st.session_state.intake_complete:
        st.warning("⚠️ Please complete patient intake first.")
        if st.button("Go to Intake", key="go_intake"):
            st.session_state.current_page = "intake"
            st.rerun()
        return
    
    st.markdown("""
    <div class="progress-bar">
        <div class="progress-fill" style="width: 50%;"></div>
    </div>
    <p style="text-align: center; color: #A0A6B1; font-size: 0.9rem;">Step 2 of 4: Symptom Analysis & Differential Diagnosis</p>
    """, unsafe_allow_html=True)
    
    if not init_orchestrator():
        st.error(st.session_state.error_message)
        return
    
    # Run analysis if not done
    if not st.session_state.analysis_complete:
        st.info("📊 Analyzing symptoms against medical knowledge base...")
        
        try:
            with st.spinner("🔍 Processing medical data..."):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    st.session_state.orchestrator.analysis_agent.process(
                        st.session_state.patient_data
                    )
                )
            
            st.session_state.analysis_results = result
            st.session_state.analysis_complete = True
            st.success("✅ Analysis complete!")
            st.rerun()
        
        except Exception as e:
            st.error(f"❌ Analysis Error: {str(e)}")
            logger.error(f"Analysis error: {str(e)}")
            return
    
    # Display analysis results
    st.markdown('<h2 class="subheader-title">📋 Differential Diagnosis</h2>', unsafe_allow_html=True)
    
    diagnoses = st.session_state.analysis_results.get("differential_diagnosis", [])
    
    if diagnoses:
        # Chart view
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = create_diagnosis_chart(diagnoses)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("""
            <div class="info-box">
            <h3 style="color: #00D4FF; margin-top: 0;">Analysis Stats</h3>
            """ + f"<p><strong>Diseases Found:</strong> {len(diagnoses)}</p>" +
            f"<p><strong>Top Match:</strong> {diagnoses[0].get('disease', 'Unknown')}</p>" +
            f"<p><strong>Probability:</strong> {diagnoses[0].get('probability', 0):.0%}</p>" +
            f"<p><strong>Confidence:</strong> {diagnoses[0].get('confidence', 0):.0%}</p>" +
            """</div>
            """, unsafe_allow_html=True)
        
        # Detailed diagnosis cards
        st.markdown('<h2 class="subheader-title">🎯 Detailed Diagnosis</h2>', unsafe_allow_html=True)
        
        for idx, dx in enumerate(diagnoses[:5], 1):
            with st.expander(f"#{idx} {dx.get('disease', 'Unknown')} - {dx.get('probability', 0):.0%} Match"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Probability", f"{dx.get('probability', 0):.0%}")
                
                with col2:
                    st.metric("Confidence", f"{dx.get('confidence', 0):.0%}")
                
                with col3:
                    st.metric("Severity", dx.get('severity', 'N/A'))
                
                st.markdown(f"""
                <div class="diagnostic-box">
                <h4>Clinical Reasoning</h4>
                <p>{dx.get('reasoning', 'No reasoning available')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                supporting = dx.get('supporting_features', [])
                if supporting:
                    st.markdown("""<p style="color: #00D4FF; font-weight: bold;">✓ Supporting Features</p>""", unsafe_allow_html=True)
                    for feature in supporting:
                        st.write(f"• {feature}")
                
                tests = dx.get('distinguishing_tests', [])
                if tests:
                    st.markdown("""<p style="color: #00D4FF; font-weight: bold;">🧪 Recommended Tests</p>""", unsafe_allow_html=True)
                    for test in tests:
                        st.write(f"• {test}")
    else:
        st.warning("⚠️ No diagnoses found. Please try again.")
    
    # Clinical reasoning
    st.markdown('<h2 class="subheader-title">💡 Clinical Reasoning</h2>', unsafe_allow_html=True)
    
    reasoning_text = st.session_state.analysis_results.get("clinical_reasoning", "No reasoning available")
    st.info(reasoning_text)
    
    # Recommended tests
    tests = st.session_state.analysis_results.get("recommended_tests", [])
    if tests:
        st.markdown('<h2 class="subheader-title">🧪 Recommended Investigations</h2>', unsafe_allow_html=True)
        
        for test in tests:
            st.markdown(f"<div class='step-box'>✓ {test}</div>", unsafe_allow_html=True)
    
    # Navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("➡️ Proceed to Emergency Triage", key="proceed_triage", use_container_width=True):
            st.session_state.workflow_stage = "TRIAGE"
            st.session_state.current_page = "triage"
            st.rerun()

# ============================================
# PAGE: EMERGENCY TRIAGE
# ============================================

def page_emergency_triage():
    """Emergency triage assessment page"""
    
    st.markdown('<h1 class="header-title">🚨 Emergency Triage & Risk Assessment</h1>', 
                unsafe_allow_html=True)
    
    if not st.session_state.analysis_complete:
        st.warning("⚠️ Please complete symptom analysis first.")
        if st.button("Go to Analysis", key="go_analysis"):
            st.session_state.current_page = "analysis"
            st.rerun()
        return
    
    st.markdown("""
    <div class="progress-bar">
        <div class="progress-fill" style="width: 75%;"></div>
    </div>
    <p style="text-align: center; color: #A0A6B1; font-size: 0.9rem;">Step 3 of 4: Emergency Risk Assessment</p>
    """, unsafe_allow_html=True)
    
    if not init_orchestrator():
        st.error(st.session_state.error_message)
        return
    
    # Run triage if not done
    if not st.session_state.triage_complete:
        st.info("🔍 Assessing emergency risk...")
        
        try:
            with st.spinner("⚠️ Analyzing for life-threatening conditions..."):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    st.session_state.orchestrator.triage_agent.process(
                        st.session_state.patient_data
                    )
                )
            
            st.session_state.triage_results = result
            st.session_state.triage_complete = True
            st.rerun()
        
        except Exception as e:
            st.error(f"❌ Triage Error: {str(e)}")
            logger.error(f"Triage error: {str(e)}")
            return
    
    # Display triage results
    urgency = st.session_state.triage_results.get("urgency_level", "ROUTINE")
    risk_score = st.session_state.triage_results.get("risk_score", 0)
    confidence = st.session_state.triage_results.get("confidence", 0)
    
    # Urgency banner
    banner_class = f"{urgency.lower()}-banner"
    st.markdown(f"""
    <div class="{banner_class}">
        <h2>⚠️ URGENCY LEVEL: {urgency}</h2>
        <p>Risk Score: {risk_score:.2f}/1.00 | Confidence: {confidence:.0%}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Metrics and gauge
    col1, col2 = st.columns([1, 1])
    
    with col1:
        col_metrics1, col_metrics2, col_metrics3 = st.columns(3)
        
        with col_metrics1:
            st.metric("Risk Score", f"{risk_score:.2f}/1.00", delta=f"{risk_score*100:.1f}%")
        
        with col_metrics2:
            st.metric("Confidence", f"{confidence:.0%}")
        
        with col_metrics3:
            urgency_text = {"EMERGENCY": "🚨 IMMEDIATE", "URGENT": "⚠️ SAME-DAY", "ROUTINE": "📅 SCHEDULED"}
            st.metric("Action", urgency_text.get(urgency, "UNKNOWN"))
    
    with col2:
        fig = create_gauge_chart(risk_score, "Risk Assessment Score", 1.0)
        st.plotly_chart(fig, use_container_width=True)
    
    # Contributing factors
    st.markdown('<h2 class="subheader-title">📊 Contributing Risk Factors</h2>', unsafe_allow_html=True)
    
    factors = st.session_state.triage_results.get("contributing_factors", {})
    
    if factors:
        col1, col2, col3, col4 = st.columns(4)
        
        risk_factors = {
            "age_risk": ("Age Risk", "👤"),
            "symptom_severity_risk": ("Symptom Severity", "🏥"),
            "medical_history_risk": ("Medical History", "📋"),
            "vital_sign_risk": ("Vital Signs", "💓")
        }
        
        columns = [col1, col2, col3, col4]
        
        for (key, (label, icon)), col in zip(risk_factors.items(), columns):
            with col:
                value = factors.get(key, 0)
                st.markdown(f"""
                <div class="metric-card">
                <p style="font-size: 2rem;">{icon}</p>
                <h3 style="color: #00D4FF; margin: 0.5rem 0;">{value:.2f}</h3>
                <p style="color: #A0A6B1; font-size: 0.9rem; margin: 0;">{label}</p>
                </div>
                """, unsafe_allow_html=True)
    
    # Recommendation
    st.markdown('<h2 class="subheaker-title">💊 Clinical Recommendation</h2>', unsafe_allow_html=True)
    
    recommendation = st.session_state.triage_results.get("recommendation", "N/A")
    
    if urgency == "EMERGENCY":
        st.markdown(f"""<div class="emergency-banner">{recommendation}</div>""", unsafe_allow_html=True)
    elif urgency == "URGENT":
        st.markdown(f"""<div class="urgent-banner">{recommendation}</div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""<div class="routine-banner">{recommendation}</div>""", unsafe_allow_html=True)
    
    # Red flags if any
    red_flags = st.session_state.triage_results.get("red_flags_detected", [])
    if red_flags:
        st.markdown('<h2 class="subheader-title">⚠️ Red Flags Detected</h2>', unsafe_allow_html=True)
        
        for flag in red_flags:
            st.markdown(f"""<div class="emergency-banner">🚩 {flag}</div>""", unsafe_allow_html=True)
    
    # Navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("➡️ Generate Care Plan & Referrals", key="proceed_coordination", use_container_width=True):
            st.session_state.workflow_stage = "COORDINATION"
            st.session_state.current_page = "coordination"
            st.rerun()

# ============================================
# PAGE: CARE COORDINATION
# ============================================

def page_care_coordination():
    """Care coordination and referral page"""
    
    st.markdown('<h1 class="header-title">🏥 Care Plan & Hospital Referral</h1>', 
                unsafe_allow_html=True)
    
    if not st.session_state.triage_complete:
        st.warning("⚠️ Please complete emergency triage first.")
        if st.button("Go to Triage", key="go_triage"):
            st.session_state.current_page = "triage"
            st.rerun()
        return
    
    st.markdown("""
    <div class="progress-bar">
        <div class="progress-fill" style="width: 100%;"></div>
    </div>
    <p style="text-align: center; color: #A0A6B1; font-size: 0.9rem;">Step 4 of 4: Care Coordination & Referral</p>
    """, unsafe_allow_html=True)
    
    if not init_orchestrator():
        st.error(st.session_state.error_message)
        return
    
    # Run coordination if not done
    if not st.session_state.coordination_complete:
        st.info("🔍 Generating care plan and finding hospitals...")
        
        try:
            with st.spinner("🏥 Coordinating care with hospital network..."):
                diagnosis = st.session_state.orchestrator.analysis_agent.get_top_diagnosis()
                diagnosis_name = diagnosis.get("disease", "Unknown Condition")
                urgency_level = st.session_state.triage_results.get("urgency_level", "ROUTINE")
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    st.session_state.orchestrator.coordinator_agent.process(
                        st.session_state.patient_data,
                        diagnosis_name,
                        urgency_level
                    )
                )
            
            st.session_state.coordination_results = result
            st.session_state.coordination_complete = True
            st.rerun()
        
        except Exception as e:
            st.error(f"❌ Care Coordination Error: {str(e)}")
            logger.error(f"Coordination error: {str(e)}")
            return
    
    # Display care plan
    st.markdown('<h2 class="subheader-title">📋 Recommended Care Plan</h2>', unsafe_allow_html=True)
    
    care_plan = st.session_state.coordination_results.get("care_plan", {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="step-box" style="border-left: 4px solid #00D97E;">
        <h4 style="color: #00D97E; margin-top: 0;">✅ Immediate Action</h4>
        <p>{care_plan.get('immediate_action', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="step-box" style="border-left: 4px solid #00D4FF;">
        <h4 style="color: #00D4FF; margin-top: 0;">📅 Follow-up Schedule</h4>
        <p>{care_plan.get('follow_up_schedule', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Patient instructions
    st.markdown('<h2 class="subheader-title">📝 Patient Instructions</h2>', unsafe_allow_html=True)
    
    for i, instruction in enumerate(care_plan.get('patient_instructions', []), 1):
        st.markdown(f"""
        <div class="step-box">
        <h4 style="color: #00D4FF; margin-top: 0;">Step {i}</h4>
        <p>{instruction}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Primary referral
    st.markdown('<h2 class="subheader-title">🏥 Primary Hospital Referral</h2>', unsafe_allow_html=True)
    
    referral = st.session_state.coordination_results.get("primary_referral", {})
    
    if referral and referral.get("status") != "no_hospital":
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"""
            <div class="diagnostic-box">
            <h3 style="color: #00D4FF; margin-top: 0;">📍 {referral.get('hospital_name', 'N/A')}</h3>
            <p><strong>Address:</strong> {referral.get('address', 'N/A')}</p>
            <p><strong>📞 Phone:</strong> {referral.get('phone', 'N/A')}</p>
            <p><strong>🎫 Tracking ID:</strong> {referral.get('tracking_id', 'N/A')}</p>
            <p><strong>Status:</strong> {"🚨 URGENT ADMISSION" if referral.get('urgent') else "✅ ROUTINE ADMISSION"}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if st.button("📄 View Referral Letter", key="view_letter", use_container_width=True):
                st.session_state.show_referral_letter = not st.session_state.show_referral_letter
        
        if st.session_state.show_referral_letter:
            with st.expander("📋 Official Referral Letter", expanded=True):
                letter = referral.get('referral_letter', 'No letter available')
                st.text(letter)
    else:
        st.warning("⚠️ No suitable hospital found")
    
    # Alternative hospitals
    alternatives = st.session_state.coordination_results.get("alternative_hospitals", [])
    
    if alternatives:
        st.markdown('<h2 class="subheader-title">🏥 Alternative Hospitals</h2>', unsafe_allow_html=True)
        
        for idx, hospital in enumerate(alternatives[:3], 1):
            with st.expander(f"Option #{idx}: {hospital.get('name', 'Unknown')} ({hospital.get('rating', 'N/A')}/5)"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                    <p><strong>📍 Address:</strong> {hospital.get('address', 'N/A')}<br>
                    <strong>📞 Phone:</strong> {hospital.get('phone', 'N/A')}</p>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <p><strong>⭐ Rating:</strong> {hospital.get('rating', 'N/A')}/5<br>
                    <strong>🛏️ Available Beds:</strong> {hospital.get('available_beds', 'N/A')}</p>
                    """, unsafe_allow_html=True)
    
    # Diagnosis summary
    st.markdown('<h2 class="subheader-title">📊 Assessment Summary</h2>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        diagnosis = st.session_state.orchestrator.analysis_agent.get_top_diagnosis()
        st.metric("Primary Diagnosis", diagnosis.get("disease", "Unknown")[:20])
    
    with col2:
        st.metric("Urgency", st.session_state.triage_results.get("urgency_level"))
    
    with col3:
        st.metric("Risk Score", f"{st.session_state.triage_results.get('risk_score', 0):.2f}")
    
    with col4:
        st.metric("Confidence", f"{st.session_state.triage_results.get('confidence', 0):.0%}")
    
    # Save case
    st.markdown('<h2 class="subheader-title">💾 Case Management</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("💾 Save Case", key="save_case", use_container_width=True):
            case = save_case(st.session_state)
            st.success(f"✅ Case saved: {case['case_id']}")
            st.balloons()
    
    with col2:
        if st.button("🔄 Start New Patient", key="new_patient", use_container_width=True):
            reset_workflow()
            st.session_state.workflow_stage = "IDLE"
            st.session_state.current_page = "home"
            st.rerun()
    
    with col3:
        if st.button("📚 View History", key="view_history", use_container_width=True):
            st.session_state.current_page = "history"
            st.rerun()

# ============================================
# PAGE: CASE HISTORY
# ============================================

def page_case_history():
    """Case history and analytics page"""
    
    st.markdown('<h1 class="header-title">📚 Case History & Analytics</h1>', 
                unsafe_allow_html=True)
    
    if not st.session_state.case_history:
        st.info("ℹ️ No cases yet. Complete a patient assessment to build history.")
        if st.button("Start Assessment", key="start_from_history"):
            st.session_state.current_page = "home"
            st.rerun()
        return
    
    # Summary statistics
    st.markdown('<h2 class="subheader-title">📊 Summary Statistics</h2>', unsafe_allow_html=True)
    
    total_cases = len(st.session_state.case_history)
    emergency_cases = sum(1 for case in st.session_state.case_history 
                         if case.get("results", {}).get("triage", {}).get("urgency_level") == "EMERGENCY")
    urgent_cases = sum(1 for case in st.session_state.case_history 
                      if case.get("results", {}).get("triage", {}).get("urgency_level") == "URGENT")
    routine_cases = total_cases - emergency_cases - urgent_cases
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Cases", total_cases)
    
    with col2:
        st.metric("🚨 Emergency", emergency_cases, delta=f"{(emergency_cases/max(total_cases,1))*100:.1f}%")
    
    with col3:
        st.metric("⚠️ Urgent", urgent_cases, delta=f"{(urgent_cases/max(total_cases,1))*100:.1f}%")
    
    with col4:
        st.metric("📅 Routine", routine_cases, delta=f"{(routine_cases/max(total_cases,1))*100:.1f}%")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Urgency distribution pie chart
        urgency_dist = {
            "EMERGENCY": emergency_cases,
            "URGENT": urgent_cases,
            "ROUTINE": routine_cases
        }
        
        fig = go.Figure(data=[
            go.Pie(
                labels=list(urgency_dist.keys()),
                values=list(urgency_dist.values()),
                marker=dict(colors=["#FF4757", "#FFB800", "#00D97E"]),
                hole=0.3
            )
        ])
        
        fig.update_layout(
            title="Urgency Distribution",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E4E6EB"),
            height=350
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Risk score distribution
        risk_scores = [case.get("results", {}).get("triage", {}).get("risk_score", 0) 
                      for case in st.session_state.case_history]
        
        fig = go.Figure(data=[
            go.Histogram(
                x=risk_scores,
                nbinsx=10,
                marker=dict(color="#00D4FF"),
                name="Risk Score Distribution"
            )
        ])
        
        fig.update_layout(
            title="Risk Score Distribution",
            xaxis_title="Risk Score",
            yaxis_title="Number of Cases",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E4E6EB"),
            height=350,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Case list
    st.markdown('<h2 class="subheader-title">📋 Detailed Case List</h2>', unsafe_allow_html=True)
    
    cases_data = []
    for case in st.session_state.case_history:
        cases_data.append({
            "Case ID": case["case_id"],
            "Date": case["timestamp"][:10],
            "Time": case["timestamp"][11:19],
            "Age": case["patient_data"].get("age", "N/A"),
            "Chief Complaint": case["patient_data"].get("chief_complaint", "N/A")[:30],
            "Urgency": case["results"]["triage"].get("urgency_level", "N/A"),
            "Risk": f"{case['results']['triage'].get('risk_score', 0):.2f}",
            "Hospital": case["results"]["coordination"].get("primary_referral", {}).get("hospital_name", "N/A")[:20]
        })
    
    df = pd.DataFrame(cases_data)
    
    st.dataframe(df, use_container_width=True, height=400)
    
    # Detailed case view
    st.markdown('<h2 class="subheader-title">🔍 Detailed Case Review</h2>', unsafe_allow_html=True)
    
    case_ids = [case["case_id"] for case in st.session_state.case_history]
    selected_case_id = st.selectbox("Select case to view details:", case_ids, key="case_select")
    
    if selected_case_id:
        selected_case = next((c for c in st.session_state.case_history if c["case_id"] == selected_case_id), None)
        
        if selected_case:
            tab1, tab2, tab3 = st.tabs(["👤 Patient", "📊 Assessment", "🏥 Referral"])
            
            with tab1:
                patient = selected_case["patient_data"]
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                    <div class="diagnostic-box">
                    <h4 style="color: #00D4FF; margin-top: 0;">Demographics</h4>
                    <p><strong>Age:</strong> {patient.get('age')} years<br>
                    <strong>Gender:</strong> {patient.get('gender')}<br>
                    <strong>Location:</strong> {patient.get('location')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="diagnostic-box">
                    <h4 style="color: #00D4FF; margin-top: 0;">Chief Complaint</h4>
                    <p><strong>{patient.get('chief_complaint')}</strong><br>
                    Duration: {patient.get('symptom_duration')}<br>
                    Severity: {patient.get('symptom_severity')}/10</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                if patient.get('medical_history'):
                    st.markdown(f"""
                    <div class="diagnostic-box">
                    <h4 style="color: #00D4FF; margin-top: 0;">Medical History</h4>
                    <p>{', '.join(patient.get('medical_history', []))}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            with tab2:
                triage = selected_case["results"]["triage"]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Urgency", triage.get('urgency_level'))
                    st.metric("Risk Score", f"{triage.get('risk_score'):.2f}")
                
                with col2:
                    st.metric("Confidence", f"{triage.get('confidence'):.0%}")
                    st.metric("Recommendation", triage.get('recommendation')[:30])
            
            with tab3:
                referral = selected_case["results"]["coordination"].get("primary_referral", {})
                
                st.markdown(f"""
                <div class="diagnostic-box">
                <h4 style="color: #00D4FF; margin-top: 0;">Hospital</h4>
                <p><strong>{referral.get('hospital_name', 'N/A')}</strong><br>
                📍 {referral.get('address', 'N/A')}<br>
                📞 {referral.get('phone', 'N/A')}<br>
                🎫 {referral.get('tracking_id', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)

# ============================================
# MAIN APP - NAVIGATION
# ============================================

def main():
    """Main application with sidebar navigation"""
    
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <h2 style="color: #00D4FF; margin: 0; text-shadow: 0 0 10px rgba(0, 212, 255, 0.3);">🏥 MediGuide</h2>
        <p style="color: #A0A6B1; font-size: 0.9rem; margin: 0.5rem 0;">Professional Healthcare Triage AI</p>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        page = st.radio(
            "Navigation",
            ["🏠 Home", "📋 Intake", "🔬 Analysis", "🚨 Triage", "🏥 Care Plan", "📚 History"],
            index=["home", "intake", "analysis", "triage", "coordination", "history"].index(st.session_state.current_page) if st.session_state.current_page in ["home", "intake", "analysis", "triage", "coordination", "history"] else 0
        )
        
        # Map page selection
        page_map = {
            "🏠 Home": "home",
            "📋 Intake": "intake",
            "🔬 Analysis": "analysis",
            "🚨 Triage": "triage",
            "🏥 Care Plan": "coordination",
            "📚 History": "history"
        }
        
        st.session_state.current_page = page_map.get(page, "home")
        
        st.divider()
        
        # Status indicator
        st.markdown("""<h3 style="color: #00D4FF; font-size: 1rem;">📊 Workflow Status</h3>""", unsafe_allow_html=True)
        
        st.write(f"**Stage:** {st.session_state.workflow_stage}")
        
        # Progress
        progress = sum([
            st.session_state.intake_complete,
            st.session_state.analysis_complete,
            st.session_state.triage_complete,
            st.session_state.coordination_complete
        ]) / 4
        
        st.progress(progress, text=f"{progress:.0%} Complete")
        
        st.divider()
        
        # Info
        st.markdown("""
        <div class="info-box">
        <h4 style="color: #00D4FF; margin-top: 0;">System Info</h4>
        <p style="font-size: 0.85rem; margin: 0;">
        <strong>MediGuide v2.0</strong><br>
        Professional Healthcare Triage<br>
        Powered by DeepSeek API
        </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Error handling
    if st.session_state.error_message:
        st.error(st.session_state.error_message)
        if st.button("Clear Error"):
            st.session_state.error_message = None
            st.rerun()
    
    # Page routing
    if st.session_state.current_page == "home":
        page_home()
    elif st.session_state.current_page == "intake":
        page_patient_intake()
    elif st.session_state.current_page == "analysis":
        page_symptom_analysis()
    elif st.session_state.current_page == "triage":
        page_emergency_triage()
    elif st.session_state.current_page == "coordination":
        page_care_coordination()
    elif st.session_state.current_page == "history":
        page_case_history()

if __name__ == "__main__":
    main()