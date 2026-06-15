# main.py
import pygame
import os
import sys
import argparse
import time
from board import Board

# 우측에 버튼과 정보를 넣기 위해 가로 폭을 늘림
BOARD_WIDTH, BOARD_HEIGHT = 640, 640
PANEL_WIDTH = 200
WIDTH, HEIGHT = BOARD_WIDTH + PANEL_WIDTH, BOARD_HEIGHT
TILE_SIZE = BOARD_WIDTH // 8
FPS = 60

# ── 명령줄 인자 파싱 ──────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(
        # description="Chess Game",
        # usage="python main.py [1P|2P] [--ai-delay 초]",
        # epilog=(
        #     "예시:\n"
        #     "  python main.py 1P          사람(White) vs AI(Black)\n"
        #     "  python main.py 2P          사람 vs 사람\n"
        #     "  python main.py 1P --ai-delay 2.0   AI 응답 대기 2초\n"
        # ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "players",
        nargs="?",
        choices=["1P", "2P", "1p", "2p"],
        default="2P",
        # metavar="1P|2P",
        # help="1P = 사람 vs AI,  2P = 사람 vs 사람 (기본값: 2P)",
    )
    parser.add_argument(
        "--ai-delay",
        type=float,
        default=1.0,
        help="AI가 수를 두기 전 대기 시간(초). 기본값: 1.0",
    )
    args = parser.parse_args()

    # 대소문자 통일 후 mode 문자열로 변환
    p = args.players.upper()
    args.mode = "ai-black" if p == "1P" else "pvp"
    return args


def load_images():
    images = {}
    piece_names = ['wp', 'wr', 'wn', 'wb', 'wq', 'wk', 'bp', 'br', 'bn', 'bb', 'bq', 'bk']
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pieces_dir = os.path.join(base_dir, '../pieces')
    for name in piece_names:
        png_path = os.path.join(pieces_dir, f'{name}.png')
        webp_path = os.path.join(pieces_dir, f'{name}.webp')
        img = None
        if os.path.exists(png_path):
            img = pygame.image.load(png_path).convert_alpha()
        elif os.path.exists(webp_path):
            img = pygame.image.load(webp_path).convert_alpha()
        if img:
            images[name] = pygame.transform.smoothscale(img, (TILE_SIZE, TILE_SIZE))
        else:
            print(f"경고: 이미지를 찾을 수 없습니다 -> {png_path}")
    return images


def draw_board(screen):
    colors = [pygame.Color("#eeeed2"), pygame.Color("#769656")]
    for row in range(8):
        for col in range(8):
            pygame.draw.rect(screen, colors[(row + col) % 2],
            (col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE))


def draw_pieces(screen, board, images):
    for row in range(8):
        for col in range(8):
            piece = board.grid[row][col]
            if piece and piece.image_key in images:
                screen.blit(images[piece.image_key], (col * TILE_SIZE, row * TILE_SIZE))


def draw_panel(screen, board, font, surrender_rect, draw_rect, mode_label):
    pygame.draw.rect(screen, pygame.Color("#312e2b"), (BOARD_WIDTH, 0, PANEL_WIDTH, HEIGHT))

    # 모드 표시
    mode_surf = font.render(mode_label, True, pygame.Color("#aaaaaa"))
    screen.blit(mode_surf, (BOARD_WIDTH + 10, 15))

    turn_str = "White's Turn" if board.turn == 'w' else "Black's Turn"
    turn_color = pygame.Color("white") if board.turn == 'w' else pygame.Color("gray")
    text_surface = font.render(turn_str, True, turn_color)
    screen.blit(text_surface, (BOARD_WIDTH + 20, 50))

    pygame.draw.rect(screen, pygame.Color("#b23b3b"), surrender_rect)
    surrender_text = font.render("Surrender", True, pygame.Color("white"))
    screen.blit(surrender_text, (surrender_rect.x + 15, surrender_rect.y + 10))

    pygame.draw.rect(screen, pygame.Color("#555555"), draw_rect)
    draw_text = font.render("Offer Draw", True, pygame.Color("white"))
    screen.blit(draw_text, (draw_rect.x + 12, draw_rect.y + 10))


