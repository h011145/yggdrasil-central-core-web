#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import curses
import time
import os
import json
import traceback
import sys
# ### MODIFIED: 絶対パスを相対パスに修正 ###
# sys.path.append('/home/hirosi/my_gemini_project/games') # この行は削除またはコメントアウト
import random

# --- 定数とパス設定 ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__)) # yggdrasil_web ディレクトリを指す
GAMES_DIR = os.path.join(PROJECT_ROOT, 'games')
GAME_DATA_DIR = os.path.join(PROJECT_ROOT, 'game_data')
DIALOGUE_PATH = os.path.join(GAME_DATA_DIR, 'kanata_dialogue.json')

if GAMES_DIR not in sys.path:
    sys.path.insert(0, GAMES_DIR) # GAMES_DIR をパスに追加

os.makedirs(GAME_DATA_DIR, exist_ok=True)

# --- モジュールインポート ---
try:
    import archive_combat
    import archive_social
    import cyborg_garage
    import archive_trade
    import archive_snipe
    import archive_next_war
    import archive_election
    import archive_mato_senki
except ImportError as e:
    print(f"致命的なエラー: ゲームモジュールのインポートに失敗しました: {e}", file=sys.stderr)
    sys.exit(1)

class Kanata:
    def __init__(self):
        self.name = "カナタ"
        self.dialogues = {}
        try:
            with open(DIALOGUE_PATH, 'r', encoding='utf-8') as f:
                self.dialogues = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.dialogues = {"default": ["..."], "welcome": ["ひろし、起きて。"], "status": ["神格Lv {level} ({rank_title}) / GP {points}"], "deploy_end_defeat": ["まだだ…まだ終わらぬ！"], "deploy_end_victory_fast": ["流石ひろし、見事な勝利だ！"], "deploy_end_victory_slow": ["よくやった、ひろし。"], "deploy_end": ["勝利だ！"]}

    def talk(self, key, profile=None, report=None):
        profile = profile or {}
        report = report or {}
        
        if key == "deploy_end" and report:
            dialogue_key = "deploy_end_defeat" if not report.get("victory", False) else \
                           "deploy_end_victory_fast" if report.get("turns", 100) < 8 else \
                           "deploy_end_victory_slow"
        else:
            dialogue_key = key

        message_list = self.dialogues.get(dialogue_key, self.dialogues.get("default", ["...",]))
        message_template = random.choice(message_list)
        
        current_level = profile.get("divine_level", 1)
        rank_title = RANK_TITLES.get(current_level, "不明")

        format_values = {
            "level": current_level,
            "points": profile.get("garage_points", 0),
            "turns": report.get("turns", 'N/A'),
            "rank_title": rank_title
        }
        return f"{self.name}: 「{message_template.format(**format_values)}」"

