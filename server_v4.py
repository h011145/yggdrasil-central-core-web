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
    
    master_fd, slave_fd = pty.openpty()
    base_path = os.path.dirname(os.path.abspath(__file__))
    orchestrator_path = os.path.join(base_path, "yggdrasil_orchestrator_v3.py")

    # -u オプションでPythonの標準入出力をノンバッファリング(即時)にします
    process = await asyncio.create_subprocess_exec(
        sys.executable, "-u", orchestrator_path,
        stdin=slave_fd, stdout=slave_fd, stderr=slave_fd,
        preexec_fn=os.setsid
    )

    fcntl.fcntl(master_fd, fcntl.F_SETFL, os.O_NONBLOCK)

    async def pty_to_ws():
        loop = asyncio.get_event_loop()
        while process.returncode is None:
            try:
                output = await loop.run_in_executor(None, lambda: os.read(master_fd, 4096))
                if output:
                    await ws.send_str(output.decode('utf-8', errors='replace'))
            except (BlockingIOError, OSError):
                await asyncio.sleep(0.01)

    async def ws_to_pty():
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                payload = json.loads(msg.data)
                if payload['type'] == 'input':
                    # 入力をそのまま書き込む
                    os.write(master_fd, payload['data'].encode('utf-8'))
                elif payload['type'] == 'resize':
                    winsize = struct.pack("HHHH", payload['rows'], payload['cols'], 0, 0)
                    fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)

    await asyncio.gather(pty_to_ws(), ws_to_pty())
    return ws

async def main():
    app = web.Application()
    app.router.add_get('/websocket', websocket_handler)
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', port).start()
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
