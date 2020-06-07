# kanji\_to\_furigana.py
A tool which automatically converts sentences with kanji to sentences with furigana formatted for anki.

# How to Use

    python kanji_to_furigana.py --paste_key "<ctrl>+<cmd>+v"

Copy anything into your clipboard using ctrl+c. If it has kanji in it, this script will scrape the furigana for it
from jisho.org and can be pasted using `ctrl+cmd+v` (`cmd` is the windows key on windows).

eg: if we copy: 
よく平気でいられますね

This script will paste: 
よく 平気\[へいき\]でいられますね

# Requirements
This script was developped with Python 3.8.3. The other requirements can be downloaded via: 

    pip install -r requirements.txt

# Detailed Steps for Non-Progammer Windows Users
- Install Python [here](https://www.python.org/downloads/).
- Clone this repo or download it unpack the zip file.
- Navigate to the script in windows explorer and type `cmd` in the path bar to open up cmd in the location of the script.
- run `pip install -r requirements.txt`
- To have this python script run in the background, run `pythonw kanji_to_furigana.py --paste_key "<ctrl>+<cmd>+v"`


# How to stop the script
The script can be stopped by pressing `<ctrl>+<cmd>+<alt>+d`

# Changing the paste keybind 
You can change the keybind according to other things like `<cmd>+<alt>+v`.
For a full list of keys, see [here](https://pynput.readthedocs.io/en/latest/keyboard.html#pynput.keyboard.Key)

CAUTION: Do not use `<ctrl>+v` as a keybind, because that will cause the contents to paste more than once. 
The reason we do not use `<ctrl>+v` is because we don't want to modify normal clipboard contents.

# Executing this as a startup script on Windows
1. Copy run\_automatically.bat to C:\Users\\`YOUR_USERNAME`\\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
2. Replace `YOUR_USERNAME` with your username in run\_automatically.bat
3. Replace `INSERT_PATH_TO_SCRIPT` with the directory of where the script is in run\_automatically.bat

The variable `PASTE_KEYBIND` in the batch script can be changed to the keybind of your choosing

# TODO
 - Add Wanikani integration to ignore kanji which has already been learned
