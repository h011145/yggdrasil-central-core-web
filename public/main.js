const term = new Terminal({
    cursorBlink: true,
    fontSize: 18,
    fontFamily: 'Courier New, monospace'
});
term.open(document.getElementById('terminal'));

// サーバーのURL（自分のRenderのURLに書き換えてください）
const socket = new WebSocket('wss://yggdrasil-websocket-backend.onrender.com/websocket');

socket.onopen = () => {
    term.write('[SYSTEM] サーバーに接続しました。\r\n');
};

// サーバーからのデータ（文字）を画面に表示
socket.onmessage = (event) => {
    term.write(event.data);
};

// 【重要】キーボード入力をサーバーに送る処理
term.onData(data => {
    if (socket.readyState === WebSocket.OPEN) {
        // 文字をそのまま送るとバックエンドが受け取れないことがあるためJSONで送る
        socket.send(JSON.stringify({ type: 'input', data: data }));
    }
});

socket.onclose = () => {
    term.write('\r\n[ERROR] サーバーとの接続が切れました。再読み込みしてください。\r\n');
};
