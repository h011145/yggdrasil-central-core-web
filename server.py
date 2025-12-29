#!/usr/bin/env python3
import asyncio
import websockets
import os
import pty
import subprocess
import fcntl
import termios
import json
import struct # for TIOCSWINSZ

async def handler(websocket, path):
    """
    WebSocketクライアントからの接続を処理し、ゲームプロセスを中継するハンドラ
    """
    print(f"クライアントが接続しました: {websocket.remote_address}")
    
    master_fd, slave_fd = pty.openpty()

    # ゲームプロセスのコマンド (Render環境ではpython3がパスに含まれる)
    # yggdrasil_orchestrator.py へのパスも相対パスに変更
    game_command = [
        "python3", # Render環境のpython3を使用
        "./yggdrasil_orchestrator.py" # 相対パス
    ]
    
    # Render環境で仮想環境は不要なので、直接 subprocess.Popen を使用
    # preexec_fn=os.setsid は重要 (プロセスグループを作成し、ターミナルセッションから独立させる)
    process = await asyncio.create_subprocess_exec(
        *game_command,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        preexec_fn=os.setsid
    )
    
    fcntl.fcntl(master_fd, fcntl.F_SETFL, os.O_NONBLOCK)

    print(f"ゲームプロセスを開始しました (PID: {process.pid})")

    async def forward_pty_to_ws():
        try:
            loop = asyncio.get_event_loop()
            while process.returncode is None:
                try:
                    # 疑似ターミナルからデータをノンブロッキングで読み取る
                    output = await loop.run_in_executor(None, lambda: os.read(master_fd, 1024))
                    if output:
                        await websocket.send(output.decode('utf-8', errors='replace'))
                except BlockingIOError:
                    await asyncio.sleep(0.01) # データがなければ少し待つ
        except websockets.exceptions.ConnectionClosed:
            print("PTY->WS: クライアント接続が切れました。")
        finally:
            if process.returncode is None:
                print("PTY->WS: プロセスを終了します。")
                process.terminate()

    async def forward_ws_to_pty():
        try:
            async for message in websocket:
                msg_data = json.loads(message)
                
                if msg_data['type'] == 'resize':
                    # TIOCSWINSZを使ってptyのサイズを設定
                    # struct.packでcolsとrowsをバイト列に変換
                    winsize = struct.pack("HHHH", msg_data['rows'], msg_data['cols'], 0, 0)
                    fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)
                    print(f"ターミナルサイズを変更: {msg_data['cols']}x{msg_data['rows']}")
                
                elif msg_data['type'] == 'input':
                    os.write(master_fd, msg_data['data'].encode('utf-8'))

        except websockets.exceptions.ConnectionClosed:
            print("WS->PTY: クライアント接続が切れました。")
        except json.JSONDecodeError:
            print("無効なJSONメッセージを受信しました。")
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
        print(f"クライアントとの接続を終了しました: {websocket.remote_address}")

async def main():
    """
    WebSocketサーバーを起動するメイン関数
    """
    # Render環境では環境変数からポートとホストを取得
    host = os.environ.get("HOST", "0.0.0.0") # 外部からの接続を許可
    port = int(os.environ.get("PORT", 8765)) # 環境変数PORTから取得、デフォルトは8765
    async with websockets.serve(handler, host, port):
        print(f"WebSocketサーバーが http://{host}:{port} で起動しました。")
        print("ブラウザで /home/hirosi/my_gemini_project/yggdrasil_web/public/index.html を開いてください。")
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nサーバーをシャットダウンします。")