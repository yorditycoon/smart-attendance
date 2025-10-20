@echo off

echo Starting backend...
start cmd /k "cd backend && set FLASK_APP=app.py && set FLASK_ENV=development && flask run"

echo Starting frontend...
cd frontend
npm start
pause
