#!/usr/bin/env python3
import asyncio
import os
import pty
import subprocess
import fcntl
import termios
import json
import struct # for TIOCSWINSZ
from aiohttp import web

async def websocket_handler(request):
    """
    WebSocketクライアントからの接続を処理し、ゲームプロセスを中継するハンドラ
    """
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    print(f"クライアントが接続しました: {request.remote}")

    master_fd, slave_fd = pty.openpty()

    game_command = [
        "python3",
        "./yggdrasil_orchestrator_v3.py" # 相対パス
    ]
    
    process = await asyncio.create_subprocess_exec(
        *game_command,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        preexec_fn=os.setsid
    )
    
    # Add logging for process lifecycle
    async def monitor_process():
        await process.wait()
        print(f"ゲームプロセス (PID: {process.pid}) が終了しました。Exit Code: {process.returncode}")
    asyncio.create_task(monitor_process())

    fcntl.fcntl(master_fd, fcntl.F_SETFL, os.O_NONBLOCK)

    print(f"ゲームプロセスを開始しました (PID: {process.pid})")

    async def forward_pty_to_ws():
        try:
            loop = asyncio.get_event_loop()
            while True:  # Loop indefinitely to read output
                try:
                    # Read from PTY non-blocking
                    output = await loop.run_in_executor(None, lambda: os.read(master_fd, 1024))
                    if output:
                        await ws.send_str(output.decode('utf-8', errors='replace'))
                        # Give a chance for the client to receive the data
                        await asyncio.sleep(0.001) 
                    else:
                        # No output, check if process is done or sleep
                        if process.returncode is not None:
                            # Process finished, and no more output immediately.
                            # Give a tiny bit more time for any last-ditch buffered output.
                            await asyncio.sleep(0.1)
                            # Try one more read
                            final_output = await loop.run_in_executor(None, lambda: os.read(master_fd, 1024))
                            if final_output:
                                await ws.send_str(final_output.decode('utf-8', errors='replace'))
                            break # Break loop if process done and no more output
                        else:
                            await asyncio.sleep(0.01) # Sleep briefly if no output and process still running
                except BlockingIOError:
                    if process.returncode is not None:
                        # Process finished, no more blocking output.
                        # Give a tiny bit more time for any last-ditch buffered output.
                        await asyncio.sleep(0.1)
                        # Try one more read
                        final_output = await loop.run_in_executor(None, lambda: os.read(master_fd, 1024))
                        if final_output:
                            await ws.send_str(final_output.decode('utf-8', errors='replace'))
                        break # Break loop if process done and no more output
                    else:
                        await asyncio.sleep(0.01) # Sleep briefly if no output and process still running
        except ConnectionResetError:
            print("PTY->WS: クライアントが切断されました (ConnectionResetError)。")
        except Exception as e:
            print(f"PTY->WS: 予期せぬエラー: {e}")
        finally:
            if process.returncode is None:
                print("PTY->WS: プロセスを終了します。")
                process.terminate()

    async def forward_ws_to_pty():
        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    msg_data = json.loads(msg.data)
                    
                    if msg_data['type'] == 'resize':
                        winsize = struct.pack("HHHH", msg_data['rows'], msg_data['cols'], 0, 0)
                        fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)
                        print(f"ターミナルサイズを変更: {msg_data['cols']}x{msg_data['rows']}")
                    
                    elif msg_data['type'] == 'input':
                        os.write(master_fd, msg_data['data'].encode('utf-8'))
                elif msg.type == web.WSMsgType.ERROR:
                    print(f"WS->PTY: WebSocket接続でエラー: {ws.exception()}")
        except Exception as e:
            print(f"WS->PTY: 予期せぬエラー: {e}")
        finally:
            if process.returncode is None:
                print("WS->PTY: プロセスを終了します。")
                process.terminate()

    try:
        await asyncio.gather(
            forward_pty_to_ws(),
            forward_ws_to_pty()
        )
    finally:
        if process.returncode is None:
            process.terminate()
            await process.wait()
        os.close(master_fd)
        os.close(slave_fd)
        print(f"クライアントとの接続を終了しました: {request.remote}")
    return ws


async def main():
    """
    aiohttpウェブサーバーとWebSocketサーバーを起動するメイン関数
    """
    app = web.Application()

    # 静的ファイルの提供 (public ディレクトリ全体)
    app.router.add_static('/public', './public') # /public/index.html でアクセス可能

    # ルートパスへのアクセス時に index.html を返すハンドラ
    async def index_handler(request):
        return web.FileResponse('./public/index_v2.html')
    app.router.add_get('/', index_handler)

    # WebSocketハンドラの追加
    app.router.add_get('/websocket', websocket_handler)

    # Render環境では環境変数からポートとホストを取得
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8765))

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()

    print(f"aiohttpサーバーが http://{host}:{port} で起動しました。")
    print(f"WebSocketは ws://{host}:{port}/websocket で利用可能です。")

    # サーバーを起動し続けるためにFutureを待機
    await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nサーバーをシャットダウンします。")
    except Exception as e:
        print(f"サーバーの起動中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
