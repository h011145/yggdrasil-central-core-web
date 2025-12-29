#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import curses
import time
import os
import sys

try:
    from core_engine import BaseArchive
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core_engine import BaseArchive

class MatoSenkiGame(BaseArchive):
    def __init__(self, stdscr, profile):
        super().__init__(stdscr, profile)
        self.logs = ["《魔塔戦記》テキストアドベンチャー開始。"]
        self.is_running = True
        self.current_scene = "start"
        self.story_log = [] # ストーリーの進行を記録するログ

    def play(self):
        curses.curs_set(0) # カーソル非表示
        self.stdscr.nodelay(False) # ブロッキングモード
        
        while self.is_running:
            self.stdscr.clear()
            self.draw_story_ui()
            
            # シーンの実行
            if self.current_scene == "start":
                self.scene_start()
            elif self.current_scene == "hall":
                self.scene_hall()
            elif self.current_scene == "library":
                self.scene_library()
            elif self.current_scene == "ending_clear":
                self.scene_ending_clear()
                self.is_running = False
            elif self.current_scene == "ending_fail":
                self.scene_ending_fail()
                self.is_running = False

            # シーンが変わったら画面を更新
            self.stdscr.refresh()
            if self.is_running: # 終了シーンでなければ入力を待つ
                key = self.stdscr.getch()
                if key == ord('q'):
                    self.is_running = False
            
            time.sleep(0.1) # 描画負荷軽減

        self.stdscr.nodelay(True) # ノンブロッキングモードに戻す
        return {"victory": self.current_scene == "ending_clear", "points_earned": 5000 if self.current_scene == "ending_clear" else 0}

    def draw_story_ui(self):
        h, w = self.stdscr.getmaxyx()
        
        self.safe_addstr(1, 2, "--- 魔塔戦記 ---", curses.A_BOLD)
        self.safe_addstr(3, 2, f"現在のシーン: {self.current_scene}")
        
        # ストーリーログを表示
        story_y = 5
        max_story_lines = h - story_y - 10 # ログとプロンプトの領域を考慮
        for i, line in enumerate(self.story_log[-max_story_lines:]):
            self.safe_addstr(story_y + i, 4, line)

        # ログウィンドウ
        log_y = h - 8
        self.safe_addstr(log_y, 2, "--- SYSTEM LOG ---")
        for i, log in enumerate(self.logs[-(h - log_y - 2):]):
            self.safe_addstr(log_y + 1 + i, 4, log[:w - 6])
            
        self.stdscr.refresh()

    def add_story_line(self, text):
        h, w = self.stdscr.getmaxyx()
        wrapped_lines = self.wrap_text(text, w - 8) # 左右マージン考慮
        self.story_log.extend(wrapped_lines)

    def get_choice(self, choices):
        h, w = self.stdscr.getmaxyx()
        selection = 0
        while True:
            # 選択肢を表示
            choice_y_start = h - len(choices) - 5
            for i, choice_text in enumerate(choices):
                style = curses.A_REVERSE if i == selection else curses.A_NORMAL
                self.safe_addstr(choice_y_start + i, 4, f"> {choice_text}", style)
            
            self.stdscr.refresh()
            key = self.stdscr.getch()

            if key == curses.KEY_UP:
                selection = (selection - 1 + len(choices)) % len(choices)
            elif key == curses.KEY_DOWN:
                selection = (selection + 1) % len(choices)
            elif key == ord('\n'):
                self.add_story_line(f"> {choices[selection]}") # 選択した項目をストーリーログに追加
                return selection
        
    def scene_start(self):
        self.add_story_line("あなたはプロミネンスを起動し、古の魔塔へと足を踏み入れた。")
        self.add_story_line("静寂が広がる広大なホールに、あなたの足音だけが響く。")
        self.current_scene = "hall"
        self.get_choice(["Enterを押して先に進む..."]) # テキスト表示後、何かキーを押すまで待つ

    def scene_hall(self):
        self.add_story_line("ホールの中央には、二つの大きな扉があった。")
        self.add_story_line("左の扉には古びた文字で「書庫」と書かれ、右の扉には「未知」とだけ記されている。")
        choices = ["左の扉「書庫」へ進む", "右の扉「未知」へ進む"]
        choice = self.get_choice(choices)
        if choice == 0:
            self.current_scene = "library"
        elif choice == 1:
            self.current_scene = "ending_fail" # 未実装のため仮に失敗

    def scene_library(self):
        self.add_story_line("書庫の扉を開けると、無数の古文書が整然と並んでいた。")
        self.add_story_line("埃っぽい空気の中、遠くで何かが囁く声が聞こえる。")
        choices = ["古文書を調べる", "囁きの声の主を探す"]
        choice = self.get_choice(choices)
        if choice == 0:
            self.add_story_line("あなたは古文書から世界の真実の一部を発見した！")
            self.current_scene = "ending_clear"
        elif choice == 1:
            self.add_story_line("あなたは囁きの声に誘われ、暗闇に飲み込まれた...")
            self.current_scene = "ending_fail"

    def scene_ending_clear(self):
        self.add_story_line("魔塔の謎を解き明かし、あなたは新たなる力と知恵を得た。")
        self.add_story_line("Yggdrasilの真の目的が、今、明らかにされる... (To Be Continued)")
        self.get_choice(["Enterを押してメインメニューに戻る..."])

    def scene_ending_fail(self):
        self.add_story_line("あなたの冒険は、ここで幕を閉じた。")
        self.add_story_line("魔塔の深淵は、あなたの理解を超えていたようだ。")
        self.get_choice(["Enterを押してメインメニューに戻る..."])

    def wrap_text(self, text, width):
        lines = []
        for paragraph in text.split('\n'):
            words = paragraph.split(' ')
            current_line = []
            for word in words:
                if len(' '.join(current_line + [word])) <= width:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
            if current_line:
                lines.append(' '.join(current_line))
        return lines

if __name__ == "__main__":
    def test_run(stdscr):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.curs_set(0)
        dummy_profile = {"divine_level": 5, "garage_points": 3000}
        game = MatoSenkiGame(stdscr, dummy_profile)
        game.play()

    try:
        curses.wrapper(test_run)
    except Exception as e:
        curses.endwin()
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
