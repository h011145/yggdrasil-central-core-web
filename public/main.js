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
const socket = new WebSocket('wss://yggdrasil-websocket-backend.onrender.com/websocket');

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
socket.onopen = () => {
    term.write('\x1b[1;33m[SYSTEM] サーバーに接続しました。\x1b[0m\r\n');
    term.write('\x1b[1;32m【重要】まずこの黒い画面内を一度クリックしてください。\x1b[0m\r\n');
    term.write('\x1b[1;32mそのあと、キーボードで入力が可能になります。\x1b[0m\r\n');
    term.write('--------------------------------------------------\r\n');
    // 接続時に最初のサイズを送信
    fitAddon.fit();
    sendTerminalSize();
};

// サーバーからメッセージを受信したときのイベント
socket.onmessage = (event) => {
    term.write(event.data);
};

// ターミナルでユーザーがキー入力したときのイベント
term.onData(data => {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'input', data: data }));
    }
});

// 接続が閉じたときのイベント
socket.onclose = () => {
    term.write('\r\n\x1b[1;31m[ERROR] 接続が切れました。再読み込みしてください。\x1b[0m\r\n');
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
