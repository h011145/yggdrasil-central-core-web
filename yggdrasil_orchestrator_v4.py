#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import curses # Commented out for testing
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
    print(f"致命的なエラー: ゲームモジュールのインポートに失敗しました: {e}\n", file=sys.stderr) # Added \r\n
    sys.exit(1)

# ### ADDED: ランク称号の定義をオーケストレーターに移動 ###
RANK_TITLES = {
    1: "下級市民",
    2: "一般市民",
    3: "上級市民",
    4: "元老院議員",
    5: "神"
}

# ### ADDED: 義体/ロボットIDからゲームモードへのマッピング ###
# cyborg_garage.py の定義と同期している必要があります
PROSTHETIC_ID_TO_MODE = {
    "TYPE-A_BASIC": "戦闘アーカイブ (COMBAT)", # 基本義体で戦闘アーカイブは常に利用可能だが、形式的にここに含める
    "TYPE-B_BRAWLER": "戦闘アーカイブ (COMBAT)", # 戦闘特化義体も戦闘アーカイブ
    "TYPE-D_SOCIAL": "社交アーカイブ (SOCIAL)",
    "TYPE-C_SNIPER": "狙撃アーカイブ (SNIPE)",
    "TYPE-E_TRADE": "貿易アーカイブ (TRADE)",
}

ROBOT_ID_TO_MODE = {
    "SENTINEL": "ネクスト戦記 (NEXT WAR)",
    "PROMINENCE": "魔塔戦記 (MATO SENKI)",
}

# ### ADDED: 各メニュー項目の説明文 ###
MODE_DESCRIPTIONS = {
    "義体改造 (GARAGE)": "義体やロボットを開発・購入し、自身の能力を強化します。",
    "戦闘アーカイブ (COMBAT)": "仮想戦闘空間で敵と戦い、実践的なスキルとGPを獲得します。",
    "社交アーカイブ (SOCIAL)": "交渉や情報収集を通じて、社会的な影響力とGPを増やします。",
    "狙撃アーカイブ (SNIPE)": "精密な射撃技術を磨き、高難易度の標的を排除してGPを得ます。",
    "貿易アーカイブ (TRADE)": "都市間での物資売買を通じて、経済的なGPを蓄積します。",
    "選挙 (ELECTION)": "神格レベルを上げるため、選挙に立候補します。実績と運が重要です。",
    "ネクスト戦記 (NEXT WAR)": "ネクストとの大規模戦闘をシミュレートし、戦略的な指揮能力が試されます。",
    "魔塔戦記 (MATO SENKI)": "プロミネンスと共に古の魔塔の謎を解き明かす、テキストアドベンチャーです。",
    "終了": "YGGDRASIL CENTRAL COREのシステムを終了します。"
}

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
        return f"{self.name}: 「{message_template.format(**format_values)}"" # Corrected: Removed extra closing quote

