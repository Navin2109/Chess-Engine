"""
This is our main driver file. It will be responsible for handling user input and displaying
the current GameState object.
"""

import pygame as p
import ChessEngine
import ChessAI
from multiprocessing import Process, Queue

BOARD_WIDTH = BOARD_HEIGHT = 512  # 400 is also another option
MOVE_LOG_PANEL_WIDTH = 250
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSION = 8  # dimension of chess board are 8x8
SQ_SIZE = BOARD_HEIGHT // DIMENSION
MAX_FPS = 15  # for animations
IMAGES = {}

'''
Initialize a global dictionary of images. This will be called exactly once in the main.
'''


def load_images():
    pieces = ['wp', 'wR', 'wN', 'wB', 'wQ', 'wK', 'bp', 'bR', 'bN', 'bB', 'bQ', 'bK']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("./pieces/images/" + piece + ".png"), (SQ_SIZE, SQ_SIZE))
    # NOTE: we can access an image by saying 'IMAGES['wp']


'''
The main driver for our code. This will handle user input and updating the graphics.
'''


def main():
    p.init()
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    move_log_font = p.font.SysFont("Arial", 14, False, False)
    gs = ChessEngine.GameState()
    valid_moves = gs.get_valid_moves()
    move_made = False  # flag variable when a move is made
    animate = False  # flag variable when we should animate a move
    load_images()  # only do this once, before the while loop
    running = True
    sq_selected = ()  # no square selected, keep track of the last click of the user (tuple: (row, col))
    player_clicks = []  # keep track of player clicks (two tuples: (6, 4), (4, 4))
    game_over = False
    player_one = True  # If human is playing white, then this is true. If AI is playing, then it is false
    player_two = False  # same as above but for black
    AI_thinking = False
    move_finder_process = None
    move_undone = False

    while running:
        human_turn = (gs.white_to_move and player_one) or (not gs.white_to_move and player_two)
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False

            # mouse handler
            elif e.type == p.MOUSEBUTTONDOWN:
                if not game_over:
                    location = p.mouse.get_pos()  # (x, y) location of mouse
                    col = location[0]//SQ_SIZE
                    row = location[1]//SQ_SIZE

                    if sq_selected == (row, col) or col >= 8:  # user clicked the same square twice or user clicked mouse log
                        sq_selected = ()  # deselect
                        player_clicks = []  # clear player clicks
                    else:
                        sq_selected = (row, col)
                        player_clicks.append(sq_selected)  # appends for both 1st and 2nd click

                    if len(player_clicks) == 2 and human_turn:
                        move = ChessEngine.Move(player_clicks[0], player_clicks[1], gs.board)
                        print(move.get_chess_notations())

                        for i in range(len(valid_moves)):
                            if move == valid_moves[i]:
                                gs.make_move(valid_moves[i])
                                move_made = True
                                animate = True
                                sq_selected = ()  # reset user clicks
                                player_clicks = []
                        if not move_made:
                            player_clicks = [sq_selected]

            # key handler
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:  # undo when 'z' is pressed
                    gs.undo_move()
                    move_made = True
                    animate = False
                    game_over = False
                    if AI_thinking:
                        move_finder_process.terminate()
                        AI_thinking = False
                    move_undone = True
                if e.key == p.K_r:  # reset the board when r is pressed
                    gs = ChessEngine.GameState()
                    valid_moves = gs.get_valid_moves()
                    sq_selected = ()
                    player_clicks = []
                    move_made = False
                    animate = False
                    game_over = False
                    if AI_thinking:
                        move_finder_process.terminate()
                        AI_thinking = False
                    move_undone = True

        # AI move finder
        if not game_over and not human_turn and not move_undone:
            if not AI_thinking:
                AI_thinking = True
                print("thinking...")
                return_queue = Queue()  # used to pass data between threads
                move_finder_process = Process(target=ChessAI.find_best_move, args=(gs, valid_moves, return_queue))
                move_finder_process.start()  # call find_best_move(gs, valid_moves, return_queue)

            if not move_finder_process.is_alive():
                print("done thinking")
                AI_move = return_queue.get()
                if AI_move is None:
                    AI_move = ChessAI.find_random_move(valid_moves)
                gs.make_move(AI_move)
                move_made = True
                animate = True
                AI_thinking = False

        if move_made:
            if animate:
                animate_move(gs.move_log[-1], screen, gs.board, clock)
            valid_moves = gs.get_valid_moves()
            move_made = False
            animate = False
            move_undone = False

        draw_game_state(screen, gs, valid_moves, sq_selected, move_log_font)

        if gs.checkmate or gs.stalemate:
            game_over = True
            if gs.stalemate:
                text = "Stalemate"
            else:
                text = "Black wins by Checkmate" if gs.white_to_move else "White wins by Checkmate"
            draw_end_game_text(screen, text)

        clock.tick(MAX_FPS)
        p.display.flip()


