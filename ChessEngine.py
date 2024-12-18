"""
This class is responsible for storing all the information about the current state of chess
game. It will be also be responsible for determining the valid move of the current state. It
will also keep move log.
"""


class GameState:
    def __init__(self):
        # Board is a 8x8 2d list, each element of the list has 2 characters.
        # The first character represents the colour of the piece, 'b' or 'w'.
        # The second character represents type of the piece,'K', 'Q', 'B', 'N', 'R' or 'p'.
        # "__" represents an empty space with no pieces.
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]]

        self.move_function = {"p": self.get_pawn_moves, "R": self.get_rook_moves,
                              "N": self.get_knight_moves, "B": self.get_bishop_moves,
                              "Q": self.get_queen_moves, "K": self.get_king_moves}

        self.white_to_move = True
        self.move_log = []
        self.white_king_location = (7, 4)
        self.black_king_location = (0, 4)
        self.in_check = False
        self.pins = []
        self.checks = []
        self.checkmate = False
        self.stalemate = False
        self.en_passant_possible = ()  # coordinates for square where en passant capture is possible
        self.en_passant_possible_log = [self.en_passant_possible]
        # Castling rights
        self.white_castle_kingside = True
        self.white_castle_Queenside = True
        self.black_castle_kingside = True
        self.black_castle_Queenside = True
        self.castle_rights_log = [CastleRights(self.white_castle_kingside, self.black_castle_kingside,
                                               self.white_castle_Queenside, self.black_castle_Queenside)]

    '''
    Takes a moves as a parameter and executes it.(this will not work for castling, pawn-promotion, en-passant)
    '''
    def make_move(self, move):
        self.board[move.start_row][move.start_col] = "--"
        self.board[move.end_row][move.end_col] = move.piece_moved
        self.move_log.append(move)  # log the move so we can undo it later
        self.white_to_move = not self.white_to_move  # swap players
        # update the king's location if moved
        if move.piece_moved == "wK":
            self.white_king_location = (move.end_row, move.end_col)
        elif move.piece_moved == "bK":
            self.black_king_location = (move.end_row, move.end_col)

        # if pawn moves twice, next move can capture en_passant
        if move.piece_moved[1] == "p" and abs(move.start_row - move.end_row) == 2:
            self.en_passant_possible = ((move.end_row + move.start_row)//2, move.end_col)
        else:
            self.en_passant_possible = ()
        # if en_passant_move, must update the board to capture pawn
        if move.en_passant:
            self.board[move.start_row][move.end_col] = "--"

        # pawn promotion
        if move.pawn_promotion:
            # promoted_piece = input("Promote to Q, R, B, N: ")  # we can make this part of the ui later
            self.board[move.end_row][move.end_col] = move.piece_moved[0] + "Q"

        # update castling rights
        self.update_castle_rights(move)
        self.castle_rights_log.append(CastleRights(self.white_castle_kingside, self.black_castle_kingside,
                                                   self.white_castle_Queenside, self.black_castle_Queenside))
        # castle moves
        if move.castle:
            if move.end_col - move.start_col == 2:  # kingside
                self.board[move.end_row][move.end_col-1] = self.board[move.end_row][move.end_col+1]  # move rook
                self.board[move.end_row][move.end_col+1] = "--"  # empty space where rook was
            else:  # Queenside
                self.board[move.end_row][move.end_col+1] = self.board[move.end_row][move.end_col-2]  # move rook
                self.board[move.end_row][move.end_col-2] = "--"  # empty space where rook was

        self.en_passant_possible_log.append(self.en_passant_possible)

    '''
    Undo the last move made
    '''
    def undo_move(self):
        if self.move_log != 0:  # make sure there is a move to undo.
            move = self.move_log.pop()
            self.board[move.start_row][move.start_col] = move.piece_moved
            self.board[move.end_row][move.end_col] = move.piece_capture
            self.white_to_move = not self.white_to_move  # switch turn back
            # update the king's location if needed
            if move.piece_moved == "wK":
                self.white_king_location = (move.start_row, move.start_col)
            elif move.piece_moved == "bK":
                self.black_king_location = (move.start_row, move.start_col)
            # undo enpassant is different
            if move.en_passant:
                self.board[move.end_row][move.end_col] = "--"  # move that pawn that was added in the square
                self.board[move.start_row][move.end_col] = move.piece_capture  # puts the pawn on the correct square it was captured from

            self.en_passant_possible_log.pop()
            self.en_passant_possible = self.en_passant_possible_log[-1]

            # give back castle rights if move took them away
            self.castle_rights_log.pop()  # remove the last moves updates
            castle_rights = self.castle_rights_log[-1]
            self.white_castle_kingside = castle_rights.wks
            self.black_castle_kingside = castle_rights.bks
            self.white_castle_Queenside = castle_rights.wqs
            self.black_castle_Queenside = castle_rights.bqs

            # undo castle
            if move.castle:
                if move.end_col - move.start_col == 2:  # kingside
                    self.board[move.end_row][move.end_col+1] = self.board[move.end_row][move.end_col-1]  # move rook
                    self.board[move.end_row][move.end_col-1] = "--"  # empty space where rook was
                else:  # Queenside
                    self.board[move.end_row][move.end_col-2] = self.board[move.end_row][move.end_col+1]  # move rook
                    self.board[move.end_row][move.end_col+1] = "--"  # empty space where rook was

            # ADD THESE
            self.checkmate = False
            self.stalemate = False

    '''
    All moves considering checks
    '''
    def get_valid_moves(self):
        moves = []
        self.in_check, self.pins, self.checks = self.check_for_pins_and_checks()
        if self.white_to_move:
            king_row = self.white_king_location[0]
            king_col = self.white_king_location[1]
        else:
            king_row = self.black_king_location[0]
            king_col = self.black_king_location[1]

        if self.in_check:
            if len(self.checks) == 1:  # only 1 check, block check or move king
                moves = self.get_all_possible_moves()
                # To block a check you must move a piece into one of the squares between enemy piece and king
                check = self.checks[0]
                check_row = check[0]
                check_col = check[1]
                piece_checking = self.board[check_row][check_col]  # Enemy piece causing the check
                valid_squares = []  # valid squares move to
                # if knight , we must capture knight or move king
                if piece_checking[1] == "N":
                    valid_squares = [(check_row, check_col)]
                else:
                    for i in range(1, 8):
                        valid_square = (king_row + check[2]*i, king_col + check[3]*i)  # check[2] and check[3] are check directions
                        valid_squares.append(valid_square)
                        if valid_square[0] == check_row and valid_square[1] == check_col:  # once you get to piece end checks
                            break
                # get rid of any moves that don't block check or move king
                for i in range(len(moves)-1, -1, -1):  # go through backwards when removing from a list as iterating
                    if moves[i].piece_moved[1] != "K":  # doesn't move king so it must block or capture
                        if not (moves[i].end_row, moves[i].end_col) in valid_squares:  # move doesn't block or check a piece
                            moves.remove(moves[i])
            else:  # double check king has to move
                self.get_king_moves(king_row, king_col, moves)
        else:  # not in check so all moves are fine
            moves = self.get_all_possible_moves()

        if len(moves) == 0:
            if self.in_check:
                self.checkmate = True
            else:
                self.stalemate = True
        else:
            self.checkmate = False
            self.stalemate = False

        return moves

    '''
    All moves without considering checks
    '''
    def get_all_possible_moves(self):
        moves = []

        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                turn = self.board[r][c][0]
                if (turn == "w" and self.white_to_move) or (turn == "b" and not self.white_to_move):
                    piece = self.board[r][c][1]
                    self.move_function[piece](r, c, moves)  # calls the appropriate move function based on piece type.
        return moves

    '''
    Get all the pawn moves for the pawn located at row, col and add these moves to the list
    '''
    def get_pawn_moves(self, r, c, moves):
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        if self.white_to_move:
            move_amount = -1
            start_row = 6
            back_row = 0
            enemy_color = "b"
            king_row, king_col = self.white_king_location
        else:
            move_amount = 1
            start_row = 1
            back_row = 7
            enemy_color = "w"
            king_row, king_col = self.black_king_location

        if self.board[r+move_amount][c] == "--":  # 1 sq pawn advance
            if not piece_pinned or pin_direction == (move_amount, 0):
                moves.append(Move((r, c), (r+move_amount, c), self.board))
                if r == start_row and self.board[r+2*move_amount][c] == "--":  # 2 square move
                    moves.append(Move((r, c), (r+2*move_amount, c), self.board))

        # captures
        if c-1 >= 0:  # captures to left
            if not piece_pinned or pin_direction == (move_amount, -1):
                if self.board[r+move_amount][c-1][0] == enemy_color:  # enemy piece to capture
                    moves.append(Move((r, c), (r+move_amount, c-1), self.board))
                if (r + move_amount, c-1) == self.en_passant_possible:
                    attacking_piece = blocking_piece = False
                    if king_row == r:
                        if king_col < c:  # king is left of the pawn
                            # inside between king and pawn; outside range between border
                            inside_range = range(king_col+1, c-1)
                            outside_range = range(c+1, 8)
                        else:  # king right of the pawn
                            inside_range = range(king_col-1, c, -1)
                            outside_range = range(c-2, -1, -1)
                        for i in inside_range:
                            if self.board[r][i] != "--":  # some other piece beside en-passant and pawn block
                                blocking_piece = True
                        for i in outside_range:
                            square = self.board[r][i]
                            if square[0] == enemy_color and (square[1] == "R" or square[1] == "Q"):  # attacking piece
                                attacking_piece = True
                            elif square != "--":
                                blocking_piece = True
                    if not attacking_piece or blocking_piece:
                        moves.append(Move((r, c), (r+move_amount, c-1), self.board, en_passant=True))
        if c+1 <= 7:  # captures to right
            if not piece_pinned or pin_direction == (move_amount, 1):
                if self.board[r + move_amount][c + 1][0] == enemy_color:  # enemy piece to capture
                    moves.append(Move((r, c), (r + move_amount, c+1), self.board))
                if (r + move_amount, c+1) == self.en_passant_possible:
                    attacking_piece = blocking_piece = False
                    if king_row == r:
                        if king_col < c:  # king is left of the pawn
                            # inside between king and pawn; outside range between border
                            inside_range = range(king_col + 1, c)
                            outside_range = range(c+2, 8)
                        else:  # king right of the pawn
                            inside_range = range(king_col - 1, c+1, -1)
                            outside_range = range(c-1, -1, -1)
                        for i in inside_range:
                            if self.board[r][i] != "--":  # some other piece beside en-passant and pawn block
                                blocking_piece = True
                        for i in outside_range:
                            square = self.board[r][i]
                            if square[0] == enemy_color and (square[1] == "R" or square[1] == "Q"):  # attacking piece
                                attacking_piece = True
                            elif square != "--":
                                blocking_piece = True
                    if not attacking_piece or blocking_piece:
                        moves.append(Move((r, c), (r + move_amount, c - 1), self.board, en_passant=True))

    '''
    Get all the rook moves for the rook located at row, col and add these moves to the list
    '''
    def get_rook_moves(self, r, c, moves):
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                if self.board[r][c][1] != "Q":  # can't remove queen from pin on rook moves, only remove it on bishop moves
                    self.pins.remove(self.pins[i])
                break

        directions = ((-1, 0), (0, -1), (1, 0), (0, 1))
        enemy_color = "b" if self.white_to_move else "w"

        for d in directions:
            for i in range(1, 8):
                end_row = r + d[0]*i
                end_col = c + d[1]*i
                if 0 <= end_row < 8 and 0 <= end_col < 8:  # on the board
                    if not piece_pinned or pin_direction == d or pin_direction == (-d[0], -d[1]):
                        end_piece = self.board[end_row][end_col]
                        if end_piece == "--":  # empty space valid
                            moves.append(Move((r, c), (end_row, end_col), self.board))
                        elif end_piece[0] == enemy_color:  # enemy piece capture
                            moves.append(Move((r, c), (end_row, end_col), self.board))
                            break
                        else:  # friendly piece
                            break
                else:  # off board
                    break

    '''
    Get all the knight moves for the knight located at row, col and add these moves to the list
    '''
    def get_knight_moves(self, r, c, moves):
        piece_pinned = False
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piece_pinned = True
                self.pins.remove(self.pins[i])
                break

        knight_moves = ((-2, -1), (-2, 1), (2, -1), (2, 1), (1, -2), (1, 2), (-1, -2), (-1, 2))
        ally_color = "w" if self.white_to_move else "b"

        for m in knight_moves:
            end_row = r + m[0]
            end_col = c + m[1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:  # on the board
                if not piece_pinned:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] != ally_color:  # not an ally piece (empty or enemy piece)
                        moves.append(Move((r, c), (end_row, end_col), self.board))

    '''
    Get all the bishop moves for the bishop located at row, col and add these moves to the list
    '''
    def get_bishop_moves(self, r, c, moves):
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        directions = ((-1, -1), (-1, 1), (1, -1), (1, 1))  # 4 diagonals
        enemy_color = "b" if self.white_to_move else "w"

        for d in directions:
            for i in range(1, 8):
                end_row = r + d[0]*i
                end_col = c + d[1]*i
                if 0 <= end_row < 8 and 0 <= end_col < 8:  # on the board
                    if not piece_pinned or pin_direction == d or pin_direction == (-d[0], -d[1]):
                        end_piece = self.board[end_row][end_col]
                        if end_piece == "--":  # empty space valid
                            moves.append(Move((r, c), (end_row, end_col), self.board))
                        elif end_piece[0] == enemy_color:  # enemy piece capture
                            moves.append(Move((r, c), (end_row, end_col), self.board))
                            break
                        else:  # friendly piece
                            break
                else:  # off board
                    break

    '''
    Get all the queen moves for the queen located at row, col and add these moves to the list
    '''
    def get_queen_moves(self, r, c, moves):
        self.get_rook_moves(r, c, moves)
        self.get_bishop_moves(r, c, moves)

    '''
    Get all the king moves for the king located at row, col and add these moves to the list
    '''
    def get_king_moves(self, r, c, moves):
        row_moves = (-1, -1, -1, 0, 0, 1, 1, 1)
        col_moves = (-1, 0, 1, -1, 1, -1, 0, 1)
        ally_color = "w" if self.white_to_move else "b"

        for i in range(8):
            end_row = r + row_moves[i]
            end_col = c + col_moves[i]
            if 0 <= end_row < 8 and 0 <= end_col < 8:  # on the board
                end_piece = self.board[end_row][end_col]
                if end_piece[0] != ally_color:  # not an ally piece (empty or enemy piece)
                    # place king on end square and check for checks
                    if ally_color == "w":
                        self.white_king_location = (end_row, end_col)
                    else:
                        self.black_king_location = (end_row, end_col)

                    in_check, pins, check = self.check_for_pins_and_checks()
                    if not in_check:
                        moves.append(Move((r, c), (end_row, end_col), self.board))
                    # place king back on original position
                    if ally_color == "w":
                        self.white_king_location = (r, c)
                    else:
                        self.black_king_location = (r, c)
        self.get_castle_moves(r, c, moves, ally_color)

    '''
    Generate castle moves for king at (r, c) and add them  to the list of moves
    '''
    def get_castle_moves(self, r, c, moves, ally_color):
        in_check = self.square_under_attack(r, c, ally_color)
        if in_check:
            # print("oof")
            return  # can't castle in check
        if(self.white_to_move and self.white_castle_kingside) or (not self.white_to_move and self.black_castle_kingside):
            # can't castle if given up rights
            self.get_kingside_castle_moves(r, c, moves, ally_color)
        if (self.white_to_move and self.white_castle_Queenside) or (not self.white_to_move and self.black_castle_Queenside):
            self.get_Queenside_castle_moves(r, c, moves, ally_color)

    '''
    Generate kingside castle moves for the king at (r, c). This method will only be called if 
    player still has castle rights kingside.
    '''
    def get_kingside_castle_moves(self, r, c, moves, ally_color):
        # check if two square between king and rook are clear and not under attack
        if self.board[r][c+1] == "--" and self.board[r][c+2] == "--" and \
                not self.square_under_attack(r, c+1, ally_color) and not self.square_under_attack(r, c+2, ally_color):
            moves.append(Move((r, c), (r, c+2), self.board, castle=True))

    '''
    Generate Queenside castle moves for the king at (r, c). This method will only be called if 
    player still has castle rights Queenside.
    '''
    def get_Queenside_castle_moves(self, r, c, moves, ally_color):
        # check if two square between king and rook are clear and not under attack
        if self.board[r][c-1] == "--" and self.board[r][c-2] == "--" and self.board[r][c-3] == "--" and \
                not self.square_under_attack(r, c-1, ally_color) and not self.square_under_attack(r, c-2, ally_color):
            moves.append(Move((r, c), (r, c-2), self.board, castle=True))

    '''
    determine if the enemy can attack the square r, c
    '''
    def square_under_attack(self, r, c, ally_color):
        # check outward from square
        enemy_color = "w" if ally_color == "b" else "b"
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
        for j in range(len(directions)):
            d = directions[j]
            for i in range(1, 8):
                end_row = r + d[0]*i
                end_col = c + d[1]*i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] == ally_color:  # no attack from that direction
                        break
                    elif end_piece[0] == enemy_color:
                        type = end_piece[1]
                        # 5 possibilities in this complex conditional
                        # 1. orthogonally away from square and piece is a rook
                        # 2. diagonally away from square and piece is a bishop
                        # 3. 1 square diagonally away from square and piece is a pawn
                        # 4. any direction and piece is a queen
                        # 5. any direction 1 square away and piece is a king
                        if (0 <= j <= 3 and type == "R") or \
                                (4 <= j <= 7 and type == "B") or \
                                (i == 1 and type == "p" and (
                                    (enemy_color == "w" and 6 <= j <= 7) or (enemy_color == "b" and 4 <= j <= 5))) or \
                                (type == "Q") or (i == 1 and type == "K"):
                            return True
                        else:  # enemy piece not applying check
                            break
                else:
                    break  # off the board
        # check for knight checks
        knight_moves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        for m in knight_moves:
            end_row = r + m[0]
            end_col = c + m[1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] == enemy_color and end_piece[1] == "N":  # enemy knight attacking king
                    return True

        return False

    '''
    Returns if player is in check, a list of pins, a list of checks
    '''
    def check_for_pins_and_checks(self):
        pins = []
        checks = []
        in_check = False

        if self.white_to_move:
            enemy_color = "b"
            ally_color = "w"
            start_row = self.white_king_location[0]
            start_col = self.white_king_location[1]
        else:
            enemy_color = "w"
            ally_color = "b"
            start_row = self.black_king_location[0]
            start_col = self.black_king_location[1]
        # check outward of king for pins and checks, keep track of pins
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
        for j in range(len(directions)):
            d = directions[j]
            possible_pin = ()  # reset pin
            for i in range(1, 8):
                end_row = start_row + d[0]*i
                end_col = start_col + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] == ally_color and end_piece[1] != "K":
                        if possible_pin == ():  # 1st allied piece could be pinned
                            possible_pin = (end_row, end_col, d[0], d[1])
                        else:  # 2nd allied piece so no pin or check possible
                            break
                    elif end_piece[0] == enemy_color:
                        type = end_piece[1]
                        # 5 possibilities in this complex condition
                        # 1. Orthogonally away from king and piece is a rook
                        # 2. Diagonally away from king and piece is a bishop
                        # 3. 1 square away diagonally from king and piece is a pawn
                        # 4. any direction and piece is a queen
                        # 5. any direction 1 square away and piece is a king (this is necessary to prevent king move to a square controlled by another king)
                        if (0 <= j <= 3 and type == "R") or \
                                (4 <= j <= 7 and type == "B") or \
                                (i == 1 and type == "p" and ((enemy_color == "w" and 6 <= j <= 7) or (enemy_color == "b" and 4 <= j <= 5))) or \
                                (type == "Q") or (i == 1 and type == "K"):
                            if possible_pin == ():  # no piece blocking so check
                                in_check = True
                                checks.append((end_row, end_col, d[0], d[1]))
                                break
                            else:  # piece blocking so pin
                                pins.append(possible_pin)
                                break
                        else:  # enemy piece not applying check
                            break
                else:  # off the board
                    break

        # check for knight checks
        knight_moves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        for m in knight_moves:
            end_row = start_row + m[0]
            end_col = start_col + m[1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] == enemy_color and end_piece[1] == "N":  # enemy knight attacking king
                    in_check = True
                    checks.append((end_row, end_col, m[0], m[1]))
        return in_check, pins, checks

    '''
    Update the castle rights given the move
    '''
    def update_castle_rights(self, move):
        if move.piece_moved == "wK":
            self.white_castle_kingside = False
            self.white_castle_Queenside = False
        elif move.piece_moved == "bK":
            self.black_castle_kingside = False
            self.black_castle_Queenside = False
        elif move.piece_moved == "wR":
            if move.start_row == 7:
                if move.start_col == 0:  # left rook
                    self.white_castle_Queenside = False
                elif move.start_col == 7:
                    self.white_castle_kingside = False
        elif move.piece_moved == "bR":
            if move.start_row == 0:
                if move.start_col == 0:  # left rook
                    self.black_castle_Queenside = False
                elif move.start_col == 7:
                    self.black_castle_kingside = False

        # if rook is captured
        if move.piece_capture == "wR":
            if move.end_row == 7:
                if move.end_col == 0:
                    self.white_castle_Queenside = False
                elif move.end_col == 7:
                    self.white_castle_kingside = False
        elif move.piece_capture == "bR":
            if move.end_row == 0:
                if move.end_col == 0:
                    self.black_castle_Queenside = False
                elif move.end_col == 7:
                    self.black_castle_kingside = False


