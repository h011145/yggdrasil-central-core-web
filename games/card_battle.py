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
        
        # 外枠
        self.stdscr.attron(curses.color_pair(1))
        self.stdscr.border()
        
        # 敵ステータス
        self.stdscr.addstr(2, 4, f"ENEMY OS [HP: {'#' * (self.enemy_hp // 10)}{'-' * (10 - self.enemy_hp // 10)}] {self.enemy_hp}%")
        
        # ログエリア
        for i, log in enumerate(self.logs[-5:]):
            self.stdscr.addstr(5 + i, 4, f"> {log}")

        # プレイヤーステータス
        self.stdscr.addstr(h-8, 4, f"PLAYER [HP: {'#' * (self.player_hp // 10)}{'-' * (10 - self.player_hp // 10)}] {self.player_hp}%")
        self.stdscr.addstr(h-7, 4, f"ENERGY: {'●' * self.player_energy}")

        # 手札描画
        for i, card in enumerate(self.hand):
            start_x = 4 + (i * 22)
            self.stdscr.rectangle(h-6, start_x, h-2, start_x + 20)
            self.stdscr.addstr(h-5, start_x + 2, f"[{i+1}] {card[0]}")
            self.stdscr.addstr(h-4, start_x + 2, f"COST: {card[3]}")

        self.stdscr.addstr(h-1, 2, " [1-3]:Card Select  [Q]:Retreat ")
        self.stdscr.refresh()

    def play(self):
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        while self.player_hp > 0 and self.enemy_hp > 0:
            self.draw_ui()
            key = self.stdscr.getch()
            
            if key == ord('q'): break
            
            idx = -1
            if key == ord('1'): idx = 0
            elif key == ord('2'): idx = 1
            elif key == ord('3'): idx = 2
            
            if 0 <= idx < len(self.hand):
                card = self.hand[idx]
                if self.player_energy >= card[3]:
                    # プレイヤーのターン
                    self.player_energy -= card[3]
                    dmg = card[1]
                    self.enemy_hp = max(0, self.enemy_hp - dmg)
                    self.logs.append(f"YOU: {card[0]} を実行。{dmg}ダメージ。")
                    
                    # 敵のターン（簡易AI）
                    time.sleep(0.5)
                    self.draw_ui()
                    e_dmg = random.randint(10, 20)
                    self.player_hp = max(0, self.player_hp - e_dmg)
                    self.logs.append(f"ENEMY: 攻撃を検知。{e_dmg}のダメージ。")
                    
                    # 手札補充とエネルギー回復
                    self.hand[idx] = random.choice(self.deck)
                    self.player_energy = min(3, self.player_energy + 1)
                else:
                    self.logs.append("ERROR: エネルギー不足。")

def main(stdscr):
    game = CardBattle(stdscr)
    game.play()
