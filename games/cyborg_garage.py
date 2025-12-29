#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import curses
import os
import sys
import json

try:
    from core_engine import BaseArchive
except ImportError:
    sys.path.append("/home/hirosi/my_gemini_project")
    from core_engine import BaseArchive

PROSTHETIC_BODIES = {
    "TYPE-A_BASIC": {
        "name": "汎用基本義体 Type-A", "cost": 0, "base_hp_bonus": 100, "attack_buff_bonus": 0, "rank_level": 1,
        "description": "標準的な基本義体。バランスが良い。", "id": "TYPE-A_BASIC"
    },
    "TYPE-B_BRAWLER": {
        "name": "格闘強化義体 Type-B", "cost": 200, "base_hp_bonus": 150, "attack_buff_bonus": 10, "rank_level": 2,
        "description": "近接戦闘に特化した義体。HPと攻撃力が増加。", "id": "TYPE-B_BRAWLER"
    },
    "TYPE-C_SNIPER": {
        "name": "精密狙撃義体 Type-C", "cost": 300, "base_hp_bonus": 120, "attack_buff_bonus": 15, "rank_level": 3,
        "description": "狙撃に最適な精密射撃用義体。攻撃力が高め。", "id": "TYPE-C_SNIPER"
    },
    "TYPE-D_SOCIAL": {
        "name": "社交特化義体 Type-D", "cost": 150, "base_hp_bonus": 80, "attack_buff_bonus": 0, "rank_level": 2,
        "description": "社交活動をサポートする義体。交渉を有利に運ぶ。", "id": "TYPE-D_SOCIAL"
    },
    "TYPE-E_TRADE": {
        "name": "貿易支援義体 Type-E", "cost": 180, "base_hp_bonus": 90, "attack_buff_bonus": 5, "rank_level": 2,
        "description": "貿易での積載量と交渉力を向上させる義体。", "id": "TYPE-E_TRADE"
    }
}

ROBOT_UNITS = {
    "SENTINEL": {
        "name": "最終兵器センチネル", "cost": 1000, "base_hp_bonus": 500, "attack_buff_bonus": 50, "rank_level": 5,
        "description": "全ての義体を超越した究極の戦闘ロボット。", "id": "SENTINEL"
    },
    "PROMINENCE": {
        "name": "超戦略プロミネンス", "cost": 1200, "base_hp_bonus": 400, "attack_buff_bonus": 60, "rank_level": 5,
        "description": "戦況を完全に覆す戦略型ロボット。特殊能力を持つ。", "id": "PROMINENCE"
    }
}


