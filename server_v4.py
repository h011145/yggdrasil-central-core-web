import os
import asyncio
from aiohttp import web

# ブラウザが wss://.../ws に繋ぎに来た時に動く処理
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    # 接続成功メッセージ（これが出れば成功！）
    await ws.send_str("--- YGGDRASIL CORE ONLINE ---\r\n")
    await ws.send_str("SYSTEM: サーバーとの接続に成功しました。\r\n")
    await ws.send_str("COMMAND [1]攻撃 [2]防御 [Q]終了\r\n")

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                cmd = msg.data.strip()
                if cmd == '1':
                    await ws.send_str(">> 攻撃実行！ 敵に20ダメージ！\r\n")
                elif cmd == '2':
                    await ws.send_str(">> 防御展開！ ダメージを軽減しました。\r\n")
                elif cmd.lower() == 'q':
                    await ws.send_str(">> 終了します...\r\n")
                    break
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await ws.close()
    return ws

async def init_app():
    app = web.Application()
    # 🚨 ここを /ws に固定することで 404 エラーを回避します
    app.add_routes([web.get('/ws', websocket_handler)])
    # 🚨 publicフォルダのファイルを配信する設定
    app.router.add_static('/', path='public', name='public', show_index=True)
    return app

if __name__ == '__main__':
    # Renderが指定するポートを環境変数から取得
    port = int(os.environ.get('PORT', 8080))
    
    app = asyncio.run(init_app())
    print(f"Starting server on port {port}")
    
    # Renderで動かすためのホスト設定
    web.run_app(app, host='0.0.0.0', port=port)
