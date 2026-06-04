# pieces.py

class Piece:
    def __init__(self, color, name):
        self.color = color  # 'w' or 'b'
        self.name = name
        self.image_key = color + name 
        self.has_moved = False  # 캐슬링 및 폰 2칸 전진 검증용
        
    def __repr__(self):
        return self.image_key

    def get_valid_moves(self, current_pos, board_grid, last_move=None):
        return []

    def _get_sliding_moves(self, current_pos, board_grid, directions):
        moves = []
        r, c = current_pos
        for dr, dc in directions:
            for step in range(1, 8):
                nr, nc = r + (dr * step), c + (dc * step)
                if not (0 <= nr < 8 and 0 <= nc < 8): break
                target = board_grid[nr][nc]
                if target is None:
                    moves.append((nr, nc))
                else:
                    if target.color != self.color:
                        moves.append((nr, nc))
                    break
        return moves


class Pawn(Piece):
    def __init__(self, color): super().__init__(color, 'p')
    def get_valid_moves(self, current_pos, board_grid, last_move=None):
        moves = []
        r, c = current_pos
        direction = -1 if self.color == 'w' else 1
        
        # 1. 한 칸 전진
        nr = r + direction
        if 0 <= nr < 8 and board_grid[nr][c] is None:
            moves.append((nr, c))
            # 두 칸 전진
            if not self.has_moved:
                nr2 = r + (2 * direction)
                if board_grid[nr2][c] is None:
                    moves.append((nr2, c))

        # 2. 일반 대각선 잡기
        for dc in [-1, 1]:
            nc = c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                target = board_grid[nr][nc]
                if target and target.color != self.color:
                    moves.append((nr, nc))

        # 3. 특수 규칙: 앙파상 (En Passant)
        if last_move:
            start_p, end_p, p_piece = last_move
            # 직전 턴에 상대 폰이 2칸 전진해서 내 폰 바로 옆에 나란히 섰을 때
            if p_piece.name == 'p' and abs(start_p[0] - end_p[0]) == 2 and end_p[0] == r:
                if end_p[1] == c + 1 or end_p[1] == c - 1:
                    moves.append((r + direction, end_p[1])) # 적 폰의 뒤 칸으로 이동 가능
                    
        return moves


class Knight(Piece):
    def __init__(self, color): super().__init__(color, 'n')
    def get_valid_moves(self, current_pos, board_grid, last_move=None):
        moves = []
        r, c = current_pos
        jumps = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
        for dr, dc in jumps:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                target = board_grid[nr][nc]
                if target is None or target.color != self.color: moves.append((nr, nc))
        return moves


class Rook(Piece):
    def __init__(self, color): super().__init__(color, 'r')
    def get_valid_moves(self, current_pos, board_grid, last_move=None):
        return self._get_sliding_moves(current_pos, board_grid, [(-1, 0), (1, 0), (0, -1), (0, 1)])


class Bishop(Piece):
    def __init__(self, color): super().__init__(color, 'b')
    def get_valid_moves(self, current_pos, board_grid, last_move=None):
        return self._get_sliding_moves(current_pos, board_grid, [(-1, -1), (-1, 1), (1, -1), (1, 1)])


class Queen(Piece):
    def __init__(self, color): super().__init__(color, 'q')
    def get_valid_moves(self, current_pos, board_grid, last_move=None):
        return self._get_sliding_moves(current_pos, board_grid, [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)])


class King(Piece):
    def __init__(self, color): super().__init__(color, 'k')
    def get_valid_moves(self, current_pos, board_grid, last_move=None):
        moves = []
        r, c = current_pos
        steps = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in steps:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                target = board_grid[nr][nc]
                if target is None or target.color != self.color: moves.append((nr, nc))
                
        # 특수 규칙: 캐슬링 (Castling) - 단순 이동 범위만 추가 (실제 위험 검증은 board에서 진행)
        if not self.has_moved:
            # 킹사이드 캐슬링 (우측)
            r_rook = board_grid[r][7]
            if r_rook and r_rook.name == 'r' and not r_rook.has_moved:
                if board_grid[r][5] is None and board_grid[r][6] is None:
                    moves.append((r, 6))
            # 퀸사이드 캐슬링 (좌측)
            l_rook = board_grid[r][0]
            if l_rook and l_rook.name == 'r' and not l_rook.has_moved:
                if board_grid[r][1] is None and board_grid[r][2] is None and board_grid[r][3] is None:
                    moves.append((r, 2))
                    
        return moves