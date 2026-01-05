import os
import pty
import fcntl
import termios
import struct
import asyncio
from aiohttp import web

# --- 実行するゲームの指定 ---
# V3を起動するように指定
COMMAND = ["python3", "yggdrasil_orchestrator_v3.py"]

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    # 疑似端末 (PTY) の作成
    master_fd, slave_fd = pty.openpty()
    
    # ターミナルのサイズ設定
    buf = struct.pack('HHHH', 24, 80, 0, 0)
    fcntl.ioctl(master_fd, termios.TIOCSWINSZ, buf)

    # V3 (オーケストレーター) をサブプロセスとして起動
    process = await asyncio.create_subprocess_exec(
        *COMMAND,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        preexec_fn=os.setsid
    )
    os.close(slave_fd)

    async def read_from_ws():
        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    os.write(master_fd, msg.data.encode())
        except Exception: pass

    async def write_to_ws():
        loop = asyncio.get_event_loop()
        try:
            while process.returncode is None:
                data = await loop.run_in_executor(None, lambda: os.read(master_fd, 1024))
                if not data: break
                await ws.send_str(data.decode(errors='ignore'))
        except Exception: pass

    await asyncio.gather(read_from_ws(), write_to_ws())
    return ws

async def init_app():
    app = web.Application()
    app.add_routes([web.get('/ws', websocket_handler)])
    # publicフォルダの中身をブラウザで見れるようにする
    app.router.add_static('/', path='public', name='public', show_index=True)
    return app

if __name__ == '__main__':
    # Renderのポートを取得
    port = int(os.environ.get('PORT', 8080))
    app = asyncio.run(init_app())
    print(f"=== SERVER RUNNING ON PORT {port} ===")
    web.run_app(app, host='0.0.0.0', port=port)
