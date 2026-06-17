@echo off
REM ===== Atualizar o dashboard FPTE 2026 e publicar no GitHub =====
REM Basta dar duplo-clique neste arquivo.
cd /d "%~dp0"

echo.
echo === [1/2] Baixando resultados e recalculando (pode levar ~2 min) ===
python run_all.py
if errorlevel 1 (
  echo.
  echo *** ERRO ao rodar run_all.py. Nada foi enviado. ***
  pause
  exit /b 1
)

echo.
echo === [2/2] Enviando para o GitHub ===
git add dashboard.html
git diff --cached --quiet
if %errorlevel%==0 (
  echo Nenhuma mudanca nos dados desde a ultima atualizacao. Nada a enviar.
  pause
  exit /b 0
)
git commit -m "update results %date% %time%"
git push
echo.
echo === Pronto! Dashboard atualizado online. ===
echo Link: https://ffantel.github.io/stah-fpte-dashboard/dashboard.html
pause
