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
from lib.pytweener import Easing

class Canvas(graphics.Area):
    def __init__(self):
        graphics.Area.__init__(self)
        #self.connect("mouse-move", self.on_mouse_move)
        self.tile_size = 40
        self.tile_map = {}
        self.x, self.y = 0, 0
        self.dx, self.dy = -1, -1
        #self.framerate = 40
        self.connect("configure-event", self.on_window_reconfigure)
        self.connect("mouse-move", self.on_mouse_move)
        self.pattern = []
        self.pattern_tiles = 2

    def on_window_reconfigure(self, area, stuff):
        self.tile_map = {}

    def on_mouse_move(self, area, coords, mouse_areas):
        x, y = coords

        #self.tile_size = min([max(int(100 * float(x) / self.width), 3), self.width * 2, self.height * 2])
        self.redraw_canvas()


    def on_expose(self):
        """here happens all the drawing"""
        if not self.height: return

        tile_size = int(self.tile_size)

        pattern_tiles = self.pattern_tiles
        #we move, and then we change the tile
        if not self.pattern:
            self.generate_tile_map(pattern_tiles, pattern_tiles)

        pattern_size = tile_size * pattern_tiles

        # draw the tile that we will clone
        for y, row in enumerate(self.pattern):
            for x, col in enumerate(self.pattern[y]):
                self.fill_tile(x * tile_size, y * tile_size, tile_size, self.pattern[y][x])

        # now get our pixmap
        tile_image = self.window.get_image(0, 0, min(pattern_size, self.width), min(pattern_size, self.height))

        for y in range(-pattern_size - int(abs(self.y)), self.height + pattern_size + int(abs(self.y)), pattern_size):
            for x in range(-pattern_size - int(abs(self.x)), self.width+pattern_size + int(abs(self.y)), pattern_size):
                self.window.draw_image(self.get_style().black_gc, tile_image, 0, 0, int(x + self.x), int(y + self.y), -1, -1)




        self.x += self.dx
        self.y -= self.dy


        if self.x > pattern_size or self.x < -pattern_size or \
           self.y > pattern_size or self.y < -pattern_size:
            self.randomize()

        self.redraw_canvas()

    def randomize(self):
        self.x = 0
        self.y = 0

        def switch_tiles():
            self.pattern = None
            self.pattern_tiles = random.randint(1, 5) * 2

        new_dx = (random.random() * 0.8 + 0.1) * random.choice([-1,1])
        new_dy = (random.random() * 0.8 + 0.1) * random.choice([-1,1])
        #new_tile_size = random.randint(4, min([self.width / self.pattern_tiles, self.height / self.pattern_tiles]))

        self.tweener.addTween(self,
                              tweenType = Easing.Expo.easeInOut,
                              tweenTime = 1,
                              dx = new_dx,
                              dy = new_dy,
                              onComplete = switch_tiles)


    def generate_tile_map(self, horizontal, vertical):
        """generate a 2x2 square and then see tile it"""
        pattern = []
        for y in range(vertical):
            pattern.append([])
            for x in range(horizontal):
                if (x + y) % 2:
                    tile = random.choice([1, 4])
                else:
                    tile = random.choice([2, 3])

                pattern[y].append(tile)

        self.pattern = pattern


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
