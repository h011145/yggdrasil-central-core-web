#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import time

def main():
    # 画面を綺麗にする
    sys.stdout.write("\033[2J\033[H")
    
    print("Selecting slot... (Simulated)")
    print("\nカナタ: 「接続を感知。……またやるの？」")
    print("\n" + "="*50)
    print(" YGGDRASIL CENTRAL CORE - TEST MODE")
    print("="*50)
    print("カナタ: 「ひろしの神格レベル 1。ガレージポイント 3000。」")
    
    # プログラムが終了しないようにループを作る
    while True:
        print("\n--- 【メニュー】番号を打って Enter を押してね ---")
        print(" 1: 義体改造 (GARAGE)")
        print(" 2: 戦闘アーカイブ (COMBAT)")
        print(" 3: ネクスト戦記 (NEXT WAR)")
        print(" q: 終了する")
        print("-" * 50)
        
        # ここでユーザーの入力をじっと待ちます
        sys.stdout.write("どれにする？ > ")
        sys.stdout.flush()
        
        # 入力を受け取る（Enterを押すまでここで止まります）
        line = sys.stdin.readline()
        
        if not line:
            break
            
        choice = line.strip().lower()

        # 入力内容に応じた反応
        if choice == '1':
            print("\nカナタ: 「ガレージを開くよ。でも今は準備中なんだ。」")
        elif choice == '2':
            print("\nカナタ: 「戦闘シミュレーションをロードするね…（準備中）」")
        elif choice == '3':
            print("\nカナタ: 「ネクスト戦記……あの地獄に戻るつもり？」")
        elif choice == 'q':
            print("\nカナタ: 「バイバイ、ひろし。また接続してね。」")
            break # ここで初めてループを抜けて終了する
        else:
            print(f"\nカナタ: 「 '{choice}' ？ ……ちょっと、真面目に選んでよ。」")
        
        print("\n" + "." * 30)
        time.sleep(0.5)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"エラーが発生したよ: {e}")
