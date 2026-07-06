# start_servers.py
# Starts all 3 MCP servers as background processes and tracks PIDs

import subprocess
import sys
import time
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PID_FILE = ROOT / ".server_pids.json"

SERVERS = [
    {"name": "medical_kb", "path": "mcp_servers/medical_kb.py", "port": 8001},
    {"name": "emergency_detector", "path": "mcp_servers/emergency_detector.py", "port": 8002},
    {"name": "care_network", "path": "mcp_servers/care_network.py", "port": 8003},
]


def stop_all():
    """Kill any previously tracked server processes."""
    if not PID_FILE.exists():
        print("No tracked PIDs found.")
        return

    with open(PID_FILE) as f:
        pids = json.load(f)

    for name, pid in pids.items():
        try:
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
            print(f"Stopped {name} (PID {pid})")
        except Exception as e:
            print(f"Could not stop {name} (PID {pid}): {e}")

    PID_FILE.unlink()


def start_all():
    """Start all servers fresh and record their PIDs."""
    stop_all()  # clean slate first

    pids = {}
    python_exe = sys.executable

    for server in SERVERS:
        print(f"Starting {server['name']} on port {server['port']}...")
        proc = subprocess.Popen(
            [python_exe, server["path"]],
            cwd=str(ROOT),
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
        )
        pids[server["name"]] = proc.pid
        time.sleep(1)  # give it a moment to bind the port

    with open(PID_FILE, "w") as f:
        json.dump(pids, f, indent=2)

    print("\nAll servers started:")
    for name, pid in pids.items():
        print(f"  {name}: PID {pid}")
    print(f"\nPIDs saved to {PID_FILE}")
    print("Run 'python start_servers.py stop' to shut them all down.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stop":
        stop_all()
    else:
        start_all()