import os
import asyncio
from aiohttp import web

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    await ws.send_str("SYSTEM: 接続に成功しました！コア起動準備中...\r\n")

    try:
        # ここで直接ゲームロジックを動かすテスト
        await ws.send_str("=== CARDS OF YGGDRASIL v1.0 ===\r\n")
        await ws.send_str("1: ATTACK | 2: SHIELD | Q: EXIT\r\n")
        
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                cmd = msg.data.strip()
                if cmd == '1':
                    await ws.send_str("YOU: ATTACK EXE! -> ENEMY HP -20\r\n")
                elif cmd == '2':
                    await ws.send_str("YOU: SHIELD PROT! -> DEFENSE UP\r\n")
                elif cmd.lower() == 'q':
                    break
    finally:
        await ws.close()
    return ws

async def init_app():
    app = web.Application()
    app.add_routes([web.get('/ws', websocket_handler)])
    app.router.add_static('/', path='public', name='public', show_index=True)
    return app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app = asyncio.run(init_app())
    print(f"DEBUG: Starting on port {port}")
    web.run_app(app, host='0.0.0.0', port=port)
