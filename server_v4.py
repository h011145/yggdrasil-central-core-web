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
    print(f"クライアントが接続しました: {request.remote}")

    base_path = os.path.dirname(os.path.abspath(__file__))
    orchestrator_path = os.path.join(base_path, "yggdrasil_orchestrator_v3.py")

    # PTYの作成
    master_fd, slave_fd = pty.openpty()

    # 実行コマンドの構成
    game_command = [sys.executable, "-u", orchestrator_path]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *game_command,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            preexec_fn=os.setsid
        )
    except Exception as e:
        print(f"プロセス起動失敗: {e}")
        await ws.send_str(f"\r\n[SYSTEM ERROR] 起動失敗: {e}")
        await ws.close()
        return ws

    # 非ブロッキング設定
    fcntl.fcntl(master_fd, fcntl.F_SETFL, os.O_NONBLOCK)

    async def forward_pty_to_ws():
        loop = asyncio.get_event_loop()
        try:
            while process.returncode is None:
                try:
                    # PTYからの出力を読み取ってWebSocketへ送る
                    output = await loop.run_in_executor(None, lambda: os.read(master_fd, 4096))
                    if output:
                        await ws.send_str(output.decode('utf-8', errors='replace'))
                except (BlockingIOError, OSError):
                    await asyncio.sleep(0.01)
        except Exception as e:
            print(f"PTYリードエラー: {e}")

    async def forward_ws_to_pty():
        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    payload = json.loads(msg.data)
                    
                    if payload['type'] == 'resize':
                        winsize = struct.pack("HHHH", payload['rows'], payload['cols'], 0, 0)
                        fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)
                    
                    elif payload['type'] == 'input':
                        # 重要: 受信したキー入力をPTYのマスター側に書き込む
                        input_data = payload['data'].encode('utf-8')
                        os.write(master_fd, input_data)
                        
        except Exception as e:
            print(f"WSリードエラー: {e}")

    # 両方のタスクを並行実行
    await asyncio.gather(forward_pty_to_ws(), forward_ws_to_pty())
    
    os.close(master_fd)
    os.close(slave_fd)
    return ws

async def main():
    app = web.Application()
    app.router.add_get('/websocket', websocket_handler)
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Server started on port {port}")
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
