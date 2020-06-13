#!/usr/bin/env python
import sys
from pynput import keyboard
from pynput.keyboard import Key, HotKey
import re
import clipboard
from typing import List, Match, Dict, Type, Union
import requests
from bs4 import BeautifulSoup
import time
import argparse
import traceback
from threading import Thread, Lock


class KanjiToFurigana():

    def __init__(self):
        self.kanji_dict = dict()
        self.furigana_clipboard = ""
        self.controller = keyboard.Controller()
        self.paste_hotkeys = {}
        self.lock = Lock()
        self.kanji_reg = re.compile(r'[㐀-䶵一-鿋豈-頻]+')
        self.japanese_reg = re.compile(
            r'[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff66-\uff9f\(\)]+')
        self.furigana_res_reg = re.compile(r'(.*)\((.*)\)')
        self.on_copy()

    def set_hotkeys(self, hotkeys: Dict) -> None:
        for hotkey in hotkeys:
            try:
                if hotkeys[hotkey].__name__ == 'on_paste':
                    self.paste_hotkeys = HotKey.parse(hotkey)
                    break
            except Exception:
                continue

    def tap_key(self, key: Union[str, Type[Key]]) -> None:
        self.controller.press(key)
        time.sleep(0.15)
        self.controller.release(key)

    def get_furigana(self, sentence: str) -> str:
        try:
            payload = {
                'type': 'furigana',
                'text': sentence
            }
            resp = requests.post('https://nihongodera.com/tools/convert', data=payload)
            if (resp.status_code != 200):
                raise Exception(f"Got HTTP code: {resp.status_code}")
            content = resp.text
            soup = BeautifulSoup(content, 'html.parser')
            answer_block = soup.find("div", class_="tool__results")
            furigana_res = []
            for child in answer_block.children:
                if child.name == 'ruby':
                    match = self.furigana_res_reg.search(child.getText())
                    furigana = ' {}[{}]'.format(match.group(1), match.group(2))
                    furigana_res.append(furigana)
                else:
                    japanese = self.japanese_reg.search(str(child))
                    if (japanese):
                        furigana_res.append(japanese.group(0))
            return ''.join(furigana_res)
        except Exception:
            traceback.print_exc()
            return sentence

    def _copy_thread(self):
        # I sleep just to make sure there's no race condition with ctrl+c setting the new clipboard
        # and me getting the clipboard here
        time.sleep(0.1)
        text_clipboard = clipboard.paste()
        # This just removes extra formatting for convenience
        clipboard.copy(text_clipboard)
        if self.kanji_reg.search(text_clipboard):
            self.furigana_clipboard = self.get_furigana(text_clipboard)
        self.lock.release()

    def on_copy(self) -> None:
        # We launch this in a different thread so that we don't
        # block on I/O which can lock up the keyboard.
        if(self.lock.acquire(blocking=False)):
            t = Thread(target=self._copy_thread)
            t.start()

    def on_paste(self) -> None:
        # Save actual clipboard
        _ = clipboard.paste()
        self.lock.acquire()
        furi_clipboard = self.furigana_clipboard
        self.lock.release()
        try:
            # Output our internal clipboard
            clipboard.copy(furi_clipboard)
        except:
            print(f"failed to paste: {furi_clipboard}")
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
    description='Adds Furigana to Kanji in clipboard. Press ctrl+cmd+alt+d to quit')
arg_parser.add_argument('--paste_key',
                        dest='paste_key',
                        help='the key press to paste the furigana contents.'
                        ' eg: ./kanji_to_furigana --paste_key "<alt>+<ctrl>+<cmd>+v ',
                        default='<ctrl>+<cmd>+v'
                        )
arg_parser.add_argument('--copy_key',
                        dest='copy_key',
                        help='The key combination to copy. Mac users should enter <cmd>+c'
                        ' eg: ./kanji_to_furigana --copy_key "<cmd>+c ',
                        default='<ctrl>+c'
                        )
args = arg_parser.parse_args()

kanji_to_furigana = KanjiToFurigana()

hotkeys = {
    args.copy_key: kanji_to_furigana.on_copy,
    args.paste_key: kanji_to_furigana.on_paste,
    '<ctrl>+<cmd>+<alt>+d': sys.exit
}

kanji_to_furigana.set_hotkeys(hotkeys)

with keyboard.GlobalHotKeys(hotkeys) as h:
    h.join()
