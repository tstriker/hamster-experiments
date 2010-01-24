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
from random import randint


class Canvas(graphics.Area):
    def __init__(self):
        graphics.Area.__init__(self)
        self.connect("mouse-move", self.on_mouse_move)
        self.tile_size = 50

    def on_mouse_move(self, area, coords, mouse_areas):
        self.tile_size = int(coords[0] / float(self.width) * 200 + 5) # x changes size of tile from 20 to 200(+20)
        self.redraw_canvas()


    def draw_tile(self, x, y, size, top_left = True):
        # draws a tile, there are just two orientations
        arc_radius = size / 2
        x2, y2 = x + size, y + size

        # i got lost here with all the numbers, drawing a rectangle around will help
        if top_left:
            self.context.move_to(x + arc_radius, y)
            self.context.arc(x, y, arc_radius, 0, math.pi / 2);

            self.context.move_to(x2 - arc_radius, y2)
            self.context.arc(x2, y2, arc_radius, math.pi, math.pi + math.pi / 2);
        else:
            self.context.move_to(x2, y + arc_radius)
            self.context.arc(x2, y, arc_radius, math.pi - math.pi / 2, math.pi);

            self.context.move_to(x, y2 - arc_radius)
            self.context.arc(x, y2, arc_radius, math.pi + math.pi / 2, 0);



    def on_expose(self):
        self.set_color("#000")
        self.context.set_line_width(1)

        for y in range(0, self.height, self.tile_size):
            for x in range(0, self.width, self.tile_size):
                self.draw_tile(x, y, self.tile_size, randint(-1, 1) > 0)

        self.context.stroke()
        self.context.fill()


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
