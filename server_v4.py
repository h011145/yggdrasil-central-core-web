import os
import pty
import fcntl
import termios
import struct
import asyncio
from aiohttp import web

# --- 設定エリア ---
# メインのオーケストレーターを指定
COMMAND = ["python3", "yggdrasil_orchestrator_v3.py"]

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    # 疑似端末 (PTY) の作成
    master_fd, slave_fd = pty.openpty()
    
    # ターミナルのサイズ設定（カードバトルが見やすいサイズに）
    buf = struct.pack('HHHH', 24, 80, 0, 0)
    fcntl.ioctl(master_fd, termios.TIOCSWINSZ, buf)

    # サブプロセス（ゲーム）の起動
    process = await asyncio.create_subprocess_exec(
        *COMMAND,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        preexec_fn=os.setsid
    )
    os.close(slave_fd)

    # ブラウザからの入力をサーバーに送るタスク
    async def read_from_ws():
        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    os.write(master_fd, msg.data.encode())
        except Exception as e:
            print(f"WS Read Error: {e}")

    # サーバーの出力をブラウザに送るタスク
    async def write_to_ws():
        loop = asyncio.get_event_loop()
        try:
            while process.returncode is None:
                # データを非同期で読み取り
                data = await loop.run_in_executor(None, lambda: os.read(master_fd, 1024))
                if not data:
                    break
                await ws.send_str(data.decode(errors='ignore'))
        except Exception as e:
            print(f"WS Write Error: {e}")

    # 両方のタスクを並行実行
    await asyncio.gather(read_from_ws(), write_to_ws())
    
    await ws.close()
    return ws

async def init_app():
    app = web.Application()
    # /ws というパスで接続を待機
    app.add_routes([web.get('/ws', websocket_handler)])
    
    # Renderの静的ファイルを表示するための設定（index.html等）
    app.router.add_static('/', path='public', name='public', show_index=True)
    return app

if __name__ == '__main__':
    # 【重要】Renderが指定するポート番号を環境変数から取得
    port = int(os.environ.get('PORT', 8080))
    
    app = asyncio.run(init_app())
    print(f"=== SYSTEM: Server starting on port {port} ===")
    
    # Renderで動かすためのホスト設定 '0.0.0.0'
    web.run_app(app, host='0.0.0.0', port=port)
