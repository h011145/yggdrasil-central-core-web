import json
import os

class HCodeEngine:
    """
    Hコードシーケンスのロジックをシミュレートするエンジン。
    """
    def __init__(self, dictionary_path):
        """
        エンジンの初期化。Hコード辞書を読み込む。
        """
        self.sequences = {}
        self.current_h_code = None
        self.load_dictionary(dictionary_path)

    def load_dictionary(self, dictionary_path):
        """
        JSON形式のHコード辞書ファイルを読み込み、IDをキーにした辞書に変換する。
        """
        if not os.path.exists(dictionary_path):
            print(f"エラー: 辞書ファイルが見つかりません: {dictionary_path}")
            return

        with open(dictionary_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for seq in data.get('sequences', []):
                self.sequences[seq['id']] = seq
        print(f"Hコード辞書をロードしました。{len(self.sequences)}個のシーケンスを認識。")

    def equip_h_code(self, sequence_id):
        """
        指定されたIDのHコードを「装備」する。
        """
        if sequence_id in self.sequences:
            self.current_h_code = self.sequences[sequence_id]
            print(f"\n[H-Code Equipped: {self.current_h_code['name']}]")
        else:
            print(f"エラー: 不明なシーケンスIDです: {sequence_id}")
            self.current_h_code = None

    def execute_command(self, command, context):
        """
        コマンドを実行し、現在のHコードと状況に基づいて結果を返す。
        """
        print(f"> Executing command '{command}' with context: {context}")

        if not self.current_h_code:
            return "結果: Hコードが装備されていません。標準的な行動を実行しました。"

        # Hコードの効果リストをチェック
        for effect in self.current_h_code.get('effects', []):
            # トリガーがコンテキストと一致するか確認
            if effect.get('trigger') == context.get('trigger'):
                result_parts = []
                
                # 主なアクションを処理
                if 'action' in effect:
                    action_details = effect['action']
                    result_parts.append(f"アクション: {action_details}")
                
                # ソーシャルアクションを処理
                if 'social_action' in effect:
                    social_action_details = effect['social_action']
                    result_parts.append(f"ソーシャルアクション: {social_action_details}")

                # 副次効果を処理
                if 'after_effect' in effect:
                    after_effect_details = effect['after_effect']
                    result_parts.append(f"追加効果: {after_effect_details}")

                if not result_parts:
                     return "結果: トリガーは一致しましたが、定義されたアクションがありません。"

                return f"結果({self.current_h_code['name']}): " + " | ".join(result_parts)

        return f"結果({self.current_h_code['name']}): 現在の状況に一致する特別な効果はありません。標準的な行動を実行しました。"


# --- メインの実行ブロック ---
if __name__ == "__main__":
    # エンジンのインスタンスを作成
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dict_path = os.path.join(script_dir, 'h_code_sequence_dictionary.json')
    engine = HCodeEngine(dict_path)

    print("\n--- シナリオ1: 戦闘での『最善の選択』 ---")
    engine.equip_h_code("SEQ_29")
    context = {"trigger": "TIMING_WINDOW_SUCCESS"}
    result = engine.execute_command("mo COUNTER", context)
    print(result)

    print("\n--- シナリオ2: 戦闘での『最悪の選択』 ---")
    engine.equip_h_code("SEQ_20")
    context = {"trigger": "TIMING_WINDOW_FAILURE"}
    result = engine.execute_command("mo COUNTER", context)
    print(result)

    print("\n--- シナリオ3: 窮地での『自爆覚悟の全力攻撃』 ---")
    engine.equip_h_code("SEQ_580")
    context = {"trigger": "HP_BELOW_20_PERCENT"}
    result = engine.execute_command("mo ATTACK", context)
    print(result)
    
    print("\n--- シナリオ4: 状況に合わないHコード ---")
    engine.equip_h_code("SEQ_580") # 戦闘用コード
    context = {"trigger": "CUSTOMER_IS_HAPPY"} # 接客のコンテキスト
    result = engine.execute_command("mo GREET_CUSTOMER", context) # 接客コマンド
    print(result)