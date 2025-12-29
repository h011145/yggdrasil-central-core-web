#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, curses, json
try:
    from core_engine import BaseArchive
except ImportError:
    sys.path.append("/home/hirosi/my_gemini_project")
    from core_engine import BaseArchive

class CyborgGarage(BaseArchive):
    def __init__(self, stdscr, profile):
        super().__init__(stdscr, profile)
        self.PROFILE_PATH = "/home/hirosi/my_gemini_project/game_data/player_profile.json"
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import curses
import time
import random
import json
import os
import sys

# --- 親クラスとコアエンジンのインポート ---
try:
    from core_engine import BaseArchive
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
    from core_engine import BaseArchive

class BattleEntity:
    def __init__(self, name, max_hp):
        self.name = name
        self.max_hp = max_hp
        self.hp = max_hp
        self.stance = "NORMAL"
        self.traits = []

    def is_alive(self):
        return self.hp > 0

    def react(self, h_code_data, power, turn_count):
        base_bonus = 1.0
        structural_bonus = 1.0
        logs = []
        h_code_str = str(h_code_data.get('code', ''))
        
        if self.stance == "TELEGRAPHING" and h_code_str.startswith("2"):
            base_bonus = 3.0
            logs.append(f"【カウンター！】{self.name}の攻撃の隙を突いた！")
        elif self.stance == "DEFENDING":
            base_bonus = 0.2
            logs.append(f"【防御】{self.name}は防御している！")

        if h_code_str.endswith('9') and self.hp < self.max_hp * 0.3:
            structural_bonus *= 2.0
            logs.append(f"【構造ボーナス】完結(9) - 弱った相手への完璧な一撃！")
        
        damage = power * base_bonus * structural_bonus
        self.hp = max(0, self.hp - damage)
        return logs, damage

    def update_stance(self):
        self.stance = random.choice(["NORMAL", "TELEGRAPHING", "DEFENDING"])

class AdvancedBattleGame(BaseArchive):
    def __init__(self, stdscr, profile):
        super().__init__(stdscr, profile)
        self.logs = ["強敵が立ちはだかっている！"]
        self.deck = [
            {"code": "101", "name": "応急打撃", "p": 15},
            {"code": "202", "name": "反撃コード", "p": 10},
            {"code": "709", "name": "終焉分析", "p": 20}
        ]
        
        player_hp = self.profile.get('base_hp', 100)
        self.player = BattleEntity("改良型義体", player_hp)
        self.enemy = BattleEntity("フェイズシフト・ドロイド", 150)
        self.enemy.attack_power = 12

    def draw_ui(self, sel, turn_count):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        self.safe_addstr(1, 2, f"--- BATTLE ARCHIVE (TURN {turn_count}) ---", curses.A_BOLD)
        
        hp_p = "#" * int(self.player.hp / self.player.max_hp * 20) if self.player.max_hp > 0 else ""
        self.safe_addstr(3, 2, f"PLAYER: {int(self.player.hp)}/{self.player.max_hp}")
        self.safe_addstr(4, 2, f"[{hp_p:<20}]", curses.color_pair(2))

        hp_e = "#" * int(self.enemy.hp / self.enemy.max_hp * 20) if self.enemy.max_hp > 0 else ""
        self.safe_addstr(6, 2, f"ENEMY : {int(self.enemy.hp)}/{self.enemy.max_hp}")
        self.safe_addstr(7, 2, f"[{hp_e:<20}]", curses.color_pair(3))
        self.safe_addstr(8, 2, f"STANCE: {self.enemy.stance}")

        for i, m in enumerate(self.logs[-5:]):
            self.safe_addstr(10 + i, 2, f"> {m}")

        self.safe_addstr(16, 2, "--- AI H-CODE SELECTION ---")
        for i, item in enumerate(self.deck):
            style = curses.A_REVERSE if i == sel else curses.A_NORMAL
            self.safe_addstr(18 + i, 4, f"{item['code']} : {item['name']}", style)
        self.stdscr.refresh()

    def play(self):
        curses.start_color()
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.curs_set(0)

        turn = 1
        while self.player.is_alive() and self.enemy.is_alive():
            # --- AUTO BATTLE LOGIC ---
            sel = random.randint(0, len(self.deck) - 1) if self.deck else 0
            self.draw_ui(sel, turn)
            
            # Player (AI) Turn
            if self.deck:
                target = self.deck[sel]
                atk_buff = self.profile.get('attack_buff', 0)
                res_logs, dmg = self.enemy.react(target, target['p'] + atk_buff, turn)
                self.logs.append(f"AI射出: {target['name']} -> {dmg:.0f}ダメ")
                self.logs.extend(res_logs)
            
            self.draw_ui(sel, turn)
            time.sleep(1)
            
            if not self.enemy.is_alive(): break

            # Enemy Turn
            e_dmg = self.enemy.attack_power
            self.player.hp -= e_dmg
            self.logs.append(f"敵の反撃: {e_dmg}ダメージ")
            self.enemy.update_stance()
            self.draw_ui(-1, turn)
            time.sleep(1)
            turn += 1

        victory = self.player.is_alive()
        pts = 150 if victory else 30
        self.logs.append("【勝利】" if victory else "【大破】")
        
        self.draw_ui(-1, turn)
        self.safe_addstr(15, 2, f"結果: {pts}ポイント獲得", curses.A_BOLD)
        self.stdscr.getch()
        return {"victory": victory, "points_earned": pts, "turns": turn}