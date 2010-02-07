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

class Tile(graphics.Sprite):
    def __init__(self, x, y, size, orient):
        graphics.Sprite.__init__(self, interactive = False)

        self.x, self.y = x, y

        if orient % 2 == 0: # tiles 2 and 4 are flipped 1 and 3
            self.rotation = math.pi / 2
            self.x = self.x + size

        arc_radius = size / 2
        front, back = "#999", "#ccc"
        if orient > 2:
            front, back = back, front

        self.graphics.fill_area(0, 0, size, size, back)
        self.graphics.set_color(front)

        self.graphics.move_to(0, 0)
        self.graphics.line_to(arc_radius, 0)
        self.graphics.arc(0, 0, arc_radius, 0, math.pi / 2);
        self.graphics.close_path()

        self.graphics.move_to(size, size)
        self.graphics.line_to(size - arc_radius, size)
        self.graphics.arc(size, size, arc_radius, math.pi, math.pi + math.pi / 2);
        self.graphics.close_path()
        self.graphics.fill()


class Canvas(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.tile_size = 40
        self.connect("mouse-move", self.on_mouse_move)
        self.connect("on-enter-frame", self.on_enter_frame)

    def checker_fill(self):
        """fill area with 4-type matching tiles, where the other two have same
           shapes as first two, but colors are inverted"""
        self.clear()

        for y in range(0, self.height / self.tile_size + 1):
            for x in range(0, self.width / self.tile_size + 1):
                if (x + y) % 2:
                    tile = random.choice([1, 4])
                else:
                    tile = random.choice([2, 3])

                self.add_child(Tile(x * self.tile_size, y * self.tile_size, self.tile_size, tile))

    def on_mouse_move(self, area, event):
        self.tile_size = int(event.x / float(self.width) * 200 + 5) # x changes size of tile from 20 to 200(+20)
        self.tile_size = min([max(self.tile_size, 10), self.width, self.height])
        self.redraw_canvas()

    def on_enter_frame(self, scene, context):
        self.checker_fill()





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
