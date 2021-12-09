from dlgo.gotypes import Point


def is_point_an_eye(board, point, color):
    if board.get(point) is not None:  # 집는 빈 점이다.
        return False
    # 모든 근접한 점에 돌들이 놓여 있다.
    for neighbor in point.neighbors():
        if board.is_on_grid(neighbor):
            neighbor_color = board.get(neighbor)
            if neighbor_color != color:
                return False

    # 점이 판 가운데라면 네 개의 귀퉁이 중 세 개가 사용 가능해야 한다.
    # 경계선에서는 모든 귀퉁이가 사용 가능해야 한다.
    friendly_corners = 0
    off_board_corners = 0

    corners = [
        Point(point.row - 1, point.col - 1),
        Point(point.row - 1, point.col + 1),
        Point(point.row + 1, point.col - 1),
        Point(point.row + 1, point.col + 1),
    ]
    for corner in corners:
        if board.is_on_grid(corner):
            corner_color = board.get(corner)
            if corner_color == color:
                friendly_corners += 1
        else:
            off_board_corners += 1
    if off_board_corners > 0:
        return off_board_corners + friendly_corners == 4  # 점이 경계선이나 귀퉁이에 있다.
    return friendly_corners >= 3  # 점이 가운데에 있다.
