set VAR1=--paste_key
set PASTE_KEYBIND="<ctrl>+<cmd>+v"
set VAR2=--copy_key
set COPY_KEYBIND="<ctrl>+c"
start "" "C:\Users\YOUR_USERNAME\AppData\Local\Programs\Python\Python39\pythonw" "INSERT_PATH_TO_SCRIPT\kanji_to_furigana.py" %VAR1% %PASTE_KEYBIND% %VAR2% %COPY_KEYBIND%
