@echo off
REM Launch Streamlit App
echo.
echo ================================================
echo 🎨 MediGuide Streamlit Frontend
echo ================================================
echo.

REM Activate virtual environment
call .venv\Scripts\activate

REM Launch Streamlit
streamlit run streamlit_app.py --logger.level=info

pause