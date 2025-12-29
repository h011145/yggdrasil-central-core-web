#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import curses
import time
import random
import os
import sys

try:
    from core_engine import BaseArchive
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core_engine import BaseArchive

class AdvancedElectionGame(BaseArchive):
    RANK_TITLES = {
        1: "下級市民",
        2: "一般市民",
        3: "上級市民",
        4: "元老院議員",
        5: "神"
    }
    
    # ランクアップに必要な divine_level と garage_points
    RANK_UP_REQUIREMENTS = {
        # 現在のdivine_level: (次のdivine_level, 必要なgarage_points, 当選確率(%) )
        1: (2, 500, 70),  # 下級市民 -> 一般市民
        2: (3, 1500, 60), # 一般市民 -> 上級市民
        3: (4, 3000, 50), # 上級市民 -> 元老院議員
        4: (5, 5000, 40)  # 元老院議員 -> 神
    }

    def __init__(self, stdscr, profile):
        super().__init__(stdscr, profile)
        self.logs = ["選挙システムを起動しました。"]
        self.is_running = True

    def play(self):
        self.stdscr.nodelay(False) # ブロッキングモードに戻す
        
        current_level = self.profile.get("divine_level", 1)
        current_gp = self.profile.get("garage_points", 0)
        current_rank_title = self.RANK_TITLES.get(current_level, "不明")

        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()

        self.safe_addstr(1, 2, "--- 選挙管理委員会 ---", curses.A_BOLD)
        self.safe_addstr(3, 2, f"現在の神格レベル: {current_level} ({current_rank_title})")
        self.safe_addstr(4, 2, f"所持ガレージポイント: {current_gp} GP")
        self.safe_addstr(6, 2, "選挙に立候補しますか？")
        self.safe_addstr(7, 4, "Y: はい / N: いいえ")

        self.stdscr.refresh()

        key = self.stdscr.getch()
        if key == ord('y') or key == ord('Y'):
            return self.run_election()
        else:
            self.logs.append("選挙をキャンセルしました。")
            self.safe_addstr(h // 2 + 3, (w - 30) // 2, "Enterキーでメインメニューに戻ります...")
            self.stdscr.getch()
            return {"victory": False, "points_earned": 0, "new_divine_level": current_level}

    def run_election(self):
        current_level = self.profile.get("divine_level", 1)
        current_gp = self.profile.get("garage_points", 0)
        
        # 既に最高ランクであれば立候補できない
        if current_level >= max(self.RANK_UP_REQUIREMENTS.keys(), default=0) +1: # Assuming max level is 5
            self.display_message("あなたは既に最高の地位にいます！", "Enterで続行...")
            return {"victory": False, "points_earned": 0, "new_divine_level": current_level}

        # ランクアップ要件を取得
        requirements = self.RANK_UP_REQUIREMENTS.get(current_level)
        if not requirements:
            self.display_message("これ以上のランクアップ要件はありません。", "Enterで続行...")
            return {"victory": False, "points_earned": 0, "new_divine_level": current_level}

        next_level, required_gp, win_chance = requirements

        # 要件を満たしているかチェック
        if current_gp < required_gp:
            self.display_message(f"ポイント不足！ {required_gp} GPが必要です。", "Enterで続行...")
            return {"victory": False, "points_earned": 0, "new_divine_level": current_level}

        self.display_message(f"神格レベル {current_level} から {next_level} への立候補！\n" 
                             f"必要ポイント: {required_gp} GP (現在: {current_gp} GP)\n" 
                             f"当選確率: {win_chance} %", "Enterで抽選を開始...")
        self.stdscr.getch()

        # 選挙抽選
        roll = random.randint(1, 100)
        if roll <= win_chance:
            # 当選！
            self.profile["divine_level"] = next_level
            self.profile["garage_points"] -= required_gp # ポイント消費
            self.display_message(f"当選しました！神格レベルが {next_level} に上昇！\n" 
                                 f"新しい称号: {self.RANK_TITLES.get(next_level, '不明')}", "Enterで続行...")
            return {"victory": True, "points_earned": 0, "new_divine_level": next_level}
        else:
            # 落選
            self.display_message(f"残念！落選しました。\n" 
                                 f"選挙活動には {required_gp} GPが消費されました。", "Enterで続行...")
            self.profile["garage_points"] -= required_gp # ポイント消費
            return {"victory": False, "points_earned": 0, "new_divine_level": current_level}

    def display_message(self, message, prompt=""):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        
        # メッセージを複数行に分割し、中央揃えで表示
        lines = message.split('\n')
        for i, line in enumerate(lines):
            self.safe_addstr(h // 2 - len(lines) // 2 + i, (w - len(line)) // 2, line)
        
        if prompt:
            self.safe_addstr(h // 2 + len(lines) // 2 + 2, (w - len(prompt)) // 2, prompt)
        
        self.stdscr.refresh()
        self.stdscr.getch()

if __name__ == "__main__":
    def test_run(stdscr):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.curs_set(0)
        dummy_profile = {"divine_level": 1, "garage_points": 500} # テスト用プロファイル
        game = AdvancedElectionGame(stdscr, dummy_profile)
        game.play()

    try:
        curses.wrapper(test_run)
    except Exception as e:
        curses.endwin()
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()