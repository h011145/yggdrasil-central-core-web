#!/usr/bin/env python3
import sys
import random
import time

class NextWarGame:
    def __init__(self, stdscr, profile):
        self.profile = profile
        self.logs = ["《ネクスト戦記》Webアーカイブ・同期完了。"]
        # マップサイズ（ブラウザの画面に収まるサイズ）
        self.MAP_WIDTH = 20
        self.MAP_HEIGHT = 10
        self.player_q = 10
        self.player_r = 5
        self.enemies = []
        self.spawn_enemies(5)

    def spawn_enemies(self, count):
        for _ in range(count):
            self.enemies.append({
                "q": random.randint(0, self.MAP_WIDTH - 1),
                "r": random.randint(0, self.MAP_HEIGHT - 1),
                "hp": 100
            })

    def play(self):
        while True:
            self.draw_hex_map()
            sys.stdout.write("\n移動(w/a/s/d) または 終了(q) > ")
            sys.stdout.flush()
            
            # 入力待機
            cmd = sys.stdin.readline().strip().lower()
            if cmd == 'q': 
                self.logs.append("作戦を中断して帰還します。")
                break
            
            # 移動処理
            old_q, old_r = self.player_q, self.player_r
            if cmd == 'w': self.player_r -= 1
            elif cmd == 's': self.player_r += 1
            elif cmd == 'a': self.player_q -= 1
            elif cmd == 'd': self.player_q += 1
            
            # 範囲外チェック
            self.player_q = max(0, min(self.MAP_WIDTH - 1, self.player_q))
            self.player_r = max(0, min(self.MAP_HEIGHT - 1, self.player_r))
            
            if (old_q, old_r) != (self.player_q, self.player_r):
                self.logs.append(f"Q:{self.player_q}, R:{self.player_r} へ移動。")

    def draw_hex_map(self):
        # 画面をリセットして描画
        sys.stdout.write("\033[2J\033[H")
        print("=== NEXT WAR: HEX STRATEGY ARCHIVE ===")
        print(f" プレイヤー: Q:{self.player_q}, R:{self.player_r}")
        print("-" * 50)

        for r in range(self.MAP_HEIGHT):
            line = ""
            # HEXっぽさを出すために奇数行をずらす
            if r % 2 == 1: line += "  "
            
            for q in range(self.MAP_WIDTH):
                if q == self.player_q and r == self.player_r:
                    line += "\x1b[1;32m[P]\x1b[0m" # 緑色のプレイヤー
                elif any(e['q'] == q and e['r'] == r for e in self.enemies):
                    line += "\x1b[1;31m[E]\x1b[0m" # 赤色の敵
                else:
                    line += " . " # 平地
            print(line)

        print("-" * 50)
        print("--- SYSTEM LOG ---")
        for log in self.logs[-3:]:
            print(f" {log}")
