// main.js - 案内表示 & 入力強化版
const term = new Terminal({
    cursorBlink: true,
    fontSize: 18,
    theme: { background: '#000000', foreground: '#00ff00' }
});
term.open(document.getElementById('terminal'));

// RenderのバックエンドURLに書き換えてください
const socket = new WebSocket('wss://yggdrasil-websocket-backend.onrender.com/websocket');

socket.onopen = () => {
    term.write('\x1b[1;33m[SYSTEM] サーバーに接続しました。\x1b[0m\r\n');
    term.write('\x1b[1;32m【重要】まずこの黒い画面内を一度クリックしてください。\x1b[0m\r\n');
    term.write('\x1b[1;32mそのあと、キーボードで入力が可能になります。\x1b[0m\r\n');
    term.write('--------------------------------------------------\r\n');
};

socket.onmessage = (event) => {
    term.write(event.data);
};

// 入力をリアルタイムでサーバーへ送信
term.onData(data => {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'input', data: data }));
    }
});

socket.onclose = () => {
    term.write('\r\n\x1b[1;31m[ERROR] 接続が切れました。再読み込みしてください。\x1b[0m\r\n');
};
