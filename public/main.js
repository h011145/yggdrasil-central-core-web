const terminal = document.getElementById('game-container');
let ws;

// 画面クリックで通信開始（ブラウザのセキュリティ制限対策）
window.addEventListener('click', () => {
    if (!ws) {
        initWebSocket();
        terminal.innerHTML = "SYSTEM: 接続中...<br>";
    }
}, { once: true });

function initWebSocket() {
    // 今のURLが https なら wss、http なら ws に自動切り替え
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        terminal.innerHTML = "SYSTEM: 接続完了。データ同期中...<br>";
        // サーバー側が PTY/Curses を開始するための信号を送る（必要に応じて）
        ws.send("\n"); 
    };

    ws.onmessage = (event) => {
        // サーバーから届いた文字を画面に表示
        // Cursesの制御文字が含まれるため、本来はxterm.js等が必要ですが、
        // まずは文字が出るか確認するために innerText を更新します。
        const data = event.data;
        terminal.innerText = data; 
    };

    ws.onclose = () => {
        terminal.innerHTML += "<br>SYSTEM: 接続が切断されました。再読み込みしてください。";
    };

    ws.onerror = (err) => {
        console.error("WebSocket Error:", err);
    };
}

// キー入力をサーバーに送信
window.addEventListener('keydown', (e) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
        // Cursesが認識できるように1文字ずつ送る
        ws.send(e.key);
    }
});
