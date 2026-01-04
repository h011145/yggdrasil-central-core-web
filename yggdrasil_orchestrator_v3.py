#!/usr/bin/env python3
import sys
import os
import time

# ゲーム本体（archive_next_war.py）を読み込む
try:
    from games.archive_next_war import NextWarGame
except ImportError:
    # パスが通っていない場合の予備処理
    sys.path.append(os.path.join(os.path.dirname(__file__), 'games'))
    from archive_next_war import NextWarGame

def main():
    # 画面を一度クリア
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()
    
    # テスト用プロファイル
    profile = {"divine_level": 1, "garage_points": 3000, "base_hp": 500, "attack_buff": 50}
    
    while True:
        print("\n" + "="*50)
        print(" YGGDRASIL CENTRAL CORE - ORCHESTRATOR v3")
        print("="*50)
        print(" [3] ネクスト戦記 (NEXT WAR) 起動")
        print(" [q] システム終了")
        print("-" * 50)
        sys.stdout.write("COMMAND > ")
        sys.stdout.flush()
        
        line = sys.stdin.readline()
        if not line: break
        cmd = line.strip().lower()

        if cmd == '3':
            # 本番のゲームクラスを起動
            game = NextWarGame(None, profile)
            game.play()
            sys.stdout.write("\033[2J\033[H") # 戻ってきたら画面クリア
        elif cmd == 'q':
            print("\nシステムを終了します。またの接続を。")
            break

if __name__ == "__main__":
    main()
