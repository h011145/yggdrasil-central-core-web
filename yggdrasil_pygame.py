import pygame
import sys
import json
import time
import struct
import os
import random
import math

# --- ゲームエンジンクラス ---
class WorldEngine:
    def __init__(self):
        pygame.init()
        self.width, self.height = 800, 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Yggdrasil Central Core")
        
        self.font_large = pygame.font.SysFont('monospace', 30, bold=True)
        self.font_medium = pygame.font.SysFont('monospace', 24, bold=True)
        self.font_small = pygame.font.SysFont('monospace', 18)
        
        self.is_running = True
        self.logs = []
        self.input_buffer = ""

        # ゲーム状態
        self.game_state = "MENU" # "MENU" or "NEXT_WAR"

        # メニュー関連
        self.menu_items = ["ガレージ", "ネクスト戦記", "終了"]
        self.current_selection = 0

        # NEXT_WAR state variables
        self.player_q = 10
        self.player_r = 10
        self.hex_map_size = 20

    def run(self):
        """メインループ"""
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
            time.sleep(1/30)

    def handle_input(self):
        try:
            self.input_buffer += sys.stdin.read()
            if '\n' in self.input_buffer:
                line, self.input_buffer = self.input_buffer.split('\n', 1)
                data = json.loads(line)
                if data.get('type') == 'key_event' and data.get('event') == 'keydown':
                    self.process_key(data.get('key'))
        except (IOError, json.JSONDecodeError):
            pass
            
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
            if event.type == pygame.KEYDOWN:
                self.process_key(event.key)

    def process_key(self, key):
        key_map = { 'ArrowUp': pygame.K_UP, 'ArrowDown': pygame.K_DOWN, 'Enter': pygame.K_RETURN, 'q': pygame.K_q, 'Escape': pygame.K_ESCAPE, 'ArrowLeft': pygame.K_LEFT, 'ArrowRight': pygame.K_RIGHT }
        pygame_key = key if isinstance(key, int) else key_map.get(key)
        
        if self.game_state == "MENU":
            if pygame_key == pygame.K_UP:
                self.current_selection = (self.current_selection - 1) % len(self.menu_items)
            elif pygame_key == pygame.K_DOWN:
                self.current_selection = (self.current_selection + 1) % len(self.menu_items)
            elif pygame_key == pygame.K_RETURN:
                self.select_menu()
            elif pygame_key == pygame.K_q:
                self.is_running = False
        
        elif self.game_state == "NEXT_WAR":
            # 軸に合わせた移動ロジック（奇数行/偶数行で挙動が変わる）
            if pygame_key == pygame.K_UP: self.player_r -= 1
            elif pygame_key == pygame.K_DOWN: self.player_r += 1
            elif pygame_key == pygame.K_LEFT: self.player_q -= 1
            elif pygame_key == pygame.K_RIGHT: self.player_q += 1
            elif pygame_key == pygame.K_ESCAPE:
                self.game_state = "MENU"
                self.add_log("メインメニューへ帰還。")
    
    def update(self):
        pass

    def select_menu(self):
        """メニュー項目を決定"""
        self.draw_noise_effect()
        selected = self.menu_items[self.current_selection]
        if selected == "終了":
            self.is_running = False
        elif selected == "ネクスト戦記":
            self.game_state = "NEXT_WAR"
            self.add_log("ネクスト戦記アーカイブへ接続。")
        else:
            self.add_log(f"'{selected}' は現在開発中です。")

    def draw_noise_effect(self, duration=0.15, strength=100):
        """画面にノイズエフェクトを描画"""
        end_time = time.time() + duration
        while time.time() < end_time:
            self.screen.lock()
            for _ in range(strength):
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)
                color_val = random.randint(40, 120)
                color = (0, color_val, 0)
                self.screen.set_at((x, y), color)
                if random.random() > 0.9:
                    x2 = x + random.randint(-20, 20); y2 = y
                    pygame.draw.line(self.screen, (0, color_val // 2, 0), (x, y), (x2, y2), 1)
            self.screen.unlock()
            pygame.display.flip() # ローカルテスト用
            self.send_frame()
            time.sleep(1/60)

    def draw_grid(self):
        for x in range(0, self.width, 20):
            pygame.draw.line(self.screen, (0, 50, 0), (x, 0), (x, self.height))
        for y in range(0, self.height, 20):
            pygame.draw.line(self.screen, (0, 50, 0), (0, y), (self.width, y))

    def draw_menu(self):
        for i, item in enumerate(self.menu_items):
            color = (0, 255, 0) if i == self.current_selection else (0, 150, 0)
            text_surface = self.font_medium.render(f"> {item}", False, color) # アンチエイリアス無効
            self.screen.blit(text_surface, (50, 100 + i * 40))
            
    def draw_logs(self):
        for i, log in enumerate(self.logs[-5:]):
             text_surface = self.font_small.render(log, False, (0, 200, 0)) # アンチエイリアス無効
             self.screen.blit(text_surface, (20, self.height - 120 + i * 20))

    def draw(self):
        self.screen.fill((0, 0, 0))
        self.draw_grid()
        if self.game_state == "MENU":
            self.draw_menu()
        elif self.game_state == "NEXT_WAR":
            self.draw_hex_map()
        self.draw_logs()
        pygame.display.flip()

    def hex_to_pixel(self, q, r, size=20):
        x = size * 3/2 * q
        y = size * math.sqrt(3) * (r + q/2)
        return x + self.width / 2.5, y + self.height / 5

    def draw_hex(self, surface, color, center, size, width=0):
        points = []
        for i in range(6):
            angle_rad = math.radians(60 * i)
            points.append((center[0] + size * math.cos(angle_rad), center[1] + size * math.sin(angle_rad)))
        pygame.draw.polygon(surface, color, points, width)

    def draw_hex_map(self):
        hex_size = 18
        for q_offset in range(-self.hex_map_size // 2, self.hex_map_size // 2):
            for r_offset in range(-self.hex_map_size // 2, self.hex_map_size // 2):
                q, r = self.player_q + q_offset, self.player_r + r_offset
                center = self.hex_to_pixel(q_offset, r_offset, hex_size)
                
                if q == self.player_q and r == self.player_r:
                    self.draw_hex(self.screen, (0, 255, 0), center, hex_size + 2, width=2)
                    self.draw_hex(self.screen, (0, 150, 0), center, hex_size)
                else:
                    self.draw_hex(self.screen, (0, 80, 0), center, hex_size, width=1)

    def send_frame(self):
        try:
            img_data = pygame.image.tostring(self.screen, "RGB")
            size_bytes = struct.pack('>I', len(img_data))
            sys.stdout.buffer.write(size_bytes)
            sys.stdout.buffer.write(img_data)
            sys.stdout.buffer.flush()
        except Exception:
            self.is_running = False

    def add_log(self, text):
        self.logs.append(f"[{time.strftime('%H:%M:%S')}] {text}")

if __name__ == "__main__":
    engine = WorldEngine()
    engine.run()
