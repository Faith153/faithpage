import streamlit as st
import numpy as np
import time
import random
from typing import Optional, List, Tuple, Dict

# 페이지 설정
st.set_page_config(
    page_title="오목 게임",
    page_icon="⚫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 게임 상수
BOARD_SIZE = 15
EMPTY = 0
BLACK = 1  # 플레이어
WHITE = 2  # 컴퓨터

class OmokGame:
    def __init__(self):
        self.board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)
        self.current_player = BLACK
        self.game_over = False
        self.winner = None
        self.move_history = []
        
    def reset_game(self):
        """게임 초기화"""
        self.board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)
        self.current_player = BLACK
        self.game_over = False
        self.winner = None
        self.move_history = []
        
    def is_valid_move(self, row: int, col: int) -> bool:
        """유효한 수인지 확인"""
        return (0 <= row < BOARD_SIZE and 
                0 <= col < BOARD_SIZE and 
                self.board[row][col] == EMPTY)
    
    def make_move(self, row: int, col: int) -> bool:
        """수를 두고 승부 확인"""
        if not self.is_valid_move(row, col) or self.game_over:
            return False
            
        self.board[row][col] = self.current_player
        self.move_history.append((row, col, self.current_player))
        
        # 승부 확인
        if self.check_winner(row, col):
            self.winner = self.current_player
            self.game_over = True
        elif np.all(self.board != EMPTY):
            self.game_over = True  # 무승부
        else:
            self.current_player = WHITE if self.current_player == BLACK else BLACK
            
        return True
    
    def check_winner(self, row: int, col: int) -> bool:
        """승리 조건 확인"""
        player = self.board[row][col]
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for dx, dy in directions:
            count = 1
            
            # 한 방향으로 확인
            for i in range(1, 5):
                new_row, new_col = row + i * dx, col + i * dy
                if (0 <= new_row < BOARD_SIZE and 
                    0 <= new_col < BOARD_SIZE and 
                    self.board[new_row][new_col] == player):
                    count += 1
                else:
                    break
            
            # 반대 방향으로 확인
            for i in range(1, 5):
                new_row, new_col = row - i * dx, col - i * dy
                if (0 <= new_row < BOARD_SIZE and 
                    0 <= new_col < BOARD_SIZE and 
                    self.board[new_row][new_col] == player):
                    count += 1
                else:
                    break
            
            if count >= 5:
                return True
                
        return False
    
    def get_available_moves(self) -> List[Tuple[int, int]]:
        """가능한 수 목록 반환"""
        moves = []
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if self.board[row][col] == EMPTY:
                    moves.append((row, col))
        return moves

