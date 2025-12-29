import json
import os
import time
import random

# HCodeEngineは自己完結のため、ここに含めます
class HCodeEngine:
    def __init__(self, dictionary_path):
        self.sequences = {}
        self.current_h_code = None
        self.load_dictionary(dictionary_path)

    def load_dictionary(self, dictionary_path):
        if not os.path.exists(dictionary_path):
            print(f"エラー: 辞書ファイルが見つかりません: {dictionary_path}")
            return
        with open(dictionary_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for seq in data.get('sequences', []):
                self.sequences[seq['id']] = seq
        print(f"Hコード辞書をロードしました。{len(self.sequences)}個のシーケンスを認識。")

    def equip_h_code(self, sequence_id):
        self.current_h_code = self.sequences.get(sequence_id)

    def execute_command(self, command, context):
        if not self.current_h_code: return "結果: Hコードが装備されていません。"
        
        result_str = f"結果({self.current_h_code['name']}): "
        for effect in self.current_h_code.get('effects', []):
            if effect.get('trigger') == context.get('trigger'):
                actions = [f"アクション: {effect['action']}"] if 'action' in effect else []
                if actions: return result_str + " | ".join(actions)
        
        return f"結果({self.current_h_code['name']}): 現在の状況に一致する特別な効果はありません。"

# --- データ構造クラス ---
class BattleEntity:
    def __init__(self, name, hp, traits=None):
        self.name, self.max_hp, self.hp, self.traits = name, hp, hp, traits or []
    def is_alive(self): return self.hp > 0
    def take_damage(self, amount, damage_type="NORMAL_ATTACK"):
        if f"{damage_type}_IMMUNE" in self.traits:
            print(f"  {self.name} は {damage_type} を無効化！ (ダメージ 0)")
            return
        if f"{damage_type}_VULNERABLE" in self.traits:
            amount *= 2
            print(f"  {self.name} の弱点を突いた！")
        self.hp = max(0, self.hp - amount)
        print(f"  {self.name} は {int(amount)} のダメージ！ (残りHP: {int(self.hp)}/{int(self.max_hp)})")
    def update_state(self): pass
    def __str__(self): return f"{self.name} (HP: {int(self.hp)}/{int(self.max_hp)}, 特性: {self.traits})"

class PlayerEntity(BattleEntity):
    def __init__(self, name, hp, traits=None):
        super().__init__(name, hp, traits)
        self.h_code_deck = ["SEQ_DEFAULT_ATTACK", "SEQ_29"]

class EnemyEntity(BattleEntity):
    def __init__(self, name, hp, attack_power, traits=None):
        super().__init__(name, hp, traits)
        self.attack_power, self.is_telegraphing, self.phase_shifted = attack_power, False, False
    def update_state(self):
        if not self.phase_shifted and self.hp < self.max_hp / 2:
            print("\n!! 警告: フェイズシフト・ドロイドの装甲が剥がれ、モードが変化した !!")
            self.traits, self.attack_power, self.phase_shifted = ["ATTACK_UP"], self.attack_power * 1.5, True
            time.sleep(0.5)

# --- プレイヤーコントローラークラス (AIロジック修正版) ---
class PlayerController:
    def get_choice(self, player, enemy, engine): raise NotImplementedError

class InteractivePlayerController(PlayerController):
    def get_choice(self, player, enemy, engine):
        print("\n使用可能なHコード:")
        for i, seq_id in enumerate(player.h_code_deck):
            print(f"{i + 1}: {engine.sequences[seq_id]['name']}")
        while True:
            try:
                choice = int(input("どのHコードを使用しますか？ 番号を入力してください: "))
                if 1 <= choice <= len(player.h_code_deck): return player.h_code_deck[choice - 1]
                else: print("無効な番号。")
            except ValueError: print("数字を入力してください。")

class AIPlayerController(PlayerController):
    def __init__(self, rules):
        self.rules = rules
    def get_choice(self, player, enemy, engine):
        for rule in self.rules:
            condition = rule["condition"]
            action = rule["action"]
            
            is_met = False
            if condition == "enemy.is_telegraphing" and enemy.is_telegraphing: is_met = True
            elif condition == "enemy.phase_shifted" and enemy.phase_shifted: is_met = True
            elif condition == "default": is_met = True
            
            if is_met:
                choice_index = action - 1
                if 0 <= choice_index < len(player.h_code_deck):
                    chosen_seq_id = player.h_code_deck[choice_index]
                    print(f"\nAIロジック '{condition}' に従い、[{engine.sequences[chosen_seq_id]['name']}] を選択。")
                    return chosen_seq_id
        return player.h_code_deck[0]

# --- アクション解決クラス ---
class ActionResolver:
    @staticmethod
    def resolve_and_apply(context, engine, target):
        h_code = engine.current_h_code
        if not h_code: return
        for effect in h_code.get('effects', []):
            if effect.get('trigger') == context.get('trigger'):
                action = effect.get('action', {})
                target.take_damage(action.get('power', 0), action.get('type', 'NORMAL_ATTACK'))

# --- 戦闘シミュレーター司令塔クラス ---
class BattleSimulator:
    def __init__(self, player, enemy, controller):
        self.engine = HCodeEngine(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'h_code_sequence_dictionary.json'))
        self.player, self.enemy, self.controller, self.turn = player, enemy, controller, 1
    def _determine_context(self):
        return {"trigger": "ENEMY_ATTACKING"} if self.enemy.is_telegraphing else {"trigger": "ALWAYS"}
    def _player_turn(self):
        print(f"\n--- ターン {self.turn} (プレイヤーのターン) ---")
        print(f"あなた: {self.player}")
        enemy_state = "力を溜めている" if self.enemy.is_telegraphing else "通常状態"
        print(f"敵: {self.enemy} | 状態: {enemy_state}")
        context = self._determine_context()
        chosen_seq_id = self.controller.get_choice(self.player, self.enemy, self.engine)
        self.engine.equip_h_code(chosen_seq_id)
        result_str = self.engine.execute_command("mo BATTLE_ACTION", context)
        print(f"  {result_str}")
        ActionResolver.resolve_and_apply(context, self.engine, self.enemy)
    def _enemy_turn(self):
        print(f"\n--- ターン {self.turn} (敵のターン) ---")
        if self.enemy.phase_shifted:
            print(f"  {self.enemy.name} の猛攻！")
            self.player.take_damage(self.enemy.attack_power)
            return
        if not self.enemy.is_telegraphing and random.random() < 0.4:
            self.enemy.is_telegraphing = True
            print(f"  {self.enemy.name} は力を溜めている...！")
        else:
            attack_type = "強力な攻撃" if self.enemy.is_telegraphing else "攻撃"
            print(f"  {self.enemy.name} の{attack_type}！")
            self.player.take_damage(self.enemy.attack_power)
            self.enemy.is_telegraphing = False
    def run(self):
        mode_text = "対話型" if isinstance(self.controller, InteractivePlayerController) else "AIロジック実行型"
        print(f"====== {mode_text}シミュレーター開始 ======")
        print(f"{self.player}\n  vs\n{self.enemy}")
        while self.player.is_alive() and self.enemy.is_alive():
            self._player_turn()
            self.player.update_state(); self.enemy.update_state()
            time.sleep(0.5)
            if self.enemy.is_alive(): self._enemy_turn(); time.sleep(0.5)
            self.turn += 1
        print(f"\n====== 戦闘終了 ======\n勝利者: {self.player.name if self.player.is_alive() else self.enemy.name}")

