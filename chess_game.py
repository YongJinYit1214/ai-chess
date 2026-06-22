import pygame
import sys
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Tuple
import copy

pygame.init()

BOARD_SIZE = 8
SQUARE_SIZE = 80
BOARD_WIDTH = SQUARE_SIZE * BOARD_SIZE
BOARD_HEIGHT = SQUARE_SIZE * BOARD_SIZE
INFO_HEIGHT = 60
WINDOW_WIDTH = BOARD_WIDTH
WINDOW_HEIGHT = BOARD_HEIGHT + INFO_HEIGHT

LIGHT_COLOR   = (240, 217, 181)
DARK_COLOR    = (181, 136, 99)
HIGHLIGHT_COLOR = (186, 202, 43)
SELECTED_COLOR  = (205, 210, 106)
CHECK_COLOR     = (220, 50, 50)
LAST_MOVE_COLOR = (170, 162, 58, 160)


class PieceType(Enum):
    PAWN   = 1
    KNIGHT = 2
    BISHOP = 3
    ROOK   = 4
    QUEEN  = 5
    KING   = 6

PIECE_VALUES = {
    PieceType.PAWN: 1,
    PieceType.KNIGHT: 3,
    PieceType.BISHOP: 3,
    PieceType.ROOK: 5,
    PieceType.QUEEN: 9,
    PieceType.KING: 0,
}

class Color(Enum):
    WHITE = 1
    BLACK = 2


@dataclass
class Piece:
    piece_type: PieceType
    color: Color
    has_moved: bool = False

    def __str__(self):
        color_str = "w" if self.color == Color.WHITE else "b"
        piece_map = {
            PieceType.PAWN:   "P",
            PieceType.KNIGHT: "N",
            PieceType.BISHOP: "B",
            PieceType.ROOK:   "R",
            PieceType.QUEEN:  "Q",
            PieceType.KING:   "K",
        }
        return f"{color_str}{piece_map[self.piece_type]}"


