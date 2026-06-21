# AI Chess

A Python chess game built with Pygame featuring a playable chess board with piece movement validation.

## Features

- **Interactive Chess Board**: 8x8 board with standard chess starting position
- **Piece Movement**: Support for all standard chess pieces (Pawn, Knight, Bishop, Rook, Queen, King)
- **Move Validation**: Basic move validation for each piece type
- **Visual Feedback**: Highlighted selected squares and valid moves
- **Click-to-Move**: Simple click-based interface for moving pieces

## Installation

1. Clone the repository:
```bash
git clone https://github.com/YongJinYit1214/ai-chess.git
cd ai-chess
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Game

```bash
python chess_game.py
```

## How to Play

1. Click on a piece to select it (it will be highlighted)
2. Valid moves will be shown as small circles
3. Click on a valid move to move the piece
4. Click on the selected piece again to deselect it

## Piece Movements

- **Pawn**: Moves forward one square (white moves up, black moves down)
- **Knight**: Moves in an L-shape (2 squares in one direction, 1 in perpendicular)
- **Bishop**: Moves diagonally any number of squares
- **Rook**: Moves horizontally or vertically any number of squares
- **Queen**: Combines bishop and rook movement
- **King**: Moves one square in any direction

## Colors

- Light squares: #F0D9B5
- Dark squares: #B58863
- Selected piece: #CDCE6A
- Valid moves: #BACA2B

## Future Enhancements

- Checkmate/Check detection
- Castling, En passant, Pawn promotion
- AI opponent
- Move history and undo functionality
- Game save/load
- Network multiplayer support
