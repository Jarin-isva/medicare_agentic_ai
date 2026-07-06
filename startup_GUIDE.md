# MediGuide - Complete Startup Guide

## 🚀 Quick Start (All Services)

### Terminal 1: Start All MCP Servers
```bash
python run_servers.py
```
Wait for: "✅ ALL SERVERS RUNNING SUCCESSFULLY!"

### Terminal 2: Start Streamlit Frontend
```bash
# Windows
run_streamlit.bat

# Mac/Linux
bash run_streamlit.sh
```
Wait for: "You can now view your Streamlit app..."

### Terminal 3: Open Browser
Streamlit will open automatically at: http://localhost:8501

---

## 📋 System Requirements

- Python 3.10+
- Virtual environment activated
- Ollama running (download from ollama.ai)
- DeepSeek API key (free from platform.deepseek.com)

---

## 🔧 Troubleshooting

### Port Already in Use
```bash
# Find process using port 8501
lsof -i :8501  # Mac/Linux
netstat -ano | findstr :8501  # Windows

# Kill process
kill -9 <PID>  # Mac/Linux
taskkill /PID <PID> /F  # Windows
```

### Missing DeepSeek API Key
1. Update .env file
2. Get key from: https://platform.deepseek.com/
3. Restart Streamlit app

### MCP Servers Not Running
1. Check all 3 are started
2. Verify ports: 8001, 8002, 8003
3. Check logs for errors

---

## 📊 Expected Workflow

1. **Home** → System overview and case statistics
2. **Patient Intake** → Collect patient information
3. **Symptom Analysis** → AI differential diagnosis
4. **Triage** → Emergency risk assessment
5. **Care Plan** → Hospital referral and care coordination
6. **History** → Case analytics and tracking

---

## 💾 Data Management

- Cases are saved in session state
- Export cases as JSON: `json.dumps(st.session_state.case_history)`
- Clear history: Reset app in Streamlit settings

---

## 🎨 Customization

Edit these files for styling:
- `.streamlit/config.toml` - Theme and server settings
- `streamlit_app.py` - CSS styles in st.markdown

---

## 📞 Support

- Docs: https://docs.streamlit.io
- GitHub: https://github.com/mediguide
- Issues: Use Streamlit error messages for debugging