if __name__ == "__main__":
    mode_choice = ''
    controller = None
    while mode_choice not in ['1', '2']:
        mode_choice = input("モードを選択してください:\n1: 対話型モード\n2: AIロジック構築モード\n選択: ")
    if mode_choice == '1':
        controller = InteractivePlayerController()
    elif mode_choice == '2':
        rules = []
        print("\nAIロジックを '条件:行動番号' の形式で入力してください。")
        print("例: enemy.is_telegraphing:2")
        print("条件一覧: enemy.is_telegraphing, enemy.phase_shifted, default")
        print("入力が終わったら、'done'と入力してください。")
        while True:
            rule_str = input(f"ルール {len(rules) + 1}: ").strip()
            if rule_str.lower() == 'done': break
            try:
                condition, action = rule_str.split(':')
                rules.append({"condition": condition, "action": int(action)})
            except ValueError:
                print("無効な形式です。'条件:行動番号' の形式で入力してください。")
        controller = AIPlayerController(rules)
    
    player = PlayerEntity(name="改良型義体", hp=100)
    enemy = EnemyEntity(name="フェイズシフト・ドロイド", hp=80, attack_power=10, traits=["NORMAL_ATTACK_IMMUNE", "COUNTER_ATTACK_VULNERABLE"])
    
    if controller:
        simulator = BattleSimulator(player, enemy, controller)
        simulator.run()
