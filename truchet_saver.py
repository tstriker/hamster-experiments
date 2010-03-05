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

class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.tile_size = 40
        self.tile_map = {}
        self.x, self.y = 0, 0
        self.dx, self.dy = -1, -1
        #self.framerate = 40
        self.pattern = []
        self.pattern_tiles = 2
        self.connect("configure-event", self.on_window_reconfigure)
        self.connect("on-enter-frame", self.on_enter_frame)

    def on_window_reconfigure(self, area, stuff):
        self.tile_map = {}

    def on_enter_frame(self, scene, context):
        tile_size = int(self.tile_size)
        pattern_tiles = self.pattern_tiles
        #we move, and then we change the tile
        if not self.pattern:
            self.generate_tile_map(pattern_tiles, pattern_tiles)

        pattern_size = tile_size * pattern_tiles

        # draw the tile that we will clone
        for y, row in enumerate(self.pattern):
            for x, col in enumerate(self.pattern[y]):
                self.fill_tile(context, x * tile_size, y * tile_size, tile_size, self.pattern[y][x])

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

        self.redraw()

    def randomize(self):
        self.x = 0
        self.y = 0

        def switch_tiles(sprite):
            self.pattern = None
            self.pattern_tiles = random.randint(1, 5) * 2

        new_dx = (random.random() * 0.8 + 0.1) * random.choice([-1,1])
        new_dy = (random.random() * 0.8 + 0.1) * random.choice([-1,1])
        #new_tile_size = random.randint(4, min([self.width / self.pattern_tiles, self.height / self.pattern_tiles]))

        self.tweener.add_tween(self,
                              easing = Easing.Expo.ease_in_out,
                              duration = 1,
                              dx = new_dx,
                              dy = new_dy,
                              on_complete = switch_tiles)


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


    def fill_tile(self, context, x, y, size, orient):
        # draws a tile, there are just two orientations
        arc_radius = size / 2

        front, back = "#666", "#aaa"
        if orient > 2:
            front, back = back, front

        context.set_source_rgb(*self.colors.parse(back))
        context.rectangle(x, y, size, size)
        context.fill()

        context.set_source_rgb(*self.colors.parse(front))


        context.save()
        context.translate(x, y)
        if orient % 2 == 0: # tiles 2 and 4 are flipped 1 and 3
            context.rotate(math.pi / 2)
            context.translate(0, -size)

        context.move_to(0, 0)
        context.line_to(arc_radius, 0)
        context.arc(0, 0, arc_radius, 0, math.pi / 2);
        context.close_path()

        context.move_to(size, size)
        context.line_to(size - arc_radius, size)
        context.arc(size, size, arc_radius, math.pi, math.pi + math.pi / 2);
        context.close_path()

        context.fill()
        context.restore()



class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(500, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        window.add(Scene())
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    gtk.main()
