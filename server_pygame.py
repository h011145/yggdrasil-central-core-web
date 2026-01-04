import asyncio
import os
import subprocess
import json
from aiohttp import web
from PIL import Image
import io

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    print(f"クライアントが接続しました: {request.remote}")

    # 環境変数を設定して、Pygameをヘッドレスモードで実行
    env = os.environ.copy()
    env['SDL_VIDEODRIVER'] = 'dummy'
    
    game_command = ["python3", "./yggdrasil_pygame.py"]
    
    # パイプを使って子プロセスと通信
    process = await asyncio.create_subprocess_exec(
        *game_command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env
    )
    
    print(f"Pygameプロセスを開始しました (PID: {process.pid})")

    async def forward_game_to_ws():
        """子プロセスの出力をWebSocketに転送"""
        while process.returncode is None:
            try:
                # stdoutから生の画像データのサイズを読み込む (4バイト)
                size_bytes = await process.stdout.readexactly(4)
                if not size_bytes:
                    break
                
                img_size = int.from_bytes(size_bytes, 'big')
                
                # 画像データを読み込む
                img_bytes = await process.stdout.readexactly(img_size)
                
                # この時点でimg_bytesは生のRGBデータなので、PillowでJPEGに変換
                # バックエンドとフロントエンドでサイズを合わせる
                img = Image.frombytes('RGB', (800, 600), img_bytes)
                
                # メモリ上のファイルにJPEGとして保存
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=80)
                jpeg_bytes = buf.getvalue()

                await ws.send_bytes(jpeg_bytes)
                await asyncio.sleep(1 / 30) # 30FPSを目指す

            except asyncio.IncompleteReadError:
                print("Pygameプロセスからの読み込みが不完全なまま終了しました。")
                break
            except Exception as e:
                print(f"ゲーム->WS転送エラー: {e}")
                break
        print("Pygameからの転送を終了します。")

    async def forward_ws_to_game():
        """WebSocketの入力を子プロセスに転送"""
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    if data.get('type') == 'key_event':
                        # キーイベントをJSON文字列として子プロセスに送信
                        process.stdin.write((json.dumps(data) + '\n').encode())
                        await process.stdin.drain()
                except Exception as e:
                    print(f"WS->ゲーム転送エラー: {e}")
            elif msg.type == web.WSMsgType.ERROR:
                print(f"WebSocket接続エラー: {ws.exception()}")
                break
        print("クライアントからの転送を終了します。")
    
    async def log_stderr():
        """子プロセスのエラー出力をログに記録"""
        while process.returncode is None:
            line = await process.stderr.readline()
            if not line:
                break
            print(f"[Pygame stderr]: {line.decode().strip()}")

    # タスクを実行
    game_task = asyncio.create_task(forward_game_to_ws())
    client_task = asyncio.create_task(forward_ws_to_game())
    stderr_task = asyncio.create_task(log_stderr())

    await asyncio.wait([game_task, client_task, stderr_task], return_when=asyncio.FIRST_COMPLETED)

    # クリーンアップ
    if process.returncode is None:
        process.terminate()
        await process.wait()
    
    await ws.close()
    print(f"クライアントとの接続を終了しました: {request.remote}")
    return ws

async def main():
    app = web.Application()
    app.router.add_get('/websocket', websocket_handler)
    app.router.add_static('/', path='./public/', name='static') # 静的ファイル配信

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8765))

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()

    print(f"aiohttpサーバーが http://{host}:{port} で起動しました。")
    await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nサーバーをシャットダウンします。")
