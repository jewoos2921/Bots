import copy

from dlgo import zobrist
from dlgo.gotypes import Player


# 수 설정: 돌 놓기, 차례 넘기기, 대국 포기
class Move:
    def __init__(self, point=None, is_pass=False, is_resign=False):
        assert (point is not None) ^ is_pass ^ is_resign
        self.point = point
        self.is_play = (self.point is not None)
        self.is_pass = is_pass
        self.is_resign = is_resign

    @classmethod
    def play(cls, point):  # 이 수는 바둑판에 돌을 놓는다.
        return Move(point=point)

    @classmethod
    def pass_turn(cls):  # 이 수는 차례를 넘긴다.
        return Move(is_pass=True)

    @classmethod
    def resign(cls):  # 이 수는 현재 대국을 포기한다.
        return Move(is_resign=True)


# 이음을 set으로 인코딩
# 돌과 활로에 대한 불변 집합형을 사용
class GoString:
    def __init__(self, color, stones, liberties):
        self.color = color
        self.stones = frozenset(stones)  # 돌과 활로는 frozenset인스턴스이다.
        self.liberties = frozenset(liberties)

    def without_liberty(self, point):  # remove_liberty 대체
        new_liberties = self.liberties - set([point])
        return GoString(self.color, self.stones, new_liberties)

    def with_liberty(self, point):  # add_liberty 대체
        new_liberties = self.liberties | set([point])
        return GoString(self.color, self.stones, new_liberties)

    def merged_with(self, go_string):  # 양 선수의 이음의 모든 돌을 저장한 새 이음츨 반환한다.
        assert go_string.color == self.color
        combined_stones = self.stones | go_string.stones
        return GoString(self.color, combined_stones, (self.liberties | go_string.liberties) - combined_stones)

    @property
    def num_liberties(self):
        return len(self.liberties)

    def __eq__(self, other):
        return isinstance(other,
                          GoString) and self.color == other.color \
               and self.stones == other.stones and self.liberties == other.liberties


class Board:
    # 빈 바둑파에 _hash값을 넣음
    # 주어진 열과 행 수의 빈 격자로 바둑판을 초기화한다.
    def __init__(self, num_rows, num_cols):
        self.num_rows = num_rows
        self.num_cols = num_cols
        self._grid = {}
        self._hash = zobrist.EMPTY_BOARD

    # 활로 파악용 이웃 점 확인
    def place_stone(self, player, point):
        assert self.is_on_grid(point)
        assert self._grid.get(point) is None
        adjacent_same_color = []
        adjacent_opposite_color = []
        liberties = []
        for neighbor in point.neighbors():  # 우선 이 점과 바로 연결된 이웃을 확인한다.
            if not self.is_on_grid(neighbor):
                continue
            neighbor_string = self._grid.get(neighbor)
            if neighbor_string is None:
                liberties.append(neighbor)
            elif neighbor_string.color == player:
                if neighbor_string not in adjacent_same_color:
                    adjacent_same_color.append(neighbor_string)
            else:
                if neighbor_string not in adjacent_opposite_color:
                    adjacent_opposite_color.append(neighbor_string)

        # 돌은 놓는 것은 해당 돌의 해시값을 적용하는 것이다.
        new_string = GoString(player, [point], liberties)

        for same_color_string in adjacent_same_color:  # 같은 색의 근접한 이음을 합친다.
            new_string = new_string.merged_with(same_color_string)
        for new_string_point in new_string.stones:
            self._grid[new_string_point] = new_string

        self._hash ^= zobrist.HASH_CODE[point, player]  # 이 점과 선수의 해시 코드를 적용한다.

        for other_color_string in adjacent_opposite_color:  # 다른 색의 근접한 이음의 활로를 줄인다.
            replacement = other_color_string.without_liberty(point)
            if replacement.num_liberties:  # 반대색의 이음에세 활로를 제거한다.
                self._replace_string(other_color_string.without_liberty(point))
            else:  # 다른 색 이음의 활로가 0이 되면 그 돌을 제거한다.
                self._remove_string(other_color_string)

    # 돌 놓기
    def is_on_grid(self, point):
        return 1 <= point.row <= self.num_rows and 1 <= point.col <= self.num_cols

    # 돌 따내기
    def get(self, point):
        # 바둑판 위의 점 내용을 반환한다. 만약 돌이
        # 해당 점 위에 있으면 Player를 반환하고,
        # 아니면 None을 반환한다.
        string = self._grid.get(point)
        if string is None:
            return None
        return string.color

    def get_go_string(self, point):
        # 해당 점의 돌에 연결된 모든 이음을 반환한다.
        # 만약 돌이 해당 점 위에 있으면 GoString을
        # 반환하고, 아니면 None을 반환한다.
        string = self._grid.get(point)
        if string is None:
            return None
        return string

    def _remove_string(self, string):
        for point in string.stones:
            for neighbor in point.neighbors():  # 이음을 제거하면 다른 이음에 활로가 생긴다.
                neighbor_string = self._grid.get(neighbor)
                if neighbor_string is None:
                    continue
                if neighbor_string is not string:
                    self._replace_string(neighbor_string.with_liberty(point))
            self._grid[point] = None

            # 조브리스트 해싱으로 이 수의 해시값을 비적용해야한다.
            self._hash ^= zobrist.HASH_CODE[point, string.color]

    # 돌을 제거하는 것은 돌의 해시값을 비적용하는 것이다.
    def _replace_string(self, new_string):
        for point in new_string.stones:
            self._grid[point] = new_string

    # 판의 햔재 조브리스트 해시값을 반환함
    def zobrist_hash(self):
        return self._hash


