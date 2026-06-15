# ai_player.py
import os
import json
import random
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def _board_to_fen_simple(board):
    piece_map = {
        ('w', 'p'): 'P', ('w', 'r'): 'R', ('w', 'n'): 'N',
        ('w', 'b'): 'B', ('w', 'q'): 'Q', ('w', 'k'): 'K',
        ('b', 'p'): 'p', ('b', 'r'): 'r', ('b', 'n'): 'n',
        ('b', 'b'): 'b', ('b', 'q'): 'q', ('b', 'k'): 'k',
    }
    rows = []
    for r in range(8):
        row_str = ""
        empty = 0
        for c in range(8):
            piece = board.grid[r][c]
            if piece is None:
                empty += 1
            else:
                if empty > 0:
                    row_str += str(empty)
                    empty = 0
                row_str += piece_map.get((piece.color, piece.name), '?')
        if empty > 0:
            row_str += str(empty)
        rows.append(row_str)
    turn = 'w' if board.turn == 'w' else 'b'
    return "/".join(rows) + f" {turn}"


def _pos_to_algebraic(pos):
    r, c = pos
    return "abcdefgh"[c] + str(8 - r)


def _algebraic_to_pos(alg):
    alg = alg.strip().lower()
    if len(alg) < 2:
        return None
    c = "abcdefgh".find(alg[0])
    try:
        r = 8 - int(alg[1])
    except ValueError:
        return None
    if 0 <= r < 8 and 0 <= c < 8:
        return (r, c)
    return None


def get_all_legal_moves(board):
    moves = []
    for r in range(8):
        for c in range(8):
            piece = board.grid[r][c]
            if piece and piece.color == board.turn:
                for end in board.get_strict_legal_moves((r, c)):
                    moves.append(((r, c), end))
    return moves


class GeminiPlayer:
    def __init__(self, color):
        self.color = color  # 'w' or 'b'
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY가 .env 파일에 없습니다.\n"
                ".env 파일에 GEMINI_API_KEY=your_key_here 형태로 입력해주세요."
            )
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-3.5-flash")
        print(f"[AI] Gemini AI ({('White' if color == 'w' else 'Black')}) 초기화 완료")

    def choose_move(self, board):
        all_moves = get_all_legal_moves(board)
        if not all_moves:
            return None

        moves_algebraic = [
            f"{_pos_to_algebraic(s)}{_pos_to_algebraic(e)}"
            for s, e in all_moves
        ]
        board_state = _board_to_fen_simple(board)

        prompt = f"""You are a chess engine. Choose the best move for {'White' if self.color == 'w' else 'Black'}.

Current board (FEN-like notation, uppercase=White, lowercase=Black):
{board_state}

Legal moves available (in format 'from_square to_square' combined, e.g. 'e2e4'):
{', '.join(moves_algebraic)}

Respond with ONLY a JSON object in this exact format, nothing else:
{{"move": "e2e4", "reason": "brief reason"}}

Pick the strongest move from the legal moves list above.
And you are rating over 500
"""

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()

            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            text = text.strip()

            data = json.loads(text)
            move_str = data.get("move", "").strip().lower()
            reason = data.get("reason", "")

            if len(move_str) >= 4:
                start = _algebraic_to_pos(move_str[:2])
                end = _algebraic_to_pos(move_str[2:4])
                if (start, end) in all_moves:
                    print(f"[AI {'W' if self.color == 'w' else 'B'}] {move_str} — {reason}")
                    return (start, end)

            print(f"[AI] 유효하지 않은 응답 '{move_str}', 랜덤으로 대체합니다.")
            return random.choice(all_moves)

        except Exception as e:
            print(f"[AI] Gemini 오류: {e}, 랜덤 수를 선택합니다.")
            return random.choice(all_moves)
