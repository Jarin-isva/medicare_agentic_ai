# MediGuide - Professional Healthcare Triage System
# Streamlit Frontend - Production Grade
# streamlit_app.py

import os
import sys
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.agent_orchestrator import AgentOrchestrator

# ============================================
# PAGE CONFIGURATION
# ============================================

st.set_page_config(
    page_title="MediGuide - Healthcare Triage",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/mediguide",
        "Report a bug": "https://github.com/mediguide/issues",
        "About": "MediGuide v1.0 - AI Healthcare Triage System"
    }
)

# ============================================
# CUSTOM CSS
# ============================================

st.markdown("""
<style>
    :root {
        --primary-color: #1f77b4;
        --secondary-color: #ff7f0e;
        --success-color: #2ca02c;
        --danger-color: #d62728;
        --warning-color: #ff9800;
    }
    
    .main {
        padding: 2rem 1rem;
    }
    
    .patient-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    
    .emergency-banner {
        background-color: #ffebee;
        border-left: 4px solid #d62728;
        padding: 1rem;
        border-radius: 0.5rem;
        color: #c62828;
        font-weight: bold;
    }
    
    .urgent-banner {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        border-radius: 0.5rem;
        color: #e65100;
        font-weight: bold;
    }
    
    .routine-banner {
        background-color: #e8f5e9;
        border-left: 4px solid #2ca02c;
        padding: 1rem;
        border-radius: 0.5rem;
        color: #1b5e20;
        font-weight: bold;
    }
    
    .diagnostic-box {
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    
    .metric-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        text-align: center;
    }
    
    .header-title {
        color: #1f77b4;
        font-weight: bold;
        font-size: 2rem;
        margin-bottom: 1rem;
    }
    
    .subheader-title {
        color: #1f77b4;
        font-weight: bold;
        font-size: 1.3rem;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# SESSION STATE INITIALIZATION
# ============================================

def initialize_session_state():
    """Initialize all session state variables"""
    
    defaults = {
        "orchestrator": None,
        "patient_session": None,
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
        "current_case_id": None,
        "error_message": None,
        "success_message": None
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
            st.session_state.orchestrator = AgentOrchestrator()
            logger.info("✅ Agent Orchestrator initialized")
        return True
    except ValueError as e:
        st.session_state.error_message = f"❌ Configuration Error: {str(e)}"
        logger.error(f"Failed to initialize orchestrator: {str(e)}")
        return False
    except Exception as e:
        st.session_state.error_message = f"❌ Unexpected Error: {str(e)}"
        logger.error(f"Unexpected error in init_orchestrator: {str(e)}")
        return False

def save_case(case_data: Dict[str, Any]):
    """Save case to history"""
    case_entry = {
        "case_id": st.session_state.current_case_id or f"CASE-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "timestamp": datetime.now().isoformat(),
        "patient_data": st.session_state.patient_data,
        "results": {
            "analysis": st.session_state.analysis_results,
            "triage": st.session_state.triage_results,
            "coordination": st.session_state.coordination_results
        }
    }
    
    st.session_state.case_history.append(case_entry)
    st.session_state.current_case_id = case_entry["case_id"]
    
    logger.info(f"✅ Case saved: {case_entry['case_id']}")

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
    logger.info("🔄 Workflow reset for new patient")

def get_urgency_color(urgency_level: str) -> str:
    """Get color for urgency level"""
    colors = {
        "EMERGENCY": "#d62728",
        "URGENT": "#ff9800",
        "ROUTINE": "#2ca02c"
    }
    return colors.get(urgency_level, "#1f77b4")

# ============================================
# PAGE: HOME
# ============================================

def page_home():
    """Home page with system overview"""
    
    st.markdown('<div class="header-title">🏥 MediGuide Healthcare Triage System</div>', 
                unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>Cases Processed</h3>
            <h1>{}</h1>
        </div>
        """.format(len(st.session_state.case_history)), unsafe_allow_html=True)
    
    with col2:
        emergencies = sum(1 for case in st.session_state.case_history 
                         if case["results"]["triage"].get("urgency_level") == "EMERGENCY")
        st.markdown(f"""
        <div class="metric-card">
            <h3>Emergency Cases</h3>
            <h1 style="color: #d62728;">{emergencies}</h1>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        avg_severity = sum(case["results"]["triage"].get("risk_score", 0) 
                          for case in st.session_state.case_history) / max(len(st.session_state.case_history), 1)
        st.markdown(f"""
        <div class="metric-card">
            <h3>Avg Risk Score</h3>
            <h1>{avg_severity:.2f}</h1>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div class='subheader-title'>ℹ️ System Information</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **MediGuide** is an AI-powered healthcare triage system designed to:
        
        ✅ Collect patient information through conversational intake
        ✅ Analyze symptoms against medical knowledge base
        ✅ Assess emergency risk and urgency levels
        ✅ Generate referrals to appropriate facilities
        
        """)
    
    with col2:
        st.success("""
        **Key Features:**
        
        🎯 Multi-agent architecture
        🔄 Real-time processing
        📊 Differential diagnosis
        🚨 Emergency detection
        🏥 Hospital referral system
        📈 Analytics dashboard
        
        **Ready for clinical deployment**
        """)
    
    st.markdown("<div class='subheader-title'>🚀 Get Started</div>", unsafe_allow_html=True)
    
    if st.button("Start New Patient Assessment", key="home_start", use_container_width=True):
        reset_workflow()
        st.session_state.workflow_stage = "INTAKE"
        st.success("✅ New patient session started. Go to 'Patient Intake' tab.")
        st.rerun()

# ============================================
# PAGE: PATIENT INTAKE
# ============================================

def page_patient_intake():
    """Patient intake form page"""
    
    st.markdown('<div class="header-title">📋 Patient Intake</div>', unsafe_allow_html=True)
    
    if st.session_state.workflow_stage == "IDLE":
        st.warning("⚠️ No active patient session. Start a new assessment from the Home page.")
        return
    
    # Initialize orchestrator
    if not init_orchestrator():
        st.error(st.session_state.error_message)
        return
    
    # Intake form
    st.markdown("<div class='subheader-title'>Patient Information</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        age = st.number_input("Age (years)", min_value=1, max_value=120, value=st.session_state.patient_data.get("age", 30))
    
    with col2:
        gender = st.selectbox("Gender", ["M", "F", "Other"], 
                             index=["M", "F", "Other"].index(st.session_state.patient_data.get("gender", "M")))
    
    chief_complaint = st.text_input(
        "Chief Complaint (main health concern)",
        value=st.session_state.patient_data.get("chief_complaint", ""),
        placeholder="e.g., Severe headache with fever"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        symptom_duration = st.text_input(
            "Symptom Duration",
            value=st.session_state.patient_data.get("symptom_duration", ""),
            placeholder="e.g., 3 days, 2 weeks"
        )
    
    with col2:
        symptom_severity = st.slider(
            "Symptom Severity (1-10)",
            min_value=1, max_value=10,
            value=st.session_state.patient_data.get("symptom_severity", 5)
        )
    
    st.markdown("<div class='subheader-title'>Medical History</div>", unsafe_allow_html=True)
    
    allergies_input = st.text_area(
        "Allergies (comma-separated)",
        value=", ".join(st.session_state.patient_data.get("allergies", [])),
        placeholder="e.g., Penicillin, Aspirin"
    )
    
    medications_input = st.text_area(
        "Current Medications (comma-separated)",
        value=", ".join(st.session_state.patient_data.get("current_medications", [])),
        placeholder="e.g., Aspirin 500mg, Metformin 1000mg"
    )
    
    medical_history_input = st.text_area(
        "Past Medical Conditions (comma-separated)",
        value=", ".join(st.session_state.patient_data.get("medical_history", [])),
        placeholder="e.g., Hypertension, Diabetes, Asthma"
    )
    
    # Submit button
    if st.button("📊 Submit & Proceed to Analysis", key="submit_intake", use_container_width=True):
        # Validate input
        if not chief_complaint or not age:
            st.error("❌ Please fill in Chief Complaint and Age")
            return
        
        # Update patient data
        st.session_state.patient_data = {
            "age": age,
            "gender": gender,
            "chief_complaint": chief_complaint,
            "symptom_duration": symptom_duration,
            "symptom_severity": symptom_severity,
            "allergies": [a.strip() for a in allergies_input.split(",") if a.strip()],
            "current_medications": [m.strip() for m in medications_input.split(",") if m.strip()],
            "medical_history": [h.strip() for h in medical_history_input.split(",") if h.strip()],
            "location": "Chittagong"
        }
        
        st.session_state.intake_complete = True
        st.session_state.workflow_stage = "ANALYSIS"
        st.success("✅ Intake complete. Proceeding to symptom analysis...")
        st.balloons()
        st.rerun()
    
    # Summary
    if st.session_state.patient_data:
        st.markdown("<div class='subheader-title'>📝 Current Summary</div>", unsafe_allow_html=True)
        
        summary_col1, summary_col2 = st.columns(2)
        
        with summary_col1:
            st.write(f"**Age:** {st.session_state.patient_data.get('age')} years")
            st.write(f"**Gender:** {st.session_state.patient_data.get('gender')}")
            st.write(f"**Chief Complaint:** {st.session_state.patient_data.get('chief_complaint')}")
        
        with summary_col2:
            st.write(f"**Duration:** {st.session_state.patient_data.get('symptom_duration')}")
            st.write(f"**Severity:** {st.session_state.patient_data.get('symptom_severity')}/10")
            st.write(f"**Allergies:** {', '.join(st.session_state.patient_data.get('allergies', ['None']))}")

# ============================================
# PAGE: SYMPTOM ANALYSIS
# ============================================

def page_symptom_analysis():
    """Symptom analysis and differential diagnosis page"""
    
    st.markdown('<div class="header-title">🔬 Symptom Analysis & Diagnosis</div>', unsafe_allow_html=True)
    
    if not st.session_state.intake_complete:
        st.warning("⚠️ Please complete patient intake first.")
        return
    
    if not init_orchestrator():
        st.error(st.session_state.error_message)
        return
    
    # Run analysis if not done
    if not st.session_state.analysis_complete:
        st.info("📊 Analyzing symptoms using Medical Knowledge Base...")
        
        try:
            with st.spinner("Analyzing symptoms..."):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    st.session_state.orchestrator.analysis_agent.process(
                        st.session_state.patient_data
                    )
                )
            
            st.session_state.analysis_results = result
            st.session_state.analysis_complete = True
            st.rerun()
        
        except Exception as e:
            st.error(f"❌ Error during analysis: {str(e)}")
            logger.error(f"Analysis error: {str(e)}")
            return
    
    # Display analysis results
    st.markdown("<div class='subheader-title'>📋 Differential Diagnosis</div>", unsafe_allow_html=True)
    
    diagnoses = st.session_state.analysis_results.get("differential_diagnosis", [])
    
    if diagnoses:
        for idx, dx in enumerate(diagnoses[:5], 1):
            with st.expander(f"#{idx} {dx.get('disease', 'Unknown')} ({dx.get('probability', 0):.0%})"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Probability", f"{dx.get('probability', 0):.0%}")
                
                with col2:
                    st.metric("Confidence", f"{dx.get('confidence', 0):.0%}")
                
                with col3:
                    st.metric("Severity", dx.get('severity', 'Unknown'))
                
                st.write(f"**Reasoning:** {dx.get('reasoning', 'N/A')}")
                
                supporting = dx.get('supporting_features', [])
                if supporting:
                    st.write(f"**Supporting Features:** {', '.join(supporting)}")
                
                tests = dx.get('distinguishing_tests', [])
                if tests:
                    st.write(f"**Recommended Tests:** {', '.join(tests)}")
    
    # Clinical reasoning
    st.markdown("<div class='subheader-title'>💡 Clinical Reasoning</div>", unsafe_allow_html=True)
    st.info(st.session_state.analysis_results.get("clinical_reasoning", "N/A"))
    
    # Recommended tests
    tests = st.session_state.analysis_results.get("recommended_tests", [])
    if tests:
        st.markdown("<div class='subheader-title'>🧪 Recommended Investigations</div>", unsafe_allow_html=True)
        for test in tests:
            st.write(f"• {test}")
    
    # Proceed to triage
    if st.button("🚨 Proceed to Emergency Triage", key="proceed_triage", use_container_width=True):
        st.session_state.workflow_stage = "TRIAGE"
        st.rerun()

# ============================================
# PAGE: EMERGENCY TRIAGE
# ============================================

def page_emergency_triage():
    """Emergency triage assessment page"""
    
    st.markdown('<div class="header-title">🚨 Emergency Triage Assessment</div>', unsafe_allow_html=True)
    
    if not st.session_state.analysis_complete:
        st.warning("⚠️ Please complete symptom analysis first.")
        return
    
    if not init_orchestrator():
        st.error(st.session_state.error_message)
        return
    
    # Run triage if not done
    if not st.session_state.triage_complete:
        st.info("🔍 Assessing emergency risk...")
        
        try:
            with st.spinner("Assessing urgency..."):
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
            st.error(f"❌ Error during triage: {str(e)}")
            logger.error(f"Triage error: {str(e)}")
            return
    
    # Display triage results
    urgency = st.session_state.triage_results.get("urgency_level", "ROUTINE")
    risk_score = st.session_state.triage_results.get("risk_score", 0)
    confidence = st.session_state.triage_results.get("confidence", 0)
    
    # Urgency banner
    st.markdown(f"""
    <div class="{urgency.lower()}-banner">
        <h2>⚠️ URGENCY LEVEL: {urgency}</h2>
        <p>Risk Score: {risk_score:.2f} | Confidence: {confidence:.0%}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Risk Score", f"{risk_score:.2f}/1.00")
    
    with col2:
        st.metric("Confidence", f"{confidence:.0%}")
    
    with col3:
        urgency_text = {"EMERGENCY": "🚨 IMMEDIATE", "URGENT": "⚠️ SAME-DAY", "ROUTINE": "📅 SCHEDULED"}
        st.metric("Action", urgency_text.get(urgency, "UNKNOWN"))
    
    # Contributing factors
    st.markdown("<div class='subheader-title'>📊 Contributing Factors</div>", unsafe_allow_html=True)
    
    factors = st.session_state.triage_results.get("contributing_factors", {})
    
    if factors:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Age Risk", f"{factors.get('age_risk', 0):.2f}")
        
        with col2:
            st.metric("Symptom Risk", f"{factors.get('symptom_severity_risk', 0):.2f}")
        
        with col3:
            st.metric("History Risk", f"{factors.get('medical_history_risk', 0):.2f}")
        
        with col4:
            st.metric("Vital Risk", f"{factors.get('vital_sign_risk', 0):.2f}")
    
    # Recommendation
    st.markdown("<div class='subheader-title'>💊 Recommendation</div>", unsafe_allow_html=True)
    st.warning(st.session_state.triage_results.get("recommendation", "N/A"))
    
    # Immediate action
    st.markdown("<div class='subheader-title'>🎯 Immediate Action</div>", unsafe_allow_html=True)
    action = st.session_state.triage_results.get("immediate_action", "No action specified")
    st.error(action) if urgency == "EMERGENCY" else st.warning(action) if urgency == "URGENT" else st.success(action)
    
    # Proceed to coordination
    if st.button("🏥 Generate Care Plan & Referrals", key="proceed_coordination", use_container_width=True):
        st.session_state.workflow_stage = "COORDINATION"
        st.rerun()

# ============================================
# PAGE: CARE COORDINATION
# ============================================

def page_care_coordination():
    """Care coordination and referral page"""
    
    st.markdown('<div class="header-title">🏥 Care Plan & Hospital Referral</div>', unsafe_allow_html=True)
    
    if not st.session_state.triage_complete:
        st.warning("⚠️ Please complete emergency triage first.")
        return
    
    if not init_orchestrator():
        st.error(st.session_state.error_message)
        return
    
    # Run coordination if not done
    if not st.session_state.coordination_complete:
        st.info("🔍 Generating care plan and finding hospitals...")
        
        try:
            with st.spinner("Coordinating care..."):
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
            st.error(f"❌ Error during care coordination: {str(e)}")
            logger.error(f"Coordination error: {str(e)}")
            return
    
    # Display care plan
    st.markdown("<div class='subheader-title'>📋 Care Plan</div>", unsafe_allow_html=True)
    
    care_plan = st.session_state.coordination_results.get("care_plan", {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.success(f"**Immediate Action:** {care_plan.get('immediate_action', 'N/A')}")
    
    with col2:
        st.info(f"**Follow-up Schedule:** {care_plan.get('follow_up_schedule', 'N/A')}")
    
    # Patient instructions
    st.markdown("<div class='subheader-title'>📝 Patient Instructions</div>", unsafe_allow_html=True)
    
    for instruction in care_plan.get('patient_instructions', []):
        st.write(f"✓ {instruction}")
    
    # Primary referral
    st.markdown("<div class='subheader-title'>🏥 Primary Hospital Referral</div>", unsafe_allow_html=True)
    
    referral = st.session_state.coordination_results.get("primary_referral", {})
    
    if referral and referral.get("status") != "no_hospital":
        with st.container():
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"""
                <div class="diagnostic-box">
                    <h3>{referral.get('hospital_name', 'N/A')}</h3>
                    <p><strong>Address:</strong> {referral.get('address', 'N/A')}</p>
                    <p><strong>Phone:</strong> {referral.get('phone', 'N/A')}</p>
                    <p><strong>Tracking ID:</strong> {referral.get('tracking_id', 'N/A')}</p>
                    <p><strong>Status:</strong> {"🚨 URGENT" if referral.get('urgent') else "✅ ROUTINE"}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if st.button("📄 View Referral Letter", key="view_letter"):
                    with st.expander("Referral Letter", expanded=True):
                        st.text(referral.get('referral_letter', 'No letter available'))
    else:
        st.warning("⚠️ No suitable hospital found in database")
    
    # Alternative hospitals
    alternatives = st.session_state.coordination_results.get("alternative_hospitals", [])
    
    if alternatives:
        st.markdown("<div class='subheader-title'>🏥 Alternative Hospitals</div>", unsafe_allow_html=True)
        
        for idx, hospital in enumerate(alternatives[:3], 1):
            with st.expander(f"Option #{idx}: {hospital.get('name', 'Unknown')}"):
                st.write(f"**Address:** {hospital.get('address', 'N/A')}")
                st.write(f"**Phone:** {hospital.get('phone', 'N/A')}")
                st.write(f"**Rating:** {hospital.get('rating', 'N/A')}/5")
                st.write(f"**Available Beds:** {hospital.get('available_beds', 'N/A')}")
    
    # Save case and complete workflow
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Save Case & Complete", key="save_case", use_container_width=True):
            save_case(st.session_state)
            st.success("✅ Case saved successfully!")
            st.session_state.success_message = "Case completed and saved"
            st.rerun()
    
    with col2:
        if st.button("🔄 Start New Patient", key="new_patient", use_container_width=True):
            reset_workflow()
            st.session_state.workflow_stage = "IDLE"
            st.rerun()

# ============================================
# PAGE: CASE HISTORY
# ============================================

def page_case_history():
    """Case history and analytics page"""
    
    st.markdown('<div class="header-title">📚 Case History & Analytics</div>', unsafe_allow_html=True)
    
    if not st.session_state.case_history:
        st.info("ℹ️ No cases yet. Start a new patient assessment to build history.")
        return
    
    # Summary statistics
    st.markdown("<div class='subheader-title'>📊 Summary Statistics</div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_cases = len(st.session_state.case_history)
    emergency_cases = sum(1 for case in st.session_state.case_history 
                         if case["results"]["triage"].get("urgency_level") == "EMERGENCY")
    urgent_cases = sum(1 for case in st.session_state.case_history 
                      if case["results"]["triage"].get("urgency_level") == "URGENT")
    avg_risk = sum(case["results"]["triage"].get("risk_score", 0) 
                   for case in st.session_state.case_history) / max(total_cases, 1)
    
    with col1:
        st.metric("Total Cases", total_cases)
    
    with col2:
        st.metric("Emergency", emergency_cases)
    
    with col3:
        st.metric("Urgent", urgent_cases)
    
    with col4:
        st.metric("Avg Risk Score", f"{avg_risk:.2f}")
    
    # Case list
    st.markdown("<div class='subheader-title'>📋 Case List</div>", unsafe_allow_html=True)
    
    # Create dataframe
    cases_data = []
    for case in st.session_state.case_history:
        cases_data.append({
            "Case ID": case["case_id"],
            "Date": case["timestamp"][:10],
            "Time": case["timestamp"][11:19],
            "Age": case["patient_data"].get("age", "N/A"),
            "Chief Complaint": case["patient_data"].get("chief_complaint", "N/A")[:30],
            "Urgency": case["results"]["triage"].get("urgency_level", "N/A"),
            "Risk Score": f"{case['results']['triage'].get('risk_score', 0):.2f}",
            "Hospital": case["results"]["coordination"].get("primary_referral", {}).get("hospital_name", "N/A")[:25]
        })
    
    df = pd.DataFrame(cases_data)
    st.dataframe(df, use_container_width=True, height=400)
    
    # Detailed case view
    st.markdown("<div class='subheader-title'>🔍 Detailed Case View</div>", unsafe_allow_html=True)
    
    case_ids = [case["case_id"] for case in st.session_state.case_history]
    selected_case_id = st.selectbox("Select case to view details:", case_ids)
    
    if selected_case_id:
        selected_case = next((c for c in st.session_state.case_history if c["case_id"] == selected_case_id), None)
        
        if selected_case:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Patient Information**")
                patient = selected_case["patient_data"]
                st.write(f"- Age: {patient.get('age')} years")
                st.write(f"- Gender: {patient.get('gender')}")
                st.write(f"- Chief Complaint: {patient.get('chief_complaint')}")
                st.write(f"- Duration: {patient.get('symptom_duration')}")
                st.write(f"- Severity: {patient.get('symptom_severity')}/10")
            
            with col2:
                st.markdown("**Assessment Results**")
                triage = selected_case["results"]["triage"]
                st.write(f"- Urgency: **{triage.get('urgency_level')}**")
                st.write(f"- Risk Score: {triage.get('risk_score'):.2f}")
                st.write(f"- Confidence: {triage.get('confidence'):.0%}")
                st.write(f"- Recommendation: {triage.get('recommendation')}")
            
            st.markdown("**Diagnosis**")
            diagnosis = selected_case["results"]["coordination"].get("primary_referral", {})
            st.write(f"- Hospital: {diagnosis.get('hospital_name', 'N/A')}")
            st.write(f"- Phone: {diagnosis.get('phone', 'N/A')}")
            st.write(f"- Tracking: {diagnosis.get('tracking_id', 'N/A')}")

# ============================================
# MAIN APP - NAVIGATION
# ============================================

def main():
    """Main application with sidebar navigation"""
    
    # Sidebar
    with st.sidebar:
        st.markdown("# 🏥 MediGuide")
        st.markdown("Professional Healthcare Triage System")
        st.divider()
        
        page = option_menu(
            "Navigation",
            ["Home", "Patient Intake", "Symptom Analysis", "Triage", "Care Plan", "History"],
            icons=["house", "clipboard", "microscope", "exclamation", "hospital", "archive"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "#f0f2f6"},
                "icon": {"color": "#1f77b4", "font-size": "20px"},
                "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px"},
                "nav-link-selected": {"background-color": "#1f77b4", "color": "white"},
            }
        )
        
        st.divider()
        
        # Status indicator
        st.markdown("### 📊 Workflow Status")
        st.write(f"**Current Stage:** {st.session_state.workflow_stage}")
        
        # Progress
        progress = sum([
            st.session_state.intake_complete,
            st.session_state.analysis_complete,
            st.session_state.triage_complete,
            st.session_state.coordination_complete
        ]) / 4
        
        st.progress(progress, text=f"{progress:.0%}")
        
        st.divider()
        
        # Info
        st.info("""
        **MediGuide v1.0**
        
        Healthcare AI Triage System
        
        Powered by:
        - DeepSeek API
        - Medical Knowledge Base
        - 3 MCP Servers
        - 4 Collaborative Agents
        """)
    
    # Error handling
    if st.session_state.error_message:
        st.error(st.session_state.error_message)
    
    if st.session_state.success_message:
        st.success(st.session_state.success_message)
    
    # Page routing
    if page == "Home":
        page_home()
    elif page == "Patient Intake":
        page_patient_intake()
    elif page == "Symptom Analysis":
        page_symptom_analysis()
    elif page == "Triage":
        page_emergency_triage()
    elif page == "Care Plan":
        page_care_coordination()
    elif page == "History":
        page_case_history()

if __name__ == "__main__":
    main()