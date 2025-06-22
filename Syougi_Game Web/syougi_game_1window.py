import pygame
import os

pygame.init()

WINDOW_WIDTH = 640
WINDOW_HEIGHT = 640

ANIM_FRAMES = 58
ANIM_PATTERN = "battle_anim_{:04d}.png"
SWORD_FRAME = 2

FONT = pygame.font.SysFont("meiryo", 42)
SMALLFONT = pygame.font.SysFont("meiryo", 32)
PARAM_FONT = pygame.font.SysFont("meiryo", 30)

# サウンド
pygame.mixer.init()
def load_bgm(name):
    try:
        return pygame.mixer.Sound(name)
    except:
        return None

def safe_music_load(name):
    try:
        pygame.mixer.music.load(name)
        return True
    except:
        return False

board_bgm_path = "Tense_Tactics_2.mp3"
battle_bgm_path = "kettou.mp3"
sword_se_path = "soword_sound.mp3"
wadaiko_se_path = "koma_syoumetu.mp3"
hu_nari_se_path = "hu_nari.mp3"

battle_bgm = load_bgm(battle_bgm_path)
sword_se = load_bgm(sword_se_path)
koma_syoumetu_se = load_bgm(wadaiko_se_path)
hu_nari_se = load_bgm(hu_nari_se_path)
safe_music_load(board_bgm_path)

PIECE_IMAGES = {
    "fu": "fu.png",
    "gin": "gin.png",
    "kin": "kin.png",
    "ou": "ou.png",
}

PIECE_STATS = {
    "ou": {"hp": 6, "atk": 4},
    "gin": {"hp": 3, "atk": 4},
    "kin": {"hp": 4, "atk": 3},
    "fu": {"hp": 2, "atk": 2},
}

PIECE_ORDER = ["fu", "gin", "ou", "kin", "fu"]

class Piece:
    def __init__(self, name, x, y, owner):
        self.name = name
        self.x = x
        self.y = y
        self.owner = owner
        self.hp = PIECE_STATS[name]["hp"]
        self.atk = PIECE_STATS[name]["atk"]
        self.alive = True
        self.promoted = False
        self.img = self.get_img()
        self.rect = self.img.get_rect()

    def get_img(self):
        img = pygame.image.load(PIECE_IMAGES[self.name]).convert_alpha()
        img = pygame.transform.smoothscale(img, (96, 96))
        if self.owner == "ai":
            img = pygame.transform.rotate(img, 180)
        return img

    def promote(self):
        self.name = "kin"
        self.hp = PIECE_STATS["kin"]["hp"]
        self.atk = PIECE_STATS["kin"]["atk"]
        self.img = self.get_img()
        self.promoted = True

    def get_moves(self, board):
        moves = []
        if self.name == "fu":
            dy = -1 if self.owner == "player" else 1
            tx, ty = self.x, self.y + dy
            if 0 <= ty < 5 and (board.get_piece(tx, ty) is None or board.get_piece(tx, ty).owner != self.owner):
                moves.append((tx, ty))
        elif self.name == "gin":
            dy = -1 if self.owner == "player" else 1
            dirs = [(-1, dy), (0, dy), (1, dy), (-1, -dy), (1, -dy)]
            for dx, dy2 in dirs:
                tx, ty = self.x + dx, self.y + dy2
                if 0 <= tx < 5 and 0 <= ty < 5:
                    p = board.get_piece(tx, ty)
                    if p is None or p.owner != self.owner:
                        moves.append((tx, ty))
        elif self.name == "kin":
            dy = -1 if self.owner == "player" else 1
            dirs = [(-1, 0), (1, 0), (0, dy), (0, -dy), (-1, dy), (1, dy)]
            for dx, dy2 in dirs:
                tx, ty = self.x + dx, self.y + dy2
                if 0 <= tx < 5 and 0 <= ty < 5:
                    p = board.get_piece(tx, ty)
                    if p is None or p.owner != self.owner:
                        moves.append((tx, ty))
        elif self.name == "ou":
            dirs = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
            for dx, dy in dirs:
                tx, ty = self.x + dx, self.y + dy
                if 0 <= tx < 5 and 0 <= ty < 5:
                    p = board.get_piece(tx, ty)
                    if p is None or p.owner != self.owner:
                        moves.append((tx, ty))
        return moves

