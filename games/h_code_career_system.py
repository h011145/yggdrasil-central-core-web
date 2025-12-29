#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import curses
import time

class GameState:
    def __init__(self):
        # 階級データ: ランク名, 最大容量
        self.ranks = [
            {"name": "下層市民 (Untouchable)", "storage": 40},
            {"name": "パブ経営者 (Keeper)", "storage": 120},
            {"name": "元老院 (Senator)", "storage": 999}
        ]
        self.current_rank_idx = 0
        self.reputation = 0
        self.target_reputation = 100
        
        # 義体のスロット情報
        self.installed_codes = ["101", "000"] # 初期装備
        
    def add_reputation(self, amount):
        self.reputation += amount
        if self.reputation >= self.target_reputation and self.current_rank_idx < len(self.ranks) - 1:
            self.current_rank_idx += 1
            self.reputation = 0
            self.target_reputation *= 5 # 次のランクへの壁
            return True
        return False

    def get_current_storage(self):
        return self.ranks[self.current_rank_idx]["storage"]

    def calculate_memory_usage(self):
        usage = 0
        for code in self.installed_codes:
            # 5や9などの重い数字が含まれると容量を食うロジック
            size = 10
            if '5' in code: size += 20
            if '9' in code: size += 25
            if '0' in code: size -= 5
            usage += size
        return usage

def draw_main_ui(stdscr, state, logs):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    
    # --- ステータスエリア ---
    rank_info = state.ranks[state.current_rank_idx]
    stdscr.addstr(1, 2, f"【 階級: {rank_info['name']} 】", curses.A_BOLD)
    stdscr.addstr(2, 2, f"  次期昇進まで: {state.reputation} / {state.target_reputation} REP")
    
    # ストレージゲージ
    usage = state.calculate_memory_usage()
    cap = rank_info['storage']
    bar_len = 20
    filled = int((usage / cap) * bar_len) if cap > 0 else 0
    stdscr.addstr(4, 2, f"  MEMORY: [{'#'*filled}{'-'*(bar_len-filled)}] {usage}/{cap} MB")
    
    # --- インストール済みHコード ---
    stdscr.addstr(6, 2, "--- CURRENT H-CODES ---")
    for i, code in enumerate(state.installed_codes):
        stdscr.addstr(7 + i, 4, f"SLOT {i+1}: [ {code} ]")

    # --- ログエリア ---
    stdscr.addstr(12, 0, "-" * w)
    for i, log in enumerate(logs[-5:]):
        stdscr.addstr(13 + i, 2, f"> {log}")

    stdscr.addstr(20, 2, "[S]: 社交モード(Rep稼ぎ)  [G]: ガレージ(換装)  [Q]: 終了")
    stdscr.refresh()

def main(stdscr):
    curses.curs_set(0)
    state = GameState()
    logs = ["システムオンライン。階級: 下層市民からスタートします。"]
    
    while True:
        draw_main_ui(stdscr, state, logs)
        key = stdscr.getch()
        
        if key == ord('q'):
            break
        
        elif key == ord('s'):
            # 社交シミュレーション（簡易版）
            logs.append("パブで接待を行い、評価(REP)を獲得した。")
            if state.add_reputation(40):
                logs.append("！！【昇進】階級が上がり、ストレージが解放された！")
            time.sleep(0.1)
            
        elif key == ord('g'):
            # ガレージシミュレーション
            logs.append("ガレージ起動。新しいHコード(505)の同期を試みる...")
            new_code = "505"
            # 容量チェック
            temp_codes = state.installed_codes + [new_code]
            # 一時的に計算
            current_usage = state.calculate_memory_usage()
            new_code_size = 30 # 5が含まれるので重い
            
            if current_usage + new_code_size <= state.get_current_storage():
                state.installed_codes.append(new_code)
                logs.append(f"同期成功: {new_code} をインストールした。")
            else:
                logs.append("警告: メモリ不足！ 昇進してストレージを増設してください。")
            time.sleep(0.1)

if __name__ == "__main__":
    curses.wrapper(main)
