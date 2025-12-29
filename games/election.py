#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import curses
import sys
import os

try:
    from core_engine import BaseArchive
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core_engine import BaseArchive

class ElectionScreen(BaseArchive):
    def __init__(self, stdscr, profile):
        super().__init__(stdscr, profile)
        self.logs = ["「選挙」へようこそ。ここでは名声が力となる。"]
        self.selection = 0
        self.ranks = [
            "下層市民",
            "執行市民",
            "評議委員",
            "元老院"
        ]

    def draw_ui(self):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()

        self.safe_addstr(1, 2, ">>> ELECTION / 選挙 <<<", curses.A_BOLD)
        
        promo_points = self.profile.get("promotion_points", 0)
        current_rank = self.profile.get("social_rank", "N/A")
        
        self.safe_addstr(3, 2, f"PROMOTION POINTS: {promo_points} pp", curses.color_pair(2) | curses.A_BOLD)
        self.safe_addstr(4, 2, f"CURRENT RANK: {current_rank}", curses.color_pair(4) | curses.A_BOLD)

        self.safe_addstr(6, 2, "--- 昇格メニュー ---")
        
        # TODO: Implement actual rank-up logic and cost
        menu_items = [
            "次のランクへ昇格 (未実装)",
            "ロビー活動を行う (未実装)",
            "選挙から退出する"
        ]

        for i, item_text in enumerate(menu_items):
            style = curses.A_REVERSE if i == self.selection else curses.A_NORMAL
            self.safe_addstr(8 + i, 4, f" {item_text} ", style)
        
        log_y_start = h - 6
        self.safe_addstr(log_y_start, 2, "--- ELECTION LOG ---")
        visible_logs = self.logs[-(h - log_y_start - 2):]
        for i, log in enumerate(visible_logs):
            self.safe_addstr(log_y_start + 1 + i, 4, log)

        self.stdscr.refresh()

    def play(self):
        curses.curs_set(0)
        curses.start_color()
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)

        while self.is_running:
            self.draw_ui()
            key = self.stdscr.getch()

            if key == curses.KEY_UP:
                self.selection = (self.selection - 1) % 3
            elif key == curses.KEY_DOWN:
                self.selection = (self.selection + 1) % 3
            elif key == ord('\n'):
                if self.selection == 0 or self.selection == 1:
                    self.logs.append("この機能はまだ実装されていません。")
                else: # Exit option
                    self.is_running = False
        
        # Return the profile, even if unmodified
        return self.profile
