#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>
"""
    Truchet pasta tiling (http://mathworld.wolfram.com/TruchetTiling.html)
    Most entertaining.
    Basically there are two types of tiles - "/" and "\" and we just randomly
    generate the whole thing
"""

import gtk
from lib import graphics
import math
import random


class Canvas(graphics.Area):
    def __init__(self):
        graphics.Area.__init__(self)
        self.connect("mouse-move", self.on_mouse_move)
        self.tile_size = 40


    def on_mouse_move(self, area, coords, mouse_areas):
        self.tile_size = int(coords[0] / float(self.width) * 200 + 5) # x changes size of tile from 20 to 200(+20)
        self.tile_size = min([max(self.tile_size, 10), self.width, self.height])
        self.redraw_canvas()


    def fill_tile(self, x, y, size, orient):
        # draws a tile, there are just two orientations
        arc_radius = size / 2

        front, back = "#666", "#aaa"
        if orient > 2:
            front, back = back, front

        self.fill_area(x, y, size, size, back)
        self.set_color(front)


        self.context.save()

        self.context.translate(x, y)
        if orient % 2 == 0: # tiles 2 and 4 are flipped 1 and 3
            self.context.rotate(math.pi / 2)
            self.context.translate(0, -size)

        self.context.move_to(0, 0)
        self.context.line_to(arc_radius, 0)
        self.context.arc(0, 0, arc_radius, 0, math.pi / 2);
        self.context.close_path()

        self.context.move_to(size, size)
        self.context.line_to(size - arc_radius, size)
        self.context.arc(size, size, arc_radius, math.pi, math.pi + math.pi / 2);
        self.context.close_path()

        self.context.fill()
        self.context.restore()


    def on_expose(self):
        """here happens all the drawing"""
        if not self.height: return
        self.checker_fill()
        #self.fill_tile(100, 100, 100, 1)


    def checker_fill(self):
        """fill area with 4-type matching tiles, where the other two have same
           shapes as first two, but colors are inverted"""

        for y in range(0, self.height / self.tile_size + 1):
            for x in range(0, self.width / self.tile_size + 1):
                if (x + y) % 2:
                    tile = random.choice([1, 4])
                else:
                    tile = random.choice([2, 3])
                self.fill_tile(x * self.tile_size, y * self.tile_size, self.tile_size, tile)


class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(500, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        canvas = Canvas()

        box = gtk.VBox()
        box.pack_start(canvas)


        window.add(box)
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    gtk.main()
