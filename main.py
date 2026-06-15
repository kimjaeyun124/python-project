# main.py
import pygame
import os
import sys
from board import Board

# 우측에 버튼과 정보를 넣기 위해 가로 폭을 늘림
BOARD_WIDTH, BOARD_HEIGHT = 640, 640
PANEL_WIDTH = 200
WIDTH, HEIGHT = BOARD_WIDTH + PANEL_WIDTH, BOARD_HEIGHT
TILE_SIZE = BOARD_WIDTH // 8
FPS = 60


def load_images():
    images = {}
    piece_names = ['wp', 'wr', 'wn', 'wb', 'wq', 'wk', 'bp', 'br', 'bn', 'bb', 'bq', 'bk']

    # 💡 핵심 수정: main.py 파일이 위치한 절대 경로를 알아냅니다.
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # base_dir 기준으로 pieces 폴더 경로를 생성합니다.
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
    colors = [pygame.Color("#eeeed2"), pygame.Color("#769656")]  # 대중적인 체스판 색상 고정
    for row in range(8):
        for col in range(8):
            pygame.draw.rect(screen, colors[(row + col) % 2], (col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE))


def draw_pieces(screen, board, images):
    for row in range(8):
        for col in range(8):
            piece = board.grid[row][col]
            if piece and piece.image_key in images:
                screen.blit(images[piece.image_key], (col * TILE_SIZE, row * TILE_SIZE))


def draw_panel(screen, board, font, surrender_rect, draw_rect):
    """우측 스코어보드 및 버튼 패널 디자인"""
    # 배경 칸 채우기
    pygame.draw.rect(screen, pygame.Color("#312e2b"), (BOARD_WIDTH, 0, PANEL_WIDTH, HEIGHT))

    # 현재 턴 텍스트 출력
    turn_str = "White's Turn" if board.turn == 'w' else "Black's Turn"
    turn_color = pygame.Color("white") if board.turn == 'w' else pygame.Color("gray")
    text_surface = font.render(turn_str, True, turn_color)
    screen.blit(text_surface, (BOARD_WIDTH + 20, 50))

    # 항복 버튼 그리기
    pygame.draw.rect(screen, pygame.Color("#b23b3b"), surrender_rect)
    surrender_text = font.render("Surrender", True, pygame.Color("white"))
    screen.blit(surrender_text, (surrender_rect.x + 15, surrender_rect.y + 10))

    # 무승부 합의 버튼 그리기
    pygame.draw.rect(screen, pygame.Color("#555555"), draw_rect)
    draw_text = font.render("Offer Draw", True, pygame.Color("white"))
    screen.blit(draw_text, (draw_rect.x + 12, draw_rect.y + 10))


def draw_popup(screen, font, message, yes_rect, no_rect):
    """한 번 더 확인할 때 띄우는 반투명 팝업 창"""
    # 가림막 효과 (반투명 서피스)
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(150)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    # 창 바디
    popup_center = pygame.Rect(WIDTH // 2 - 170, HEIGHT // 2 - 100, 340, 180)
    pygame.draw.rect(screen, pygame.Color("#262522"), popup_center, border_radius=10)

    # 질문 내용 메세지
    msg_surface = font.render(message, True, pygame.Color("white"))
    screen.blit(msg_surface, (popup_center.x + 20, popup_center.y + 30))

    # 예 / 아니오 버튼
    pygame.draw.rect(screen, pygame.Color("#769656"), yes_rect, border_radius=5)
    pygame.draw.rect(screen, pygame.Color("#444444"), no_rect, border_radius=5)

    yes_txt = font.render("YES", True, pygame.Color("white"))
    no_txt = font.render("NO", True, pygame.Color("white"))
    screen.blit(yes_txt, (yes_rect.x + 35, yes_rect.y + 8))
    screen.blit(no_txt, (no_rect.x + 40, no_rect.y + 8))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Chess with Special Rules & UI")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 24, bold=True)

    images = load_images()
    board = Board()

    # 버튼 및 팝업창 범위 미리 사각형(Rect) 객체로 구축 (마우스 클릭 충돌 연산 최적화)
    surrender_btn = pygame.Rect(BOARD_WIDTH + 20, 200, 160, 50)
    draw_btn = pygame.Rect(BOARD_WIDTH + 20, 280, 160, 50)

    popup_yes_btn = pygame.Rect(WIDTH // 2 - 140, HEIGHT // 2 + 10, 110, 40)
    popup_no_btn = pygame.Rect(WIDTH // 2 + 30, HEIGHT // 2 + 10, 110, 40)

    selected_pos = None
    legal_moves = []

    # 팝업 상태 트리거 변수들 ('normal', 'confirm_surrender', 'confirm_draw', 'game_over')
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

                # 1. 일반 게임 진행 중일 때 마우스 액션
                if game_state == 'normal':
                    if mx < BOARD_WIDTH:  # 보드 안쪽 클릭
                        col, row = mx // TILE_SIZE, my // TILE_SIZE
                        if (row, col) in legal_moves:
                            board.move_piece(selected_pos, (row, col))
                            selected_pos, legal_moves = None, []
                            # 이동 후 혹시 체크메이트나 스테일메이트가 떴는지 검증
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
                    else:  # 우측 패널 클릭
                        if surrender_btn.collidepoint(mx, my):
                            game_state = 'confirm_surrender'
                            popup_msg = "Really Surrender?"
                        elif draw_btn.collidepoint(mx, my):
                            game_state = 'confirm_draw'
                            popup_msg = "Offer a Draw?"

                # 2. 버튼 확인창이 떠 있을 때 마우스 액션 (더블 체크 시스템)
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
                        game_state = 'normal'  # 취소하고 복귀

                # 3. 게임이 끝났을 때 팝업 클릭하면 리셋 후 새 게임 시작
                elif game_state == 'game_over':
                    board = Board()
                    game_state = 'normal'

        # 화면 출력 부분 정리
        draw_board(screen)

        # 선택 영역 및 가이드라인 하이라이트
        if selected_pos:
            s = pygame.Surface((TILE_SIZE, TILE_SIZE));
            s.set_alpha(120)
            s.fill(pygame.Color('#7b61ff'));
            screen.blit(s, (selected_pos[1] * TILE_SIZE, selected_pos[0] * TILE_SIZE))  # 선택 기물
            s.fill(pygame.Color('#ff8484'))
            for r, c in legal_moves: screen.blit(s, (c * TILE_SIZE, r * TILE_SIZE))  # 갈 수 있는 칸 표시

        draw_pieces(screen, board, images)
        draw_panel(screen, board, font, surrender_btn, draw_btn)

        # 특수 상황 창 전시 우선권 분배
        if game_state in ['confirm_surrender', 'confirm_draw']:
            draw_popup(screen, font, popup_msg, popup_yes_btn, popup_no_btn)
        elif game_state == 'game_over':
            # 결과 안내창 (클릭 시 확인용이므로 더블체크 예/아니오 사각형 좌표를 재활용하여 확인 처리)
            draw_popup(screen, font, result_msg, pygame.Rect(WIDTH // 2 - 60, HEIGHT // 2 + 10, 120, 40),
                       pygame.Rect(0, 0, 0, 0))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()