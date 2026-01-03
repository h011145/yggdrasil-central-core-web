// main.js - 修正版
const term = new Terminal({
    cursorBlink: true,
    fontSize: 18
});
term.open(document.getElementById('terminal'));

// URLを現在のバックエンドのものに修正してください（wss://...）
// 末尾に /websocket が付いていることを確認してください
const socket = new WebSocket('wss://yggdrasil-websocket-backend.onrender.com/websocket');

socket.onopen = () => {
    term.write('[SYSTEM] サーバーに接続しました。\r\n');
};

socket.onmessage = (event) => {
    // サーバーからデータが届いたら画面に表示
    term.write(event.data);
};

// 入力処理：二重定義を避け、確実に1文字ずつ送る
term.onData(data => {
    if (socket && socket.readyState === WebSocket.OPEN) {
        // バックエンドがJSON形式を待っている場合はこちら
        socket.send(JSON.stringify({ type: 'input', data: data }));
    }
});

socket.onerror = (error) => {
    console.error('WebSocket Error:', error);
};

socket.onclose = () => {
    term.write('\r\n[ERROR] サーバーとの接続が切れました。\r\n');
};
