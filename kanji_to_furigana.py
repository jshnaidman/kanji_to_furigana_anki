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
import traceback


class KanjiToFurigana():

    def __init__(self):
        self.kanji_dict = dict()
        self.furigana_clipboard = ""
        self.controller = keyboard.Controller()
        self.paste_hotkeys = {}
        self.kanji_reg = re.compile(r'[㐀-䶵一-鿋豈-頻]+')
        self.not_jap_reg = re.compile(
            r'[^\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff66-\uff9f]+')
        self.jap_reg = re.compile(
            r'[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff66-\uff9f]+')
        self.on_copy()

    def set_hotkeys(self, hotkeys: Dict):
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

    def get_furigana_kanji(self, kanji: str):
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
            traceback.print_exc()
            return None

    def _get_furigana_from_zenbar(self, zen_bar):
        word_ul = zen_bar.find("ul", class_="clearfix")
        word_list = [li for li in word_ul.contents if li.name == 'li']
        furigana_sentence = ""
        for word_li in word_list:
            furigana = word_li.find("span",
                                    class_="japanese_word__furigana_wrapper").text
            furigana = self.not_jap_reg.sub("", furigana)
            word_orig = word_li.find("span",
                                     class_="japanese_word__text_wrapper").text
            word_orig = self.not_jap_reg.sub("", word_orig)
            if(furigana):
                orig_iter = iter(reversed(word_orig))
                furi_iter = iter(reversed(furigana))
                num_common = 0
                try:
                    orig_char = next(orig_iter)
                    furi_char = next(furi_iter)
                    while (orig_char == furi_char):
                        num_common += 1
                        orig_char = next(orig_iter)
                        furi_char = next(furi_iter)
                except StopIteration:
                    pass
                if (num_common != 0):
                    furigana = furigana[:-num_common]
                    kanji_part = word_orig[:-num_common]
                    rest = word_orig[-num_common:]
                else:
                    kanji_part = word_orig
                    rest = ""

                furigana_sentence += "{}[{}]{}".format(
                    kanji_part, furigana, rest)
            else:
                furigana_sentence += word_orig
        return furigana_sentence

    def _get_furigana_from_main_result(self, soup):
        main_result = soup.find("div", id="main_results").find(
            "div", class_="exact_block")
        reading_div = main_result.find("div", class_="japanese", lang="ja")

        furigana_span = reading_div.find(class_="furigana")
        furigana_list = [self.jap_reg.search(content.text) if content.name == 'span'
                         else self.jap_reg.search(content) for content in furigana_span.contents]
        furigana_list = [part.group(0) for part in furigana_list if part]

        text_span = reading_div.find("span", class_="text")
        text = self.not_jap_reg.sub("", text_span.text)

        furigana_idx = 0
        furigana_sentence = ""
        for char in text:
            if (furigana_idx < len(furigana_list) and self.kanji_reg.search(char)):
                furigana_sentence += "{}[{}]".format(
                    char, furigana_list[furigana_idx])
                furigana_idx += 1
            else:
                furigana_sentence += char

        return furigana_sentence

    def get_furigana(self, sentence: str):
        url = f'https://jisho.org/search/{sentence}'
        try:
            page = requests.get(url)
            content = page.content.decode('utf-8', 'ignore')
            soup = BeautifulSoup(content, 'html.parser')
            zen_bar = soup.find("section", id="zen_bar")
            if (zen_bar):
                return self._get_furigana_from_zenbar(zen_bar)
            else:
                return self._get_furigana_from_main_result(soup)
        except Exception:
            traceback.print_exc()
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

        if self.kanji_reg.search(text_clipboard):
            self.furigana_clipboard = self.get_furigana(text_clipboard)

    def on_paste(self):
        # Save actual clipboard
        _ = clipboard.paste()
        try:
            # Output our internal clipboard
            clipboard.copy(self.furigana_clipboard)
        except:
            print(f"failed to paste: {self.furigana_clipboard}")
            print(f"old clipboard: {_}")
            clipboard.copy(_)
            traceback.print_exc()
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
args = arg_parser.parse_args()

kanji_to_furigana = KanjiToFurigana()

hotkeys = {
    '<ctrl>+c': kanji_to_furigana.on_copy,
    args.paste_key: kanji_to_furigana.on_paste,
    '<ctrl>+<cmd>+<alt>+d': sys.exit
}

kanji_to_furigana.set_hotkeys(hotkeys)

with keyboard.GlobalHotKeys(hotkeys) as h:
    h.join()