class CastleRights():
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs


class Move:
    # maps keys to values
    # key : values
    rank_to_rows = {"1": 7, "2": 6, "3": 5, "4": 4,
                    "5": 3, "6": 2, "7": 1, "8": 0}
    rows_to_ranks = {v: k for k, v in rank_to_rows.items()}
    files_to_cols = {"a": 0, "b": 1, "c": 2, "d": 3,
                     "e": 4, "f": 5, "g": 6, "h": 7}

    cols_to_files = {v: k for k, v in files_to_cols.items()}

    def __init__(self, start_sq, end_sq, board, en_passant=False, castle=False):
        self.start_row = start_sq[0]
        self.start_col = start_sq[1]
        self.end_row = end_sq[0]
        self.end_col = end_sq[1]
        self.piece_moved = board[self.start_row][self.start_col]
        self.piece_capture = board[self.end_row][self.end_col]
        self.en_passant = en_passant
        if en_passant:
            self.piece_capture = "bp" if self.piece_moved == "wp" else "wp"  # en passant capture opposite color pawn

        self.pawn_promotion = (self.piece_moved == "wp" and self.end_row == 0) or (
                                self.piece_moved == "bp" and self.end_row == 7)

        self.castle = castle

        self.is_capture = self.piece_capture != "--"
        self.move_id = self.start_row*1000 + self.start_col*100 + self.end_row*10 + self.end_col
    '''
    Overriding equals method
    '''
    def __eq__(self, other):
        if isinstance(other, Move):
            return self.move_id == other.move_id
        return False

    def get_chess_notations(self):
        # you can add to make this a real chess notation
        return self.get_rank_file(self.start_row, self.start_col) + self.get_rank_file(self.end_row, self.end_col)

    def get_rank_file(self, r, c):
        return self.cols_to_files[c] + self.rows_to_ranks[r]

    # overriding the str() function
    def __str__(self):
        # castle move
        if self.castle:
            return "O-O" if self.end_col == 6 else "O-O-O"

        end_square = self.get_rank_file(self.end_row, self.end_col)

        # pawn moves
        if self.piece_moved[1] == "p":
            if self.is_capture:
                return self.cols_to_files[self.start_col] + "x" + end_square
            else:
                return end_square

        # pawn promotions

        # two of same type of piece moving to a square

        # also adding + for check move and # for checkmate

        # piece moves
        move_string = self.piece_moved[1]
        if self.is_capture:
            move_string += "x"
        return move_string + end_square
