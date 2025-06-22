import pygame
import sys
import os
import random
import numpy as np

from ffpyplayer.player import MediaPlayer
import cv2

# --- 設定 ---
BOARD_SIZE = 5
WIN_W, WIN_H = 640, 480
CELL_W, CELL_H = WIN_W // BOARD_SIZE, WIN_H // BOARD_SIZE
FPS = 30

PIECE_IMAGE_FILES = {"歩": "fu.png", "銀": "gin.png", "金": "kin.png", "王": "ou.png"}
PIECE_SCALE = (CELL_W - 8, CELL_H - 8)

BGM_SHOGI = "Tense_Tactics_2.mp3"
BGM_BATTLE = "決闘.mp3"
MP4_FILE = "battle_anim.mp4"  # 戦闘アニメ動画

def play_battle_video_ffpyplayer(video_path):
    # Pygameを一時停止してmp4再生
    video = cv2.VideoCapture(video_path)
    player = MediaPlayer(video_path)
    while True:
        grabbed, frame = video.read()
        audio_frame, val = player.get_frame()
        if not grabbed:
            break
        if cv2.waitKey(28) & 0xFF == ord("q"):
            break
        cv2.imshow("Battle Animation", frame)
        # ウィンドウ閉じたら終了
        if cv2.getWindowProperty("Battle Animation", cv2.WND_PROP_VISIBLE) < 1:
            break
    video.release()
    cv2.destroyAllWindows()