class WorldEngine:
    def __init__(self, stdscr=None): # stdscr is now optional
        self.stdscr = stdscr
        if self.stdscr:
            curses.start_color()
            curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK) # For general text
            curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK) # For highlight / cyberpunk green
            curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK) # For errors / alerts
            curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK) # For warnings
            self.stdscr.attron(curses.color_pair(2)) # Default to green
            self.stdscr.clear()
            self.stdscr.refresh()
            curses.curs_set(0) # Hide cursor
        self.kanata = Kanata()
        self.player_profile = {
            "divine_level": 1, "garage_points": 3000, "base_hp": 100, "attack_buff": 0,
            "scenario_unlocked_next_war": False,
            "owned_prosthetics": ["TYPE-A_BASIC"],
            "owned_robots": [],
            "equipped_prosthetic_id": "TYPE-A_BASIC",
            "equipped_robot_id": None
        }
        self.profile_path = "" # Not relevant for this test
        self.logs = []
        self.is_running = True

    def add_log(self, text):
        self.logs.append(f"[{time.strftime('%H:%M:%S')}] {text}")

    def get_profile_path(self, slot_index):
        return os.path.join(GAME_DATA_DIR, f'profile_{slot_index + 1}.json')

    def save_profile(self):
        # Dummy save for testing
        if self.stdscr: self.safe_addstr(0, 0, "Profile would be saved here. (curses)")
        else: print("Profile would be saved here.\n", file=sys.stderr) # Added \r\n

    def safe_addstr(self, y, x, text, attr=0):
        if self.stdscr:
            h, w = self.stdscr.getmaxyx()
            if 0 <= y < h and 0 <= x < w:
                try:
                    self.stdscr.addstr(y, x, text[:w-x], attr)
                except curses.error:
                    pass # ignore error when string is too long

    def draw_menu(self, selection, items, title, sub_text):
        if not self.stdscr: return # cursesが有効でない場合は何もしない

        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()

        # Title
        self.safe_addstr(0, 0, f"--- {title} ---", curses.A_BOLD | curses.color_pair(1))

        # Kanata's dialogue
        y_offset = 2
        for line in self.wrap_text(f"カナタ: 「{sub_text}」", w - 4):
            self.safe_addstr(y_offset, 2, line, curses.color_pair(2))
            y_offset += 1

        # Menu items
        menu_start_y = y_offset + 2
        for i, item in enumerate(items):
            display_text = f"> {item}"
            if i == selection:
                self.safe_addstr(menu_start_y + i, 2, display_text, curses.A_REVERSE | curses.color_pair(2))
            else:
                self.safe_addstr(menu_start_y + i, 2, display_text, curses.color_pair(1))
            
            # Add description if available
            description = MODE_DESCRIPTIONS.get(item.split(" (")[0], "")
            if description:
                self.safe_addstr(menu_start_y + i, 2 + len(display_text) + 2, f"- {description}", curses.color_pair(1))

        # System Log
        log_start_y = h - 5
        self.safe_addstr(log_start_y, 0, "--- SYSTEM LOG ---", curses.A_BOLD | curses.color_pair(1))
        for i, log in enumerate(self.logs[-3:]):
            self.safe_addstr(log_start_y + 1 + i, 2, log, curses.color_pair(1))

        self.stdscr.refresh()

    def wrap_text(self, text, width):
        # curses環境では画面幅に合わせてテキストを折り返す
        if not self.stdscr: # cursesが有効でない場合はダミーを返す
            return [text[i:i+width] for i in range(0, len(text), width)]
        
        lines = []
        current_line = ""
        words = text.split(' ')
        for word in words:
            if len(current_line + word) < width:
                current_line += word + ' '
            else:
                lines.append(current_line.strip())
                current_line = word + ' '
        if current_line:
            lines.append(current_line.strip())
        return lines


    def slot_select(self):
        # Always load a default profile for now
        self.player_profile = {
            "divine_level": 1, "garage_points": 3000, "base_hp": 100, "attack_buff": 0,
            "scenario_unlocked_next_war": False,
            "owned_prosthetics": ["TYPE-A_BASIC"],
            "owned_robots": [],
            "equipped_prosthetic_id": "TYPE-A_BASIC",
            "equipped_robot_id": None
        }
        
        if self.stdscr:
            self.safe_addstr(0, 0, "スロット選択中... (シミュレート)", curses.color_pair(1))
            welcome_msg = self.kanata.talk('welcome')
            self.safe_addstr(1, 0, welcome_msg, curses.color_pair(2))
            self.stdscr.refresh()
            time.sleep(1) # 短時間表示
            return True
        else:
            print("Selecting slot... (Simulated)\n", file=sys.stderr) # Added \r\n
            print(f"{self.kanata.talk('welcome')}\n", file=sys.stderr) # Added \r\n
            return True

    def main_loop(self):
        current_selection_index = 0
        menu_items = list(MODE_DESCRIPTIONS.keys()) # メニュー項目をリスト化

        # cursesが有効な場合のみgetch()で入力を受け付ける
        if self.stdscr:
            self.stdscr.nodelay(True) # 非ブロッキングモード
            curses.curs_set(0) # カーソル非表示

        while self.is_running:
            status_text = self.kanata.talk("status", self.player_profile)
            self.draw_menu(current_selection_index, menu_items, "YGGDRASIL CENTRAL CORE", status_text)

            key = -1
            if self.stdscr:
                key = self.stdscr.getch()

            if key != -1:
                if key == curses.KEY_UP:
                    current_selection_index = (current_selection_index - 1) % len(menu_items)
                elif key == curses.KEY_DOWN:
                    current_selection_index = (current_selection_index + 1) % len(menu_items)
                elif key == ord('\n') or key == curses.KEY_ENTER: # Enterキー
                    selected_mode = menu_items[current_selection_index]
                    self.add_log(f"選択: {selected_mode}")

                    if selected_mode == "ネクスト戦記 (NEXT WAR)":
                        self.add_log("ネクスト戦記アーカイブへ接続中...")
                        self.stdscr.nodelay(False) # ゲーム中はブロッキングモードに戻す
                        curses.curs_set(1) # カーソルを表示
                        game = archive_next_war.NextWarGame(self.stdscr, self.player_profile)
                        report = game.play()
                        self.player_profile["garage_points"] += report.get("points_earned", 0)
                        self.add_log(self.kanata.talk("deploy_end", report=report))
                        self.stdscr.nodelay(True) # 非ブロッキングモードに戻す
                        curses.curs_set(0) # カーソル非表示
                    elif selected_mode == "終了":
                        self.is_running = False
                        self.add_log("システムを終了します。")
                    else:
                        self.add_log(f"'{selected_mode}' は現在開発中です。")
            
            if not self.stdscr: # curses無効な場合は1回で終了
                self.is_running = False
            else:
                time.sleep(0.1) # CPU負荷軽減
        
        if self.stdscr:
            self.stdscr.nodelay(False) # 終了前に元のモードに戻す
            curses.curs_set(1) # 終了前にカーソルを表示
            self.stdscr.clear()
            self.safe_addstr(0, 0, "YGGDRASIL CENTRAL CORE を終了しました。", curses.color_pair(2))
            self.stdscr.refresh()
            time.sleep(1)

def start_app(stdscr): # stdscrは必須とする
    engine = WorldEngine(stdscr) # stdscrを渡す
    if engine.slot_select():
        engine.main_loop()

if __name__ == "__main__":
    try:
        curses.wrapper(start_app) # curses.wrapper で呼び出す
    except Exception as e:
        # curses.endwin() はcurses.wrapperが自動的に行う
        print(f"\nエラーが発生しました: {e}\n", file=sys.stderr) # Added \r\n
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
    sys.exit(0)