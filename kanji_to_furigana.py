#!/usr/bin/env python
import sys
from pynput import keyboard
from pynput.keyboard import Key, HotKey
import re
import clipboard
from typing import List, Match, Dict
import requests
from bs4 import BeautifulSoup
import time



class KanjiToFurigana():

    def __init__(self):
        self.kanji_dict = dict()
        self.furigana_clipboard = ""
        self.controller = keyboard.Controller()
        self.paste_hotkeys = {}
        self.kanji_block_reg = re.compile(r'[㐀-䶵一-鿋豈-頻]+')

    def setHotkeys(self, hotkeys: Dict):
        for hotkey in hotkeys:
            try:
                if hotkeys[hotkey].__name__ == 'on_paste':
                    self.paste_hotkeys = HotKey.parse(hotkey)
                    break
            except Exception:
                continue

    def tap_key(self, key):
        self.controller.press(key)
        time.sleep(0.15)
        self.controller.release(key)

    def getFurigana(self, kanji: str):
        url = f'https://jisho.org/search/{kanji}'
        try:
            page = requests.get(url)
            content = page.content.decode('utf-8', 'ignore')
            soup = BeautifulSoup(content, 'html.parser')
            answer_block = soup.find("div", class_="exact_block")
            furigana_block = answer_block.find(class_='furigana')
            furigana_spans = furigana_block.find_all("span")
            furigana = "".join([span.getText() for span in furigana_spans])
            return furigana
        except Exception:
            return None

    def match_to_anki_furigana(self, match: Match):
        kanji = match.group(0)
        if kanji in self.kanji_dict:
            return f" {kanji}[{self.kanji_dict[kanji]}]"
        return kanji

    def on_copy(self):
        # I sleep just to make sure there's no race condition with ctrl+c setting the new clipboard
        # and me getting the clipboard here
        time.sleep(0.1)
        text_clipboard = clipboard.paste()

        kanji_list = self.kanji_block_reg.findall(text_clipboard)
        if (not kanji_list):
            return
        for kanji in kanji_list:
            if kanji not in self.kanji_dict:
                furigana = self.getFurigana(kanji)
                if (furigana):
                    self.kanji_dict[kanji] = furigana
        self.furigana_clipboard = self.kanji_block_reg.sub(
            self.match_to_anki_furigana, text_clipboard)

    def on_paste(self):
        # Save actual clipboard
        _ = clipboard.paste()
        # Output our internal clipboard
        clipboard.copy(self.furigana_clipboard)
        # Have to unpress the currently held keys on shortcut
        for key in self.paste_hotkeys:
            self.controller.release(key)
        # Assumes that ctrl+v is the hotkey to paste
        with self.controller.pressed(Key.ctrl):
            self.tap_key('v')
        # Return to the original clipboard
        clipboard.copy(_)


kanji_to_furigana = KanjiToFurigana()
hotkeys = {
    '<ctrl>+c': kanji_to_furigana.on_copy,
    '<cmd>+<shift>+v': kanji_to_furigana.on_paste
}
kanji_to_furigana.setHotkeys(hotkeys)

with keyboard.GlobalHotKeys(hotkeys) as h:
    h.join()
