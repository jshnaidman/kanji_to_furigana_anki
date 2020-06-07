# kanji\_to\_furigana.py
A tool which automatically converts sentences with kanji to sentences with furigana formatted for anki.

# How to Use
python kanji\_to\_furigana.py --paste\_key "\<ctrl>+\<shift>+x"
or 
pythonw kanji\_to\_furigana.py --paste\_key "\<ctrl>+\<shift>+x"
to run the script in the background on windows.

Copy anything into your clipboard using ctrl+c. If it has kanji in it, this script will scrape the furigana for it
from jisho.org and can be pasted using ctrl+shift+x by default.

eg: if we copy: 
よく平気でいられますね

This script will paste: 
よく 平気\[へいき\]でいられますね


# Changing the paste keybind 
You can change the keybind according to other things like "\<cmd>+\<ctrl>+v" where cmd is the windows key.
For a full list of keys, see [here](https://pynput.readthedocs.io/en/latest/keyboard.html#pynput.keyboard.Key)

CAUTION: Do not use ctrl+v as a keybind, because that will cause the contents to paste more than once. 
The reason we do not use ctrl+v is because we don't want to modify normal clipboard contents.

# Executing this as a startup script on Windows
1. Copy run\_automatically.bat to C:\Users\YOUR_USERNAME\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
2. Replace YOUR_USERNAME with your username
3. Replace INSERT\_PATH\_TO\_SCRIPT with the directory of where the script is

The variable PASTE_KEYBIND in the batch script can be changed to the keybind of your choosing

# TODO
 - Add Wanikani integration to ignore kanji which has already been learned
