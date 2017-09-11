#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2017 Toms Baugis <toms.baugis@gmail.com>

import math
import random

from gi.repository import Gtk as gtk
from gi.repository import GObject as gobject

from lib import graphics
from lib.pytweener import Easing


class Piece(graphics.Sprite):
    def __init__(self, col, row, shape=None):
        graphics.Sprite.__init__(self)
        self.interactive = True
        self.col = col
        self.row = row
        self.shape = shape
        self.selected = False
        self.reacting = False
        self.special = None
        self.recently_moved = False

        self.connect("on-render", self.on_render)

    def on_render(self, sprite):
        if self.shape == 0:
            self.graphics.rectangle(-15, -15, 30, 30)
            self.graphics.fill_preserve("#ff0000")
        elif self.shape == 1:
            self.graphics.circle(0, 0, 15)
            self.graphics.fill_preserve("#00ff00")
        elif self.shape == 2:
            self.graphics.rotate(math.radians(180))
            self.graphics.triangle(-15, -15, 30, 30)
            self.graphics.fill_preserve("#0000ff")
        elif self.shape == 3:
            self.graphics.rotate(math.radians(45))
            self.graphics.rectangle(-15, -15, 30, 30)
            self.graphics.fill_preserve("#ff00ff")
        elif self.shape == 4:
            self.graphics.rotate(math.radians(45))
            self.graphics.rectangle(-15, -15, 30, 30)
            self.graphics.fill_preserve("#ffffff")
        elif self.shape == 5:
            self.graphics.rectangle(-15, -15, 30, 30)
            self.graphics.fill_preserve("#00ffff")
        elif self.shape == 6:
            self.graphics.rectangle(-15, -15, 30, 30)
            self.graphics.fill_preserve("#ffff00")

        if self.selected:
            self.graphics.set_line_style(width=5)

        if self.reacting:
            self.graphics.set_line_style(width=5)
            self.graphics.stroke("#f00")
        else:
            self.graphics.stroke("#333")

        if self.special == "explode":
            self.graphics.circle(0, 0, 20)
            self.graphics.set_line_style(width=5)
            self.graphics.stroke("#f00")


class Board(graphics.Sprite):
    """
       we create a 10x10 board and fill it with pieces
       board consists of logic checking for consecutive pieces in rows and columns
       there are 6 different type of pieces and the board has to be initiated
       then again it would make sense to think about these as horizontally
       positioned buckets next to each other, and do a horiz scan
       the board controls the position of each piece
    """
    def __init__(self):
        # our board is an {(col, row): piece} dict
        graphics.Sprite.__init__(self)
        self.reset_board()
        self.move_pieces()
        self.interactive = True
        self.dummy = 1
        self.frame = 0
        self.cursor_item = None


    def on_click(self, piece, evt):
        if not piece:
            return

        selected = [sel for sel in self.sprites if sel.selected]
        selected = selected[0] if selected else None

        proximity = 10
        if selected:
            proximity = abs(selected.col - piece.col) + abs(selected.row - piece.row)

        if piece == selected:
            piece.selected = False
        if proximity == 1 and piece.shape != selected.shape:
            # swap
            piece.col, selected.col = selected.col, piece.col
            piece.row, selected.row = selected.row, piece.row
            piece.recently_moved, selected.recently_moved = True, True

            reactions = self.get_reactions()
            if not reactions:
                # undo if the move doesn't do anything
                piece.col, selected.col = selected.col, piece.col
                piece.row, selected.row = selected.row, piece.row
            else:
                piece.selected, selected.selected = False, False
                self.move_pieces(0.3)
                self.animate(duration=0.3, dummy=1, on_complete=self.check_board)

        else:
            self.select_item(piece)
            if selected:
                selected.selected = False

    def check_board(self, board=None):
        # this process can repeat several times via cleanup and fill
        reactions = self.get_reactions()
        if reactions:
            for group in reactions:
                special_piece = [piece for piece in group if piece.recently_moved]
                special_piece = special_piece[0] if special_piece else group[1]

                if len(group) == 4:
                     # XXX in bejeweled the special one is the one you moved or the merger point
                    special_piece.special = "explode"
                elif len(group) == 5:
                    group[1].special = "electricity"

                for piece in group:
                    if not piece.special:
                        piece.reacting = True
                        piece.animate(opacity=0, duration=0.4)
            self.animate(duration=0.4, dummy=1, on_complete=self.cleanup_and_fill)

        for piece in self.sprites:
            piece.recently_moved = False


    def cleanup_and_fill(self, board):
        for col in range(8):
            cur_idx = 7
            for piece in reversed(self._get_line(col, horiz=False)):
                if not piece.reacting:
                    if piece.row != cur_idx:
                        piece.row = cur_idx
                        piece.recently_moved = True
                    cur_idx -= 1
                else:
                    self.remove_child(piece)

            missing = 8 - len(self._get_line(col, horiz=False))
            for i in range(missing):
                piece = Piece(col, i, random.randint(0, 6))
                piece.x = 50 + col * 50
                piece.y = 50 + (i - missing) * 50
                self.add_child(piece)
                piece.connect("on-click", self.on_click)

        self.move_pieces()
        self.check_board()


    def reset_board(self):
        """renders a new board that doesn't have any explody conditions
        it does so by filling the buckets 1-by-1 horizontally and then performs
        scan on the whole board.
        add piece -> check for explosions. if explosions do not actually add the piece

        """
        for col in range(8):
            for row in range(8):
                piece = Piece(col, row, random.randint(0, 6))
                self.add_child(piece)
                piece.connect("on-click", self.on_click)

                while self.get_reactions():
                    piece.shape = random.randint(0, 6)

    def move_pieces(self, duration=0.4):
        for piece in self.sprites:
            piece.animate(x=50 + piece.col * 50, y = 50 + piece.row * 50, duration=duration, easing=Easing.Sine.ease_out)

    def get_reactions(self):
        """runs through the board and returns list of pieces that have to be destroyed.
        columns are actually rows pivoted - a plain list, so we don't need special cases
        just a getter func
        """
        reactions = []
        def check_sequence(sequence):
            if len(sequence) >= 3:
                reactions.append(sequence)

        for row in [True, False]:
            for i in  range(8):
                sequence = []
                for piece in self._get_line(i, row):
                    if not sequence or sequence[-1].shape != piece.shape:
                        check_sequence(sequence)
                        sequence = [piece]
                    else:
                        sequence.append(piece)
                check_sequence(sequence)
        return reactions


    def _get_line(self, line_no, horiz=True):
        line_items = []
        for piece in self.sprites:
            if (not horiz and piece.col == line_no) or (horiz and piece.row == line_no):
                line_items.append(piece)
        return sorted(line_items, key=lambda rec:rec.col if horiz else rec.row)


    def select_item(self, item):
        selected = [sel for sel in self.sprites if sel.selected]
        selected = selected[0] if selected else None
        if selected:
            selected.selected = False

        item.selected = item != selected
        self.cursor_item = item if item.selected else None


class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        self.board = Board()
        self.add_child(self.board)



class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_default_size(450, 450)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()



if __name__ == '__main__':
    window = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
