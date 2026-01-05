import curses
from games.card_battle import CardBattle

def main(stdscr):
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, -1)
    
    while True:
        stdscr.clear()
        stdscr.attron(curses.color_pair(1))
        stdscr.border()
        stdscr.addstr(1, 2, " YGGDRASIL CENTRAL CORE OS - v3.0 ")
        stdscr.addstr(4, 6, "[2] 戦闘アーカイブ (CARD BATTLE)")
        stdscr.addstr(5, 6, "[q] システム終了")
        stdscr.addstr(10, 4, "COMMAND > ")
        stdscr.refresh()
        
        key = stdscr.getch()
        if key == ord('q'): break
        elif key == ord('2'):
            # カードバトル起動
            game = CardBattle(stdscr)
            game.play()

if __name__ == "__main__":
    curses.wrapper(main)