class Board:
    def __init__(self):
        self.grid = [[None for _ in range(5)] for _ in range(5)]
        self.pieces = []
        for i, name in enumerate(PIECE_ORDER):
            self.place_piece(Piece(name, i, 4, "player"))
        for i, name in enumerate(PIECE_ORDER):
            self.place_piece(Piece(name, i, 0, "ai"))
        self.selected = None
        self.turn = "player"
        self.turn_count = 1
        self.animating = False
        self.result = None
        self.show_continue = False
        self.continue_selected = 0
        self.player_param_text = ""
        self.ai_param_text = ""
        self.last_ai_selected_piece = None
        self.last_ai_selected_moves = []

    def judge_result(self):
        ai_ou_alive = any(p.name == "ou" and p.owner == "ai" and p.alive for p in self.pieces)
        player_ou_alive = any(p.name == "ou" and p.owner == "player" and p.alive for p in self.pieces)
        if not ai_ou_alive and not self.result:
            self.result = "win"
            if koma_syoumetu_se: koma_syoumetu_se.play()
            pygame.mixer.music.stop()
            self.show_continue = True
        elif not player_ou_alive and not self.result:
            self.result = "lose"
            if koma_syoumetu_se: koma_syoumetu_se.play()
            pygame.mixer.music.stop()
            self.show_continue = True

    def place_piece(self, piece):
        self.grid[piece.x][piece.y] = piece
        self.pieces.append(piece)

    def remove_piece(self, piece):
        self.grid[piece.x][piece.y] = None
        piece.alive = False
        if koma_syoumetu_se:
            koma_syoumetu_se.play()
        if piece.name == "ou":
            self.judge_result()

    def move_piece(self, piece, nx, ny):
        self.grid[piece.x][piece.y] = None
        piece.x, piece.y = nx, ny
        self.grid[nx][ny] = piece

    def get_piece(self, x, y):
        if 0 <= x < 5 and 0 <= y < 5:
            return self.grid[x][y]
        return None

    def reset(self):
        self.__init__()

def draw_board(screen, board, ai_highlight=None, ai_moves=None):
    screen.fill((24, 24, 24))
    for i in range(6):
        pygame.draw.line(screen, (180, 180, 180), (i*128, 0), (i*128, 640), 4)
        pygame.draw.line(screen, (180, 180, 180), (0, i*128), (640, i*128), 4)
    # AIハイライト
    if ai_highlight:
        px, py = ai_highlight.x * 128, ai_highlight.y * 128
        pygame.draw.rect(screen, (255,0,0), (px+4, py+4, 120, 120), 6)
    if ai_moves:
        for mx, my in ai_moves:
            highlight = pygame.Surface((128,128), pygame.SRCALPHA)
            pygame.draw.rect(highlight, (255,255,0,90), (0,0,128,128))
            screen.blit(highlight, (mx*128, my*128))
    # プレイヤーのハイライト
    if board.selected and not ai_highlight:
        moves = board.selected.get_moves(board)
        for mx, my in moves:
            highlight = pygame.Surface((128,128), pygame.SRCALPHA)
            pygame.draw.rect(highlight, (255,255,0,90), (0,0,128,128))
            screen.blit(highlight, (mx*128, my*128))
    for piece in board.pieces:
        if not piece.alive: continue
        px, py = piece.x * 128, piece.y * 128
        img = piece.img
        screen.blit(img, (px+16, py+16))
        hp_text = SMALLFONT.render(f"{piece.hp}", True, (255, 0, 0))
        screen.blit(hp_text, (px+90, py+10))

def draw_param_text(screen, text):
    if text:
        txt = PARAM_FONT.render(text, True, (255,255,0))
        screen.blit(txt, (8, 640-40))

def draw_ai_param_text(screen, text):
    if text:
        txt = PARAM_FONT.render(text, True, (0,255,255))
        screen.blit(txt, (8, 640-80))

def draw_turn(screen, turn_count):
    txt = FONT.render(f"ターン: {turn_count}/10", True, (255,255,255))
    screen.blit(txt, (8,8))

def draw_continue(screen, selected):
    surf = pygame.Surface((400,100), pygame.SRCALPHA)
    surf.fill((20,20,20,220))
    pygame.draw.rect(surf, (180, 180, 70), (30,50,130,50))
    pygame.draw.rect(surf, (160, 160, 160), (180,50,130,50))
    yes = PARAM_FONT.render("はい", True, (0,0,0))
    no  = PARAM_FONT.render("いいえ", True, (64,64,64))
    surf.blit(yes, (65,55))
    surf.blit(no, (210,55))
    screen.blit(surf, (120, 380))

