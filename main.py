# main.py
import pygame
import os
import sys
from board import Board
from ai_player import GeminiPlayer  # ← AI 플레이어 추가

# BOARD_HEIGHT는 실제로 안 쓰이므로 제거해도 됨 (아래 주석 참고)
BOARD_WIDTH, BOARD_HEIGHT = 640, 640  # ※ BOARD_HEIGHT 미사용 → 제거 가능
PANEL_WIDTH = 200
WIDTH, HEIGHT = BOARD_WIDTH + PANEL_WIDTH, BOARD_HEIGHT
TILE_SIZE = BOARD_WIDTH // 8
FPS = 60


def load_images():
    images = {}
    piece_names = ['wp', 'wr', 'wn', 'wb', 'wq', 'wk', 'bp', 'br', 'bn', 'bb', 'bq', 'bk']
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pieces_dir = os.path.join(base_dir, 'pieces')
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


def draw_panel(screen, board, font, surrender_rect, draw_rect):
    pygame.draw.rect(screen, pygame.Color("#312e2b"), (BOARD_WIDTH, 0, PANEL_WIDTH, HEIGHT))
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


# ─────────────────────────────────────────
# [추가] 모드 선택 화면
# ─────────────────────────────────────────
def draw_mode_select(screen, font, pvp_rect, pva_rect):
    """게임 시작 전 모드 선택 화면"""
    screen.fill(pygame.Color("#312e2b"))

    title_font = pygame.font.SysFont("arial", 36, bold=True)
    title = title_font.render("Chess - Select Mode", True, pygame.Color("white"))
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 140))

    pygame.draw.rect(screen, pygame.Color("#769656"), pvp_rect, border_radius=8)
    pvp_text = font.render("Player vs Player", True, pygame.Color("white"))
    screen.blit(pvp_text, (pvp_rect.x + 20, pvp_rect.y + 12))

    pygame.draw.rect(screen, pygame.Color("#4a90d9"), pva_rect, border_radius=8)
    pva_text = font.render("Player vs AI (Gemini)", True, pygame.Color("white"))
    screen.blit(pva_text, (pva_rect.x + 10, pva_rect.y + 12))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Chess")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 24, bold=True)
    images = load_images()

    # ─── [추가] 모드 선택 버튼 ───
    pvp_btn = pygame.Rect(WIDTH // 2 - 160, HEIGHT // 2 - 40, 320, 50)
    pva_btn = pygame.Rect(WIDTH // 2 - 160, HEIGHT // 2 + 40, 320, 50)

    # ─── [추가] 모드 선택 단계 ───
    mode = None          # None=선택 전, 'pvp'=사람vs사람, 'pva'=사람vsAI
    ai_player = None     # GeminiPlayer 인스턴스 (pva 모드일 때만 사용)
    ai_thinking = False  # AI가 수를 계산 중인지 표시용 (단순 플래그)

    board = Board()
    surrender_btn = pygame.Rect(BOARD_WIDTH + 20, 200, 160, 50)
    draw_btn = pygame.Rect(BOARD_WIDTH + 20, 280, 160, 50)
    popup_yes_btn = pygame.Rect(WIDTH // 2 - 140, HEIGHT // 2 + 10, 110, 40)
    popup_no_btn = pygame.Rect(WIDTH // 2 + 30, HEIGHT // 2 + 10, 110, 40)

    selected_pos = None
    legal_moves = []
    game_state = 'normal'
    popup_msg = ""
    result_msg = ""

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()

                # ── [추가] 모드 미선택 상태 ──
                if mode is None:
                    if pvp_btn.collidepoint(mx, my):
                        mode = 'pvp'
                    elif pva_btn.collidepoint(mx, my):
                        mode = 'pva'
                        # AI는 흑(Black) 담당으로 고정
                        ai_player = GeminiPlayer('b')

                # ── 기존: 일반 게임 진행 중 ──
                elif game_state == 'normal':
                    # [추가] AI 턴에는 사람이 클릭해도 무시
                    if mode == 'pva' and board.turn == 'b':
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
                            if board.grid[row][col] and board.grid[row][col].color == board.turn:
                                selected_pos = (row, col)
                                legal_moves = board.get_strict_legal_moves(selected_pos)
                            else:
                                selected_pos, legal_moves = None, []
                    else:
                        if surrender_btn.collidepoint(mx, my):
                            game_state = 'confirm_surrender'
                            popup_msg = "Really Surrender?"
                        elif draw_btn.collidepoint(mx, my):
                            game_state = 'confirm_draw'
                            popup_msg = "Offer a Draw?"

                elif game_state in ['confirm_surrender', 'confirm_draw']:
                    if popup_yes_btn.collidepoint(mx, my):
                        if game_state == 'confirm_surrender':
                            loser = "White" if board.turn == 'w' else "Black"
                            winner = "Black" if board.turn == 'w' else "White"
                            result_msg = f"{loser} Surrendered. {winner} Wins!"
                        else:
                            result_msg = "Draw Agreement Reached."
                        game_state = 'game_over'
                    elif popup_no_btn.collidepoint(mx, my):
                        game_state = 'normal'

                elif game_state == 'game_over':
                    # 새 게임 시작 시 모드 선택 화면으로 돌아감
                    board = Board()
                    mode = None
                    ai_player = None
                    game_state = 'normal'
                    selected_pos, legal_moves = None, []

        # ─────────────────────────────────────────
        # [추가] AI 자동 이동 처리
        # pva 모드이고 흑 차례이며 게임이 정상 진행 중일 때만 실행
        # ─────────────────────────────────────────
        if mode == 'pva' and board.turn == 'b' and game_state == 'normal':
            move = ai_player.choose_move(board)
            if move:
                board.move_piece(move[0], move[1])
                if board.game_over_status:
                    game_state = 'game_over'
                    if 'Checkmate' in board.game_over_status:
                        winner = "White" if 'w' in board.game_over_status else "Black"
                        result_msg = f"CHECKMATE! {winner} Wins."
                    else:
                        result_msg = "STALEMATE! It's a Draw."

        # ── 화면 그리기 ──
        if mode is None:
            draw_mode_select(screen, font, pvp_btn, pva_btn)
        else:
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
            draw_panel(screen, board, font, surrender_btn, draw_btn)

            # [추가] AI 생각 중 표시
            if mode == 'pva' and board.turn == 'b' and game_state == 'normal':
                ai_msg = font.render("AI thinking...", True, pygame.Color("yellow"))
                screen.blit(ai_msg, (BOARD_WIDTH + 10, 130))

            if game_state in ['confirm_surrender', 'confirm_draw']:
                draw_popup(screen, font, popup_msg, popup_yes_btn, popup_no_btn)
            elif game_state == 'game_over':
                draw_popup(screen, font, result_msg,
                           pygame.Rect(WIDTH // 2 - 60, HEIGHT // 2 + 10, 120, 40),
                           pygame.Rect(0, 0, 0, 0))  # ※ no_rect(0,0,0,0)는 화면 밖 더미 → 리팩토링 가능

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()