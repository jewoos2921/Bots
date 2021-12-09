# 붓이 자테 대국을 치르는 스크립트
from dlgo import agent
from dlgo import goboard_slow
from dlgo import gotypes
from dlgo.utils import print_move, print_board
import time


def main():
    board_size = 9
    game = goboard_slow.GameState.new_game(board_size)
    bots = {
        gotypes.Player.black: agent.naive.RandomBot(),
        gotypes.Player.white: agent.naive.RandomBot(),
    }
    while not game.is_over():
        time.sleep(0.3)
        # 봇의 수가 일기 어려울 정도로 빠르지 않도록 0.3초의 휴지 기간을 둔다.
        print(chr(27) + "[2J")  # 각 수에 앞서 화면을 초기화한다. 그러면 항항 명령줄의 같은 위치에 화면이 출력될 것이다.
        print_board(game.board)
        bot_move = bots[game.next_player].select_move(game)
        print_move(game.next_player, bot_move)
        game = game.apply_move(bot_move)


if __name__ == '__main__':
    main()
