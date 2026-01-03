#!/usr/bin/env python3
import asyncio
import os
import sys
import pty
import fcntl
import termios
import json
import struct
from aiohttp import web

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    print(f"Connection from: {request.remote}")

    base_path = os.path.dirname(os.path.abspath(__file__))
    orchestrator_path = os.path.join(base_path, "yggdrasil_orchestrator_v3.py")

    master_fd, slave_fd = pty.openpty()

    # ゲームプロセスの起動 (-u でバッファリングを無効化)
    process = await asyncio.create_subprocess_exec(
        sys.executable, "-u", orchestrator_path,
        stdin=slave_fd, stdout=slave_fd, stderr=slave_fd,
        preexec_fn=os.setsid
    )

    fcntl.fcntl(master_fd, fcntl.F_SETFL, os.O_NONBLOCK)

    async def pty_to_ws():
        loop = asyncio.get_event_loop()
        try:
            while process.returncode is None:
                try:
                    output = await loop.run_in_executor(None, lambda: os.read(master_fd, 4096))
                    if output:
                        await ws.send_str(output.decode('utf-8', errors='replace'))
                except (BlockingIOError, OSError):
                    await asyncio.sleep(0.01)
        except Exception as e: print(f"PTY Error: {e}")

    async def ws_to_pty():
        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    if data['type'] == 'input':
                        # 入力文字をPTYに書き込む
                        os.write(master_fd, data['data'].encode('utf-8'))
                    elif data['type'] == 'resize':
                        winsize = struct.pack("HHHH", data['rows'], data['cols'], 0, 0)
                        fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)
        except Exception as e: print(f"WS Error: {e}")

    await asyncio.gather(pty_to_ws(), ws_to_pty())
    return ws

async def main():
    app = web.Application()
    app.router.add_get('/websocket', websocket_handler)
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', port).start()
    print(f"Backend Server running on {port}")
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
