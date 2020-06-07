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
import argparse


class KanjiToFurigana():

    def __init__(self):
        self.kanji_dict = dict()
        self.furigana_clipboard = ""
        self.controller = keyboard.Controller()
        self.paste_hotkeys = {}
        self.kanji_block_reg = re.compile(r'[㐀-䶵一-鿋豈-頻]+')
        self.on_copy()

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

    def getFurigana_Kanji(self, kanji: str):
        url = f'https://jisho.org/search/{kanji}'
        try:
            page = requests.get(url)
            content = page.content.decode('utf-8', 'ignore')
            soup = BeautifulSoup(content, 'html.parser')
            answer_block = soup.find("div", class_="exact_block")
            furigana_block = answer_block.find(class_='furigana')
            furigana_spans = furigana_block.find_all("span")
            furigana = "".join([span.getText() for span in furigana_spans])
            if (furigana):
                self.kanji_dict[kanji] = furigana
            return furigana
        except Exception:
            return None

    def getFurigana(self, sentence: str):
        url = f'https://jisho.org/search/{sentence}'
        try:
            page = requests.get(url)
            content = page.content.decode('utf-8', 'ignore')
            soup = BeautifulSoup(content, 'html.parser')
            word_ul = soup.find("section", id="zen_bar").find(
                "ul", class_="clearfix")
            word_list = [li for li in word_ul.contents if li.name == 'li']
            furigana_sentence = ""
            for word_li in word_list:
                furigana = word_li.find("span",
                                        class_="japanese_word__furigana_wrapper").text
                furigana = furigana.replace("\n","").replace(" ","")
                word_orig = word_li.find("span",
                                        class_="japanese_word__text_wrapper").text
                word_orig = word_orig.replace("\n", "").replace(" ", "")
                if(furigana):
                    orig_iter = iter(reversed(word_orig))
                    furi_iter = iter(reversed(furigana))
                    try:
                        orig_char = next(orig_iter)
                        furi_char = next(furi_iter)
                        num_common = 0
                        while (orig_char == furi_char):
                            num_common += 1
                            orig_char = next(orig_iter)
                            furi_char = next(furi_iter)
                    except StopIteration:
                        pass
                    if (num_common != 0):
                        furigana = furigana[:-num_common]
                        word_orig = word_orig[:-num_common]

                    furigana_sentence += " {}[{}]".format(word_orig, furigana)
                else:
                    furigana_sentence += word_orig
            return furigana_sentence
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

        if self.kanji_block_reg.search(text_clipboard):
            self.furigana_clipboard = self.getFurigana(text_clipboard)

    def on_paste(self):
        print(self.furigana_clipboard)
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


arg_parser = argparse.ArgumentParser(
    description='Adds Furigana to Kanji in clipboard.')
arg_parser.add_argument('--paste_key',
                        dest='paste_key',
                        help='the key press to paste the furigana contents.'
                        ' eg: ./kanji_to_furigana --paste_key <cmd>+<shift>+v - '
                        'See https://pynput.readthedocs.io/en/latest/keyboard.html#pynput.keyboard.Key for more info.',
                        default='<ctrl>+<cmd>+v'
                        )
arg_parser.add_argument('-e', action='store_true', default=False,
                        dest='exit_key', help='Allows program to quit by pressing <ctrl>+d')
args = arg_parser.parse_args()

kanji_to_furigana = KanjiToFurigana()

hotkeys = {
    '<ctrl>+c': kanji_to_furigana.on_copy,
    args.paste_key: kanji_to_furigana.on_paste
}
if (args.exit_key):
    hotkeys['<ctrl>+d'] = sys.exit

kanji_to_furigana.setHotkeys(hotkeys)

with keyboard.GlobalHotKeys(hotkeys) as h:
    h.join()
