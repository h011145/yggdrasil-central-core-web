import pygame
import sys
import json
import time
import struct
import os

# --- ゲームエンジンクラス ---
class WorldEngine:
    def __init__(self):
        pygame.init()
        self.width, self.height = 800, 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Yggdrasil Central Core")
        
        self.font = None # TODO: ビットマップフォントをロード
        self.is_running = True
        self.logs = []
        
        # メニュー関連
        self.menu_items = ["ガレージ", "ネクスト戦記", "終了"]
        self.current_selection = 0
        self.input_buffer = ""

    def run(self):
        """メインループ"""
        # 標準入力をノンブロッキングに設定
        # これはWindowsでは動作しないが、Render環境(Linux)を想定
        if os.name == 'posix':
            import fcntl
            fd = sys.stdin.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        while self.is_running:
            self.handle_input()
            self.update()
            self.draw()
            self.send_frame()
            time.sleep(1/30) # 30FPSを目標

    def handle_input(self):
        """親プロセスからの入力を処理"""
        try:
            # 標準入力からデータを読み込む
            self.input_buffer += sys.stdin.read()
            if '\n' in self.input_buffer:
                line, self.input_buffer = self.input_buffer.split('\n', 1)
                data = json.loads(line)
                if data.get('type') == 'key_event' and data.get('event') == 'keydown':
                    self.process_key(data.get('key'))
        except (IOError, json.JSONDecodeError):
            # データがないか、JSONとして不完全な場合は何もしない
            pass
            
        # テスト用のローカル入力処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
            if event.type == pygame.KEYDOWN:
                self.process_key(event.key)


    def process_key(self, key):
        """キー入力を解釈してゲームの状態を更新"""
        key_map = {
            'ArrowUp': pygame.K_UP,
            'ArrowDown': pygame.K_DOWN,
            'Enter': pygame.K_RETURN,
            'q': pygame.K_q,
        }
        
        # 文字列キーをPygameのキーコードに変換
        pygame_key = key if isinstance(key, int) else key_map.get(key)
        
        if pygame_key == pygame.K_UP:
            self.current_selection = (self.current_selection - 1) % len(self.menu_items)
        elif pygame_key == pygame.K_DOWN:
            self.current_selection = (self.current_selection + 1) % len(self.menu_items)
        elif pygame_key == pygame.K_RETURN:
            self.select_menu()
        elif pygame_key == pygame.K_q:
            self.is_running = False

    def update(self):
        """ゲームの状態を更新"""
        pass # 今は何もしない

    def select_menu(self):
        """メニュー項目を決定"""
        selected = self.menu_items[self.current_selection]
        if selected == "終了":
            self.is_running = False
        else:
            self.add_log(f"'{selected}' は現在開発中です。")

    def draw_grid(self):
        """背景のグリッド線を描画"""
        for x in range(0, self.width, 20):
            pygame.draw.line(self.screen, (0, 50, 0), (x, 0), (x, self.height))
        for y in range(0, self.height, 20):
            pygame.draw.line(self.screen, (0, 50, 0), (0, y), (self.width, y))

    def draw_menu(self):
        """メニューを描画"""
        # TODO: ビットマップフォントを使う
        font = pygame.font.Font(None, 36) # ダミーフォント
        for i, item in enumerate(self.menu_items):
            color = (0, 255, 0) if i == self.current_selection else (0, 150, 0)
            text_surface = font.render(f"> {item}", True, color)
            self.screen.blit(text_surface, (50, 100 + i * 40))
            
    def draw_logs(self):
        """ログを描画"""
        font = pygame.font.Font(None, 24) # ダミーフォント
        for i, log in enumerate(self.logs[-5:]):
             text_surface = font.render(log, True, (0, 200, 0))
             self.screen.blit(text_surface, (20, self.height - 120 + i * 20))


    def draw(self):
        """全体の描画"""
        self.screen.fill((0, 0, 0)) # 黒で塗りつぶし
        self.draw_grid()
        self.draw_menu()
        self.draw_logs()
        pygame.display.flip() # サーバーサイドでは不要だが、テストのために残す

    def send_frame(self):
        """現在のフレームを標準出力に送信"""
        try:
            # 生のRGBデータを取得
            img_data = pygame.image.tostring(self.screen, "RGB")
            
            # データサイズを4バイトのビッグエンディアンでパック
            size_bytes = struct.pack('>I', len(img_data))
            
            # 標準出力に書き出す
            sys.stdout.buffer.write(size_bytes)
            sys.stdout.buffer.write(img_data)
            sys.stdout.buffer.flush()
        except Exception:
            # 親プロセスが死んだ場合などにエラーになるので、正常終了
            self.is_running = False

    def add_log(self, text):
        self.logs.append(f"[{time.strftime('%H:%M:%S')}] {text}")


# --- メイン処理 ---
if __name__ == "__main__":
    engine = WorldEngine()
    engine.run()
