document.addEventListener('DOMContentLoaded', () => {
    const clickToStart = document.getElementById('click-to-start');
    const canvas = document.getElementById('game-canvas');
    const ctx = canvas.getContext('2d');
    let socket;

    // ゲーム画面の解像度（バックエンドと合わせる）
    const GAME_WIDTH = 800;
    const GAME_HEIGHT = 600;

    canvas.width = GAME_WIDTH;
    canvas.height = GAME_HEIGHT;

    clickToStart.addEventListener('click', () => {
        clickToStart.style.display = 'none';
        canvas.style.display = 'block';
        connectWebSocket();
    }, { once: true }); // イベントリスナーを一度だけ実行

    function connectWebSocket() {
        socket = new WebSocket('wss://yggdrasil-websocket-backend.onrender.com/websocket');

        socket.onopen = () => {
            console.log('[SYSTEM] WebSocket connection established.');
            // 接続成功したら、キー入力のリスニングを開始
            setupKeyboardListeners();
        };

        socket.onmessage = (event) => {
            // 受信したのが画像データの場合
            if (event.data instanceof Blob) {
                const image = new Image();
                image.src = URL.createObjectURL(event.data);
                image.onload = () => {
                    ctx.drawImage(image, 0, 0);
                    URL.revokeObjectURL(image.src); // メモリ解放
                };
            }
            // 受信したのがテキストデータの場合（デバッグ用）
            else {
                console.log('[SERVER]', event.data);
            }
        };

        socket.onclose = () => {
            console.error('[SYSTEM] WebSocket connection closed.');
            // エラーメッセージをCanvasに表示
            ctx.fillStyle = 'red';
            ctx.font = '20px "Courier New"';
            ctx.textAlign = 'center';
            ctx.fillText('サーバーとの接続が切れました。再読み込みしてください。', GAME_WIDTH / 2, GAME_HEIGHT / 2);
        };

        socket.onerror = (error) => {
            console.error('[SYSTEM] WebSocket error:', error);
            ctx.fillStyle = 'red';
            ctx.font = '20px "Courier New"';
            ctx.textAlign = 'center';
            ctx.fillText('接続エラーが発生しました。', GAME_WIDTH / 2, GAME_HEIGHT / 2);
        };
    }

    function setupKeyboardListeners() {
        window.addEventListener('keydown', (event) => {
            sendKeyEvent('keydown', event.key);
            event.preventDefault(); // ブラウザのデフォルト動作を抑制
        });

        window.addEventListener('keyup', (event) => {
            sendKeyEvent('keyup', event.key);
            event.preventDefault();
        });
    }

    function sendKeyEvent(type, key) {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                type: 'key_event',
                event: type,
                key: key
            }));
        }
    }
});