# Test Ollama Integration
# tests/test_ollama.py

import requests
import json

def test_ollama_api():
    """Test that Ollama API is accessible"""
    
    try:
        # Send request to Ollama
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'mistral',
                'prompt': 'What is healthcare?',
                'stream': False
            }
        )
        
        # Check if response is successful
        if response.status_code == 200:
            data = response.json()
            print("✅ Ollama API is working!")
            print(f"Model: {data['model']}")
            print(f"Response: {data['response'][:100]}...")
            return True
        else:
            print("❌ Ollama API error")
            return False
            
    except Exception as e:
        print(f"❌ Error connecting to Ollama: {e}")
        return False

if __name__ == "__main__":
    test_ollama_api()