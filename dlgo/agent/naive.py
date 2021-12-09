# 30급 정도 되는 무작위 바둑봇
import random
from dlgo.agent.base import Agent
from dlgo.agent.helpers import is_point_an_eye
from dlgo.goboard_slow import Move
from dlgo.gotypes import Point


class RandomBot(Agent):
    def select_move(self, game_state):
        """본인의 집을 지킬 수 있는 임의의 유효한 수를 선택한다"""
        candidates = []
        for r in range(1, game_state.board.num_rows + 1):
            for c in range(1, game_state.board.num_cols + 1):
                candidate = Point(row=r, col=c)
                if game_state.is_valid_move(Move.play(candidate)) and not is_point_an_eye(game_state.board,
                                                                                          candidate,
                                                                                          game_state.next_player):
                    candidates.append(candidate)

        if not candidates:
            return Move.pass_turn()
        return Move.play(random.choice(candidates))
