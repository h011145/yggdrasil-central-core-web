#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import curses
import time
import random
import json
import os
import sys

GAME_GRID_SIZE = 10 # 10x10 grid for the game area

class AdvancedSnipeGame:
    def __init__(self, stdscr, profile):
        self.stdscr = stdscr
        self.profile = profile
        self.logs = ["狙撃ミッション開始！"]
        self.score = 0
        self.shots_fired = 0
        self.max_shots = 5
        self.target_pos_grid = self._generate_random_pos_grid() # Target position within grid
        self.crosshair_pos_grid = (GAME_GRID_SIZE // 2, GAME_GRID_SIZE // 2) # Crosshair starts at center of grid
        self.hit_radius = 0 # Exact hit for 10x10 grid

    def _generate_random_pos_grid(self):
        return random.randint(1, GAME_GRID_SIZE), random.randint(1, GAME_GRID_SIZE)

    def _set_crosshair_pos_grid(self, new_y_grid, new_x_grid):
        # Clamp coordinates to grid boundaries (1 to GAME_GRID_SIZE)
        clamped_y = max(1, min(GAME_GRID_SIZE, new_y_grid))
        clamped_x = max(1, min(GAME_GRID_SIZE, new_x_grid))
        self.crosshair_pos_grid = (clamped_y, clamped_x)

    def draw_ui(self, input_prompt, input_buffer=""):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        
        # Header
        self.stdscr.addstr(1, 2, "--- SNIPE ARCHIVE ---", curses.A_BOLD)
        self.stdscr.addstr(3, 2, f"スコア: {self.score}  残り弾数: {self.max_shots - self.shots_fired}")

        # Draw Grid
        grid_offset_y = 5
        grid_offset_x = 5 # Adjusted for grid numbers

        # X-axis numbers
        for i in range(1, GAME_GRID_SIZE + 1):
            self.stdscr.addstr(grid_offset_y - 1, grid_offset_x + (i*2), str(i).center(2))
        
        # Y-axis numbers and grid lines
        for y in range(1, GAME_GRID_SIZE + 1):
            self.stdscr.addstr(grid_offset_y + y, grid_offset_x - 3, str(y).ljust(2)) # Y-axis label
            for x in range(1, GAME_GRID_SIZE + 1):
                char = "."
                style = curses.A_NORMAL

                if (y, x) == self.target_pos_grid:
                    char = "X"
                    style |= curses.color_pair(3) # Red target
                
                if (y, x) == self.crosshair_pos_grid:
                    char = "+"
                    style |= curses.color_pair(2) # Green crosshair
                
                self.stdscr.addstr(grid_offset_y + y, grid_offset_x + (x*2), char, style) # x*2 for spacing

        # Logs
        log_start_y = grid_offset_y + GAME_GRID_SIZE + 2
        self.stdscr.addstr(log_start_y, 2, "--- ログ ---")
        for i, m in enumerate(self.logs[-5:]):
            self.stdscr.addstr(log_start_y + 1 + i, 2, f"> {m}")

        # Input Prompt
        prompt_y = h - 4
        self.stdscr.addstr(prompt_y, 2, input_prompt + input_buffer[:w-len(input_prompt)-4])

        self.stdscr.refresh()

    def _set_crosshair_pos_grid(self, new_y_grid, new_x_grid):
        # Clamp coordinates to grid boundaries (1 to GAME_GRID_SIZE)
        clamped_y = max(1, min(GAME_GRID_SIZE, new_y_grid))
        clamped_x = max(1, min(GAME_GRID_SIZE, new_x_grid))
        self.crosshair_pos_grid = (clamped_y, clamped_x)


    def _check_hit(self):
        # Calculate distance
        dist_y = abs(self.crosshair_pos_grid[0] - self.target_pos_grid[0])
        dist_x = abs(self.crosshair_pos_grid[1] - self.target_pos_grid[1])
        return dist_y <= self.hit_radius and dist_x <= self.hit_radius

    def play(self):
        # Colors
        try:
            curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK) # Crosshair
            curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)   # Target
        except: pass

        # Input setup
        self.stdscr.nodelay(False) # Blocking input
        self.stdscr.keypad(True)  # Enable special keys
        curses.echo() # Echo user input

        # Game State
        input_state = "ASK_X" # ASK_X, ASK_Y, CONFIRM_SHOOT, GAME_OVER
        current_input_buffer = ""
        x_input = -1
        y_input = -1

        start_time = time.time()
        game_duration = 60 # seconds

        while self.shots_fired < self.max_shots and (time.time() - start_time) < game_duration:
            prompt = ""
            if input_state == "ASK_X":
                prompt = f"X座標を入力してください (1-{GAME_GRID_SIZE}): "
            elif input_state == "ASK_Y":
                prompt = f"Y座標を入力してください (1-{GAME_GRID_SIZE}): "
            elif input_state == "CONFIRM_SHOOT":
                prompt = f"({x_input}, {y_input}) に照準。S(撃つ) Q(キャンセル): "
            
            self.draw_ui(prompt, current_input_buffer)
            
            key = self.stdscr.getch()

            if key in [curses.KEY_ENTER, ord('\n'), ord('\r')]:
                if input_state == "ASK_X":
                    try:
                        val = int(current_input_buffer)
                        if 1 <= val <= GAME_GRID_SIZE:
                            x_input = val
                            input_state = "ASK_Y"
                            self.logs.append(f"X座標: {x_input}")
                        else:
                            self.logs.append(f"Xは1から{GAME_GRID_SIZE}の範囲で入力してください。")
                        current_input_buffer = ""
                    except ValueError:
                        self.logs.append("無効な入力です。数値を入力してください。")
                        current_input_buffer = ""
                elif input_state == "ASK_Y":
                    try:
                        val = int(current_input_buffer)
                        if 1 <= val <= GAME_GRID_SIZE:
                            y_input = val
                            self._set_crosshair_pos_grid(y_input, x_input) # Update crosshair
                            input_state = "CONFIRM_SHOOT"
                            self.logs.append(f"Y座標: {y_input}")
                        else:
                            self.logs.append(f"Yは1から{GAME_GRID_SIZE}の範囲で入力してください。")
                        current_input_buffer = ""
                    except ValueError:
                        self.logs.append("無効な入力です。数値を入力してください。")
                        current_input_buffer = ""
                elif input_state == "CONFIRM_SHOOT":
                    action = current_input_buffer.strip().upper()
                    if action == "S": # Shoot
                        self.shots_fired += 1
                        if self._check_hit():
                            self.score += 100
                            self.logs.append("命中！ターゲットを撃破！ (+100 スコア)")
                            self.target_pos_grid = self._generate_random_pos_grid() # New target
                            # self.crosshair_pos_grid stays for feedback
                        else:
                            self.logs.append("外した... (-10 スコア)")
                            self.score = max(0, self.score - 10) # Penalty for missing
                        input_state = "ASK_X" # Reset for next shot
                        x_input = -1
                        y_input = -1
                        current_input_buffer = ""
                    elif action == "Q": # Cancel/Quit
                        self.logs.append("射撃キャンセル。")
                        input_state = "ASK_X" # Back to input
                        x_input = -1
                        y_input = -1
                        current_input_buffer = ""
                    else:
                        self.logs.append("無効なコマンドです。S または Q を入力してください。")
                        current_input_buffer = ""
            elif key == curses.KEY_BACKSPACE or key == 127: # Handle backspace
                current_input_buffer = current_input_buffer[:-1]
            elif 32 <= key <= 126: # Regular characters
                current_input_buffer += chr(key)
            
            time.sleep(0.05) # Small delay to prevent CPU hogging

        curses.noecho() # Turn off echo
        self.stdscr.nodelay(False) # Revert getch to blocking
        self.stdscr.keypad(False)   # Disable special keys

        final_garage_points_earned = self.score # For simplicity, score directly maps to GP

        h, w = self.stdscr.getmaxyx() # Get screen dimensions before printing final messages
        self.draw_ui("", "") # Final draw without input prompt
        if self.shots_fired >= self.max_shots:
            self.stdscr.addstr(h - 8, 2, "【ミッション終了】全ての弾を撃ち尽くした！", curses.A_BOLD)
        elif (time.time() - start_time) >= game_duration:
            self.stdscr.addstr(h - 8, 2, "【ミッション終了】時間切れ！", curses.A_BOLD)
        else:
            self.stdscr.addstr(h - 8, 2, "【ミッション終了】", curses.A_BOLD)
        self.stdscr.addstr(h - 7, 2, f"最終スコア: {self.score} / 獲得GP: {final_garage_points_earned}", curses.A_BOLD)
        self.stdscr.getch() # Wait for user input

        return {"points_earned": final_garage_points_earned, "victory": self.score > 0}
