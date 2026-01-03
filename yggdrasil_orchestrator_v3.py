#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import os
import json
import traceback
import sys
import random

# --- パス設定 ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
GAMES_DIR = os.path.join(PROJECT_ROOT, 'games')
if GAMES_DIR not in sys.path:
    sys.path.insert(0, GAMES_DIR)

# --- モジュールインポート (エラー回避用) ---
try:
    # 実際のゲームロジックが必要な場合はここでインポート
    pass 
except Exception as e:
    print(f"Import Error: {e}", file=sys.stderr)

class WorldEngine:
    def __init__(self):
        self.player_profile = {
            "divine_level": 1, "garage_points": 3000, "base_hp": 100
        }
        self.is_running = True

    def main_loop(self):
        # 画面を一度クリア（エスケープシーケンス）
        sys.stdout.write("\033[2J\033[H")
        
        print("Selecting slot... (Simulated)")
        print("\nカナタ: 「ひろし、起きて。アーカイブの同期、開始した。」")
        print("\n" + "="*50)
        print(" YGGDRASIL CENTRAL CORE - ORCHESTRATOR v3")
        print("="*50)
        print(f" STATUS: 神格Lv {self.player_profile['divine_level']} / GP {self.player_profile['garage_points']}")
        
        # --- 修正点：入力を待つための無限ループ ---
        while self.is_running:
            print("\n[ Available Modes ]")
            print(" 1: 義体改造 (GARAGE)")
            print(" 2: 戦闘アーカイブ (COMBAT)")
            print(" 3: ネクスト戦記 (NEXT WAR)")
            print(" q: 終了 (QUIT)")
            print("\n番号を入力して Enter を押してください...")
            
            # 標準入力から読み取り
            sys.stdout.write("COMMAND > ")
            sys.stdout.flush()
            
            line = sys.stdin.readline()
            if not line: # 通信断など
                break
            
            cmd = line.strip().lower()

            if cmd == '1':
                print("\n>>> GARAGE モードは現在開発中です。")
            elif cmd == '2':
                print("\n>>> COMBAT モードを起動します...")
            elif cmd == '3':
                print("\n>>> NEXT WAR モードを起動します...")
            elif cmd == 'q':
                print("\nカナタ: 「システムを終了するね。お疲れ様、ひろし。」")
                self.is_running = False
            else:
                print(f"\nカナタ: 「'{cmd}'？ 入力が正しくないみたい。」")
            
            if self.is_running:
                print("\n" + "-"*30)

def start_app():
    engine = WorldEngine()
    engine.main_loop()

if __name__ == "__main__":
    try:
        start_app()
    except Exception as e:
        print(f"\nエラーが発生しました: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