class Board:
    def __init__(self):
        self.squares: List[List[Optional[Piece]]] = [
            [None] * BOARD_SIZE for _ in range(BOARD_SIZE)
        ]
        self.setup_board()

    def setup_board(self):
        piece_order = [
            PieceType.ROOK, PieceType.KNIGHT, PieceType.BISHOP,
            PieceType.QUEEN, PieceType.KING, PieceType.BISHOP,
            PieceType.KNIGHT, PieceType.ROOK,
        ]
        for col, pt in enumerate(piece_order):
            self.squares[0][col] = Piece(pt, Color.BLACK)
            self.squares[7][col] = Piece(pt, Color.WHITE)
        for col in range(BOARD_SIZE):
            self.squares[1][col] = Piece(PieceType.PAWN, Color.BLACK)
            self.squares[6][col] = Piece(PieceType.PAWN, Color.WHITE)

    def get(self, row: int, col: int) -> Optional[Piece]:
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            return self.squares[row][col]
        return None

    def set(self, row: int, col: int, piece: Optional[Piece]):
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            self.squares[row][col] = piece

    def copy(self) -> "Board":
        b = Board.__new__(Board)
        b.squares = [[None] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                p = self.squares[r][c]
                if p:
                    b.squares[r][c] = Piece(p.piece_type, p.color, p.has_moved)
        return b


def get_pseudo_legal_moves(board: Board, row: int, col: int,
                           last_move: Optional[Tuple]) -> List[Tuple[int, int]]:
    """All moves for piece at (row,col) ignoring whether king is left in check."""
    piece = board.get(row, col)
    if piece is None:
        return []

    moves = []

    if piece.piece_type == PieceType.PAWN:
        direction = -1 if piece.color == Color.WHITE else 1
        start_row = 6 if piece.color == Color.WHITE else 1

        # Forward 1
        nr = row + direction
        if 0 <= nr < BOARD_SIZE and board.get(nr, col) is None:
            moves.append((nr, col))
            # Forward 2 from starting position
            if row == start_row:
                nr2 = row + 2 * direction
                if board.get(nr2, col) is None:
                    moves.append((nr2, col))

        # Diagonal captures
        for dc in (-1, 1):
            nr, nc = row + direction, col + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                target = board.get(nr, nc)
                if target is not None and target.color != piece.color:
                    moves.append((nr, nc))

        # En passant
        if last_move is not None:
            lf_r, lf_c, lt_r, lt_c = last_move
            last_piece = board.get(lt_r, lt_c)
            if (last_piece is not None and
                    last_piece.piece_type == PieceType.PAWN and
                    last_piece.color != piece.color and
                    abs(lf_r - lt_r) == 2 and
                    lt_r == row and abs(lt_c - col) == 1):
                moves.append((row + direction, lt_c))

    elif piece.piece_type == PieceType.KNIGHT:
        for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            nr, nc = row+dr, col+dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                t = board.get(nr, nc)
                if t is None or t.color != piece.color:
                    moves.append((nr, nc))

    elif piece.piece_type in (PieceType.BISHOP, PieceType.ROOK, PieceType.QUEEN):
        if piece.piece_type == PieceType.BISHOP:
            dirs = [(-1,-1),(-1,1),(1,-1),(1,1)]
        elif piece.piece_type == PieceType.ROOK:
            dirs = [(-1,0),(1,0),(0,-1),(0,1)]
        else:
            dirs = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
        for dr, dc in dirs:
            nr, nc = row+dr, col+dc
            while 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                t = board.get(nr, nc)
                if t is None:
                    moves.append((nr, nc))
                elif t.color != piece.color:
                    moves.append((nr, nc))
                    break
                else:
                    break
                nr += dr
                nc += dc

    elif piece.piece_type == PieceType.KING:
        for dr, dc in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            nr, nc = row+dr, col+dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                t = board.get(nr, nc)
                if t is None or t.color != piece.color:
                    moves.append((nr, nc))

        # Castling
        if not piece.has_moved:
            # Kingside
            rook = board.get(row, 7)
            if (rook and rook.piece_type == PieceType.ROOK and
                    rook.color == piece.color and not rook.has_moved and
                    board.get(row, 5) is None and board.get(row, 6) is None):
                moves.append((row, 6))   # marker; handled specially
            # Queenside
            rook = board.get(row, 0)
            if (rook and rook.piece_type == PieceType.ROOK and
                    rook.color == piece.color and not rook.has_moved and
                    board.get(row, 1) is None and board.get(row, 2) is None and
                    board.get(row, 3) is None):
                moves.append((row, 2))

    return moves


def is_square_attacked(board: Board, row: int, col: int, by_color: Color) -> bool:
    """Check if (row,col) is attacked by any piece of by_color."""
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            p = board.get(r, c)
            if p is not None and p.color == by_color:
                # Use pseudo moves without en passant context for attack detection
                moves = get_pseudo_legal_moves(board, r, c, None)
                if (row, col) in moves:
                    return True
    return False


def find_king(board: Board, color: Color) -> Optional[Tuple[int, int]]:
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            p = board.get(r, c)
            if p and p.piece_type == PieceType.KING and p.color == color:
                return (r, c)
    return None


def apply_move(board: Board, from_row: int, from_col: int,
               to_row: int, to_col: int, last_move: Optional[Tuple]) -> Board:
    """Return new board after applying the move (including en passant / castling)."""
    b = board.copy()
    piece = b.get(from_row, from_col)
    assert piece is not None

    # En passant capture
    if (piece.piece_type == PieceType.PAWN and
            from_col != to_col and b.get(to_row, to_col) is None):
        b.set(from_row, to_col, None)

    # Castling – move rook too
    if piece.piece_type == PieceType.KING and abs(to_col - from_col) == 2:
        if to_col == 6:   # kingside
            rook = b.get(from_row, 7)
            b.set(from_row, 5, Piece(PieceType.ROOK, piece.color, True))
            b.set(from_row, 7, None)
        else:              # queenside
            rook = b.get(from_row, 0)
            b.set(from_row, 3, Piece(PieceType.ROOK, piece.color, True))
            b.set(from_row, 0, None)

    new_piece = Piece(piece.piece_type, piece.color, True)
    b.set(to_row, to_col, new_piece)
    b.set(from_row, from_col, None)
    return b


def get_legal_moves(board: Board, row: int, col: int,
                    last_move: Optional[Tuple]) -> List[Tuple[int, int]]:
    """Legal moves: pseudo-legal moves that don't leave own king in check,
       plus castling path safety checks."""
    piece = board.get(row, col)
    if piece is None:
        return []

    pseudo = get_pseudo_legal_moves(board, row, col, last_move)
    opponent = Color.BLACK if piece.color == Color.WHITE else Color.WHITE
    legal = []

    for (tr, tc) in pseudo:
        # Extra castling check: king must not pass through check
        if piece.piece_type == PieceType.KING and abs(tc - col) == 2:
            # King's current square must not be in check
            if is_square_attacked(board, row, col, opponent):
                continue
            # Square king passes through must not be in check
            pass_col = 5 if tc == 6 else 3
            if is_square_attacked(board, row, pass_col, opponent):
                continue

        new_board = apply_move(board, row, col, tr, tc, last_move)
        king_pos = find_king(new_board, piece.color)
        if king_pos and not is_square_attacked(new_board, king_pos[0], king_pos[1], opponent):
            legal.append((tr, tc))

    return legal


def has_any_legal_move(board: Board, color: Color, last_move: Optional[Tuple]) -> bool:
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            p = board.get(r, c)
            if p and p.color == color:
                if get_legal_moves(board, r, c, last_move):
                    return True
    return False


def evaluate_board(board: Board):
    score = 0
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            piece = board.get(row, col)
            if piece:
                value = PIECE_VALUES[piece.piece_type]
                score += value if piece.color == Color.WHITE else -value
    return score

def get_all_moves(board, color, last_move):
    moves=[]
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            piece=board.get(r,c)
            if piece and piece.color==color:
                for tr,tc in get_legal_moves(board,r,c,last_move):
                    moves.append(((r,c),(tr,tc)))
    return moves

def minimax(board, depth, alpha, beta, maximizing, last_move):
    if depth==0:
        return evaluate_board(board)

    if maximizing:
        value=float('-inf')
        for move in get_all_moves(board, Color.WHITE, last_move):
            (fr,fc),(tr,tc)=move
            nb=apply_move(board,fr,fc,tr,tc,last_move)
            value=max(value,minimax(nb,depth-1,alpha,beta,False,(fr,fc,tr,tc)))
            alpha=max(alpha,value)
            if beta<=alpha:
                break
        return value
    else:
        value=float('inf')
        for move in get_all_moves(board, Color.BLACK, last_move):
            (fr,fc),(tr,tc)=move
            nb=apply_move(board,fr,fc,tr,tc,last_move)
            value=min(value,minimax(nb,depth-1,alpha,beta,True,(fr,fc,tr,tc)))
            beta=min(beta,value)
            if beta<=alpha:
                break
        return value

def get_best_move(board,last_move,depth=3):
    best_score=float('inf')
    best_move=None
    for move in get_all_moves(board, Color.BLACK, last_move):
        (fr,fc),(tr,tc)=move
        nb=apply_move(board,fr,fc,tr,tc,last_move)
        score=minimax(nb,depth-1,float('-inf'),float('inf'),True,(fr,fc,tr,tc))
        if score<best_score:
            best_score=score
            best_move=move
    return best_move



class GameState(Enum):
    PLAYING    = 0
    CHECK      = 1
    CHECKMATE  = 2
    STALEMATE  = 3


class ChessGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Chess")
        self.clock = pygame.time.Clock()
        self.reset()
        self.piece_images = {}
        self.load_images()

    def reset(self):
        self.board = Board()
        self.current_turn = Color.WHITE
        self.selected_square: Optional[Tuple[int, int]] = None
        self.valid_moves: List[Tuple[int, int]] = []
        self.last_move: Optional[Tuple[int, int, int, int]] = None
        self.promotion_square: Optional[Tuple[int, int]] = None
        self.promotion_color: Optional[Color] = None
        self.game_state = GameState.PLAYING
        self.status_msg = "White's turn"

    def load_images(self):
        pieces = ['wP','wN','wB','wR','wQ','wK','bP','bN','bB','bR','bQ','bK']
        for piece in pieces:
            try:
                img = pygame.image.load(f"assets/{piece}.png")
                self.piece_images[piece] = pygame.transform.smoothscale(
                    img, (SQUARE_SIZE, SQUARE_SIZE))
            except (FileNotFoundError, pygame.error):
                pass

    def get_material_score(self):
        white_score = 0
        black_score = 0

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board.get(row, col)
                if piece:
                    value = PIECE_VALUES[piece.piece_type]

                    if piece.color == Color.WHITE:
                        white_score += value
                    else:
                        black_score += value

        return white_score, black_score

    # ------------------------------------------------------------------ #
    #  Input handling
    # ------------------------------------------------------------------ #
    def handle_click(self, pos: Tuple[int, int]):
        x, y = pos
        if y >= BOARD_HEIGHT:
            return  # click in info bar

        col = x // SQUARE_SIZE
        row = y // SQUARE_SIZE

        if self.promotion_square is not None:
            self.handle_promotion_click(x, y)
            return

        if self.game_state in (GameState.CHECKMATE, GameState.STALEMATE):
            self.reset()
            return

        if self.selected_square is None:
            piece = self.board.get(row, col)
            if piece and piece.color == self.current_turn:
                self.selected_square = (row, col)
                self.valid_moves = get_legal_moves(
                    self.board, row, col, self.last_move)
        else:
            if (row, col) == self.selected_square:
                self.selected_square = None
                self.valid_moves = []
            elif (row, col) in self.valid_moves:
                self.execute_move(self.selected_square[0], self.selected_square[1], row, col)
            else:
                piece = self.board.get(row, col)
                if piece and piece.color == self.current_turn:
                    self.selected_square = (row, col)
                    self.valid_moves = get_legal_moves(
                        self.board, row, col, self.last_move)
                else:
                    self.selected_square = None
                    self.valid_moves = []

    def execute_move(self, from_row: int, from_col: int, to_row: int, to_col: int):
        piece = self.board.get(from_row, from_col)

        # Apply the move to the live board
        self.board = apply_move(
            self.board, from_row, from_col, to_row, to_col, self.last_move)

        self.last_move = (from_row, from_col, to_row, to_col)
        self.selected_square = None
        self.valid_moves = []

        # Pawn promotion?
        moved = self.board.get(to_row, to_col)
        if (moved and moved.piece_type == PieceType.PAWN and
                (to_row == 0 or to_row == 7)):
            self.promotion_square = (to_row, to_col)
            self.promotion_color = moved.color
            return   # wait for promotion choice before switching turn

        self.switch_turn()

        if self.current_turn == Color.BLACK and self.game_state not in (GameState.CHECKMATE, GameState.STALEMATE):
            self.make_ai_move()

    def switch_turn(self):
        self.current_turn = (Color.BLACK if self.current_turn == Color.WHITE
                             else Color.WHITE)
        opponent = Color.BLACK if self.current_turn == Color.WHITE else Color.WHITE
        king_pos = find_king(self.board, self.current_turn)
        in_check = (king_pos is not None and
                    is_square_attacked(self.board, king_pos[0], king_pos[1], opponent))
        has_moves = has_any_legal_move(self.board, self.current_turn, self.last_move)

        if not has_moves:
            if in_check:
                self.game_state = GameState.CHECKMATE
                winner = "White" if self.current_turn == Color.BLACK else "Black"
                self.status_msg = f"Checkmate! {winner} wins! Click to restart."
            else:
                self.game_state = GameState.STALEMATE
                self.status_msg = "Stalemate! Draw. Click to restart."
        elif in_check:
            self.game_state = GameState.CHECK
            turn_str = "White" if self.current_turn == Color.WHITE else "Black"
            self.status_msg = f"{turn_str} is in check!"
        else:
            self.game_state = GameState.PLAYING
            turn_str = "White" if self.current_turn == Color.WHITE else "Black"
            self.status_msg = f"{turn_str}'s turn"

    def make_ai_move(self):
        move = get_best_move(self.board, self.last_move, 3)
        if move:
            (fr, fc), (tr, tc) = move
            self.board = apply_move(self.board, fr, fc, tr, tc, self.last_move)
            self.last_move = (fr, fc, tr, tc)
            self.current_turn = Color.WHITE
            self.game_state = GameState.PLAYING
            self.status_msg = "White's turn"

    def handle_promotion_click(self, x: int, y: int):
        options = [PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT]
        menu_width = SQUARE_SIZE * 4
        menu_x = (WINDOW_WIDTH - menu_width) // 2
        menu_y = (BOARD_HEIGHT - SQUARE_SIZE) // 2

        for i, pt in enumerate(options):
            bx = menu_x + i * SQUARE_SIZE
            by = menu_y
            if bx <= x < bx + SQUARE_SIZE and by <= y < by + SQUARE_SIZE:
                pr, pc = self.promotion_square
                self.board.set(pr, pc, Piece(pt, self.promotion_color, True))
                self.promotion_square = None
                self.promotion_color = None
                self.switch_turn()

        if self.current_turn == Color.BLACK and self.game_state not in (GameState.CHECKMATE, GameState.STALEMATE):
            self.make_ai_move()
            return

    # ------------------------------------------------------------------ #
    #  Drawing
    # ------------------------------------------------------------------ #
    def draw_board(self):
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                rect = pygame.Rect(col*SQUARE_SIZE, row*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                color = LIGHT_COLOR if (row+col) % 2 == 0 else DARK_COLOR
                pygame.draw.rect(self.screen, color, rect)

        # Last move tint
        if self.last_move:
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            s.fill((170, 162, 58, 100))
            for (r, c) in [(self.last_move[0], self.last_move[1]),
                           (self.last_move[2], self.last_move[3])]:
                self.screen.blit(s, (c*SQUARE_SIZE, r*SQUARE_SIZE))

    def draw_highlights(self):
        # King in check highlight
        if self.game_state in (GameState.CHECK, GameState.CHECKMATE):
            king_pos = find_king(self.board, self.current_turn)
            if king_pos:
                kr, kc = king_pos
                s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                s.fill((220, 50, 50, 160))
                self.screen.blit(s, (kc*SQUARE_SIZE, kr*SQUARE_SIZE))

        if self.selected_square:
            row, col = self.selected_square
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            s.fill((205, 210, 106, 180))
            self.screen.blit(s, (col*SQUARE_SIZE, row*SQUARE_SIZE))

        for (mr, mc) in self.valid_moves:
            cx = mc*SQUARE_SIZE + SQUARE_SIZE//2
            cy = mr*SQUARE_SIZE + SQUARE_SIZE//2
            target = self.board.get(mr, mc)
            if target is not None:
                # Capture indicator: ring
                pygame.draw.circle(self.screen, HIGHLIGHT_COLOR, (cx, cy), SQUARE_SIZE//2-4, 5)
            else:
                pygame.draw.circle(self.screen, HIGHLIGHT_COLOR, (cx, cy), 10)

    def draw_pieces(self):
        piece_symbols = {
            PieceType.PAWN:'P', PieceType.KNIGHT:'N', PieceType.BISHOP:'B',
            PieceType.ROOK:'R', PieceType.QUEEN:'Q', PieceType.KING:'K',
        }
        fallback_font = pygame.font.Font(None, 64)
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board.get(row, col)
                if piece:
                    key = str(piece)
                    x = col*SQUARE_SIZE
                    y = row*SQUARE_SIZE
                    if key in self.piece_images:
                        self.screen.blit(self.piece_images[key], (x, y))
                    else:
                        sym = piece_symbols[piece.piece_type]
                        fc = (255,255,255) if piece.color == Color.WHITE else (20,20,20)
                        # Shadow
                        sh = fallback_font.render(sym, True, (0,0,0) if piece.color==Color.WHITE else (200,200,200))
                        sh_rect = sh.get_rect(center=(x+SQUARE_SIZE//2+2, y+SQUARE_SIZE//2+2))
                        self.screen.blit(sh, sh_rect)
                        ts = fallback_font.render(sym, True, fc)
                        tr = ts.get_rect(center=(x+SQUARE_SIZE//2, y+SQUARE_SIZE//2))
                        self.screen.blit(ts, tr)

    def draw_promotion_menu(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        options = [
            (PieceType.QUEEN,  "Q"),
            (PieceType.ROOK,   "R"),
            (PieceType.BISHOP, "B"),
            (PieceType.KNIGHT, "N"),
        ]
        menu_width = SQUARE_SIZE * 4
        menu_x = (WINDOW_WIDTH - menu_width) // 2
        menu_y = (BOARD_HEIGHT - SQUARE_SIZE) // 2

        pygame.draw.rect(self.screen, (50,50,50),
                         (menu_x-4, menu_y-4, menu_width+8, SQUARE_SIZE+8), border_radius=6)

        for i, (pt, sym) in enumerate(options):
            bx = menu_x + i*SQUARE_SIZE
            by = menu_y
            pygame.draw.rect(self.screen, (230,230,230),
                             (bx, by, SQUARE_SIZE, SQUARE_SIZE))
            mx, my = pygame.mouse.get_pos()
            if bx <= mx < bx+SQUARE_SIZE and by <= my < by+SQUARE_SIZE:
                pygame.draw.rect(self.screen, (180,230,180),
                                 (bx, by, SQUARE_SIZE, SQUARE_SIZE))

            key = ("w" if self.promotion_color == Color.WHITE else "b") + sym
            if key in self.piece_images:
                self.screen.blit(self.piece_images[key], (bx, by))
            else:
                font = pygame.font.Font(None, 64)
                ts = font.render(sym, True, (0,0,0))
                tr = ts.get_rect(center=(bx+SQUARE_SIZE//2, by+SQUARE_SIZE//2))
                self.screen.blit(ts, tr)

    def draw_info_bar(self):
        bar_rect = pygame.Rect(0, BOARD_HEIGHT, WINDOW_WIDTH, INFO_HEIGHT)
        pygame.draw.rect(self.screen, (30, 30, 30), bar_rect)

        font = pygame.font.Font(None, 32)
        color = (255,255,255)
        if self.game_state == GameState.CHECKMATE:
            color = (255, 120, 120)
        elif self.game_state == GameState.CHECK:
            color = (255, 200, 80)
        elif self.game_state == GameState.STALEMATE:
            color = (180, 180, 255)

        ts = font.render(self.status_msg, True, color)
        tr = ts.get_rect(center=(WINDOW_WIDTH//2, BOARD_HEIGHT + INFO_HEIGHT//2))
        self.screen.blit(ts, tr)

        white_score, black_score = self.get_material_score()
        material_diff = white_score - black_score

        if material_diff > 0:
            score_text = f"+{material_diff}"
        elif material_diff < 0:
            score_text = f"{material_diff}"   # already negative
        else:
            score_text = "0"

        score_font = pygame.font.Font(None, 28)

        score_surface = score_font.render(
            score_text,
            True,
            (255, 255, 255)
        )

        self.screen.blit(
            score_surface,
            (WINDOW_WIDTH - 60, BOARD_HEIGHT + 18)
        )

        # Turn indicator dot
        dot_color = (255,255,255) if self.current_turn == Color.WHITE else (80,80,80)
        pygame.draw.circle(self.screen, dot_color, (20, BOARD_HEIGHT + INFO_HEIGHT//2), 10)
        pygame.draw.circle(self.screen, (150,150,150), (20, BOARD_HEIGHT + INFO_HEIGHT//2), 10, 2)

    def draw(self):
        self.screen.fill((20, 20, 20))
        self.draw_board()
        self.draw_highlights()
        self.draw_pieces()
        self.draw_info_bar()
        if self.promotion_square is not None:
            self.draw_promotion_menu()
        pygame.display.flip()

    # ------------------------------------------------------------------ #
    #  Main loop
    # ------------------------------------------------------------------ #
    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset()

            self.draw()
            self.clock.tick(60)


if __name__ == "__main__":
    game = ChessGame()
    game.run()