import os
import asyncio
from aiohttp import web

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    # 接続成功時にブラウザへ送るメッセージ
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
                    await ws.send_str(">> 接続を終了します...\r\n")
                    break
    except Exception as e:
        print(f"WS Error: {e}")
    finally:
        await ws.close()
    return ws

async def init_app():
    app = web.Application()
    app.add_routes([web.get('/ws', websocket_handler)])
    # publicフォルダを配信する設定
    app.router.add_static('/', path='public', name='public', show_index=True)
    return app

if __name__ == '__main__':
    # 【最重要】Renderから指定されるポート番号を取得し、なければ8080を使う
    port = int(os.environ.get('PORT', 8080))
    
    app = asyncio.run(init_app())
    print(f"=== SERVER STARTING ON PORT {port} ===")
    
    # host='0.0.0.0' で外部接続を許可
    web.run_app(app, host='0.0.0.0', port=port)
