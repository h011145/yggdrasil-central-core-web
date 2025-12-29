#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import curses
import time
import random
import json
import os
import sys

try:
    from core_engine import BaseArchive
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core_engine import BaseArchive

class SocialEntity:
    def __init__(self, name, target_satisfaction):
        self.name = name
        self.satisfaction = 0
        self.target = target_satisfaction
        self.mood = "NEUTRAL"

    def update_mood(self):
        moods = ["NEUTRAL", "BORED", "SKEPTICAL"]
        if self.satisfaction > self.target * 0.5:
            moods.append("OPEN")
        self.mood = random.choice(moods)

    def react(self, h_code_data, power, turn_count):
        base_bonus = 1.0
        structural_bonus = 1.0
        logs = []
        h_code_str = str(h_code_data.get('code', ''))

        if self.mood == "SKEPTICAL" and h_code_str.startswith("6"):
            base_bonus = 2.0
            logs.append(f"【有効】{self.name}の警戒心が和らいだ。")
        elif self.mood == "BORED" and h_code_str.startswith("3"):
            base_bonus = 1.8
            logs.append(f"【刺激】{self.name}は話に身を乗り出した。")
        elif self.mood == "OPEN":
            base_bonus = 1.2

        if h_code_str.endswith('8'):
            structural_bonus *= 1.5
            logs.append(f"【ボーナス】達成(8) - 会話が大きく進展した！")
        if h_code_str.startswith('1') and turn_count == 0:
            structural_bonus *= 1.5
            logs.append(f"【ボーナス】開始(1) - 完璧な導入だ！")

        added = power * base_bonus * structural_bonus
        self.satisfaction = min(self.target, self.satisfaction + added)
        return logs, added

class AdvancedSocialGame(BaseArchive):
    def __init__(self, stdscr, profile):
        super().__init__(stdscr, profile)
        self.logs = ["情報屋のジャックがカウンターで酒を飲んでいる。"]
        self.deck = []
        self.h_code_dictionary = {}
        self.load_h_code_dictionary()
        self.load_deck()
        self.customer = SocialEntity("情報屋のジャック", 100)

    def load_h_code_dictionary(self):
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dict_path = os.path.join(base_path, 'game_design', 'h_code_sequence_dictionary.json')
        if os.path.exists(dict_path):
            try:
                with open(dict_path, 'r', encoding='utf-8') as f:
                    self.h_code_dictionary = json.load(f)
            except: self.logs.append("警告: Hコード辞書の読み込みに失敗。")

    def load_deck(self):
        if not self.h_code_dictionary:
            self.deck = [{"code": "101", "name": "挨拶", "p": 10, "type": "Social"}]
            return
        social_codes = [s for s in self.h_code_dictionary.get('sequences', []) if s.get('type') == 'Social']
        for seq in social_codes:
            power = 0
            for effect in seq.get('effects', []):
                action = effect.get('action', {})
                if action.get('type') == 'social_satisfaction':
                    power = action.get('value', 0)
                    break
            self.deck.append({"code": seq.get('h_code'), "name": seq.get('name'), "p": power, "type": "Social"})

    def draw_ui(self, sel, turn_count):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        
        self.safe_addstr(1, 2, f"--- SOCIAL ARCHIVE (TURN {turn_count}/15) ---", curses.A_BOLD)
        self.safe_addstr(3, 2, f"TARGET: {self.customer.name}")
        self.safe_addstr(4, 2, f"MOOD  : {self.customer.mood}")
        
        bar_len = 20
        filled = int(self.customer.satisfaction / self.customer.target * bar_len) if self.customer.target > 0 else 0
        bar = "#" * filled
        self.safe_addstr(6, 2, f"SATISFACTION: [{bar:<20}] {int(self.customer.satisfaction)}/{self.customer.target}")
        
        self.safe_addstr(8, 0, "-" * min(w, 50))
        for i, m in enumerate(self.logs[-5:]):
            self.safe_addstr(9 + i, 2, f"> {m}")
        
        self.safe_addstr(16, 2, "--- AI H-CODE SELECTION ---")
        for i, item in enumerate(self.deck):
            style = curses.A_REVERSE if i == sel else curses.A_NORMAL
            self.safe_addstr(18 + i, 4, f"{item['code']} : {item['name']}", style)
        self.stdscr.refresh()

    def play(self):
        try:
            curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
        except: pass

        turn_count = 0
        turn_limit = 15

        while self.customer.satisfaction < self.customer.target and turn_count < turn_limit:
            sel = random.randint(0, len(self.deck) - 1) if self.deck else -1
            self.draw_ui(sel, turn_count)

            if sel != -1:
                target_code = self.deck[sel]
                res_logs, val = self.customer.react(target_code, target_code['p'], turn_count)
                self.logs.append(f"AI実行: {target_code['name']} (+{val:.1f})")
                self.logs.extend(res_logs)
            
            self.customer.update_mood()
            turn_count += 1
            self.draw_ui(sel, turn_count)
            time.sleep(1)

        is_victory = self.customer.satisfaction >= self.customer.target
        pts = 80 if is_victory else 15
        self.draw_ui(-1, turn_count)
        self.safe_addstr(14, 2, "【交渉成立】" if is_victory else "【交渉失敗】", curses.A_BOLD)
        self.stdscr.getch()
        
        return {"victory": is_victory, "points_earned": pts, "turns": turn_count}
