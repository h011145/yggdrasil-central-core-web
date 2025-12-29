#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import curses
import time
import random
import json
import os
import sys

class AdvancedTradeGame:
    def __init__(self, stdscr, profile):
        self.stdscr = stdscr
        self.profile = profile
        self.logs = ["市場を調査中..."]
        self.cities = {
            "CityA": {"goods": {"Spice": {"buy": 10, "sell": 15}, "Textile": {"buy": 5, "sell": 8}}},
            "CityB": {"goods": {"Spice": {"buy": 12, "sell": 18}, "Textile": {"buy": 7, "sell": 10}}},
        }
        self.current_city = "CityA"
        self.inventory = {}
        self.money = self.profile.get("garage_points", 100) # Use garage_points as starting money

    def safe_addstr(self, y, x, text, style=curses.A_NORMAL):
        h, w = self.stdscr.getmaxyx()
        if 0 <= y < h and 0 <= x < w:
            self.stdscr.addstr(y, x, str(text)[:w-x-1], style)

    def draw_ui(self, sel, mode):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        self.safe_addstr(1, 2, "--- TRADE ARCHIVE ---", curses.A_BOLD)
        self.safe_addstr(3, 2, f"Location: {self.current_city}")
        self.safe_addstr(4, 2, f"Money: {int(self.money)} GP")
        
        self.safe_addstr(6, 2, "--- Inventory ---")
        if not self.inventory:
            self.safe_addstr(7, 4, "Empty")
        else:
            for i, (item, qty) in enumerate(self.inventory.items()):
                self.safe_addstr(7 + i, 4, f"{item}: {qty}")

        y_offset = 10
        self.safe_addstr(y_offset, 2, "--- Market Prices ---")
        current_market = self.cities[self.current_city]["goods"]
        goods_list = list(current_market.keys())

        if mode == "buy":
            for i, good in enumerate(goods_list):
                style = curses.A_REVERSE if i == sel else curses.A_NORMAL
                self.safe_addstr(y_offset + 2 + i, 4, f"{good}: Buy {current_market[good]['buy']} GP", style)
            self.safe_addstr(y_offset + 2 + len(goods_list), 4, "Travel", curses.A_NORMAL if sel != len(goods_list) else curses.A_REVERSE)
            self.safe_addstr(y_offset + 3 + len(goods_list), 4, "Exit", curses.A_NORMAL if sel != len(goods_list) + 1 else curses.A_REVERSE)
        elif mode == "sell":
            items_in_inv = list(self.inventory.keys())
            for i, item in enumerate(items_in_inv):
                style = curses.A_REVERSE if i == sel else curses.A_NORMAL
                self.safe_addstr(y_offset + 2 + i, 4, f"{item} (Qty: {self.inventory[item]}): Sell {current_market[item]['sell']} GP", style)
            self.safe_addstr(y_offset + 2 + len(items_in_inv), 4, "Travel", curses.A_NORMAL if sel != len(items_in_inv) else curses.A_REVERSE)
            self.safe_addstr(y_offset + 3 + len(items_in_inv), 4, "Exit", curses.A_NORMAL if sel != len(items_in_inv) + 1 else curses.A_REVERSE)
        else: # Travel mode
            other_cities = [city for city in self.cities if city != self.current_city]
            for i, city in enumerate(other_cities):
                style = curses.A_REVERSE if i == sel else curses.A_NORMAL
                self.safe_addstr(y_offset + 2 + i, 4, f"Go to {city}", style)
            self.safe_addstr(y_offset + 2 + len(other_cities), 4, "Exit", curses.A_NORMAL if sel != len(other_cities) else curses.A_REVERSE)


        # Logs
        for i, m in enumerate(self.logs[-5:]):
            self.safe_addstr(h - 6 + i, 2, f"> {m}")

        self.stdscr.refresh()

    def play(self):
        self.logs.append(f"貿易ゲーム開始！所持金: {int(self.money)} GP")
        
        while True:
            # Main Trade Loop
            action_menu = ["Buy", "Sell", "Travel", "Exit"]
            sel = 0
            while True:
                self.draw_ui(sel, "main_menu")
                for i, action in enumerate(action_menu):
                    style = curses.A_REVERSE if i == sel else curses.A_NORMAL
                    self.safe_addstr(16 + i, 4, f"> {action}", style)
                
                key = self.stdscr.getch()
                if key == curses.KEY_UP: sel = (sel - 1) % len(action_menu)
                elif key == curses.KEY_DOWN: sel = (sel + 1) % len(action_menu)
                elif key == ord('\n'): break

            if action_menu[sel] == "Exit":
                self.logs.append("貿易ゲーム終了。")
                break
            elif action_menu[sel] == "Travel":
                other_cities = [city for city in self.cities if city != self.current_city]
                if not other_cities:
                    self.logs.append("移動できる都市がありません！")
                    continue
                
                travel_sel = 0
                while True:
                    self.draw_ui(travel_sel, "travel")
                    for i, city in enumerate(other_cities):
                        style = curses.A_REVERSE if i == travel_sel else curses.A_NORMAL
                        self.safe_addstr(18 + i, 4, f"> Go to {city}", style)
                    self.safe_addstr(18 + len(other_cities), 4, "> Back", curses.A_NORMAL if travel_sel != len(other_cities) else curses.A_REVERSE)

                    key = self.stdscr.getch()
                    if key == curses.KEY_UP: travel_sel = (travel_sel - 1) % (len(other_cities) + 1)
                    elif key == curses.KEY_DOWN: travel_sel = (travel_sel + 1) % (len(other_cities) + 1)
                    elif key == ord('\n'): break
                
                if travel_sel == len(other_cities): # Back
                    continue
                else:
                    self.current_city = other_cities[travel_sel]
                    self.logs.append(f"{self.current_city}へ移動しました。")
            
            elif action_menu[sel] == "Buy":
                current_market = self.cities[self.current_city]["goods"]
                goods_list = list(current_market.keys())
                if not goods_list:
                    self.logs.append("購入できる商品がありません。")
                    continue

                buy_sel = 0
                while True:
                    self.draw_ui(buy_sel, "buy")
                    key = self.stdscr.getch()
                    if key == curses.KEY_UP: buy_sel = (buy_sel - 1) % (len(goods_list) + 2)
                    elif key == curses.KEY_DOWN: buy_sel = (buy_sel + 1) % (len(goods_list) + 2)
                    elif key == ord('\n'): break
                
                if buy_sel == len(goods_list): # Travel from buy menu
                    other_cities = [city for city in self.cities if city != self.current_city]
                    if not other_cities:
                        self.logs.append("移動できる都市がありません！")
                        continue
                    
                    travel_sub_sel = 0
                    while True:
                        self.draw_ui(travel_sub_sel, "travel")
                        for i, city in enumerate(other_cities):
                            style = curses.A_REVERSE if i == travel_sub_sel else curses.A_NORMAL
                            self.safe_addstr(18 + i, 4, f"> Go to {city}", style)
                        self.safe_addstr(18 + len(other_cities), 4, "> Back", curses.A_NORMAL if travel_sub_sel != len(other_cities) else curses.A_REVERSE)

                        key = self.stdscr.getch()
                        if key == curses.KEY_UP: travel_sub_sel = (travel_sub_sel - 1) % (len(other_cities) + 1)
                        elif key == curses.KEY_DOWN: travel_sub_sel = (travel_sub_sel + 1) % (len(other_cities) + 1)
                        elif key == ord('\n'): break
                    
                    if travel_sub_sel == len(other_cities): # Back to buy menu
                        continue
                    else:
                        self.current_city = other_cities[travel_sub_sel]
                        self.logs.append(f"{self.current_city}へ移動しました。")
                        continue # Restart buy loop in new city

                elif buy_sel == len(goods_list) + 1: # Exit from buy menu
                    self.logs.append("貿易ゲーム終了。")
                    break
                else:
                    item_to_buy = goods_list[buy_sel]
                    price = current_market[item_to_buy]["buy"]
                    if self.money >= price:
                        self.money -= price
                        self.inventory[item_to_buy] = self.inventory.get(item_to_buy, 0) + 1
                        self.logs.append(f"{item_to_buy}を{price} GPで購入しました。")
                    else:
                        self.logs.append("所持金が足りません！")

            elif action_menu[sel] == "Sell":
                current_market = self.cities[self.current_city]["goods"]
                items_in_inv = list(self.inventory.keys())
                if not items_in_inv:
                    self.logs.append("売却できる商品がありません。")
                    continue

                sell_sel = 0
                while True:
                    self.draw_ui(sell_sel, "sell")
                    key = self.stdscr.getch()
                    if key == curses.KEY_UP: sell_sel = (sell_sel - 1) % (len(items_in_inv) + 2)
                    elif key == curses.KEY_DOWN: sell_sel = (sell_sel + 1) % (len(items_in_inv) + 2)
                    elif key == ord('\n'): break
                
                if sell_sel == len(items_in_inv): # Travel from sell menu
                    other_cities = [city for city in self.cities if city != self.current_city]
                    if not other_cities:
                        self.logs.append("移動できる都市がありません！")
                        continue
                    
                    travel_sub_sel = 0
                    while True:
                        self.draw_ui(travel_sub_sel, "travel")
                        for i, city in enumerate(other_cities):
                            style = curses.A_REVERSE if i == travel_sub_sel else curses.A_NORMAL
                            self.safe_addstr(18 + i, 4, f"> Go to {city}", style)
                        self.safe_addstr(18 + len(other_cities), 4, "> Back", curses.A_NORMAL if travel_sub_sel != len(other_cities) else curses.A_REVERSE)

                        key = self.stdscr.getch()
                        if key == curses.KEY_UP: travel_sub_sel = (travel_sub_sel - 1) % (len(other_cities) + 1)
                        elif key == curses.KEY_DOWN: travel_sub_sel = (travel_sub_sel + 1) % (len(other_cities) + 1)
                        elif key == ord('\n'): break
                    
                    if travel_sub_sel == len(other_cities): # Back to sell menu
                        continue
                    else:
                        self.current_city = other_cities[travel_sub_sel]
                        self.logs.append(f"{self.current_city}へ移動しました。")
                        continue # Restart sell loop in new city

                elif sell_sel == len(items_in_inv) + 1: # Exit from sell menu
                    self.logs.append("貿易ゲーム終了。")
                    break
                else:
                    item_to_sell = items_in_inv[sell_sel]
                    price = current_market[item_to_sell]["sell"]
                    if self.inventory.get(item_to_sell, 0) > 0:
                        self.money += price
                        self.inventory[item_to_sell] -= 1
                        if self.inventory[item_to_sell] == 0:
                            del self.inventory[item_to_sell]
                        self.logs.append(f"{item_to_sell}を{price} GPで売却しました。")
                    else:
                        self.logs.append(f"{item_to_sell}を持っていません！")

        final_points = self.money - self.profile.get("garage_points", 100)
        return {"points_earned": final_points, "victory": final_points > 0}
