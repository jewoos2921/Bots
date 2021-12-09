# 바둑 에이전트의 핵심 인터페이스
class Agent:
    def __init__(self):
        pass

    def select_move(self, game_state):
        raise NotImplementedError()