# 바둑 게임 현황 인코딩
# 조브리스트 해기로 경기 상태 초기화
class GameState:
    def __init__(self, board, next_player, previous, move):
        self.board = board
        self.next_player = next_player
        self.previous_state = previous
        if self.previous_state is None:
            self.previous_states = frozenset()
        else:
            self.previous_states = frozenset(
                previous.previous_states | {(previous.next_player, previous.board.zobrist_hash())})

        self.last_move = move

    def apply_move(self, move):  # 수를 둔 후 새 GameState 반환
        if move.is_play:
            next_board = copy.deepcopy(self.board)
            next_board.place_stone(self.next_player, move.point)
        else:
            next_board = self.board
        return GameState(next_board, self.next_player.other, self, move)

    @classmethod
    def new_game(cls, board_size):
        if isinstance(board_size, int):
            board_size = (board_size, board_size)
        board = Board(*board_size)
        return GameState(board, Player.black, None, None)

    # 대국 종료 판단
    def is_over(self):
        if self.last_move is None:
            return False
        if self.last_move.is_resign:
            return True
        second_last_move = self.previous_state.last_move
        if second_last_move is None:
            return False
        return self.last_move.is_pass and second_last_move.is_pass

    # 자충수 규칙을 적용
    def is_move_self_capture(self, player, move):
        if not move.is_play:
            return False
        next_board = copy.deepcopy(self.board)
        next_board.place_stone(player, move.point)
        new_string = next_board.get_go_string(move.point)
        return new_string.num_liberties == 0

    # 현재 게임 상태가 패 규칙을 위반하는가?
    @property
    def situation(self):
        return (self.next_player, self.board)

    # 조브리스트 해시로 패 상태를 빠르게 확인하기
    def does_move_violate_ko(self, player, move):
        if not move.is_play:
            return False
        next_board = copy.deepcopy(self.board)
        next_board.place_stone(player, move.point)
        next_situation = (player.other, next_board.zoblist_hash(),)
        return next_situation in self.previous_states

    # 주어진 게임 상태에서 이 수는 유효한가?
    def is_valid_move(self, move):
        if self.is_over():
            return False
        if move.is_pass or move.is_resign:
            return True
        return (self.board.get(move.point) is None and not self.is_move_self_capture(self.next_player, move) and
                not self.does_move_violate_ko(self.next_player, move))
