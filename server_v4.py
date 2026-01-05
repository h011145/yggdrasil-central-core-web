import os
import asyncio
from aiohttp import web

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    await ws.send_str("SYSTEM: 接続成功！クラッシュせずに動いています。\r\n")
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                await ws.send_str(f">> 受信しました: {msg.data}\r\n")
    finally:
        await ws.close()
    return ws

async def init_app():
    app = web.Application()
    app.add_routes([web.get('/ws', websocket_handler)])
    app.router.add_static('/', path='public', show_index=True)
    return app

if __name__ == '__main__':
    # 【ここが重要！】Renderが指定するポートを使い、なければ8080にする
    port = int(os.environ.get('PORT', 8080))
    
    app = asyncio.run(init_app())
    # 起動ログを出す（RenderのLogsタブで見れます）
    print(f"Server is starting on port {port}...")
    
    web.run_app(app, host='0.0.0.0', port=port)