def draw_result_message(screen, result):
    color = {"win":(255,255,0), "lose":(255,80,80), "draw":(180,180,255)}
    msg = {"win":"勝利！", "lose":"敗北...", "draw":"引き分け"}
    txt = FONT.render(msg[result], True, color[result])
    screen.blit(txt, (180, 280))

def draw_ai_turn(screen):
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0,0,0,160))
    txt = FONT.render("AIのターン", True, (255,255,0))
    rect = txt.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2))
    overlay.blit(txt, rect)
    screen.blit(overlay, (0,0))
    pygame.display.update()

def handle_move_and_promotion(piece, nx, ny, board):
    # 歩の成金
    if piece.name == "fu":
        if piece.owner == "player" and ny == 1:
            if hu_nari_se: hu_nari_se.play()
            piece.promote()
        elif piece.owner == "ai" and ny == 3:
            if hu_nari_se: hu_nari_se.play()
            piece.promote()
    board.move_piece(piece, nx, ny)

def main():
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("5x5 黒将棋バトル")

    board = Board()
    running = True

    pygame.mixer.music.play(-1)
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif board.show_continue:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    if 150 < mx < 260 and 430 < my < 480:
                        board.reset()
                        pygame.mixer.music.stop()
                        pygame.mixer.music.play(-1)
                    elif 300 < mx < 410 and 430 < my < 480:
                        running = False
                continue

            elif event.type == pygame.MOUSEBUTTONDOWN and not board.animating and not board.result:
                mx, my = event.pos
                gx, gy = mx // 128, my // 128
                piece = board.get_piece(gx, gy)
                if not (0 <= gx < 5 and 0 <= gy < 5):
                    continue

                if not board.selected:
                    if piece:
                        if piece.owner == "player":
                            board.selected = piece
                            board.player_param_text = f"{piece.name}  HP:{piece.hp}  ATK:{piece.atk}"
                            board.ai_param_text = ""
                        elif piece.owner == "ai":
                            board.selected = None
                            board.ai_param_text = f"{piece.name}  HP:{piece.hp}  ATK:{piece.atk}"
                            board.player_param_text = ""
                    continue

                if board.selected:
                    if piece and piece.owner == "player":
                        board.selected = piece
                        board.player_param_text = f"{piece.name}  HP:{piece.hp}  ATK:{piece.atk}"
                        board.ai_param_text = ""
                        continue
                    if piece and piece.owner == "ai":
                        moves = board.selected.get_moves(board)
                        if (gx, gy) in moves:
                            pygame.mixer.music.stop()
                            if battle_bgm: battle_bgm.play(-1)
                            for frame in range(ANIM_FRAMES):
                                animfile = ANIM_PATTERN.format(frame + 1)
                                if os.path.exists(animfile):
                                    frame_img = pygame.image.load(animfile).convert_alpha()
                                    frame_img = pygame.transform.smoothscale(frame_img, (WINDOW_WIDTH, WINDOW_HEIGHT))
                                    screen.blit(frame_img, (0, 0))
                                pygame.display.update()
                                if frame == SWORD_FRAME and sword_se:
                                    sword_se.play()
                                pygame.time.delay(40)
                            if battle_bgm: battle_bgm.stop()
                            piece.hp -= board.selected.atk
                            if piece.hp > 0:
                                board.selected.hp -= piece.atk
                            if piece.hp <= 0:
                                board.remove_piece(piece)
                            if board.selected.hp <= 0:
                                board.remove_piece(board.selected)
                            pygame.mixer.music.play(-1)
                            board.selected = None
                            board.turn = "ai"
                            board.player_param_text = ""
                            board.ai_param_text = ""
                        else:
                            board.ai_param_text = f"{piece.name}  HP:{piece.hp}  ATK:{piece.atk}"
                            board.player_param_text = ""
                        continue
                    if not piece:
                        moves = board.selected.get_moves(board)
                        if (gx, gy) in moves:
                            handle_move_and_promotion(board.selected, gx, gy, board)
                            board.selected = None
                            board.turn = "ai"
                            board.player_param_text = ""
                            board.ai_param_text = ""
                        continue

        # --- プレイヤーターン終了直後AIのターン表示 ---
        if board.turn == "ai" and not board.animating and not board.result:
            # AIターン演出
            draw_board(screen, board)
            draw_turn(screen, min(board.turn_count, 10))
            draw_param_text(screen, board.player_param_text)
            draw_ai_param_text(screen, board.ai_param_text)
            draw_ai_turn(screen)
            pygame.display.update()
            # 3秒停止（途中でウィンドウが反応しなくなるので最低限のイベント処理）
            t0 = pygame.time.get_ticks()
            while pygame.time.get_ticks() - t0 < 3000:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        return
                pygame.time.delay(20)
            # --- AIの行動 ---
            acted = False
            selected_piece = None
            selected_moves = []
            for piece in [p for p in board.pieces if p.owner == "ai" and p.alive]:
                moves = piece.get_moves(board)
                for mx, my in moves:
                    target = board.get_piece(mx, my)
                    if target and target.owner == "player":
                        selected_piece = piece
                        selected_moves = moves
                        break
                if selected_piece:
                    break
            # 攻撃手がなければランダム移動
            if not selected_piece:
                import random
                movable = [p for p in board.pieces if p.owner == "ai" and p.alive]
                if movable:
                    random.shuffle(movable)
                    for piece in movable:
                        moves = piece.get_moves(board)
                        random.shuffle(moves)
                        for mx, my in moves:
                            if board.get_piece(mx, my) is None:
                                selected_piece = piece
                                selected_moves = moves
                                break
                        if selected_piece:
                            break
            # AIが選択した駒と範囲を1秒間ハイライト
            if selected_piece:
                board.last_ai_selected_piece = selected_piece
                board.last_ai_selected_moves = selected_moves
                for t in range(30):  # 1秒（30フレーム）
                    draw_board(screen, board, ai_highlight=selected_piece, ai_moves=selected_moves)
                    draw_turn(screen, min(board.turn_count, 10))
                    pygame.display.update()
                    clock.tick(30)
            # 実際のAI行動
            acted = False
            if selected_piece and selected_moves:
                # 攻撃優先
                for mx, my in selected_moves:
                    target = board.get_piece(mx, my)
                    if target and target.owner == "player":
                        pygame.mixer.music.stop()
                        if battle_bgm: battle_bgm.play(-1)
                        for frame in range(ANIM_FRAMES):
                            animfile = ANIM_PATTERN.format(frame + 1)
                            if os.path.exists(animfile):
                                frame_img = pygame.image.load(animfile).convert_alpha()
                                frame_img = pygame.transform.smoothscale(frame_img, (WINDOW_WIDTH, WINDOW_HEIGHT))
                                screen.blit(frame_img, (0, 0))
                            pygame.display.update()
                            if frame == SWORD_FRAME and sword_se:
                                sword_se.play()
                            pygame.time.delay(40)
                        if battle_bgm: battle_bgm.stop()
                        target.hp -= selected_piece.atk
                        if target.hp > 0:
                            selected_piece.hp -= target.atk
                        if target.hp <= 0:
                            board.remove_piece(target)
                        if selected_piece.hp <= 0:
                            board.remove_piece(selected_piece)
                        pygame.mixer.music.play(-1)
                        acted = True
                        break
                # 移動だけ
                if not acted:
                    for mx, my in selected_moves:
                        if board.get_piece(mx, my) is None:
                            handle_move_and_promotion(selected_piece, mx, my, board)
                            acted = True
                            break
            board.last_ai_selected_piece = None
            board.last_ai_selected_moves = []
            board.turn = "player"
            board.turn_count += 1

        # ★勝敗・引き分け判定（drawだけここで判定）
        if board.turn_count > 10 and not board.result:
            board.result = "draw"
            pygame.mixer.music.stop()
            board.show_continue = True

        draw_board(
            screen,
            board,
            ai_highlight=board.last_ai_selected_piece if board.turn == "ai" else None,
            ai_moves=board.last_ai_selected_moves if board.turn == "ai" else None
        )
        draw_turn(screen, min(board.turn_count, 10))
        draw_param_text(screen, board.player_param_text)
        draw_ai_param_text(screen, board.ai_param_text)
        if board.result:
            draw_result_message(screen, board.result)
        if board.show_continue:
            draw_continue(screen, board.continue_selected)
        pygame.display.update()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()