class Piece:
    def __init__(self, kind, player, hp, atk, row, col):
        self.kind = kind
        self.player = player
        self.hp = hp
        self.max_hp = hp
        self.atk = atk
        self.row = row
        self.col = col

    def get_moves(self):
        if self.kind == '王':
            dirs = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
        else:
            forward = -1 if self.player == 1 else 1
            if self.kind == '歩':
                dirs = [(forward,0)]
            elif self.kind == '銀':
                dirs = [(forward,0),(forward,-1),(forward,1),(-forward,-1),(-forward,1)]
            else:  # 金
                dirs = [(forward,0),(-forward,0),(0,-1),(0,1),(forward,-1),(forward,1)]
        moves = []
        for dr, dc in dirs:
            nr, nc = self.row + dr, self.col + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                moves.append((nr, nc))
        return moves

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("5×5 黒将棋バトル＋戦闘アニメ(MP4/ffpyplayer)")
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont(None, 32)
        self.big_font = pygame.font.SysFont(None, 52)

        self.piece_images = self.load_piece_images()
        self.battle_mode = False

        self.reset()
        self.play_bgm(BGM_SHOGI)

    def load_piece_images(self):
        images = {}
        for kind, fn in PIECE_IMAGE_FILES.items():
            if os.path.exists(fn):
                img = pygame.image.load(fn).convert_alpha()
                img = pygame.transform.smoothscale(img, PIECE_SCALE)
                images[kind] = img
            else:
                images[kind] = None
        return images

    def reset(self):
        self.board = [[None]*BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.pieces = []
        self.current_player = 1
        self.selected = None
        self.valid_moves = []
        self.game_over = False
        self.winner = None
        self.battle_mode = False
        self.setup_board()

    def setup_board(self):
        # 上段 AI
        self.add_piece('歩',2,0,0,6,3)
        self.add_piece('銀',2,0,1,9,6)
        self.add_piece('王',2,0,2,10,4)
        self.add_piece('金',2,0,3,12,5)
        self.add_piece('歩',2,0,4,6,3)
        # 下段 プレイヤー
        self.add_piece('歩',1,4,0,6,3)
        self.add_piece('銀',1,4,1,9,6)
        self.add_piece('王',1,4,2,10,4)
        self.add_piece('金',1,4,3,12,5)
        self.add_piece('歩',1,4,4,6,3)

    def add_piece(self, kind, pl, r, c, hp, atk):
        p = Piece(kind, pl, hp, atk, r, c)
        self.board[r][c] = p
        self.pieces.append(p)

    def draw(self):
        self.draw_board()
        self.draw_pieces()
        self.draw_status()
        pygame.display.flip()

    def draw_board(self):
        self.screen.fill((0,0,0))  # 黒盤
        for r in range(BOARD_SIZE+1):
            pygame.draw.line(self.screen, (220,220,220), (0, r*CELL_H), (WIN_W, r*CELL_H), 3)
        for c in range(BOARD_SIZE+1):
            pygame.draw.line(self.screen, (220,220,220), (c*CELL_W, 0), (c*CELL_W, WIN_H), 3)

    def draw_pieces(self):
        for p in list(self.pieces):
            if p.hp <= 0:
                if self.board[p.row][p.col] == p:
                    self.board[p.row][p.col] = None
                self.pieces.remove(p)
                continue
            img = self.piece_images[p.kind]
            if img:
                x = p.col * CELL_W + CELL_W//2 - img.get_width()//2
                y = p.row * CELL_H + CELL_H//2 - img.get_height()//2
                img2 = pygame.transform.rotate(img,180) if p.player==2 else img
                self.screen.blit(img2, (x, y))
            if self.selected and (p.row, p.col)==self.selected:
                pygame.draw.rect(self.screen, (255,0,0), (p.col*CELL_W+2, p.row*CELL_H+2, CELL_W-4, CELL_H-4), 3)
        for (r,c) in self.valid_moves:
            pygame.draw.rect(self.screen, (50,150,255), (c*CELL_W+10, r*CELL_H+10, CELL_W-20, CELL_H-20), 2)

    def draw_status(self):
        if self.selected:
            r,c = self.selected
            p = self.board[r][c]
            txt = f"{p.kind}（{'自分' if p.player==1 else 'AI'}）HP:{p.hp} ATK:{p.atk}"
            surf = self.font.render(txt, True, (255,255,255))
            self.screen.blit(surf, (8, WIN_H-36))

    def play_bgm(self, filename, loop=-1):
        try:
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play(loop)
        except Exception as e:
            print("BGM再生失敗:", e)

    def stop_bgm(self):
        pygame.mixer.music.stop()

    def run(self):
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(e.pos)
            self.draw()
            self.clock.tick(FPS)

    def handle_click(self, pos):
        x,y = pos
        row, col = y//CELL_H, x//CELL_W
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            return
        p = self.board[row][col]
        if not self.selected:
            if p and p.hp > 0 and p.player == self.current_player:
                self.selected = (row, col)
                self.valid_moves = [m for m in p.get_moves()
                    if not self.board[m[0]][m[1]] or self.board[m[0]][m[1]].player != self.current_player]
        else:
            if (row, col) in self.valid_moves:
                self.move_or_attack(self.selected, (row, col))
                self.selected = None
                self.valid_moves = []
                if not self.game_over:
                    self.current_player = 2 if self.current_player == 1 else 1
                    self.ai_move()
                    self.current_player = 2 if self.current_player == 1 else 1
            else:
                self.selected = None
                self.valid_moves = []

    def move_or_attack(self, frm, to):
        fr, fc = frm; tr, tc = to
        atk = self.board[fr][fc]
        tgt = self.board[tr][tc]
        if tgt and tgt.player != atk.player:
            # ----ここでBGMを一時停止して戦闘動画を再生----
            self.stop_bgm()
            play_battle_video_ffpyplayer(MP4_FILE)
            self.play_bgm(BGM_SHOGI)
            # 戦闘解決ロジック（元のresolve_battleの内容）
            tgt.hp -= atk.atk
            if tgt.hp <= 0:
                if tgt in self.pieces:
                    self.pieces.remove(tgt)
                if self.board[tr][tc] == tgt:
                    self.board[tr][tc] = None
            else:
                atk.hp -= tgt.atk
                if atk.hp <= 0:
                    if atk in self.pieces:
                        self.pieces.remove(atk)
                    if self.board[fr][fc] == atk:
                        self.board[fr][fc] = None
            if atk in self.pieces:
                if self.board[fr][fc] == atk:
                    self.board[fr][fc] = None
                atk.row, atk.col = tr, tc
                self.board[tr][tc] = atk
            player_1_king = any(p for p in self.pieces if p.kind=='王' and p.player==1)
            player_2_king = any(p for p in self.pieces if p.kind=='王' and p.player==2)
            if not player_1_king or not player_2_king:
                self.game_over = True
                self.winner = 1 if player_1_king else 2
                print(f"勝者: {'自分' if self.winner==1 else 'AI'}")
            self.selected = None
            self.valid_moves = []
        else:
            if self.board[fr][fc] == atk:
                self.board[fr][fc] = None
            atk.row, atk.col = tr, tc
            self.board[tr][tc] = atk

    def ai_move(self):
        if self.game_over: return
        moves_attack = []
        moves_normal = []
        for p in self.pieces:
            if p.player == 2 and p.hp > 0:
                for m in p.get_moves():
                    t = self.board[m[0]][m[1]]
                    if t and t.player == 1:
                        moves_attack.append(((p.row, p.col), m))
                    elif not t:
                        moves_normal.append(((p.row, p.col), m))
        random.shuffle(moves_attack)
        for move in moves_attack:
            fr, to = move
            if self.board[to[0]][to[1]] and self.board[to[0]][to[1]].kind == "王":
                self.move_or_attack(fr, to)
                return
        if moves_attack:
            self.move_or_attack(*random.choice(moves_attack))
        elif moves_normal:
            self.move_or_attack(*random.choice(moves_normal))

if __name__ == "__main__":
    Game().run()
