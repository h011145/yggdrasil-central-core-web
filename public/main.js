// xterm.jsのターミナルを初期化
const term = new Terminal({
    cursorBlink: true,
    theme: {
        background: '#000000',
        foreground: '#00FF00',
    }
});
const fitAddon = new FitAddon.FitAddon();
term.loadAddon(fitAddon);

// 'terminal'というIDを持つdiv要素にターミナルをアタッチ
term.open(document.getElementById('terminal'));

// WebSocketサーバーに接続
const socket = new WebSocket(`wss://${window.location.host}/websocket`);

function sendTerminalSize() {
    if (socket.readyState === WebSocket.OPEN) {
        const size = {
            type: 'resize',
            cols: term.cols,
            rows: term.rows
        };
        socket.send(JSON.stringify(size));
    }
}

// 接続が開いたときのイベント
socket.onopen = function(event) {
    term.write('サーバーに接続しました。
');
    term.write('画面をクリックして、ターミナル操作を有効にしてください。
');
    // 接続時に最初のサイズを送信
    fitAddon.fit();
    sendTerminalSize();
};

// サーバーからメッセージを受信したときのイベント
socket.onmessage = function(event) {
    // サーバーからのデータをターミナルに書き込む
    term.write(event.data);
};

// ターミナルでユーザーがキー入力したときのイベント
term.onData(data => {
    // 入力されたデータをWebSocket経由でサーバーに送信
    const message = { type: 'input', data: data };
    socket.send(JSON.stringify(message));
});

// 接続が閉じたときのイベント
socket.onclose = function(event) {
    term.write('\r\nサーバーとの接続が切れました。');
};

// エラーが発生したときのイベント
socket.onerror = function(error) {
    term.write('\r\nエラーが発生しました: ' + error.message);
};

// ウィンドウサイズが変更されたときにターミナルのサイズを調整し、サーバーに通知
window.addEventListener('resize', () => {
    fitAddon.fit();
    sendTerminalSize();
});