'''
Responsible for all the graphics within a current game state.
'''


def draw_game_state(screen, gs, valid_moves, sq_selected, move_log_font):
    draw_board(screen)  # Draw squares on the board
    # add in piece highlight or move suggestion
    highlight_squares(screen, gs, valid_moves, sq_selected)
    draw_pieces(screen, gs.board)  # draw pieces on top of squares
    draw_move_log(screen, gs, move_log_font)


'''
Draw squares on the board. top left square is always white.
'''


def draw_board(screen):
    global colors
    colors = [p.Color(243, 229, 208), p.Color(198, 158, 112)]

    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[(r+c) % 2]
            p.draw.rect(screen, color, p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))


'''
Highlight square selected and moves for piece selected 
'''


def highlight_squares(screen, gs, valid_moves, sq_selected):
    if sq_selected != ():
        r, c = sq_selected
        if gs.board[r][c][0] == ("w" if gs.white_to_move else "b"):
            # highlight selected square
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100)  # transparency value -> 0 transparent; 255 opaque
            s.fill(p.Color("yellow"))
            screen.blit(s, (c*SQ_SIZE, r*SQ_SIZE))
            # highlight moves from that square
            s.fill(p.Color("yellow"))
            for move in valid_moves:
                if move.start_row == r and move.start_col == c:
                    screen.blit(s, (SQ_SIZE*move.end_col, SQ_SIZE*move.end_row))


'''
Draw the pieces on the using the current game state. board
'''


def draw_pieces(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]

            if piece != "--":  # not empty square
                screen.blit(IMAGES[piece], p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))


'''
Draws the move log
'''


def draw_move_log(screen, gs, font):
    move_log_rect = p.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen, p.Color("white"), move_log_rect)
    move_log = gs.move_log
    move_texts = []
    for i in range(0, len(move_log), 2):
        move_string = str(i//2 + 1) + ". " + str(move_log[i]) + " "
        if i+1 < len(move_log):  # make sure black made a move
            move_string += str(move_log[i+1]) + "  "
        move_texts.append(move_string)

    moves_per_row = 3
    padding = 5
    text_y = padding
    line_spacing = 3
    for i in range(0, len(move_texts), moves_per_row):
        text = ""
        for j in range(moves_per_row):
            if i+j < len(move_texts):
                text += move_texts[i+j]
        text_object = font.render(text, True, p.Color("Black"))
        text_location = move_log_rect.move(padding, text_y)
        screen.blit(text_object, text_location)
        text_y += text_object.get_height() + line_spacing

'''
Animating a move 
'''


def animate_move(move, screen, board, clock):
    global colors
    dR = move.end_row - move.start_row
    dC = move.end_col - move.start_col
    frames_per_sq = 5  # frames to move 1 square
    frame_count = (abs(dR) + abs(dC)) * frames_per_sq
    for frame in range(frame_count+1):
        r, c = (move.start_row + dR*frame/frame_count, move.start_col + dC*frame/frame_count)
        draw_board(screen)
        draw_pieces(screen, board)
        # erase the piece moved from its ending square
        color = colors[(move.end_row + move.end_col) % 2]
        end_square = p.Rect(move.end_col*SQ_SIZE, move.end_row*SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(screen, color, end_square)
        # draw captured piece onto rectangle
        if move.piece_capture != "--":
            if move.en_passant:
                en_passant_row = move.end_row+1 if move.piece_capture[0] == 'b' else move.end_row-1
                end_square = p.Rect(move.end_col * SQ_SIZE, en_passant_row * SQ_SIZE, SQ_SIZE, SQ_SIZE)
            screen.blit(IMAGES[move.piece_capture], end_square)
        # draw moving pieces
        screen.blit(IMAGES[move.piece_moved], p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(60)


def draw_end_game_text(screen, text):
    font = p.font.SysFont("Helvitca", 32, True, False)
    text_object = font.render(text, 0, p.Color("Black"))
    text_location = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(BOARD_WIDTH / 2 - text_object.get_width() / 2,
                                                                 BOARD_HEIGHT / 2 - text_object.get_height() / 2)
    screen.blit(text_object, text_location)
    text_object = font.render(text, 0, p.Color("Grey"))
    screen.blit(text_object, text_location.move(2, 2))


if __name__ == "__main__":
    main()
