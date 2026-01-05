import os
import asyncio
from aiohttp import web

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    await ws.send_str("--- YGGDRASIL CENTRAL CORE v5.0 ---\n")
    await ws.send_str("SYSTEM: ログイン成功。コマンドを入力してください。\n")
    await ws.send_str("[2] 戦闘アーカイブ (CARD BATTLE) / [Q] 終了\n")

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                cmd = msg.data.strip().lower()
                
                if cmd == '2':
                    await ws.send_str("\n--- CARD BATTLE START ---\n")
                    await ws.send_str("ENEMY: [##########] 100%\n")
                    await ws.send_str("YOU  : [##########] 100%\n")
                    await ws.send_str("COMMAND > [1]攻撃 [2]防御\n")
                elif cmd == '1':
                    await ws.send_str(">> 攻撃！ 敵に20ダメージ！\n")
                elif cmd == 'q':
                    await ws.send_str("SYSTEM: シャットダウンします...\n")
                    break
    finally:
        await ws.close()
    return ws

async def init_app():
    app = web.Application()
    app.add_routes([web.get('/ws', websocket_handler)])
    app.router.add_static('/', path='public', show_index=True)
    return app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app = asyncio.run(init_app())
    web.run_app(app, host='0.0.0.0', port=port)
