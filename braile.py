#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2011 Toms Bauģis <toms.baugis at gmail.com>

"""Braile letter toy - inspired by GSOC project
   http://srishtisethi.blogspot.com/2011/05/hallo-gnome-weekly-report-1-gsoc.html
"""

import string
from gi.repository import Gtk as gtk
from gi.repository import Pango as pango
from lib import graphics

braile_letters = {
    "a": (1,), "b": (1, 2), "c": (1, 4), "d": (1, 4, 5), "e": (1, 5),
    "f": (1, 2, 4), "g": (1, 2, 4, 5), "h": (1, 2, 5), "i": (2, 4),
    "j": (2, 4, 5), "k": (1, 3), "l": (1, 2, 3), "m": (1, 3, 4),
    "n": (1, 3, 4, 5), "o": (1, 3, 5), "p": (1, 2, 3, 4), "q": (1, 2, 3, 4, 5),
    "r": (1, 2, 3, 5), "s": (2, 3, 4), "t": (2, 3, 4, 5), "u": (1, 3, 6),
    "v": (1, 2, 3, 6), "w": (2, 4, 5, 6), "x": (1, 3, 4, 6), "y": (1, 3, 4, 5, 6),
    "z": (1, 3, 5, 6),
}


class BrailCell(graphics.Sprite):
    """a cell displaying braile character"""

    def __init__(self, letter = "", width = None, interactive = False, border = False, **kwargs):
        graphics.Sprite.__init__(self, **kwargs)
        self.interactive = interactive

        self.width = width

        padding = self.width * 0.1
        cell_size = self.width / 2 - padding

        inner_padding = self.width * 0.08
        cell_radius = cell_size - inner_padding * 2

        self.cells = []
        for x in range(2):
            for y in range(3):
                cell = graphics.Circle(cell_radius,
                                       cell_radius,
                                       interactive = interactive,
                                       stroke = "#333",
                                       x = padding + x * cell_size + inner_padding,
                                       y = padding + y * cell_size + inner_padding)
                if interactive:
                    cell.connect("on-mouse-over", self.on_mouse_over)
                    cell.connect("on-mouse-out", self.on_mouse_out)

                self.add_child(cell)
                self.cells.append(cell) # keep a separate track so we don't mix up with other sprites


        if border:
            self.add_child(graphics.Rectangle(cell_size * 2 + padding * 2,
                                              cell_size * 3 + padding * 2,
                                              stroke="#000"))

        self.letter = letter

    def on_mouse_over(self, cell):
        cell.original_fill = cell.fill
        cell.fill = "#080"

    def on_mouse_out(self, cell):
        cell.fill = cell.original_fill

    def fill_cells(self):
        fillings = braile_letters.get(self.letter.lower())
        for i in range(6):
            if (i + 1) in fillings:
                self.cells[i].fill = "#333"
            else:
                self.cells[i].fill = None

    def __setattr__(self, key, val):
        graphics.Sprite.__setattr__(self, key, val)
        if key == "letter":
            self.fill_cells()


class BrailTile(graphics.Sprite):
    """an interactive brail tile that e"""

    def __init__(self, letter, cell_width, **kwargs):
        graphics.Sprite.__init__(self, **kwargs)

        self.letter = letter

        mouse_rectangle = graphics.Rectangle(cell_width, cell_width * 1.4, 7, stroke="#000", interactive = True)
        self.add_child(mouse_rectangle)

        mouse_rectangle.connect("on-mouse-over", self.on_mouse_over)
        mouse_rectangle.connect("on-mouse-out", self.on_mouse_out)
        mouse_rectangle.connect("on-click", self.on_click)

        self.add_child(BrailCell(letter, width = cell_width))
        self.add_child(graphics.Label(letter, size = 14, color="#000",
                                      x = 12, y = cell_width * 1.4 + 5))

    def on_mouse_over(self, sprite):
        sprite.fill = "#ccc"

    def on_mouse_out(self, sprite):
        sprite.fill = None

    def on_click(self, sprite, event):
        self.emit("on-click", event)



class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)


        # letter display
        letter_display = graphics.Sprite(x=100)
        self.letter = graphics.Label(x=30, y = 40, text="F", size=200, color="#333")
        letter_display.add_child(self.letter)

        self.add_child(letter_display)


        # cell board
        cellboard = graphics.Sprite(x=450)
        self.letter_cell = BrailCell("f", x = 50, y=50, width = 200, interactive = True)
        cellboard.add_child(self.letter_cell)

        for i in range(2):
            for j in range(3):
                cellboard.add_child(graphics.Label(str(j + 1 + i * 3),
                                                   size = 50,
                                                   color = "#333",
                                                   x = i * 230 + 20,
                                                   y = j * 90 + 60))

        self.add_child(cellboard)

        # lowerboard
        lowerboard = graphics.Sprite(x=50, y = 450)
        cell_width = 40
        for i, letter in enumerate(string.ascii_uppercase[:13]):
            tile = BrailTile(letter = letter, cell_width = cell_width, x = i * (cell_width + 10) + 10)
            tile.connect("on-click", self.on_tile_click)
            lowerboard.add_child(tile)

        self.add_child(lowerboard)

    def on_tile_click(self, tile, event):
        self.letter.text = tile.letter
        self.letter_cell.letter = tile.letter



class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_default_size(800, 600)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()

if __name__ == '__main__':
    window = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
