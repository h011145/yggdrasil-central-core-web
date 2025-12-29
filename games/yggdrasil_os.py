#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import curses
import time
import random

class Kanata:
    def __init__(self):
        self.name = "カナタ"

    def talk(self, key):
        msgs = {
            "welcome": "ひろし、起きて。アーカイブの同期、開始した。",
            "deploy_start": "義体、射出。壊れたら10秒で忘れていい。",
            "deploy_end": "義体、帰還。ひろしの成果は……5。ゴミみたい。",
            "no_memory": "ひろしの容量は 40。そのコードは 100。算数からやり直して。",
            "status": "ひろしの神格レベル 1。ストレージ 40。接続義体 1。"
        }
        return f"{self.name}: 「{msgs.get(key, '……。')}」"

class WorldEngine:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.kanata = Kanata()
        self.divine_level = 1
        self.storage_capacity = 40
        self.logs = []
        self.is_running = True

    def add_log(self, text):
        self.logs.append(f"[{time.strftime('%H:%M:%S')}] {text}")

    def draw_core(self, selection):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()

        # ヘッダー：神の視点
        self.stdscr.addstr(1, 2, ">>> YGGDRASIL CENTRAL CORE / 中央核 <<<", curses.A_BOLD)
        self.stdscr.addstr(2, 2, self.kanata.talk("status"), curses.color_pair(1))

        # メインメニュー
        menu_items = ["アーカイブへ介入 (DEPLOY)", "義体カスタマイズ (GARAGE)", "瞑想を中断 (SLEEP)"]
        for i, item in enumerate(menu_items):
            style = curses.A_REVERSE if i == selection else curses.A_NORMAL
            self.stdscr.addstr(5 + i, 4, f" {item} ", style)

        # 観測ログ
        self.stdscr.addstr(10, 2, "--- OBSERVATION LOG ---")
        for i, log in enumerate(self.logs[-8:]):
            self.stdscr.addstr(11 + i, 4, log)

        self.stdscr.refresh()

    def deploy_sequence(self):
        """下界（アーカイブ）への介入シミュレーション"""
        self.add_log(self.kanata.talk("deploy_start"))
        self.draw_core(-1)
        time.sleep(1)
        
        # ここで戦闘や社交のロジックを呼び出す
        self.add_log("観測中... 義体が下層市民と接触...")
        time.sleep(1)
        self.add_log("介入成功。REP +10 を獲得。")
        self.add_log(self.kanata.talk("deploy_end"))

    def run(self):
        # カラー設定
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK) # カナタ
        curses.curs_set(0)
        
        sel = 0
        self.add_log(self.kanata.talk("welcome"))

        while self.is_running:
            self.draw_core(sel)
            key = self.stdscr.getch()

            if key == curses.KEY_UP:
                sel = (sel - 1) % 3
            elif key == curses.KEY_DOWN:
                sel = (sel + 1) % 3
            elif key == ord('\n'):
                if sel == 0: # DEPLOY
                    self.deploy_sequence()
                elif sel == 1: # GARAGE
                    self.add_log("カナタ: 「ガレージはまだ閉まってる。ひろしの権限不足。」")
                elif sel == 2: # SLEEP
                    self.is_running = False

def main(stdscr):
    engine = WorldEngine(stdscr)
    engine.run()

if __name__ == "__main__":
    curses.wrapper(main)
