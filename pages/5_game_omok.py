import random
from typing import List, Optional, Tuple, Literal

Player = Literal['black', 'white', None]
GameBoard = List[List[Optional[str]]]
Move = Tuple[int, int]

# --- 1. 승리 체크 함수 ---
def check_winner(board: GameBoard, row: int, col: int) -> Optional[str]:
    player = board[row][col]
    if not player:
        return None

    directions = [
        (0, 1),    # horizontal
        (1, 0),    # vertical
        (1, 1),    # diagonal \
        (1, -1),   # diagonal /
    ]

    for dx, dy in directions:
        count = 1
        # Check in positive direction
        for i in range(1, 5):
            new_row = row + i * dx
            new_col = col + i * dy
            if new_row < 0 or new_row >= 15 or new_col < 0 or new_col >= 15:
                break
            if board[new_row][new_col] != player:
                break
            count += 1
        # Check in negative direction
        for i in range(1, 5):
            new_row = row - i * dx
            new_col = col - i * dy
            if new_row < 0 or new_row >= 15 or new_col < 0 or new_col >= 15:
                break
            if board[new_row][new_col] != player:
                break
            count += 1
        if count >= 5:
            return player
    return None

# --- 2. 수 평가 함수 ---
def evaluate_move(board: GameBoard, row: int, col: int, difficulty: int) -> float:
    score = 0
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

    # 각 방향에서 점수 계산
    for dx, dy in directions:
        white_score = evaluate_direction(board, row, col, dx, dy, 'white')
        black_score = evaluate_direction(board, row, col, dx, dy, 'black')
        score += white_score
        # 난이도가 높을수록 상대 차단 점수 반영
        blocking_multiplier = min(1.0, difficulty / 10)
        score += black_score * blocking_multiplier

    # 중앙 근처 선호 (게임 초반)
    total_stones = sum(cell is not None for r in board for cell in r)
    if total_stones < 10:
        center_distance = abs(row - 7) + abs(col - 7)
        score += (14 - center_distance) * 2

    # 이미 놓인 돌 근처 선호
    has_nearby_stone = False
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            if dx == 0 and dy == 0:
                continue
            new_row, new_col = row + dx, col + dy
            if 0 <= new_row < 15 and 0 <= new_col < 15:
                if board[new_row][new_col] is not None:
                    has_nearby_stone = True
                    break
        if has_nearby_stone:
            break
    if has_nearby_stone:
        score += 20
    elif total_stones > 5:
        score -= 50

    return score

def evaluate_direction(board: GameBoard, row: int, col: int, dx: int, dy: int, player: str) -> int:
    score = 0
    consecutive = 0
    open_ends = 0
    blocked = False

    # 한 방향 체크
    for i in range(1, 5):
        new_row = row + i * dx
        new_col = col + i * dy
        if new_row < 0 or new_row >= 15 or new_col < 0 or new_col >= 15:
            blocked = True
            break
        if board[new_row][new_col] == player:
            consecutive += 1
        elif board[new_row][new_col] is None:
            open_ends += 1
            break
        else:
            blocked = True
            break

    # 반대 방향 체크
    for i in range(1, 5):
        new_row = row - i * dx
        new_col = col - i * dy
        if new_row < 0 or new_row >= 15 or new_col < 0 or new_col >= 15:
            break
        if board[new_row][new_col] == player:
            consecutive += 1
        elif board[new_row][new_col] is None:
            if not blocked:
                open_ends += 1
            break
        else:
            break

    # 점수 계산
    if consecutive >= 4:
        score = 1000
    elif consecutive >= 3:
        score = 200 if open_ends >= 2 else 50 if open_ends >= 1 else 10
    elif consecutive >= 2:
        score = 50 if open_ends >= 2 else 15 if open_ends >= 1 else 3
    elif consecutive >= 1:
        score = 15 if open_ends >= 2 else 5 if open_ends >= 1 else 1

    return score

# --- 3. 컴퓨터 수 선택(AI) ---
def get_computer_move(board: GameBoard, difficulty: int) -> Optional[Move]:
    available_moves: List[Move] = [
        (row, col)
        for row in range(15)
        for col in range(15)
        if board[row][col] is None
    ]
    if not available_moves:
        return None

    # 1. 즉시 승리 체크(white)
    for move in available_moves:
        test_board = [r.copy() for r in board]
        test_board[move[0]][move[1]] = 'white'
        if check_winner(test_board, move[0], move[1]) == 'white':
            return move

    # 2. 상대 승리 차단(black)
    for move in available_moves:
        test_board = [r.copy() for r in board]
        test_board[move[0]][move[1]] = 'black'
        if check_winner(test_board, move[0], move[1]) == 'black':
            return move

    # 3. 위협/기회 평가 후 점수별 정렬
    scored_moves = []
    for move in available_moves:
        score = evaluate_move(board, move[0], move[1], difficulty)
        scored_moves.append((move, score))
    scored_moves.sort(key=lambda x: x[1], reverse=True)

    # 난이도별 상위 후보군 결정
    length = len(scored_moves)
    if difficulty <= 2:
        top_moves_count = max(1, int(length * 0.5))
    elif difficulty <= 4:
        top_moves_count = max(1, int(length * 0.3))
    elif difficulty <= 6:
        top_moves_count = max(1, int(length * 0.2))
    elif difficulty <= 8:
        top_moves_count = max(1, int(length * 0.1))
    else:
        top_moves_count = max(1, min(3, length))

    top_moves = [move for move, score in scored_moves[:top_moves_count]]
    return random.choice(top_moves) if top_moves else None

# --- 4. 테스트/실행 예시 ---
if __name__ == "__main__":
    # 빈 보드
    board = [[None for _ in range(15)] for _ in range(15)]
    # 예시: 흑돌 한 수 두기
    board[7][7] = 'black'
    difficulty = 7

    move = get_computer_move(board, difficulty)
    print("AI가 추천한 수:", move)
