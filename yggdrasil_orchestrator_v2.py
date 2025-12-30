#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# import curses # Commented out for testing
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
        return f"{self.name}: 「{message_template.format(**format_values)}」"

class WorldEngine:
    def __init__(self, stdscr=None): # stdscr is now optional
        self.stdscr = stdscr # Will be None for non-curses test
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
        print("Profile would be saved here.")

    def draw_menu(self, selection, items, title, sub):
        # Dummy draw for testing
        print(f"--- {title} ---")
        print(f"Kanata says: {sub}")
        for i, item in enumerate(items):
            print(f"> {item}{' (selected)' if i == selection else ''}")
        print("--- SYSTEM LOG ---")
        for log in self.logs[-3:]:
            print(log)

    def wrap_text(self, text, width):
        # Dummy wrap for testing
        return [text[i:i+width] for i in range(0, len(text), width)]


    def slot_select(self):
        print("Selecting slot... (Simulated)")
        # For testing, just load a default profile
        self.player_profile = {
            "divine_level": 1, "garage_points": 3000, "base_hp": 100, "attack_buff": 0,
            "scenario_unlocked_next_war": False,
            "owned_prosthetics": ["TYPE-A_BASIC"],
            "owned_robots": [],
            "equipped_prosthetic_id": "TYPE-A_BASIC",
            "equipped_robot_id": None
        }
        print(self.kanata.talk("welcome"))
        return True

    def main_loop(self):
        sel = 0
        status_text = self.kanata.talk("status", self.player_profile)
        
        print("\nYggdrasil Orchestrator Test Run (non-curses)")
        print(status_text)
        print("Available modes:")
        print("義体改造 (GARAGE)")
        print("選挙 (ELECTION)")
        print("戦闘アーカイブ (COMBAT)")
        print("社交アーカイブ (SOCIAL)")
        print("狙撃アーカイブ (SNIPE)")
        print("貿易アーカイブ (TRADE)")
        print("ネクスト戦記 (NEXT WAR)")
        print("魔塔戦記 (MATO SENKI)")
        print("終了")
        print("\nIf you see this, the orchestrator process started successfully without curses.")
        self.is_running = False # Exit after printing

def start_app(stdscr=None): # stdscr is now optional
    # curses setup removed for testing
    engine = WorldEngine(stdscr) # Pass None for non-curses test
    if engine.slot_select():
        engine.main_loop()

if __name__ == "__main__":
    try:
        start_app() # Call directly, without curses.wrapper
    except Exception as e:
        print(f"\nエラーが発生しました: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
    sys.exit(0) # Ensure clean exit
