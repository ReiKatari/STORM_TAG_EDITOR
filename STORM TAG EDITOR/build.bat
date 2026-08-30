@echo off
echo Building STORM TAG EDITOR...

pyinstaller --clean --noconsole --onefile ^
    --name "STORM TAG EDITOR" ^
    --icon "stormtageditor.ico" ^
    --hidden-import "tkinterdnd2" ^
    --hidden-import "PIL._tkinter_finder" ^
    --collect-all "tkinterdnd2" ^
    --collect-all "customtkinter" ^
    --add-binary "ffmpeg.exe;." ^
    --add-data "stormtageditor.ico;." ^
    --add-data "requirements.txt;." ^
    stormtageditor.py

echo Build complete!
pause
