// 既存の定義とぶつからないように var を使用
var term = term || new Terminal({
    cursorBlink: true,
    fontSize: 18
});

// まだ開いていなければターミナルを開始
if (!document.getElementById('terminal').innerHTML) {
    term.open(document.getElementById('terminal'));
}

// 接続先URL（自分のRenderのバックエンドURLであることを確認してください）
var socketUrl = 'wss://yggdrasil-websocket-backend.onrender.com/websocket';
var socket = new WebSocket(socketUrl);

socket.onopen = function() {
    term.write('[SYSTEM] サーバーに接続しました。入力待ちです...\r\n');
};

socket.onmessage = function(event) {
    term.write(event.data);
};

// 入力をサーバーに送る
term.onData(function(data) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        // 現在のサーバー設定に合わせてJSON形式で送信
        socket.send(JSON.stringify({ type: 'input', data: data }));
    }
});

socket.onclose = function() {
    term.write('\r\n[ERROR] サーバーとの接続が切れました。再読み込みしてください。\r\n');
};
