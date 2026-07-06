# Run All MCP Servers
# run_servers.py

import os
import sys
import subprocess
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 70)
print("[MCP] MediGuide MCP Servers Manager")
print("=" * 70)

# Server configurations
servers = [
    {
        "name": "Medical Knowledge Base",
        "port": 8001,
        "file": "mcp_servers/medical_kb.py",
        "process": None
    },
    {
        "name": "Emergency Detector",
        "port": 8002,
        "file": "mcp_servers/emergency_detector.py",
        "process": None
    },
    {
        "name": "Care Network Registry",
        "port": 8003,
        "file": "mcp_servers/care_network.py",
        "process": None
    }
]

def start_server(server):
    """Start a single server"""
    print(f"\n[START] Starting {server['name']} (Port {server['port']})...")
    
    try:
        # Start process
        process = subprocess.Popen(
            [sys.executable, server["file"]],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
        )
        
        server["process"] = process
        
        # Wait for server to be ready
        time.sleep(2)
        
        # Check if server is running
        try:
            response = requests.get(f"http://localhost:{server['port']}/health", timeout=2)
            if response.status_code == 200:
                print(f"[OK] {server['name']} is running on port {server['port']}")
                return True
        except:
            pass
        
        print(f"[WAIT] {server['name']} starting... (may take a moment)")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error starting {server['name']}: {e}")
        return False

def check_servers():
    """Check if all servers are running"""
    print("\n" + "=" * 70)
    print("[STATUS] Server Status Check")
    print("=" * 70)
    
    all_running = True
    
    for server in servers:
        try:
            response = requests.get(f"http://localhost:{server['port']}/health", timeout=2)
            if response.status_code == 200:
                print(f"[OK] Port {server['port']}: {server['name']} - RUNNING")
            else:
                print(f"[WARN] Port {server['port']}: {server['name']} - NOT RESPONDING")
                all_running = False
        except:
            print(f"[ERROR] Port {server['port']}: {server['name']} - NOT RUNNING")
            all_running = False
    
    return all_running

def main():
    """Main function"""
    
    print("\n[START] Starting all servers...")
    print("-" * 70)
    
    # Start all servers
    for server in servers:
        start_server(server)
    
    # Wait for servers to fully start
    time.sleep(3)
    
    # Check status
    if check_servers():
        print("\n" + "=" * 70)
        print("[SUCCESS] ALL SERVERS RUNNING SUCCESSFULLY!")
        print("=" * 70)
        print("\n[NEXT] Next steps:")
        print("1. Keep this window open")
        print("2. Servers will run in background")
        print("3. Open new terminal for your application")
        print("\n[INFO] Server Status:")
        for server in servers:
            print(f"   - {server['name']}: http://localhost:{server['port']}")
        print("\n[STOP] To stop servers: Close this window or press Ctrl+C")
        print("=" * 70)
    else:
        print("\n[WARN] Some servers failed to start. Check the logs.")
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n[STOP] Stopping all servers...")
        for server in servers:
            if server["process"]:
                server["process"].terminate()
                print(f"   Stopped: {server['name']}")
        print("[OK] All servers stopped")
        sys.exit(0)

if __name__ == "__main__":
    main()