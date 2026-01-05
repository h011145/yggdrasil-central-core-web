const terminal = document.getElementById('game-container');
let ws;

// 画面クリックで通信開始（ブラウザの制限対策）
window.addEventListener('click', () => {
    if (!ws || ws.readyState === WebSocket.CLOSED) {
        initWebSocket();
    }
}, { once: true });

function initWebSocket() {
    // 【重要】今のブラウザのURLから、自動でWebSocketのURLを作る
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws`; // これでバックエンドの /ws を狙い撃ちする

    console.log("Connecting to:", wsUrl);
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        terminal.innerHTML = "SYSTEM: 接続完了。コアアクセス中...<br>";
        // サーバーに「繋がったよ」と合図を送る
        ws.send("hello"); 
    };

    ws.onmessage = (event) => {
        // サーバーからの文字を画面に出す
        // Cursesの制御文字を無視して文字だけ出すための簡易処理
        const data = event.data;
        terminal.innerText += data; 
        // 常に最新の行が見えるようにスクロール
        terminal.scrollTop = terminal.scrollHeight;
    };

    ws.onclose = () => {
        terminal.innerHTML += "<br>SYSTEM: 接続が切断されました。";
    };

    ws.onerror = (err) => {
        console.error("WebSocket Error:", err);
        terminal.innerHTML += "<br>SYSTEM: 通信エラーが発生しました。";
    };
}

// キー入力をサーバーに送信
window.addEventListener('keydown', (e) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
        // 1文字だけ送る（これがV3に伝わる）
        ws.send(e.key);
    }
});