def draw_panel_ai(screen, board, font, mode_label, thinking):
    """AI 대전 시 패널 (버튼 없이 상태만 표시)"""
    pygame.draw.rect(screen, pygame.Color("#312e2b"), (BOARD_WIDTH, 0, PANEL_WIDTH, HEIGHT))

    mode_surf = font.render(mode_label, True, pygame.Color("#aaaaaa"))
    screen.blit(mode_surf, (BOARD_WIDTH + 10, 15))

    turn_str = "White's Turn" if board.turn == 'w' else "Black's Turn"
    turn_color = pygame.Color("white") if board.turn == 'w' else pygame.Color("gray")
    screen.blit(font.render(turn_str, True, turn_color), (BOARD_WIDTH + 20, 50))

    if thinking:
        dots = "." * (int(time.time() * 2) % 4)
        ai_surf = font.render(f"AI thinking{dots}", True, pygame.Color("#f0c040"))
        screen.blit(ai_surf, (BOARD_WIDTH + 10, 90))


def draw_popup(screen, font, message, yes_rect, no_rect):
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(150)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    popup_center = pygame.Rect(WIDTH // 2 - 170, HEIGHT // 2 - 100, 340, 180)
    pygame.draw.rect(screen, pygame.Color("#262522"), popup_center, border_radius=10)

    msg_surface = font.render(message, True, pygame.Color("white"))
    screen.blit(msg_surface, (popup_center.x + 20, popup_center.y + 30))

    pygame.draw.rect(screen, pygame.Color("#769656"), yes_rect, border_radius=5)
    pygame.draw.rect(screen, pygame.Color("#444444"), no_rect, border_radius=5)

    yes_txt = font.render("YES", True, pygame.Color("white"))
    no_txt = font.render("NO", True, pygame.Color("white"))
    screen.blit(yes_txt, (yes_rect.x + 35, yes_rect.y + 8))
    screen.blit(no_txt, (no_rect.x + 40, no_rect.y + 8))


# ── AI 턴 여부 판단 헬퍼 ─────────────────────────────────────
def is_ai_turn(mode, current_turn):
    """현재 턴이 AI가 둬야 하는 턴인지 반환"""
    if mode == "ai-vs-ai":
        return True
    if mode == "ai-white" and current_turn == 'w':
        return True
    if mode == "ai-black" and current_turn == 'b':
        return True
    return False


def mode_label_str(mode):
    labels = {
        "pvp": "PvP",
        "ai-white": "AI(W) vs Human(B)",
        "ai-black": "Human(W) vs AI(B)",
        "ai-vs-ai": "AI vs AI",
    }
    return labels.get(mode, mode)


# ── 메인 루프 ────────────────────────────────────────────────
def main():
    args = parse_args()
    mode = args.mode
    ai_delay = args.ai_delay

    # AI 모드일 때만 GeminiPlayer 임포트 및 초기화
    ai_players = {}
    if mode != "pvp":
        try:
            from ai_player import GeminiPlayer
        except ImportError as e:
            print(f"[오류] ai_player 모듈 로드 실패: {e}")
            sys.exit(1)

        if mode in ("ai-white", "ai-vs-ai"):
            ai_players['w'] = GeminiPlayer('w')
        if mode in ("ai-black", "ai-vs-ai"):
            ai_players['b'] = GeminiPlayer('b')

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(f"Chess — {mode_label_str(mode)}")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 20, bold=True)

    images = load_images()
    board = Board()

    surrender_btn = pygame.Rect(BOARD_WIDTH + 20, 200, 160, 50)
    draw_btn      = pygame.Rect(BOARD_WIDTH + 20, 280, 160, 50)
    popup_yes_btn = pygame.Rect(WIDTH // 2 - 140, HEIGHT // 2 + 10, 110, 40)
    popup_no_btn  = pygame.Rect(WIDTH // 2 + 30,  HEIGHT // 2 + 10, 110, 40)

    selected_pos = None
    legal_moves  = []

    game_state = 'normal'   # 'normal' | 'confirm_surrender' | 'confirm_draw' | 'game_over'
    popup_msg  = ""
    result_msg = ""

    # AI가 마지막으로 수를 둔 시각 (딜레이 제어용)
    last_ai_move_time = 0.0
    ai_thinking = False

    mlabel = mode_label_str(mode)
    running = True

    while running:
        now = time.time()

        # ── 이벤트 처리 ─────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()

                if game_state == 'normal':
                    # AI 턴이면 보드 클릭 무시
                    if is_ai_turn(mode, board.turn):
                        pass
                    elif mx < BOARD_WIDTH:
                        col, row = mx // TILE_SIZE, my // TILE_SIZE
                        if (row, col) in legal_moves:
                            board.move_piece(selected_pos, (row, col))
                            selected_pos, legal_moves = None, []
                            if board.game_over_status:
                                game_state = 'game_over'
                                if 'Checkmate' in board.game_over_status:
                                    winner = "White" if 'w' in board.game_over_status else "Black"
                                    result_msg = f"CHECKMATE! {winner} Wins."
                                else:
                                    result_msg = "STALEMATE! It's a Draw."
                        else:
                            piece = board.grid[row][col]
                            if piece and piece.color == board.turn:
                                selected_pos = (row, col)
                                legal_moves = board.get_strict_legal_moves(selected_pos)
                            else:
                                selected_pos, legal_moves = None, []
                    else:
                        # 패널 버튼 (pvp / 혼합 모드에서만 의미 있음)
                        if mode == "pvp" or not is_ai_turn(mode, board.turn):
                            if surrender_btn.collidepoint(mx, my):
                                game_state = 'confirm_surrender'
                                popup_msg = "Really Surrender?"
                            elif draw_btn.collidepoint(mx, my):
                                game_state = 'confirm_draw'
                                popup_msg = "Offer a Draw?"

                elif game_state in ('confirm_surrender', 'confirm_draw'):
                    if popup_yes_btn.collidepoint(mx, my):
                        if game_state == 'confirm_surrender':
                            loser   = "White" if board.turn == 'w' else "Black"
                            winner  = "Black" if board.turn == 'w' else "White"
                            result_msg = f"{loser} Surrendered. {winner} Wins!"
                        else:
                            result_msg = "Draw Agreement Reached."
                        game_state = 'game_over'
                    elif popup_no_btn.collidepoint(mx, my):
                        game_state = 'normal'

                elif game_state == 'game_over':
                    board = Board()
                    game_state = 'normal'
                    selected_pos, legal_moves = None, []
                    last_ai_move_time = time.time()   # 리셋 후 바로 두지 않도록

        # ── AI 자동 수 처리 ──────────────────────────────────
        if (
            game_state == 'normal'
            and is_ai_turn(mode, board.turn)
            and not ai_thinking
            and now - last_ai_move_time >= ai_delay
        ):
            ai_thinking = True
            ai = ai_players.get(board.turn)
            if ai:
                move = ai.choose_move(board)
                if move:
                    board.move_piece(*move)
                    selected_pos, legal_moves = None, []
                    if board.game_over_status:
                        game_state = 'game_over'
                        if 'Checkmate' in board.game_over_status:
                            winner = "White" if 'w' in board.game_over_status else "Black"
                            result_msg = f"CHECKMATE! {winner} Wins."
                        else:
                            result_msg = "STALEMATE! It's a Draw."
            last_ai_move_time = now
            ai_thinking = False

        # ── 화면 그리기 ──────────────────────────────────────
        draw_board(screen)

        if selected_pos:
            s = pygame.Surface((TILE_SIZE, TILE_SIZE))
            s.set_alpha(120)
            s.fill(pygame.Color('#7b61ff'))
            screen.blit(s, (selected_pos[1] * TILE_SIZE, selected_pos[0] * TILE_SIZE))
            s.fill(pygame.Color('#ff8484'))
            for r, c in legal_moves:
                screen.blit(s, (c * TILE_SIZE, r * TILE_SIZE))

        draw_pieces(screen, board, images)

        # 패널: AI-vs-AI 모드는 버튼 없이 심플 패널
        if mode == "ai-vs-ai":
            draw_panel_ai(screen, board, font, mlabel, ai_thinking)
        else:
            draw_panel(screen, board, font, surrender_btn, draw_btn, mlabel)

        if game_state in ('confirm_surrender', 'confirm_draw'):
            draw_popup(screen, font, popup_msg, popup_yes_btn, popup_no_btn)
        elif game_state == 'game_over':
            draw_popup(screen, font, result_msg,
            pygame.Rect(WIDTH // 2 - 60, HEIGHT // 2 + 10, 120, 40),
            pygame.Rect(0, 0, 0, 0))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
