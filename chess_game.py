import pygame
import sys
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Tuple

pygame.init()

BOARD_SIZE = 8
SQUARE_SIZE = 80
BOARD_WIDTH = SQUARE_SIZE * BOARD_SIZE
BOARD_HEIGHT = SQUARE_SIZE * BOARD_SIZE
WINDOW_WIDTH = BOARD_WIDTH
WINDOW_HEIGHT = BOARD_HEIGHT

LIGHT_COLOR = (240, 217, 181)
DARK_COLOR = (181, 136, 99)
HIGHLIGHT_COLOR = (186, 202, 43)
SELECTED_COLOR = (205, 210, 106)

class PieceType(Enum):
    PAWN = 1
    KNIGHT = 2
    BISHOP = 3
    ROOK = 4
    QUEEN = 5
    KING = 6

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
            PieceType.PAWN: "P",
            PieceType.KNIGHT: "N",
            PieceType.BISHOP: "B",
            PieceType.ROOK: "R",
            PieceType.QUEEN: "Q",
            PieceType.KING: "K"
        }
        return f"{color_str}{piece_map[self.piece_type]}"

@dataclass
class Square:
    row: int
    col: int
    piece: Optional[Piece] = None

class Board:
    def __init__(self):
        self.squares = [[Square(row, col) for col in range(BOARD_SIZE)] for row in range(BOARD_SIZE)]
        self.setup_board()
    
    def setup_board(self):
        piece_order = [
            PieceType.ROOK, PieceType.KNIGHT, PieceType.BISHOP, 
            PieceType.QUEEN, PieceType.KING, PieceType.BISHOP, 
            PieceType.KNIGHT, PieceType.ROOK
        ]
        
        for col, piece_type in enumerate(piece_order):
            self.squares[0][col].piece = Piece(piece_type, Color.BLACK)
            self.squares[7][col].piece = Piece(piece_type, Color.WHITE)
        
        for col in range(BOARD_SIZE):
            self.squares[1][col].piece = Piece(PieceType.PAWN, Color.BLACK)
            self.squares[6][col].piece = Piece(PieceType.PAWN, Color.WHITE)
    
    def get_piece(self, row: int, col: int) -> Optional[Piece]:
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            return self.squares[row][col].piece
        return None
    
    def set_piece(self, row: int, col: int, piece: Optional[Piece]):
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            self.squares[row][col].piece = piece
    
    def is_valid_move(self, from_row: int, from_col: int, to_row: int, to_col: int) -> bool:
        if not (0 <= from_row < BOARD_SIZE and 0 <= from_col < BOARD_SIZE):
            return False
        if not (0 <= to_row < BOARD_SIZE and 0 <= to_col < BOARD_SIZE):
            return False
        
        piece = self.get_piece(from_row, from_col)
        if piece is None:
            return False
        
        target = self.get_piece(to_row, to_col)
        if target is not None and target.color == piece.color:
            return False
        
        if from_row == to_row and from_col == to_col:
            return False
        
        return True
    
    def move_piece(self, from_row: int, from_col: int, to_row: int, to_col: int) -> bool:
        if not self.is_valid_move(from_row, from_col, to_row, to_col):
            return False
        
        piece = self.get_piece(from_row, from_col)
        piece.has_moved = True
        self.set_piece(to_row, to_col, piece)
        self.set_piece(from_row, from_col, None)
        return True

class ChessGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("AI Chess")
        self.clock = pygame.time.Clock()
        self.board = Board()
        self.selected_square = None
        self.valid_moves = []
        self.running = True
        self.font = pygame.font.Font(None, 30)
        self.piece_images = {}
        self.load_images()
        
    def load_images(self):
        pieces = ['wP', 'wN', 'wB', 'wR', 'wQ', 'wK', 'bP', 'bN', 'bB', 'bR', 'bQ', 'bK']
        for piece in pieces:
            try:
                # Load the image from your assets folder
                img = pygame.image.load(f"assets/{piece}.png")
                # Scale it to fit beautifully inside the board squares
                self.piece_images[piece] = pygame.transform.scale(img, (SQUARE_SIZE, SQUARE_SIZE))
            except FileNotFoundError:
                print(f"Warning: Could not find asset assets/{piece}.png")
    
    def handle_click(self, pos: Tuple[int, int]):
        col = pos[0] // SQUARE_SIZE
        row = pos[1] // SQUARE_SIZE
        
        if self.selected_square is None:
            if self.board.get_piece(row, col) is not None:
                self.selected_square = (row, col)
                self.calculate_valid_moves()
        else:
            if (row, col) == self.selected_square:
                self.selected_square = None
                self.valid_moves = []
            elif (row, col) in self.valid_moves:
                from_row, from_col = self.selected_square
                self.board.move_piece(from_row, from_col, row, col)
                self.selected_square = None
                self.valid_moves = []
            else:
                if self.board.get_piece(row, col) is not None:
                    self.selected_square = (row, col)
                    self.calculate_valid_moves()
                else:
                    self.selected_square = None
                    self.valid_moves = []
    
    def calculate_valid_moves(self):
        if self.selected_square is None:
            self.valid_moves = []
            return
        
        row, col = self.selected_square
        piece = self.board.get_piece(row, col)
        
        if piece is None:
            self.valid_moves = []
            return
        
        moves = []
        
        if piece.piece_type == PieceType.PAWN:
            direction = -1 if piece.color == Color.WHITE else 1
            
            # Move 1 square forward
            target_row = row + direction
            if 0 <= target_row < BOARD_SIZE:
                if self.board.get_piece(target_row, col) is None:
                    moves.append((target_row, col))
            
            # Move 2 squares forward on first move
            if not piece.has_moved:
                target_row = row + 2 * direction
                if 0 <= target_row < BOARD_SIZE:
                    # Check both the 1-square and 2-square positions are empty
                    if (self.board.get_piece(row + direction, col) is None and
                        self.board.get_piece(target_row, col) is None):
                        moves.append((target_row, col))
        
        elif piece.piece_type == PieceType.KNIGHT:
            knight_moves = [
                (-2, -1), (-2, 1), (-1, -2), (-1, 2),
                (1, -2), (1, 2), (2, -1), (2, 1)
            ]
            for dr, dc in knight_moves:
                nr, nc = row + dr, col + dc
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                    target = self.board.get_piece(nr, nc)
                    if target is None or target.color != piece.color:
                        moves.append((nr, nc))
        
        elif piece.piece_type == PieceType.BISHOP:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            for dr, dc in directions:
                nr, nc = row + dr, col + dc
                while 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                    target = self.board.get_piece(nr, nc)
                    if target is None:
                        moves.append((nr, nc))
                    elif target.color != piece.color:
                        moves.append((nr, nc))
                        break
                    else:
                        break
                    nr += dr
                    nc += dc
        
        elif piece.piece_type == PieceType.ROOK:
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dr, dc in directions:
                nr, nc = row + dr, col + dc
                while 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                    target = self.board.get_piece(nr, nc)
                    if target is None:
                        moves.append((nr, nc))
                    elif target.color != piece.color:
                        moves.append((nr, nc))
                        break
                    else:
                        break
                    nr += dr
                    nc += dc
        
        elif piece.piece_type == PieceType.QUEEN:
            directions = [
                (-1, -1), (-1, 0), (-1, 1), (0, -1),
                (0, 1), (1, -1), (1, 0), (1, 1)
            ]
            for dr, dc in directions:
                nr, nc = row + dr, col + dc
                while 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                    target = self.board.get_piece(nr, nc)
                    if target is None:
                        moves.append((nr, nc))
                    elif target.color != piece.color:
                        moves.append((nr, nc))
                        break
                    else:
                        break
                    nr += dr
                    nc += dc
        
        elif piece.piece_type == PieceType.KING:
            directions = [
                (-1, -1), (-1, 0), (-1, 1), (0, -1),
                (0, 1), (1, -1), (1, 0), (1, 1)
            ]
            for dr, dc in directions:
                nr, nc = row + dr, col + dc
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                    target = self.board.get_piece(nr, nc)
                    if target is None or target.color != piece.color:
                        moves.append((nr, nc))
        
        self.valid_moves = moves
    
    def draw_board(self):
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                rect = pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                color = LIGHT_COLOR if (row + col) % 2 == 0 else DARK_COLOR
                pygame.draw.rect(self.screen, color, rect)
    
    def draw_highlights(self):
        if self.selected_square:
            row, col = self.selected_square
            rect = pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            pygame.draw.rect(self.screen, SELECTED_COLOR, rect, 3)
        
        for move_row, move_col in self.valid_moves:
            center_x = move_col * SQUARE_SIZE + SQUARE_SIZE // 2
            center_y = move_row * SQUARE_SIZE + SQUARE_SIZE // 2
            pygame.draw.circle(self.screen, HIGHLIGHT_COLOR, (center_x, center_y), 8)
    
    def draw_pieces(self):
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board.get_piece(row, col)
                if piece:
                    piece_key = str(piece) # e.g., "wP", "bK"
                    
                    # If the image exists in our dictionary, draw it
                    if piece_key in self.piece_images:
                        x = col * SQUARE_SIZE
                        y = row * SQUARE_SIZE
                        self.screen.blit(self.piece_images[piece_key], (x, y))
                    else:
                        # FALLBACK: If an image is missing, draw large text so it's centered
                        fallback_font = pygame.font.Font(None, 70)
                        piece_symbols = {
                            PieceType.PAWN: "P", PieceType.KNIGHT: "N", 
                            PieceType.BISHOP: "B", PieceType.ROOK: "R", 
                            PieceType.QUEEN: "Q", PieceType.KING: "K"
                        }
                        x = col * SQUARE_SIZE + SQUARE_SIZE // 2
                        y = row * SQUARE_SIZE + SQUARE_SIZE // 2
                        color = (255, 255, 255) if piece.color == Color.WHITE else (0, 0, 0)
                        
                        text_surface = fallback_font.render(piece_symbols[piece.piece_type], True, color)
                        text_rect = text_surface.get_rect(center=(x, y))
                        self.screen.blit(text_surface, text_rect)
    
    def draw(self):
        self.screen.fill((255, 255, 255))
        self.draw_board()
        self.draw_highlights()
        self.draw_pieces()
        pygame.display.flip()
    
    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)
            
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = ChessGame()
    game.run()
