import curses
import random
import time

class CardBattle:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.player_hp = 100
        self.enemy_hp = 100
        self.player_energy = 3
        # カード定義: [名前, ダメージ, 防御, コスト]
        self.deck = [
            ["ATTACK_EXE", 20, 0, 1],
            ["SHIELD_PROT", 0, 15, 1],
            ["GIGA_FLARE", 45, 0, 3],
            ["HEAL_RECV", -15, 0, 2]
        ]
        self.hand = random.sample(self.deck, 3)
        self.logs = ["SYST: 戦闘シーケンス開始..."]

    def draw_ui(self):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        
        # 色設定 (緑)
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        self.stdscr.attron(curses.color_pair(1))
        self.stdscr.border()
        
        # 敵ステータス
        self.stdscr.addstr(2, 4, f"ENEMY OS [HP: {'#' * (self.enemy_hp // 10)}{'-' * (10 - self.enemy_hp // 10)}] {self.enemy_hp}%")
        
        # ログエリア
        for i, log in enumerate(self.logs[-5:]):
            if 5 + i < h:
                self.stdscr.addstr(5 + i, 4, f"> {log}")

        # プレイヤーステータス
        self.stdscr.addstr(h-8, 4, f"PLAYER [HP: {'#' * (self.player_hp // 10)}{'-' * (10 - self.player_hp // 10)}] {self.player_hp}%")
        self.stdscr.addstr(h-7, 4, f"ENERGY: {'●' * self.player_energy}")

        # 手札描画
        for i, card in enumerate(self.hand):
            start_x = 4 + (i * 22)
            if start_x + 20 < w:
                # 簡易的な枠線描画
                self.stdscr.addstr(h-6, start_x, "+" + "-"*18 + "+")
                self.stdscr.addstr(h-5, start_x, f"| {card[0][:16]:<16} |")
                self.stdscr.addstr(h-4, start_x, f"| COST: {card[3]:<10} |")
                self.stdscr.addstr(h-3, start_x, "+" + "-"*18 + "+")
                self.stdscr.addstr(h-2, start_x + 8, f"[{i+1}]")

        self.stdscr.addstr(h-1, 2, " [1-3]:Select Card  [Q]:Retreat ")
        self.stdscr.refresh()

    def play(self):
        while self.player_hp > 0 and self.enemy_hp > 0:
            self.draw_ui()
            key = self.stdscr.getch()
            
            if key == ord('q') or key == ord('Q'): break
            
            idx = -1
            if key == ord('1'): idx = 0
            elif key == ord('2'): idx = 1
            elif key == ord('3'): idx = 2
            
            if 0 <= idx < len(self.hand):
                card = self.hand[idx]
                if self.player_energy >= card[3]:
                    # プレイヤーの攻撃
                    self.player_energy -= card[3]
                    dmg = card[1]
                    self.enemy_hp = max(0, self.enemy_hp - dmg)
                    self.logs.append(f"YOU: {card[0]} 実行。{dmg}Dmg。")
                    
                    # 敵の反撃（簡易演出）
                    self.draw_ui()
                    time.sleep(0.3)
                    e_dmg = random.randint(10, 20)
                    self.player_hp = max(0, self.player_hp - e_dmg)
                    self.logs.append(f"ENEMY: 攻撃を検知。{e_dmg}Dmg受。")
                    
                    # ターン終了処理
                    self.hand[idx] = random.choice(self.deck)
                    self.player_energy = min(3, self.player_energy + 1)
                else:
                    self.logs.append("ERR: エネルギー不足！")
        
        # 終了画面
        self.stdscr.clear()
        msg = "MISSION COMPLETE" if self.enemy_hp <= 0 else "CONNECTION LOST..."
        self.stdscr.addstr(h//2, (w-len(msg))//2, msg)
        self.stdscr.refresh()
        time.sleep(2)