class WorldEngine:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.kanata = Kanata()
        self.player_profile = {}
        self.profile_path = ""
        self.logs = []
        self.is_running = True

    def add_log(self, text):
        self.logs.append(f"[{time.strftime('%H:%M:%S')}] {text}")

    def get_profile_path(self, slot_index):
        return os.path.join(GAME_DATA_DIR, f'profile_{slot_index + 1}.json')

    def save_profile(self):
        if self.profile_path:
            with open(self.profile_path, 'w', encoding='utf-8') as f:
                json.dump(self.player_profile, f, indent=2, ensure_ascii=False)
            self.add_log("プロファイルを保存しました。")

    def draw_menu(self, selection, items, title, sub):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        self.stdscr.addstr(1, 2, ">>> YGGDRASIL CENTRAL CORE <<<", curses.A_BOLD)
        self.stdscr.addstr(2, 2, str(sub)[:w-4], curses.color_pair(1))
        self.stdscr.addstr(4, 2, f"--- {title} ---")
        for i, item in enumerate(items):
            style = curses.A_REVERSE if i == selection else curses.A_NORMAL
            self.stdscr.addstr(6 + i, 4, f"> {item}"[:w-6], style)
        
        selected_item_text = items[selection]
        description = MODE_DESCRIPTIONS.get(selected_item_text, "この項目に関する説明はありません。" )
        
        desc_start_y = h - 11
        self.stdscr.addstr(desc_start_y, 2, "--- 説明 ---")
        
        wrapped_desc_lines = self.wrap_text(description, w - 4)
        for i, line in enumerate(wrapped_desc_lines):
            self.stdscr.addstr(desc_start_y + 1 + i, 4, line)

        ly = h - 6
        self.stdscr.addstr(ly, 2, "--- SYSTEM LOG ---")
        for i, log in enumerate(self.logs[-(h-ly-2):]):
            self.stdscr.addstr(ly + 1 + i, 4, log[:w-6])
        self.stdscr.refresh()

    def wrap_text(self, text, width):
        """テキストを指定された幅で折り返す"""
        lines = []
        if not text:
            return [""]
        words = text.split(' ')
        current_line = []
        for word in words:
            if len(' '.join(current_line + [word])) <= width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        return lines


    def slot_select(self):
        sel = 0
        while True:
            slots = []
            for i in range(3):
                path = self.get_profile_path(i)
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        loaded_profile = json.load(f)
                        current_level = loaded_profile.get("divine_level", 1)
                        rank_title = RANK_TITLES.get(current_level, "不明")
                        slots.append(f"SLOT {i+1}: {loaded_profile.get('garage_points',0)}GP - {rank_title}")
                else:
                    slots.append(f"SLOT {i+1}: [EMPTY]")
            slots.append("終了")

            self.draw_menu(sel, slots, "セーブデータ選択", self.kanata.talk("welcome"))
            k = self.stdscr.getch()
            if k == curses.KEY_UP: sel = (sel - 1) % 4
            elif k == curses.KEY_DOWN: sel = (sel + 1) % 4
            elif k == ord('\n'):
                if sel == 3: return False
                self.profile_path = self.get_profile_path(sel)
                if os.path.exists(self.profile_path):
                    with open(self.profile_path, 'r', encoding='utf-8') as f:
                        loaded_profile = json.load(f)
                        self.player_profile = {
                            "divine_level": loaded_profile.get("divine_level", 1),
                            "garage_points": loaded_profile.get("garage_points", 0),
                            "base_hp": loaded_profile.get("base_hp", 100),
                            "attack_buff": loaded_profile.get("attack_buff", 0),
                            "scenario_unlocked_next_war": loaded_profile.get("scenario_unlocked_next_war", False),
                            "owned_prosthetics": loaded_profile.get("owned_prosthetics", ["TYPE-A_BASIC"]),
                            "owned_robots": loaded_profile.get("owned_robots", []),
                            "equipped_prosthetic_id": loaded_profile.get("equipped_prosthetic_id", "TYPE-A_BASIC"),
                            "equipped_robot_id": loaded_profile.get("equipped_robot_id", None)
                        }
                else:
                    self.player_profile = {
                        "divine_level": 1, "garage_points": 3000, "base_hp": 100, "attack_buff": 0,
                        "scenario_unlocked_next_war": False,
                        "owned_prosthetics": ["TYPE-A_BASIC"],
                        "owned_robots": [],
                        "equipped_prosthetic_id": "TYPE-A_BASIC",
                        "equipped_robot_id": None
                    }
                return True

    def main_loop(self):
        sel = 0
        status_text = self.kanata.talk("status", self.player_profile)
        
        while self.is_running:
            current_menu_items = []
            
            current_menu_items.append("義体改造 (GARAGE)")
            current_menu_items.append("選挙 (ELECTION)")
            
            owned_prosthetics = self.player_profile.get("owned_prosthetics", [])
            owned_robots = self.player_profile.get("owned_robots", [])

            if "TYPE-A_BASIC" in owned_prosthetics or "TYPE-B_BRAWLER" in owned_prosthetics:
                current_menu_items.append("戦闘アーカイブ (COMBAT)")
            
            if "TYPE-D_SOCIAL" in owned_prosthetics:
                current_menu_items.append("社交アーカイブ (SOCIAL)")
            if "TYPE-C_SNIPER" in owned_prosthetics:
                current_menu_items.append("狙撃アーカイブ (SNIPE)")
            if "TYPE-E_TRADE" in owned_prosthetics:
                current_menu_items.append("貿易アーカイブ (TRADE)")

            if "SENTINEL" in owned_robots:
                current_menu_items.append("ネクスト戦記 (NEXT WAR)")
            if "PROMINENCE" in owned_robots:
                current_menu_items.append("魔塔戦記 (MATO SENKI)")
            
            fixed_order_items = ["義体改造 (GARAGE)", "選挙 (ELECTION)"]
            final_menu = []
            for item in fixed_order_items:
                if item in current_menu_items:
                    final_menu.append(item)
                    current_menu_items.remove(item)
            
            current_menu_items.sort()
            final_menu.extend(current_menu_items)
            
            final_menu.append("終了")
            
            menu = final_menu
            num_menu_items = len(menu)
            
            self.draw_menu(sel, menu, "メインメニュー", status_text)
            
            k = self.stdscr.getch()
            if k == curses.KEY_UP: sel = (sel - 1 + num_menu_items) % num_menu_items
            elif k == curses.KEY_DOWN: sel = (sel + 1) % num_menu_items
            elif k == ord('\n'):
                selected_item_text = menu[sel]
                action_taken = False

                if "戦闘アーカイブ" in selected_item_text:
                    game = archive_combat.AdvancedBattleGame(self.stdscr, self.player_profile)
                    res = game.play()
                    self.player_profile["garage_points"] += res.get("points_earned", 0)
                    self.save_profile()
                    action_taken = True
                elif "社交アーカイブ" in selected_item_text:
                    game = archive_social.AdvancedSocialGame(self.stdscr, self.player_profile)
                    res = game.play()
                    self.player_profile["garage_points"] += res.get("points_earned", 0)
                    self.save_profile()
                    action_taken = True
                elif "義体改造" in selected_item_text:
                    garage = cyborg_garage.CyborgGarage(self.stdscr, self.player_profile)
                    self.player_profile = garage.play()
                    self.save_profile()
                    action_taken = True
                elif "貿易アーカイブ" in selected_item_text:
                    game = archive_trade.AdvancedTradeGame(self.stdscr, self.player_profile)
                    res = game.play()
                    self.player_profile["garage_points"] += res.get("points_earned", 0)
                    self.save_profile()
                    action_taken = True
                elif "狙撃アーカイブ" in selected_item_text:
                    game = archive_snipe.AdvancedSnipeGame(self.stdscr, self.player_profile)
                    res = game.play()
                    self.player_profile["garage_points"] += res.get("points_earned", 0)
                    self.save_profile()
                    action_taken = True
                elif "選挙" in selected_item_text:
                    game = archive_election.AdvancedElectionGame(self.stdscr, self.player_profile)
                    res = game.play()
                    if res.get("victory"):
                         self.player_profile["divine_level"] = res.get("new_divine_level", self.player_profile["divine_level"])
                    self.save_profile()
                    action_taken = True
                elif "ネクスト戦記" in selected_item_text:
                    game = archive_next_war.NextWarGame(self.stdscr, self.player_profile)
                    res = game.play()
                    self.player_profile["garage_points"] += res.get("points_earned", 0)
                    self.save_profile()
                    action_taken = True
                elif "魔塔戦記" in selected_item_text:
                    game = archive_mato_senki.MatoSenkiGame(self.stdscr, self.player_profile)
                    res = game.play()
                    self.player_profile["garage_points"] += res.get("points_earned", 0)
                    self.save_profile()
                    action_taken = True
                elif "終了" in selected_item_text:
                    self.is_running = False
                
                if action_taken:
                    status_text = self.kanata.talk("status", self.player_profile)
                    sel = 0

def start_app(stdscr):
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.curs_set(0)
    stdscr.keypad(True)
    
    engine = WorldEngine(stdscr)
    if engine.slot_select():
        engine.main_loop()

if __name__ == "__main__":
    try:
        curses.wrapper(start_app)
    except:
        curses.endwin()
        traceback.print_exc()
        input("\nエラーが発生しました。Enterで終了します...")
