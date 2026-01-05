import os
import sys
import asyncio
from aiohttp import web
import curses

# gamesフォルダを読み込むためのパス設定
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from games.card_battle import CardBattle
except ImportError:
    CardBattle = None

# --- Cursesメインロジック ---
def game_main(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, -1)
    
    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        stdscr.attron(curses.color_pair(1))
        stdscr.border()
        
        title = " YGGDRASIL CENTRAL CORE OS - v3.0 "
        stdscr.addstr(1, (w-len(title))//2, title)
        
        stdscr.addstr(5, 10, "--- ARCHIVE ACCESS ---")
        stdscr.addstr(7, 12, "[2] 戦闘アーカイブ (CARD BATTLE)")
        stdscr.addstr(9, 12, "[Q] システム終了")
        
        if CardBattle is None:
            stdscr.addstr(h-3, 4, "Warning: games/card_battle.py not found.", curses.A_REVERSE)
            
        stdscr.addstr(h-2, 4, "COMMAND > ")
        stdscr.refresh()
        
        key = stdscr.getch()
        if key in [ord('q'), ord('Q')]:
            break
        elif key == ord('2'):
            if CardBattle:
                game = CardBattle(stdscr)
                game.play()

# --- Render用サーバーロジック ---
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    # ここでCursesをブラウザ上でエミュレートするための処理が走ります
    # 簡易版として、まずは接続維持を優先します
    await ws.send_str("SYSTEM: 接続完了。コアシステム起動中...\n")
    
    # 本来はここで game_main を PTY 経由で動かしますが、
    # まずはポート開放を成功させるためにループを回します
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                if msg.data == '2':
                    await ws.send_str("Starting Card Battle...\n")
    finally:
        await ws.close()
    return ws

async def init_app():
    app = web.Application()
    app.add_routes([web.get('/ws', websocket_handler)])
    # publicフォルダ内のindex.html等を表示
    app.router.add_static('/', path='public', name='public', show_index=True)
    return app

if __name__ == '__main__':
    # Renderのポート取得
    port = int(os.environ.get('PORT', 8080))
    
    # もしローカル実行ならCursesを起動、Renderならサーバーを起動
    if 'RENDER' in os.environ:
        app = asyncio.run(init_app())
        web.run_app(app, host='0.0.0.0', port=port)
    else:
        # ローカルでのテスト用
        curses.wrapper(game_main)
