# board.py
from pieces import *

class Board:
    def __init__(self):
        self.grid = [[None for _ in range(8)] for _ in range(8)]#리스트 컴프리헨션
        self.turn = 'w' # 'w' 선공 시작
        self.last_move = None # 앙파상 추적용: (start_pos, end_pos, piece)
        self.game_over_status = None # None, 'Checkmate_w', 'Checkmate_b', 'Stalemate'
        self.setup_board()
    def reverseColor(self,color):
        if color =="w":
            return "b"
        elif color == "b":
            return "w"
        return
    def setup_board(self):
        placement = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for col in range(8):
            self.grid[0][col] = placement[col]('b')
            self.grid[1][col] = Pawn('b')
            self.grid[6][col] = Pawn('w')
            self.grid[7][col] = placement[col]('w')

    def find_king(self, color, grid):
        """특정 색상 킹의 위치를 반환"""
        for r in range(8):
            for c in range(8):
                if grid[r][c] and grid[r][c].name == 'k' and grid[r][c].color == color:
                    return (r, c)
        return None

    def is_under_attack(self, pos, attacker_color, grid):
        #특정 좌표(pos)가 적에게 공격받고 있는지 검증 (체크 및 캐슬링 통과 칸 확인용)
        for r in range(8):
            for c in range(8):
                piece = grid[r][c]
                if piece and piece.color == attacker_color:
                    # 무한 루프 방지를 위해 King 기물의 기본 이동(캐슬링 제외) 범위 내에 있는지 판단
                    if piece.name == 'k':
                        if max(abs(pos[0]-r), abs(pos[1]-c)) <= 1: return True
                        #킹의 공격범위 안에 있는가 따로 검사
                    elif pos in piece.get_valid_moves((r, c), grid, self.last_move):
                        #그냥 get_valid_moves 호출
                        return True
        return False

    def is_in_check(self, color, grid):
        #킹이 체크당한 상태인지 확인
        king_pos = self.find_king(color, grid)
        if not king_pos: 
            return False
        enemy_color = self.reverseColor(color)
        return self.is_under_attack(king_pos, enemy_color, grid)

    def get_strict_legal_moves(self, start_pos):
        #체크 회피 의무를 반영한 '진짜 움직일 수 있는 칸'만 필터링
        r, c = start_pos
        piece = self.grid[r][c]
        if not piece or piece.color != self.turn:
            # 자리에 말이 없거나 자기턴이 아닐경우
            return []
        pseudo_moves = piece.get_valid_moves(start_pos, self.grid, self.last_move)
        strict_moves = []

        for move in pseudo_moves:
            # 시뮬레이션: 가상으로 말을 옮겨봄
            target_r, target_c = move
            original_target = self.grid[target_r][target_c]

            self.grid[target_r][target_c] = piece
            self.grid[r][c] = None

            # 가상 이동 상태에서 내가 체크에 걸리지 않는다면 합법적인 수
            if not self.is_in_check(self.turn, self.grid):
                # 특수 예외: 캐슬링할 때 통과하는 칸들이 공격받고 있다면 제외해야 함
                if piece.name == 'k' and abs(c - target_c) == 2:
                    enemy = self.reverseColor(self.turn)
                    if target_c == 6:
                        pass_c = 5 
                    else:
                        pass_c = 3
                    if not self.is_under_attack((r, pass_c), enemy, self.grid) and not self.is_in_check(self.turn, self.grid):
                        strict_moves.append(move)
                else:
                    strict_moves.append(move)

            # 보드 원상복구 (가장 중요)
            self.grid[r][c] = piece
            self.grid[target_r][target_c] = original_target

        return strict_moves

    def move_piece(self, start_pos, end_pos):
        #실제 이동을 수행하고 특수 규칙을 정산한 후 턴을 넘깁니다.
        if end_pos not in self.get_strict_legal_moves(start_pos):
            return False

        sr, sc = start_pos
        er, ec = end_pos
        piece = self.grid[sr][sc]

        # [특수 규칙 처리 1] 앙파상 격파 처리
        if piece.name == 'p' and sc != ec and self.grid[er][ec] is None:
            self.grid[sr][ec] = None # 옆 칸에 있던 상대 폰 획득

        # [특수 규칙 처리 2] 캐슬링 발생 시 룩도 같이 이동
        if piece.name == 'k' and abs(sc - ec) == 2:
            if ec == 6: # 킹사이드
                self.grid[sr][5] = self.grid[sr][7]
                self.grid[sr][7] = None
                self.grid[sr][5].has_moved = True
            elif ec == 2: # 퀸사이드
                self.grid[sr][3] = self.grid[sr][0]
                self.grid[sr][0] = None
                self.grid[sr][3].has_moved = True

        # 실제 물리 이동
        self.grid[er][ec] = piece
        self.grid[sr][sc] = None
        piece.has_moved = True

        # [특수 규칙 처리 3] 폰 프로모션 (간결성을 위해 가장 좋은 퀸으로 즉시 자동 변환)
        if piece.name == 'p' and (er == 0 or er == 7):
            self.grid[er][ec] = Queen(piece.color)

        # 앙파상 추적용 라스트 무브 기록 후 턴 교체
        self.last_move = (start_pos, end_pos, piece)
        self.turn = self.reverseColor(self.turn)
        # 이동 직후 게임 종료 여부 정산
        self.check_game_status()
        return True

    def check_game_status(self):
        #현재 턴인 플레이어가 둘 수 있는 수가 있는지 확인하여 승패를 판단합니다.
        has_any_move = False
        for r in range(8):
            for c in range(8):
                if self.grid[r][c] and self.grid[r][c].color == self.turn:
                    if len(self.get_strict_legal_moves((r, c))) > 0:
                        has_any_move = True
                        break
            if has_any_move:
                break
        if not has_any_move:
            if self.is_in_check(self.turn, self.grid):
                # 체크 상태인데 둘 수가 없으면 '체크메이트' (이전 턴 유저 승리)
                self.game_over_status = f'Checkmate_{self.reverseColor(self.turn)}'
            else:
                # 체크가 아닌데 둘 수가 없으면 무승부 '스테일메이트'
                self.game_over_status = 'Stalemate'
    