class CyborgGarage(BaseArchive):
    def __init__(self, stdscr, profile):
        super().__init__(stdscr, profile)
        self.selection = 0
        self.prosthetic_bodies = PROSTHETIC_BODIES
        self.robot_units = ROBOT_UNITS
        
        # Ensure player profile has owned_prosthetics and an equipped prosthetic
        if "owned_prosthetics" not in self.profile or not isinstance(self.profile["owned_prosthetics"], list):
            self.profile["owned_prosthetics"] = ["TYPE-A_BASIC"]
        
        if "equipped_prosthetic_id" not in self.profile or self.profile["equipped_prosthetic_id"] not in self.prosthetic_bodies:
            self.profile["equipped_prosthetic_id"] = "TYPE-A_BASIC"
        
        # Ensure equipped prosthetic is actually owned
        if self.profile["equipped_prosthetic_id"] not in self.profile["owned_prosthetics"]:
            # If not owned, equip the first owned one, or default to BASIC if owned list is empty
            self.profile["equipped_prosthetic_id"] = self.profile["owned_prosthetics"][0] if self.profile["owned_prosthetics"] else "TYPE-A_BASIC"
            # And if still not in owned_prosthetics, add it (edge case for corrupted profiles)
            if self.profile["equipped_prosthetic_id"] not in self.profile["owned_prosthetics"]:
                self.profile["owned_prosthetics"].append(self.profile["equipped_prosthetic_id"])

        # Initialize owned_robots
        if "owned_robots" not in self.profile or not isinstance(self.profile["owned_robots"], list):
            self.profile["owned_robots"] = []
        
        if "equipped_robot_id" not in self.profile or self.profile["equipped_robot_id"] not in self.robot_units:
             self.profile["equipped_robot_id"] = None # No robot equipped by default


        self.update_profile_from_equipment() # Apply all equipped item stats to profile

        self.menu_items = self._generate_menu_items()
        # Track counts for menu section rendering
        self.num_equippable_prosthetics = 0
        self.num_purchasable_prosthetics = 0
        self.num_equippable_robots = 0
        self.num_purchasable_robots = 0


    def _generate_menu_items(self):
        menu_items_list = [] # List of (type, text, item_id, item_type_str)

        # Section for Owned (Equippable) Prosthetics
        for body_id in self.profile["owned_prosthetics"]:
            body_data = self.prosthetic_bodies.get(body_id)
            if body_data:
                status = "装備中" if body_id == self.profile["equipped_prosthetic_id"] else "装備"
                menu_items_list.append(("equip", f"{status}: {body_data['name']}", body_id, "prosthetic"))
        self.num_equippable_prosthetics = len(self.profile["owned_prosthetics"])

        # Section for Purchasable Prosthetics
        purchasable_prosthetics = []
        for body_id, body_data in self.prosthetic_bodies.items():
            if body_id not in self.profile["owned_prosthetics"]:
                purchasable_prosthetics.append(("purchase", f"購入: {body_data['name']} ({body_data['cost']} GP)", body_id, "prosthetic"))
        self.num_purchasable_prosthetics = len(purchasable_prosthetics)
        menu_items_list.extend(purchasable_prosthetics)

        # Section for Robot Units (available only after all prosthetics are owned)
        all_prosthetics_owned = (len(self.profile["owned_prosthetics"]) == len(self.prosthetic_bodies))
        
        if all_prosthetics_owned:
            # Equippable Robots
            for robot_id in self.profile["owned_robots"]:
                robot_data = self.robot_units.get(robot_id)
                if robot_data:
                    status = "装備中" if robot_id == self.profile["equipped_robot_id"] else "装備"
                    menu_items_list.append(("equip", f"{status}: {robot_data['name']}", robot_id, "robot"))
            self.num_equippable_robots = len(self.profile["owned_robots"])

            # Purchasable Robots
            purchasable_robots = []
            for robot_id, robot_data in self.robot_units.items():
                if robot_id not in self.profile["owned_robots"]:
                    purchasable_robots.append(("purchase", f"購入: {robot_data['name']} ({robot_data['cost']} GP)", robot_id, "robot"))
            self.num_purchasable_robots = len(purchasable_robots)
            menu_items_list.extend(purchasable_robots)


        menu_items_list.append(("return", "メインメニューに戻る", None, None))
        return menu_items_list


    def update_profile_from_equipment(self):
        # Reset base stats from profile (important for when unequipping robot)
        self.profile["base_hp"] = 0
        self.profile["attack_buff"] = 0
        self.profile["divine_level"] = 0 # Default if nothing equipped

        # Apply equipped prosthetic stats
        if self.profile["equipped_prosthetic_id"] and self.profile["equipped_prosthetic_id"] in self.prosthetic_bodies:
            equipped_body = self.prosthetic_bodies[self.profile["equipped_prosthetic_id"]]
            self.profile["base_hp"] += equipped_body["base_hp_bonus"]
            self.profile["attack_buff"] += equipped_body["attack_buff_bonus"]
            self.profile["divine_level"] = equipped_body["rank_level"]
            self.profile["name_current_prosthetic"] = equipped_body["name"]
        else:
            # Fallback for when no prosthetic is equipped (shouldn't happen with default BASIC)
            self.profile["base_hp"] += 100 # Basic HP
            self.profile["divine_level"] = 1
            self.profile["name_current_prosthetic"] = "なし"
        
        # Apply equipped robot stats (if any)
        if self.profile["equipped_robot_id"] and self.profile["equipped_robot_id"] in self.robot_units:
            equipped_robot = self.robot_units[self.profile["equipped_robot_id"]]
            self.profile["base_hp"] += equipped_robot["base_hp_bonus"]
            self.profile["attack_buff"] += equipped_robot["attack_buff_bonus"]
            # Robot might have its own rank logic or override prosthetic rank
            self.profile["divine_level"] = max(self.profile["divine_level"], equipped_robot["rank_level"])
            self.profile["name_current_robot"] = equipped_robot["name"]
        else:
            self.profile["name_current_robot"] = "なし"


    def draw_ui(self):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        
        self.stdscr.addstr(1, 2, "--- CYBORG GARAGE ---", curses.A_BOLD)
        self.stdscr.addstr(3, 2, f"現在のポイント: {self.profile.get('garage_points', 0)} GP")
        
        # Display Equipped Prosthetic
        equipped_body = self.prosthetic_bodies.get(self.profile.get("equipped_prosthetic_id"))
        if equipped_body:
            self.stdscr.addstr(5, 2, f"装備義体: {equipped_body['name']} (ランク: {equipped_body['rank_level']})", curses.A_BOLD)
            self.stdscr.addstr(6, 4, f"HP: {equipped_body['base_hp_bonus']}, 攻撃: {equipped_body['attack_buff_bonus']}")
            self.stdscr.addstr(7, 4, f"説明: {equipped_body['description']}")
        else:
            self.stdscr.addstr(5, 2, "装備義体: なし", curses.A_BOLD)

        # Display Equipped Robot
        equipped_robot = self.robot_units.get(self.profile.get("equipped_robot_id"))
        if equipped_robot:
            self.stdscr.addstr(9, 2, f"装備ロボット: {equipped_robot['name']} (ランク: {equipped_robot['rank_level']})", curses.A_BOLD)
            self.stdscr.addstr(10, 4, f"HP: {equipped_robot['base_hp_bonus']}, 攻撃: {equipped_robot['attack_buff_bonus']}")
            self.stdscr.addstr(11, 4, f"説明: {equipped_robot['description']}")
        else:
            self.stdscr.addstr(9, 2, "装備ロボット: なし", curses.A_BOLD)


        y_offset = 13 # Starting Y for menu items

        # Display Owned/Equippable Prosthetics
        if self.num_equippable_prosthetics > 0:
            self.stdscr.addstr(y_offset, 2, "--- 所有義体 (装備/換装) ---", curses.A_BOLD)
            for i in range(self.num_equippable_prosthetics):
                item_type, item_text, _, _ = self.menu_items[i]
                style = curses.A_REVERSE if i == self.selection else curses.A_NORMAL
                self.safe_addstr(y_offset + 2 + i, 4, f"> {item_text}", style)
            y_offset += self.num_equippable_prosthetics + 2

        # Display Purchasable Prosthetics
        if self.num_purchasable_prosthetics > 0:
            self.stdscr.addstr(y_offset, 2, "--- 未所有義体 (購入) ---", curses.A_BOLD)
            for i in range(self.num_purchasable_prosthetics):
                item_type, item_text, _, _ = self.menu_items[self.num_equippable_prosthetics + i]
                style = curses.A_REVERSE if (self.num_equippable_prosthetics + i) == self.selection else curses.A_NORMAL
                self.safe_addstr(y_offset + 2 + i, 4, f"> {item_text}", style)
            y_offset += self.num_purchasable_prosthetics + 2
        
        # Display Robot Units
        robot_menu_start_index = self.num_equippable_prosthetics + self.num_purchasable_prosthetics
        total_robot_items = self.num_equippable_robots + self.num_purchasable_robots
        if total_robot_items > 0:
            self.stdscr.addstr(y_offset, 2, "--- ロボットユニット ---", curses.A_BOLD)
            for i in range(total_robot_items):
                item_type, item_text, _, _ = self.menu_items[robot_menu_start_index + i]
                style = curses.A_REVERSE if (robot_menu_start_index + i) == self.selection else curses.A_NORMAL
                self.safe_addstr(y_offset + 2 + i, 4, f"> {item_text}", style)
            y_offset += total_robot_items + 2

        # Return to main menu option
        return_index = self.num_equippable_prosthetics + self.num_purchasable_prosthetics + total_robot_items
        item_type, item_text, _, _ = self.menu_items[return_index]
        style = curses.A_REVERSE if return_index == self.selection else curses.A_NORMAL
        self.safe_addstr(y_offset, 4, f"> {item_text}", style)

        self.stdscr.addstr(y_offset + 2, 2, "[ENTER] 決定 / [UP/DOWN] 選択")
        self.refresh_logs()
        self.stdscr.refresh()

    def play(self):
        # Apply initial prosthetic stats to player profile
        self.update_profile_from_equipment()
        self.menu_items = self._generate_menu_items() # Initial menu generation

        while True:
            self.draw_ui()
            key = self.stdscr.getch()
            
            if key == curses.KEY_UP:
                self.selection = (self.selection - 1 + len(self.menu_items)) % len(self.menu_items)
            elif key == curses.KEY_DOWN:
                self.selection = (self.selection + 1) % len(self.menu_items)
            elif key == (10 if os.name != 'nt' else 13) or key == curses.KEY_ENTER:
                item_data = self.menu_items[self.selection]
                item_type = item_data[0]
                item_id = item_data[2] # body_id or robot_id
                item_category = item_data[3] # "prosthetic" or "robot"

                if item_type == "return":
                    break
                elif item_type == "purchase":
                    if item_category == "prosthetic":
                        self._process_purchase_prosthetic(item_id)
                    elif item_category == "robot":
                        self._process_purchase_robot(item_id)
                elif item_type == "equip":
                    if item_category == "prosthetic":
                        self._process_equip_prosthetic(item_id)
                    elif item_category == "robot":
                        self._process_equip_robot(item_id)
        
        return self.profile

    def _process_purchase_prosthetic(self, body_id):
        body_data = self.prosthetic_bodies[body_id]
        cost = body_data["cost"]
        current_gp = self.profile.get('garage_points', 0)

        if current_gp >= cost:
            self.profile['garage_points'] -= cost
            self.profile["owned_prosthetics"].append(body_id)
            self.profile["equipped_prosthetic_id"] = body_id # Immediately equip
            self.update_profile_from_equipment() # Apply new prosthetic stats
            self.logs.append(f"{body_data['name']} を購入し装備しました！残GP: {self.profile['garage_points']}")
            self.menu_items = self._generate_menu_items() # Regenerate menu after purchase
            self.selection = 0 # Reset selection
        else:
            self.logs.append(f"GPが不足しています。購入には {cost} GP 必要です。")

    def _process_equip_prosthetic(self, body_id):
        if body_id == self.profile["equipped_prosthetic_id"]:
            self.logs.append("その義体は既に装備中です。")
            return
        
        self.profile["equipped_prosthetic_id"] = body_id
        self.update_profile_from_equipment() # Apply new prosthetic stats
        self.logs.append(f"{self.prosthetic_bodies[body_id]['name']} を装備しました！")
        self.menu_items = self._generate_menu_items() # Regenerate menu to update "Equipped" status
        self.selection = 0 # Reset selection

    def _process_purchase_robot(self, robot_id):
        # Check if all prosthetics are owned before allowing robot purchase
        if len(self.profile["owned_prosthetics"]) < len(self.prosthetic_bodies):
            self.logs.append("全ての義体を購入しないとロボットは購入できません。")
            return

        robot_data = self.robot_units[robot_id]
        cost = robot_data["cost"]
        current_gp = self.profile.get('garage_points', 0)

        if current_gp >= cost:
            self.profile['garage_points'] -= cost
            self.profile["owned_robots"].append(robot_id)
            self.profile["equipped_robot_id"] = robot_id # Immediately equip
            self.update_profile_from_equipment() # Apply new robot stats
            self.logs.append(f"{robot_data['name']} を購入し装備しました！残GP: {self.profile['garage_points']}")
            self.menu_items = self._generate_menu_items() # Regenerate menu after purchase
            self.selection = 0 # Reset selection

            # --- NEW LOGIC: Unlock Next War Scenario if Sentinel is purchased ---
            if robot_id == "SENTINEL":
                self.profile["scenario_unlocked_next_war"] = True
                self.logs.append("ネクスト戦記シナリオがアンロックされました！")
            # --- END NEW LOGIC ---

        else:
            self.logs.append(f"GPが不足しています。購入には {cost} GP 必要です。")

    def _process_equip_robot(self, robot_id):
        if robot_id == self.profile["equipped_robot_id"]:
            self.logs.append("そのロボットは既に装備中です。")
            return
        
        self.profile["equipped_robot_id"] = robot_id
        self.update_profile_from_equipment() # Apply new robot stats
        self.logs.append(f"{self.robot_units[robot_id]['name']} を装備しました！")
        self.menu_items = self._generate_menu_items() # Regenerate menu to update "Equipped" status
        self.selection = 0 # Reset selection