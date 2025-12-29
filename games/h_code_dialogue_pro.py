#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import curses
import time
import random
import json
import os

class Customer:
    def __init__(self, name, target_satisfaction):
        self.name = name
        self.satisfaction = 0
        self.target = target_satisfaction
        self.mood = "SKEPTICAL"  # 初対面は常に警戒
        self.mental_fatigue = 0
        self.is_active = True

    def update_state(self):
        # 満足度が上がると心を開きやすくなる
        if self.satisfaction > self.target * 0.7:
            self.mood = random.choice(["OPEN", "NEUTRAL"])
        elif self.mental_fatigue > 80:
            self.mood = "BORED"
        
        # 疲労限界チェック
        if self.mental_fatigue >= 100:
            self.is_active = False
            return "【FAILED】客は疲れ果て、会話を打ち切った。"
        return None

    def receive_h_code(self, code_str, power, turn):
        logs = []
        multiplier = 1.0

        # --- 1. Hコード構造解析（ガイドラインに基づくロジック） ---
        
        # 起点(1): 1ターン目、またはリセット直後ならボーナス
        if code_str.startswith('1') and (turn == 0 or self.mood == "NEUTRAL"):
            multiplier *= 1.8
            logs.append("【解析】起点コード(1)がスムーズな導入に成功。")

        # 調和(6): 相手が警戒(SKEPTICAL)している時に有効
        if '6' in code_str and self.mood == "SKEPTICAL":
            multiplier *= 2.0
            self.mood = "NEUTRAL"
            logs.append("【解析】調和コード(6)が警戒心を解いた。")

        # 達成(8): 終盤(満足度50%以上)で威力を発揮
        if code_str.endswith('8') and self.satisfaction > (self.target * 0.5):
            multiplier *= 1.5
            logs.append("【解析】達成コード(8)が確信を突いた！")

        # リセット(0): 疲労を少し軽減する
        if '0' in code_str:
            self.mental_fatigue = max(0, self.mental_fatigue - 15)
            logs.append("【解析】空白コード(0)により場の空気が整った。")

        # --- 2. 計算と反映 ---
        damage = power * multiplier
        self.satisfaction = min(self.target, self.satisfaction + damage)
        self.mental_fatigue += 12 # 1アクションごとの疲労

        return logs, damage

class HCodeAdventure:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.turn = 0
        self.logs = ["パブ『ネオ・アーカイブ』の奥、ターゲットが座っている。"]
        self.customer = Customer("情報屋ジャック", 150)
        
        # 手持ちのHコード（辞書から読み込む想定のサブセット）
        self.hand = [
            {"code": "106", "p": 15, "type": "Social"},
            {"code": "668", "p": 20, "type": "Social"},
            {"code": "321", "p": 25, "type": "Analysis"},
            {"code": "008", "p": 10, "type": "Recovery"},
            {"code": "519", "p": 40, "type": "Risk"} # 高リスク高リターン
        ]

    def draw(self, sel):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()

        # ヘッダー
        self.stdscr.addstr(0, 2, f"--- [ H-CODE DIALOGUE SYSTEM ] ---", curses.A_BOLD)
        self.stdscr.addstr(2, 2, f"TARGET: {self.customer.name}")
        
        # 感情・ステータス表示
        mood_attr = curses.A_REVERSE if self.customer.mood == "SKEPTICAL" else curses.A_BOLD
        self.stdscr.addstr(3, 2, f"MOOD  : {self.customer.mood}", mood_attr)
        
        # 満足度・疲労度ゲージ
        sat_bar = "■" * int(self.customer.satisfaction / self.customer.target * 20)
        fat_bar = "!" * (self.customer.mental_fatigue // 5)
        self.stdscr.addstr(5, 2, f"SATISFACTION: [{sat_bar:<20}] {int(self.customer.satisfaction)}")
        self.stdscr.addstr(6, 2, f"FATIGUE     : [{fat_bar:<20}] {self.customer.mental_fatigue}%")

        # ログ
        self.stdscr.addstr(8, 0, "-" * w)
        for i, m in enumerate(self.logs[-6:]):
            self.stdscr.addstr(9 + i, 2, f"> {m}")

        # Hコード選択（ガイドライン通り数字のみを強調）
        self.stdscr.addstr(16, 2, "SELECT H-CODE (Analyze the sequence):")
        for i, item in enumerate(self.hand):
            if i == sel:
                self.stdscr.addstr(18 + i, 4, f" > [ {item['code']} ] ", curses.A_REVERSE)
            else:
                self.stdscr.addstr(18 + i, 4, f"   [ {item['code']} ] ")

        self.stdscr.refresh()

    def main_loop(self):
        sel = 0
        while self.customer.is_active and self.customer.satisfaction < self.customer.target:
            self.draw(sel)
            key = self.stdscr.getch()

            if key == curses.KEY_UP: sel = (sel - 1) % len(self.hand)
            elif key == curses.KEY_DOWN: sel = (sel + 1) % len(self.hand)
            elif key == ord('\n'):
                # 実行
                target_code = self.hand[sel]
                res_logs, val = self.customer.receive_h_code(target_code['code'], target_code['p'], self.turn)
                
                self.logs.append(f"Execute: {target_code['code']} -> Gain: {int(val)}")
                self.logs.extend(res_logs)
                
                # 状態更新
                fail_msg = self.customer.update_state()
                if fail_msg: self.logs.append(fail_msg)
                
                self.turn += 1
                time.sleep(0.2)

        # 終了判定
        self.draw(sel)
        if self.customer.satisfaction >= self.customer.target:
            self.stdscr.addstr(25, 2, "【SUCCESS】ターゲットは口を割った。機密情報を入手。", curses.A_BOLD)
        else:
            self.stdscr.addstr(25, 2, "【MISSION FAILED】これ以上は危険だ。撤退する。", curses.A_BOLD)
        self.stdscr.getch()

def main(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)
    game = HCodeAdventure(stdscr)
    game.main_loop()

if __name__ == "__main__":
    curses.wrapper(main)
