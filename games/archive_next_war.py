#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import curses
import time
import math
import random
import os
import sys
import json

# --- 親クラスとコアエンジンのインポート ---
try:
    from core_engine import BaseArchive
    from games.archive_combat import BattleEntity
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core_engine import BaseArchive
    from games.archive_combat import BattleEntity

# --- 敵のパラメータ定義 ---
ENEMY_STATS = {
    "Scout": {"hp": 80, "power": 15, "gp_reward": 50},
    "Warrior": {"hp": 150, "power": 20, "gp_reward": 100},
}

class NextWarGame(BaseArchive):
    def __init__(self, stdscr, profile):
        super().__init__(stdscr, profile)
        self.logs = ["《ネクスト戦記》HEXマップモード起動。"]
        self.is_running = True
        
        self.MAP_WIDTH = 20
        self.MAP_HEIGHT = 20
        self.map_data = [[{"terrain": "plains"} for _ in range(self.MAP_WIDTH)] for _ in range(self.MAP_HEIGHT)]

        self.player_q = self.MAP_WIDTH // 2
        self.player_r = self.MAP_HEIGHT // 2

        self.enemies = []
        self.initial_enemy_count = 5
        self.spawn_enemies(self.initial_enemy_count)
        self.defeated_enemies_count = 0

        self.camera_x = 0
        self.camera_y = 0

        self.h_code_deck = []
        self.load_h_codes()

    def load_h_codes(self):
        dict_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'game_design', 'next_war_h_codes.json')
        try:
            with open(dict_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for code_data in data.get("h_codes", []):
                    power = 0
                    for effect in code_data.get("effects", []):
                        if effect.get("action", {}).get("type") == "damage":
                            power = effect["action"].get("value", 0)
                            break
                    self.h_code_deck.append({"code": code_data["code"], "name": code_data["name"], "p": power})
            self.logs.append("ネクスト戦記用Hコードをロードしました。")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logs.append(f"警告: Hコード辞書の読み込みに失敗 - {e}")
            self.h_code_deck = [{"code": "101", "name": "標準打撃", "p": 15}]

    def spawn_enemies(self, number_of_enemies):
        for _ in range(number_of_enemies):
            q = random.randint(0, self.MAP_WIDTH - 1)
            r = random.randint(0, self.MAP_HEIGHT - 1)
            if q == self.player_q and r == self.player_r:
                continue
            enemy_type = random.choice(list(ENEMY_STATS.keys()))
            self.enemies.append({"q": q, "r": r, "type": enemy_type})
        self.logs.append(f"{len(self.enemies)}体の敵ユニットを配置。")

    def play(self):
        curses.curs_set(0)
        self.stdscr.nodelay(True)
        was_quit_by_user = False

        while self.is_running and self.enemies:
            self.stdscr.clear()
            self.draw_hex_map()
            self.draw_ui()
            
            key = self.stdscr.getch()
            if key != -1:
                if key == ord('q'):
                    self.is_running = False
                    was_quit_by_user = True
                elif key == curses.KEY_UP: self.move_player(0, -1)
                elif key == curses.KEY_DOWN: self.move_player(0, 1)
                elif key == curses.KEY_LEFT: self.move_player(-1, 0)
                elif key == curses.KEY_RIGHT: self.move_player(1, 0)
            time.sleep(0.05)

        self.stdscr.nodelay(False)
        final_victory = len(self.enemies) == 0 and self.is_running
        points_earned = self.defeated_enemies_count * 100
        
        self.draw_final_screen(final_victory, was_quit_by_user, self.defeated_enemies_count)
        
        return {"victory": final_victory, "points_earned": points_earned}

    def move_player(self, dq, dr):
        new_q = self.player_q + dq
        new_r = self.player_r + dr
        if 0 <= new_q < self.MAP_WIDTH and 0 <= new_r < self.MAP_HEIGHT:
            self.player_q = new_q
            self.player_r = new_r
            self.check_for_encounter()

    def check_for_encounter(self):
        collided_enemy_index = -1
        for i, enemy in enumerate(self.enemies):
            if enemy["q"] == self.player_q and enemy["r"] == self.player_r:
                collided_enemy_index = i
                break
        
        if collided_enemy_index != -1:
            enemy_data = self.enemies[collided_enemy_index]
            self.logs.append(f"{enemy_data['type']}と接触！戦闘開始！")
            self.stdscr.refresh()
            time.sleep(1)

            victory = self.run_combat_stage(enemy_data)
            
            if victory:
                self.logs.append(f"{enemy_data['type']}を撃破した！")
                del self.enemies[collided_enemy_index]
                self.defeated_enemies_count += 1
            else:
                self.logs.append("戦闘に敗北...ミッション失敗。")
                self.is_running = False

    def run_combat_stage(self, enemy_data):
        self.stdscr.nodelay(False)
        enemy_stats = ENEMY_STATS[enemy_data["type"]]
        player_hp = self.profile.get('base_hp', 100)
        player = BattleEntity("改良型義体", player_hp)
        enemy = BattleEntity(enemy_data["type"], enemy_stats["hp"])
        enemy.attack_power = enemy_stats["power"]
        deck = self.h_code_deck
        if not deck: deck = [{"code": "000", "name": "攻撃不能", "p": 0}]

        turn = 1
        while player.is_alive() and enemy.is_alive():
            sel = random.randint(0, len(deck) - 1)
            self.draw_combat_ui(player, enemy, turn, deck, sel)
            time.sleep(1)
            target_code = deck[sel]
            atk_buff = self.profile.get('attack_buff', 0)
            res_logs, dmg = enemy.react(target_code, target_code['p'] + atk_buff, turn)
            self.logs.append(f"AI射出: {target_code['name']} -> {dmg:.0f}ダメ")
            self.logs.extend(res_logs)
            self.draw_combat_ui(player, enemy, turn, deck, sel)
            time.sleep(1)
            if not enemy.is_alive(): break
            e_dmg = enemy.attack_power
            player.hp -= e_dmg
            self.logs.append(f"敵の反撃: {e_dmg}ダメージ")
            enemy.update_stance()
            self.draw_combat_ui(player, enemy, turn, deck, sel)
            time.sleep(1)
            turn += 1

        self.stdscr.nodelay(True)
        return player.is_alive()

    def draw_combat_ui(self, player, enemy, turn_count, deck, selection):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        self.safe_addstr(1, 2, f"--- COMBAT (TURN {turn_count}) ---", curses.A_BOLD)
        hp_p = "#" * int(player.hp / player.max_hp * 20) if player.max_hp > 0 else ""
        self.safe_addstr(3, 2, f"PLAYER: {int(player.hp)}/{player.max_hp}")
        self.safe_addstr(4, 2, f"[{hp_p:<20}]", curses.color_pair(2))
        hp_e = "#" * int(enemy.hp / enemy.max_hp * 20) if enemy.max_hp > 0 else ""
        self.safe_addstr(6, 2, f"ENEMY : {int(enemy.hp)}/{enemy.max_hp} ({enemy.name})")
        self.safe_addstr(7, 2, f"[{hp_e:<20}]", curses.color_pair(3))
        self.safe_addstr(8, 2, f"STANCE: {enemy.stance}")
        log_start_y = 10
        for i, log in enumerate(self.logs[-(h - log_start_y - 8):]):
            self.safe_addstr(log_start_y + i, 4, log)
        deck_start_y = h - 7
        self.safe_addstr(deck_start_y, 2, "--- H-CODE ---")
        if not deck: self.safe_addstr(deck_start_y + 2, 4, "NO H-CODES AVAILABLE")
        else:
            for i, item in enumerate(deck):
                style = curses.A_REVERSE if i == selection else curses.A_NORMAL
                self.safe_addstr(deck_start_y + 2 + i, 4, f"{item['code']} : {item['name']}", style)
        self.stdscr.refresh()
    
    def draw_final_screen(self, victory, was_quit, defeated_count):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        
        if victory:
            result_text = "MISSION COMPLETE"
        elif was_quit:
            result_text = "作戦中断"
        else:
            result_text = "MISSION FAILED"

        self.safe_addstr(h // 2 - 1, (w - len(result_text)) // 2, result_text, curses.A_BOLD)
        
        result_detail = f"撃破数: {defeated_count}"
        self.safe_addstr(h // 2 + 1, (w - len(result_detail)) // 2, result_detail)

        self.safe_addstr(h // 2 + 3, (w - 30) // 2, "Enterキーでメインメニューに戻ります...")
        self.stdscr.refresh()
        self.stdscr.getch()

    def draw_hex_map(self):
        hex_height = 2; hex_width = 4
        for r in range(self.MAP_HEIGHT):
            for q in range(self.MAP_WIDTH):
                screen_x, screen_y = self.hex_to_screen(q, r)
                adjusted_x, adjusted_y = screen_x - self.camera_x + 5, screen_y - self.camera_y + 5
                if 0 < adjusted_y < curses.LINES - 4 and 0 < adjusted_x < curses.COLS - 5:
                    self.draw_hex(adjusted_y, adjusted_x)
                    char_to_draw, style = None, curses.A_NORMAL
                    if q == self.player_q and r == self.player_r:
                        char_to_draw, style = " P", curses.A_BOLD | curses.color_pair(2)
                    else:
                        for enemy in self.enemies:
                            if enemy["q"] == q and enemy["r"] == r:
                                char_to_draw, style = " E", curses.A_BOLD | curses.color_pair(3)
                                break
                    if char_to_draw: self.safe_addstr(adjusted_y + 1, adjusted_x + 1, char_to_draw, style)

    def hex_to_screen(self, q, r):
        hex_height, hex_width = 2, 4
        x, y = q * (hex_width * 3 // 4), r * hex_height
        if q % 2 == 1: y += hex_height // 2
        return x, y

    def draw_hex(self, y, x):
        self.safe_addstr(y, x + 1, "__")
        self.safe_addstr(y + 1, x, "/")
        self.safe_addstr(y + 1, x + 3, "\\\\") # 修正
        self.safe_addstr(y + 2, x, "\\\___/") # 修正

    def draw_ui(self):
        h, w = self.stdscr.getmaxyx()
        log_y = h - 8
        self.safe_addstr(log_y, 2, "--- SYSTEM LOG ---")
        for i, log in enumerate(self.logs[-(h - log_y - 3):]): self.safe_addstr(log_y + 1 + i, 4, log[:w - 6])
        self.safe_addstr(h - 2, 2, "↑↓←→: 移動 / Q: 終了")
        self.stdscr.refresh()

if __name__ == "__main__":
    def test_run(stdscr):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.curs_set(0)
        dummy_profile = {"divine_level": 5, "garage_points": 3000, "base_hp": 500, "attack_buff": 50}
        game = NextWarGame(stdscr, dummy_profile)
        game.play()
    try:
        curses.wrapper(test_run)
    except Exception as e:
        curses.endwin()
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()