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
 
    #  main.py 파일이 위치한 절대 경로를 알아냄.
    base_dir = os.path.dirname(os.path.abspath(__file__))
    #abspath:절대경로반환
    #dirname:폴더주소만 반환
    # base_dir 기준으로 pieces 폴더 경로를 생성.
    pieces_dir = os.path.join(base_dir, 'pieces')
    #join:폴더경로와 파일이름 합치기
    for name in piece_names:
        png_path = os.path.join(pieces_dir, f'{name}.png')
        webp_path = os.path.join(pieces_dir, f'{name}.webp')
        img = None
        if os.path.exists(png_path):
            img = pygame.image.load(png_path).convert_alpha()
        elif os.path.exists(webp_path):
            img = pygame.image.load(webp_path).convert_alpha()
        #convert_alpha : 배경 투명유지, 최적화
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

#blit:도장찍듯이 그리기

def draw_panel(screen, board, font, surrender_rect, draw_rect):
    pygame.draw.rect(screen, pygame.Color("#312e2b"), (BOARD_WIDTH, 0, PANEL_WIDTH, HEIGHT))
 
    # 현재 턴 텍스트 출력
    if board.turn == 'w':
        turn_str = "White's Turn"
        turn_color = pygame.Color("white")
    else:
        turn_str = "Black's Turn"
        turn_color = pygame.Color("gray")
    text_surface = font.render(turn_str, True, turn_color)
    #글자 파이게임에 그려주기 (파이게임은 텍스트 바로 못가져옴)
    screen.blit(text_surface, (BOARD_WIDTH + 20, 50))
    pygame.draw.rect(screen, pygame.Color("#b23b3b"), surrender_rect)
    surrender_text = font.render("Surrender", True, pygame.Color("white"))
    screen.blit(surrender_text, (surrender_rect.x + 15, surrender_rect.y + 10))
    pygame.draw.rect(screen, pygame.Color("#555555"), draw_rect)
    draw_text = font.render("Offer Draw", True, pygame.Color("white"))
    # True 는 잉크번짐 방지
    screen.blit(draw_text, (draw_rect.x + 12, draw_rect.y + 10))


def draw_popup(screen, font, message, yes_rect, no_rect):
    overlay = pygame.Surface((WIDTH, HEIGHT))

    overlay.set_alpha(150)#투명도
    overlay.fill((0, 0, 0))#검은색
    screen.blit(overlay, (0,0))#왼쪽위구석부터
    # 창 바디
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

    pygame.display.set_caption("A Chess Legend")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 24, bold=True)
    images = load_images()

    # ─── 모드 선택 버튼 ───
    pvp_btn = pygame.Rect(WIDTH // 2 - 160, HEIGHT // 2 - 40, 320, 50)
    pva_btn = pygame.Rect(WIDTH // 2 - 160, HEIGHT // 2 + 40, 320, 50)

    # ─── 게임 상태 변수 ───
    mode = None          # None=선택 전, 'pvp', 'pva'
    ai_player = None     
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

                # 1. 모드 미선택 상태 이벤트 처리
                if mode is None:
                    if pvp_btn.collidepoint(mx, my):
                        mode = 'pvp'
                    elif pva_btn.collidepoint(mx, my):
                        mode = 'pva'
                        ai_player = GeminiPlayer('b')

                # 2. 게임 진행 중 이벤트 처리
                elif game_state == 'normal':
                    if mode == 'pva' and board.turn == 'b':
                        pass  # AI 턴일 때는 사람 클릭 무시
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

                # 3. 팝업창 이벤트 처리
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

                # 4. 게임 오버 상태에서 클릭 시 리셋
                elif game_state == 'game_over':
                    board = Board()
                    mode = None
                    ai_player = None
                    game_state = 'normal'
                    selected_pos, legal_moves = None, []

        # ─── AI 자동 이동 처리 ───
        if mode == 'pva' and board.turn == 'b' and game_state == 'normal':
            # ※ 주의: choose_move 내부에 비동기 처리가 안 되어 있다면 순간적인 버벅임이 있을 수 있음
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

        # ─── 화면 렌더링 분기 (이 부분이 핵심 수정 항목) ───
        if mode is None:
            # 모드 선택창만 그리기
            draw_mode_select(screen, font, pvp_btn, pva_btn)
        else:
            # 게임 플레이 화면 그리기
            draw_board(screen)

            # 이전 이동 하이라이트
            if board.last_move:
                last_start, last_end, _ = board.last_move
                highlight = pygame.Surface((TILE_SIZE, TILE_SIZE))
                highlight.set_alpha(100)
                highlight.fill(pygame.Color('#e6e65a'))
                screen.blit(highlight, (last_start[1] * TILE_SIZE, last_start[0] * TILE_SIZE))
                screen.blit(highlight, (last_end[1] * TILE_SIZE, last_end[0] * TILE_SIZE))

            # 기물 선택 및 갈 수 있는 경로 하이라이트
            if selected_pos:
                s = pygame.Surface((TILE_SIZE, TILE_SIZE))
                s.set_alpha(120)
                s.fill(pygame.Color('#7b61ff'))
                screen.blit(s, (selected_pos[1] * TILE_SIZE, selected_pos[0] * TILE_SIZE))
                
                s.fill(pygame.Color('#ff8484'))
                for r, c in legal_moves:
                    screen.blit(s, (c * TILE_SIZE, r * TILE_SIZE))

            # 기물 및 패널 배치
            draw_pieces(screen, board, images)
            draw_panel(screen, board, font, surrender_btn, draw_btn)

            # AI 생각 중 메시지 표시
            if mode == 'pva' and board.turn == 'b' and game_state == 'normal':
                ai_msg = font.render("AI thinking...", True, pygame.Color("yellow"))
                screen.blit(ai_msg, (BOARD_WIDTH + 10, 130))

            # 팝업 우선 순위 처리
            if game_state in ['confirm_surrender', 'confirm_draw']:
                draw_popup(screen, font, popup_msg, popup_yes_btn, popup_no_btn)
            elif game_state == 'game_over':
                draw_popup(screen, font, result_msg, pygame.Rect(WIDTH // 2 - 60, HEIGHT // 2 + 10, 120, 40), pygame.Rect(0, 0, 0, 0))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()