class AIPlayer:
    def __init__(self, difficulty: int = 5):
        self.difficulty = difficulty
        
    def get_move(self, game: OmokGame) -> Optional[Tuple[int, int]]:
        """AI의 다음 수 결정"""
        available_moves = game.get_available_moves()
        if not available_moves:
            return None
            
        # 1단계: 즉시 승리 가능한 수 찾기
        for row, col in available_moves:
            test_board = game.board.copy()
            test_board[row][col] = WHITE
            if self._check_winner_on_board(test_board, row, col, WHITE):
                return (row, col)
        
        # 2단계: 상대방 승리 차단
        for row, col in available_moves:
            test_board = game.board.copy()
            test_board[row][col] = BLACK
            if self._check_winner_on_board(test_board, row, col, BLACK):
                return (row, col)
        
        # 3단계: 위치 평가를 통한 최적수 선택
        scored_moves = []
        for row, col in available_moves:
            score = self._evaluate_position(game.board, row, col)
            scored_moves.append((row, col, score))
        
        # 점수로 정렬
        scored_moves.sort(key=lambda x: x[2], reverse=True)
        
        # 난이도에 따른 선택 범위 조정
        if self.difficulty <= 2:
            top_moves = scored_moves[:max(1, len(scored_moves) // 2)]
        elif self.difficulty <= 4:
            top_moves = scored_moves[:max(1, len(scored_moves) // 3)]
        elif self.difficulty <= 6:
            top_moves = scored_moves[:max(1, len(scored_moves) // 4)]
        elif self.difficulty <= 8:
            top_moves = scored_moves[:max(1, len(scored_moves) // 5)]
        else:
            top_moves = scored_moves[:max(1, min(3, len(scored_moves)))]
        
        # 상위 후보 중에서 랜덤 선택
        chosen_move = random.choice(top_moves)
        return (chosen_move[0], chosen_move[1])
    
    def _check_winner_on_board(self, board: np.ndarray, row: int, col: int, player: int) -> bool:
        """특정 보드 상태에서 승리 조건 확인"""
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for dx, dy in directions:
            count = 1
            
            for i in range(1, 5):
                new_row, new_col = row + i * dx, col + i * dy
                if (0 <= new_row < BOARD_SIZE and 
                    0 <= new_col < BOARD_SIZE and 
                    board[new_row][new_col] == player):
                    count += 1
                else:
                    break
            
            for i in range(1, 5):
                new_row, new_col = row - i * dx, col - i * dy
                if (0 <= new_row < BOARD_SIZE and 
                    0 <= new_col < BOARD_SIZE and 
                    board[new_row][new_col] == player):
                    count += 1
                else:
                    break
            
            if count >= 5:
                return True
                
        return False
    
    def _evaluate_position(self, board: np.ndarray, row: int, col: int) -> float:
        """위치 평가 함수"""
        score = 0.0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        # 각 방향에서 점수 계산
        for dx, dy in directions:
            # 컴퓨터(백돌) 점수
            white_score = self._evaluate_direction(board, row, col, dx, dy, WHITE)
            # 플레이어(흑돌) 차단 점수
            black_score = self._evaluate_direction(board, row, col, dx, dy, BLACK)
            
            score += white_score
            # 난이도가 높을수록 차단에 더 신경씀
            blocking_multiplier = min(1.0, self.difficulty / 10.0)
            score += black_score * blocking_multiplier
        
        # 중앙 근처 선호 (게임 초반)
        total_stones = np.count_nonzero(board)
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
                if (0 <= new_row < BOARD_SIZE and 
                    0 <= new_col < BOARD_SIZE and 
                    board[new_row][new_col] != EMPTY):
                    has_nearby_stone = True
                    break
            if has_nearby_stone:
                break
        
        if has_nearby_stone:
            score += 20
        elif total_stones > 5:
            score -= 50  # 게임 중후반에는 떨어진 곳 불이익
            
        return score
    
    def _evaluate_direction(self, board: np.ndarray, row: int, col: int, 
                          dx: int, dy: int, player: int) -> float:
        """특정 방향에서의 연결 평가"""
        consecutive = 0
        open_ends = 0
        blocked = False
        
        # 한 방향으로 체크
        for i in range(1, 5):
            new_row, new_col = row + i * dx, col + i * dy
            
            if new_row < 0 or new_row >= BOARD_SIZE or new_col < 0 or new_col >= BOARD_SIZE:
                blocked = True
                break
            
            if board[new_row][new_col] == player:
                consecutive += 1
            elif board[new_row][new_col] == EMPTY:
                open_ends += 1
                break
            else:
                blocked = True
                break
        
        # 반대 방향으로 체크
        for i in range(1, 5):
            new_row, new_col = row - i * dx, col - i * dy
            
            if new_row < 0 or new_row >= BOARD_SIZE or new_col < 0 or new_col >= BOARD_SIZE:
                break
            
            if board[new_row][new_col] == player:
                consecutive += 1
            elif board[new_row][new_col] == EMPTY:
                if not blocked:
                    open_ends += 1
                break
            else:
                break
        
        # 점수 계산
        if consecutive >= 4:
            return 1000.0  # 4개 연결 (다음에 승리)
        elif consecutive >= 3:
            return 200.0 if open_ends >= 2 else (50.0 if open_ends >= 1 else 10.0)
        elif consecutive >= 2:
            return 50.0 if open_ends >= 2 else (15.0 if open_ends >= 1 else 3.0)
        elif consecutive >= 1:
            return 15.0 if open_ends >= 2 else (5.0 if open_ends >= 1 else 1.0)
        else:
            return 0.0

def render_board(game: OmokGame, on_click_callback=None):
    """게임 보드 렌더링"""
    st.markdown("### 🎯 오목 게임판")
    
    # 보드 스타일
    st.markdown("""
    <style>
    .board-container {
        display: flex;
        justify-content: center;
        margin: 20px 0;
    }
    .board-table {
        border-collapse: collapse;
        background: linear-gradient(135deg, #8B4513 0%, #A0522D 100%);
        border-radius: 10px;
        padding: 10px;
    }
    .board-cell {
        width: 35px;
        height: 35px;
        border: 1px solid #654321;
        background: #DEB887;
        text-align: center;
        vertical-align: middle;
        cursor: pointer;
        position: relative;
    }
    .board-cell:hover {
        background: #F5DEB3;
    }
    .stone {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        margin: 3px auto;
        box-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .black-stone {
        background: linear-gradient(135deg, #2C2C2C 0%, #000000 100%);
        border: 1px solid #444;
    }
    .white-stone {
        background: linear-gradient(135deg, #FFFFFF 0%, #F8F8FF 100%);
        border: 1px solid #CCC;
    }
    .star-point {
        background: radial-gradient(circle, #654321 2px, transparent 2px);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 좌표 표시를 위한 열 생성
    cols = st.columns(BOARD_SIZE + 1)
    
    # 상단 좌표 (A-O)
    with cols[0]:
        st.write("")
    for i in range(BOARD_SIZE):
        with cols[i + 1]:
            st.markdown(f"<div style='text-align: center; font-weight: bold;'>{chr(65 + i)}</div>", 
                       unsafe_allow_html=True)
    
    # 게임 보드 행별 렌더링
    for row in range(BOARD_SIZE):
        cols = st.columns(BOARD_SIZE + 1)
        
        # 좌측 좌표 (1-15)
        with cols[0]:
            st.markdown(f"<div style='text-align: center; font-weight: bold; line-height: 35px;'>{row + 1}</div>", 
                       unsafe_allow_html=True)
        
        # 각 셀 렌더링
        for col in range(BOARD_SIZE):
            with cols[col + 1]:
                cell_value = game.board[row][col]
                
                # 화점 표시 (천원, 고목 등)
                is_star_point = (row, col) in [(3, 3), (3, 11), (7, 7), (11, 3), (11, 11)]
                star_class = "star-point" if is_star_point and cell_value == EMPTY else ""
                
                if cell_value == EMPTY:
                    # 빈 칸 - 클릭 가능한 버튼
                    if st.button("", key=f"cell_{row}_{col}", 
                               help=f"위치: {chr(65 + col)}{row + 1}"):
                        if on_click_callback and not game.game_over:
                            on_click_callback(row, col)
                else:
                    # 돌이 놓인 칸
                    stone_class = "black-stone" if cell_value == BLACK else "white-stone"
                    stone_symbol = "⚫" if cell_value == BLACK else "⚪"
                    st.markdown(f"""
                    <div class="board-cell {star_class}">
                        <div class="stone {stone_class}"></div>
                    </div>
                    """, unsafe_allow_html=True)

def main():
    st.title("🎯 인공지능 오목 게임")
    st.markdown("---")
    
    # 세션 상태 초기화
    if 'game' not in st.session_state:
        st.session_state.game = OmokGame()
        st.session_state.ai_player = AIPlayer(5)
        st.session_state.player_name = "플레이어"
        st.session_state.difficulty = 5
        st.session_state.game_started = False
        st.session_state.ai_thinking = False
    
    # 사이드바 - 게임 설정
    with st.sidebar:
        st.header("🎮 게임 설정")
        
        # 플레이어 이름
        player_name = st.text_input("플레이어 이름", value=st.session_state.player_name)
        if player_name != st.session_state.player_name:
            st.session_state.player_name = player_name
        
        # 난이도 설정
        difficulty = st.slider("AI 난이도", min_value=1, max_value=10, 
                              value=st.session_state.difficulty,
                              help="1: 매우 쉬움, 10: 매우 어려움")
        if difficulty != st.session_state.difficulty:
            st.session_state.difficulty = difficulty
            st.session_state.ai_player = AIPlayer(difficulty)
        
        st.markdown("---")
        
        # 게임 제어 버튼
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎮 새 게임", use_container_width=True):
                st.session_state.game.reset_game()
                st.session_state.game_started = True
                st.session_state.ai_thinking = False
                st.rerun()
        
        with col2:
            if st.button("🔄 초기화", use_container_width=True):
                st.session_state.game.reset_game()
                st.session_state.game_started = False
                st.session_state.ai_thinking = False
                st.rerun()
        
        st.markdown("---")
        
        # 게임 정보
        st.header("📊 게임 정보")
        
        game = st.session_state.game
        
        if game.game_over:
            if game.winner == BLACK:
                st.success(f"🎉 {st.session_state.player_name}님 승리!")
            elif game.winner == WHITE:
                st.error("🤖 컴퓨터 승리!")
            else:
                st.info("⚖️ 무승부!")
        else:
            if st.session_state.ai_thinking:
                st.info("🤔 컴퓨터가 생각 중...")
            else:
                current = "흑돌 (플레이어)" if game.current_player == BLACK else "백돌 (컴퓨터)"
                st.info(f"현재 차례: {current}")
        
        st.metric("총 수", len([m for m in game.move_history]))
        st.metric("AI 난이도", f"레벨 {difficulty}")
        
        # 게임 규칙
        st.markdown("---")
        st.header("📋 게임 규칙")
        st.markdown("""
        • 가로, 세로, 대각선으로 **5개**를 연결하면 승리
        • **흑돌(플레이어)**이 먼저 시작
        • **백돌(컴퓨터)**가 자동으로 응수
        • 난이도가 높을수록 AI가 더 똑똑해집니다
        • 좌표는 **A-O (가로), 1-15 (세로)**로 표시
        """)
    
    # 메인 게임 영역
    if not st.session_state.game_started:
        st.info("👈 사이드바에서 '새 게임' 버튼을 눌러 게임을 시작하세요!")
        
        # 게임 소개
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            ### 🎯 게임 특징
            - **10단계 난이도** 조절 가능
            - **스마트 AI** 상대
            - **직관적인 인터페이스**
            - **실시간 게임 진행**
            """)
        
        with col2:
            st.markdown("""
            ### 🧠 AI 전략
            - **즉시 승리** 판단
            - **상대 차단** 전략
            - **위치 평가** 시스템
            - **난이도별 적응**
            """)
        
        with col3:
            st.markdown("""
            ### 🎮 조작 방법
            - **클릭**으로 돌 놓기
            - **좌표 표시**로 위치 확인
            - **실시간 상태** 확인
            - **언제든 재시작** 가능
            """)
    
    else:
        # 게임 보드 렌더링
        def handle_move(row, col):
            if st.session_state.game.make_move(row, col):
                if not st.session_state.game.game_over:
                    st.session_state.ai_thinking = True
                st.rerun()
        
        render_board(st.session_state.game, handle_move)
        
        # AI 턴 처리
        if (st.session_state.game.current_player == WHITE and 
            not st.session_state.game.game_over and 
            st.session_state.ai_thinking):
            
            with st.spinner("🤖 컴퓨터가 수를 생각하고 있습니다..."):
                time.sleep(1)  # 사용자 경험을 위한 지연
                ai_move = st.session_state.ai_player.get_move(st.session_state.game)
                if ai_move:
                    st.session_state.game.make_move(ai_move[0], ai_move[1])
                st.session_state.ai_thinking = False
                st.rerun()
        
        # 최근 수 표시
        if st.session_state.game.move_history:
            st.markdown("### 📝 최근 수")
            recent_moves = st.session_state.game.move_history[-5:]  # 최근 5수만 표시
            
            cols = st.columns(len(recent_moves))
            for i, (row, col, player) in enumerate(recent_moves):
                with cols[i]:
                    player_name = st.session_state.player_name if player == BLACK else "컴퓨터"
                    stone = "⚫" if player == BLACK else "⚪"
                    position = f"{chr(65 + col)}{row + 1}"
                    st.markdown(f"""
                    <div style='text-align: center; padding: 10px; 
                                background: {"#f0f0f0" if player == BLACK else "#e0e0e0"}; 
                                border-radius: 5px; margin: 2px;'>
                        <div style='font-size: 20px;'>{stone}</div>
                        <div style='font-size: 12px;'>{player_name}</div>
                        <div style='font-size: 14px; font-weight: bold;'>{position}</div>
                    </div>
                    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
