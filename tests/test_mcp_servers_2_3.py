# Test MCP Servers 2 & 3
# tests/test_mcp_servers_2_3.py

import requests
import json
import time

# MCP Server URLs
EMERGENCY_URL = "http://localhost:8002"
CARE_NETWORK_URL = "http://localhost:8003"

def test_emergency_server_health():
    """Test Emergency Detector Server health"""
    try:
        response = requests.get(f"{EMERGENCY_URL}/health", timeout=2)
        if response.status_code == 200:
            data = response.json()
            print("✅ Emergency Detector Server is running")
            print(f"   Status: {data.get('status')}")
            print(f"   Database: {data.get('database')}")
            return True
        else:
            print("❌ Emergency Server responded with error")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Emergency Detector Server")
        print(f"   Make sure server is running on {EMERGENCY_URL}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_care_network_server_health():
    """Test Care Network Server health"""
    try:
        response = requests.get(f"{CARE_NETWORK_URL}/health", timeout=2)
        if response.status_code == 200:
            data = response.json()
            print("✅ Care Network Registry Server is running")
            print(f"   Status: {data.get('status')}")
            print(f"   Database: {data.get('database')}")
            return True
        else:
            print("❌ Care Network Server responded with error")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Care Network Server")
        print(f"   Make sure server is running on {CARE_NETWORK_URL}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_check_red_flags():
    """Test red flag detection"""
    print("\n📋 Testing check_red_flags tool...")
    
    try:
        payload = {
            "symptoms": ["severe chest pain", "difficulty breathing"],
            "age": 55,
            "vital_signs": {"oxygen_saturation": 85},
            "medical_history": ["hypertension"]
        }
        
        response = requests.post(
            f"{EMERGENCY_URL}/tools/check_red_flags",
            json=payload,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("has_emergency"):
                print(f"✅ check_red_flags works")
                print(f"   Emergency detected: {data.get('has_emergency')}")
                print(f"   Red flags: {', '.join(data.get('red_flags', []))}")
                print(f"   Severity: {data.get('severity_score')}/10")
                print(f"   Action: {data.get('immediate_action')}")
                return True
            else:
                print("⚠️  No emergency detected (unexpected)")
                return False
        else:
            print(f"❌ Server error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_assess_emergency_level():
    """Test emergency level assessment"""
    print("\n📋 Testing assess_emergency_level tool...")
    
    try:
        payload = {
            "symptoms": ["mild headache", "fatigue"],
            "age": 30,
            "vital_signs": {"heart_rate": 75, "oxygen_saturation": 98},
            "medical_history": []
        }
        
        response = requests.post(
            f"{EMERGENCY_URL}/tools/assess_emergency_level",
            json=payload,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ assess_emergency_level works")
            print(f"   Urgency: {data.get('urgency_level')}")
            print(f"   Risk score: {data.get('risk_score'):.2f}")
            print(f"   Confidence: {data.get('confidence'):.0%}")
            print(f"   Recommendation: {data.get('recommendation')}")
            return True
        else:
            print(f"❌ Server error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_find_nearest_hospital():
    """Test hospital finder"""
    print("\n📋 Testing find_nearest_hospital tool...")
    
    try:
        payload = {
            "specialty": "Cardiology",
            "location": "Chittagong",
            "urgency_level": "URGENT"
        }
        
        response = requests.post(
            f"{CARE_NETWORK_URL}/tools/find_nearest_hospital",
            json=payload,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            hospitals = data.get("hospitals", [])
            
            if hospitals:
                print(f"✅ find_nearest_hospital works")
                print(f"   Found {len(hospitals)} hospitals")
                
                for i, h in enumerate(hospitals[:3], 1):
                    print(f"   {i}. {h['name']} ({h['rating']}/5)")
                    print(f"      - {h['address']}")
                    print(f"      - Available beds: {h['available_beds']}")
                
                return True
            else:
                print("⚠️  No hospitals found")
                return False
        else:
            print(f"❌ Server error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_generate_referral_letter():
    """Test referral letter generation"""
    print("\n📋 Testing generate_referral_letter tool...")
    
    try:
        payload = {
            "hospital_id": 1,
            "diagnosis": "Acute Myocardial Infarction",
            "urgency_level": "EMERGENCY",
            "patient_info": {
                "age": 55,
                "gender": "M",
                "patient_id": "PAT-001",
                "chief_complaint": "Severe chest pain",
                "medications": ["Aspirin", "Metoprolol"],
                "allergies": ["Penicillin"],
                "medical_history": ["Hypertension", "Type 2 Diabetes"]
            }
        }
        
        response = requests.post(
            f"{CARE_NETWORK_URL}/tools/generate_referral_letter",
            json=payload,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("status") == "success":
                letter = data.get("referral_letter", "")
                print(f"✅ generate_referral_letter works")
                print(f"   Tracking ID: {data.get('tracking_id')}")
                print(f"   Hospital: {data.get('hospital_name')}")
                print(f"   Letter preview (first 200 chars):")
                print(f"   {letter[:200]}...")
                return True
            else:
                print("❌ Failed to generate letter")
                return False
        else:
            print(f"❌ Server error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_check_availability():
    """Test hospital availability check"""
    print("\n📋 Testing check_availability tool...")
    
    try:
        payload = {
            "hospital_id": 1,
            "specialty": "Cardiology",
            "urgency_level": "EMERGENCY"
        }
        
        response = requests.post(
            f"{CARE_NETWORK_URL}/tools/check_availability",
            json=payload,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("status") == "success":
                print(f"✅ check_availability works")
                print(f"   Hospital: {data.get('hospital_name')}")
                print(f"   Accepting: {data.get('accepting_patients')}")
                print(f"   Available beds: {data.get('available_beds')}")
                print(f"   Wait time: {data.get('estimated_wait_minutes')} min")
                return True
            else:
                print("❌ Hospital not found")
                return False
        else:
            print(f"❌ Server error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    
    print("=" * 60)
    print("🔍 MCP Servers 2 & 3 - Tests")
    print("=" * 60)
    
    # Wait for servers to be ready
    print("\n⏳ Waiting for servers to be ready...")
    time.sleep(1)
    
    all_passed = True
    
    # Server health checks
    print("\n📊 SERVER HEALTH CHECKS:")
    print("-" * 60)
    all_passed &= test_emergency_server_health()
    print()
    all_passed &= test_care_network_server_health()
    
    if not all_passed:
        print("\n❌ Servers are not running. Start them with:")
        print("   Terminal 1: python mcp_servers/emergency_detector.py")
        print("   Terminal 2: python mcp_servers/care_network.py")
        return False
    
    # Tool tests
    print("\n📋 TOOL TESTS:")
    print("-" * 60)
    all_passed &= test_check_red_flags()
    all_passed &= test_assess_emergency_level()
    all_passed &= test_find_nearest_hospital()
    all_passed &= test_check_availability()
    all_passed &= test_generate_referral_letter()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL MCP SERVERS 2 & 3 TESTS PASSED")
    else:
        print("⚠️  SOME TESTS FAILED")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    main()
