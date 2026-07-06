# Test MCP Server 1: Medical Knowledge Base
# tests/test_mcp_medical_kb.py

import requests
import json
import time

# MCP Server URL
MCP_URL = "http://localhost:8001"

def test_server_health():
    """Test if server is running"""
    try:
        response = requests.get(f"{MCP_URL}/health", timeout=2)
        if response.status_code == 200:
            data = response.json()
            print("✅ MCP Server is running")
            print(f"   Status: {data.get('status')}")
            print(f"   Database: {data.get('database')}")
            return True
        else:
            print("❌ Server responded with error")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to MCP Server")
        print(f"   Make sure server is running on {MCP_URL}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_find_diseases():
    """Test find_diseases tool"""
    print("\n📋 Testing find_diseases tool...")
    
    try:
        payload = {
            "symptoms": ["fever", "headache", "body_ache"],
            "age": 30,
            "gender": "M",
            "region": "Bangladesh"
        }
        
        response = requests.post(
            f"{MCP_URL}/tools/find_diseases",
            json=payload,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("status") == "success":
                diseases = data.get("results", {}).get("diseases", [])
                print(f"✅ find_diseases works")
                print(f"   Found {len(diseases)} potential diseases")
                
                for i, disease in enumerate(diseases[:3], 1):
                    print(f"   {i}. {disease['disease_name']} ({disease['confidence']:.0%} confidence)")
                
                return True
            else:
                print("❌ Unexpected response")
                print(json.dumps(data, indent=2))
                return False
        else:
            print(f"❌ Server error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_get_disease_details():
    """Test get_disease_details tool"""
    print("\n📋 Testing get_disease_details tool...")
    
    try:
        payload = {"disease_name": "Dengue Fever"}
        
        response = requests.post(
            f"{MCP_URL}/tools/get_disease_details",
            json=payload,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("status") == "success":
                disease = data.get("disease", {})
                symptoms = data.get("symptoms", [])
                
                print(f"✅ get_disease_details works")
                print(f"   Disease: {disease.get('name')}")
                print(f"   Severity: {disease.get('severity')}")
                print(f"   Emergency: {'Yes' if disease.get('is_emergency') else 'No'}")
                print(f"   Associated symptoms: {len(symptoms)}")
                
                if symptoms:
                    print(f"   Top symptoms:")
                    for s in symptoms[:3]:
                        print(f"     - {s['name']} ({s['confidence']:.0%})")
                
                return True
            else:
                print("❌ Unexpected response")
                return False
        else:
            print(f"❌ Server error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_get_treatment_guidelines():
    """Test get_treatment_guidelines tool"""
    print("\n📋 Testing get_treatment_guidelines tool...")
    
    try:
        payload = {"disease_name": "Dengue Fever"}
        
        response = requests.post(
            f"{MCP_URL}/tools/get_treatment_guidelines",
            json=payload,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("status") == "success":
                guidelines = data.get("guidelines", {})
                
                print(f"✅ get_treatment_guidelines works")
                print(f"   First-line treatment: {guidelines.get('first_line')}")
                print(f"   Monitoring: {guidelines.get('monitoring')}")
                print(f"   Evidence level: {guidelines.get('evidence_level')}")
                
                return True
            else:
                print("❌ Unexpected response")
                return False
        else:
            print(f"❌ Server error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_search_symptoms():
    """Test search_symptoms_by_category tool"""
    print("\n📋 Testing search_symptoms_by_category tool...")
    
    try:
        payload = {"category": "respiratory"}
        
        response = requests.post(
            f"{MCP_URL}/tools/search_symptoms_by_category",
            json=payload,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("status") == "success":
                symptoms = data.get("symptoms", [])
                
                print(f"✅ search_symptoms_by_category works")
                print(f"   Found {len(symptoms)} respiratory symptoms")
                
                for s in symptoms[:3]:
                    print(f"     - {s['name']} ({s['medical_term']})")
                
                return True
            else:
                print("❌ Unexpected response")
                return False
        else:
            print(f"❌ Server error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all MCP server tests"""
    
    print("=" * 60)
    print("🔍 MCP Server 1: Medical Knowledge Base - Tests")
    print("=" * 60)
    
    # Wait for server to be ready
    print("\n⏳ Waiting for server to be ready...")
    time.sleep(1)
    
    all_passed = True
    
    # Test 1: Health check
    all_passed &= test_server_health()
    
    if not all_passed:
        print("\n❌ Server is not running. Start it with:")
        print("   python mcp_servers/medical_kb.py")
        return False
    
    # Test 2-5: Tool tests
    all_passed &= test_find_diseases()
    all_passed &= test_get_disease_details()
    all_passed &= test_get_treatment_guidelines()
    all_passed &= test_search_symptoms()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL MCP SERVER TESTS PASSED")
    else:
        print("⚠️  SOME TESTS FAILED")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    main()