#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>
"""
    Truchet pasta tiling (http://mathworld.wolfram.com/TruchetTiling.html)
    Most entertaining.
    Basically there are two types of tiles - "/" and "\" and we just randomly
    generate the whole thing

    What's extra here, is the flood fill http://en.wikipedia.org/wiki/Flood_fill
    For that we first draw with cairo and then analyse on pixel level via
    gtk.gdk.Image.
"""

import gtk
from lib import graphics
import math
from random import randint


class Canvas(graphics.Area):
    def __init__(self):
        graphics.Area.__init__(self)
        self.connect("mouse-move", self.on_mouse_move)
        self.tile_size = 20


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

        self.inverse_fill()
        #self.line_fill()  # line fill is much faster but has bugs in it


    def inverse_fill(self):
        # cairo has finished drawing and now we will run through the image
        # and fill the whole thing.
        image = self.window.get_image(0, 0, self.width, self.height)

        points = {}

        colormap = image.get_colormap()
        color1 = colormap.alloc_color(255*260,255*240,255*240)

        colors = [color1.pixel, 9684419]
        i = 1
        prev_row_color = colors[0]

        # Trying to do checkers, going left-right, top-bottom
        for y in range(0, self.height - self.tile_size/2, self.tile_size):
            if y > 0: # first row. TODO - this looks lame
                prev_row_color = image.get_pixel(self.tile_size / 2, y - self.tile_size + self.tile_size / 2)
                if prev_row_color not in colors:
                    prev_row_color = image.get_pixel(self.tile_size + self.tile_size / 2, y - self.tile_size + self.tile_size / 2)
                    if prev_row_color not in colors:
                        prev_row_color = colors[0]
            else:
                prev_row_color = colors[0]

            prev_col_color = prev_row_color

            for x in range(0, self.width - self.tile_size / 2, self.tile_size):
                current_color = image.get_pixel(x + self.tile_size / 2, y + self.tile_size / 2)
                if current_color not in colors:
                    new_color = colors[1 - colors.index(prev_col_color)]


                    # grab the midpoint of the tile, as it is guaranteed to be
                    # without stripes
                    self.bucket_fill(image, x + self.tile_size / 2, y + self.tile_size / 2,
                                     image.get_pixel(x + self.tile_size / 2, y + self.tile_size / 2), new_color)


                    prev_col_color = new_color
                else:
                    prev_col_color = current_color


        self.window.draw_image(self.get_style().black_gc, image, 0, 0, 0, 0, -1, -1)


    def line_fill(self):
        """at the end i realized that we care only about lines"""
        image = self.window.get_image(0, 0, self.width, self.height)
        x, xd = 0, 1
        y = 0

        colormap = image.get_colormap()
        color1 = colormap.alloc_color(255*260,255*240,255*240)
        background = image.get_pixel(self.tile_size / 2, self.tile_size / 2)

        colors = [color1.pixel, 9684419, background]
        i = 0
        paint_color = colors[0]
        prev_match = -1


        while y < self.height:
            current_color = image.get_pixel(x, y)

            current_match = -1
            if current_color in colors:
                current_match = colors.index(current_color)

                if current_color == colors[2]:
                    image.put_pixel(x, y, paint_color)
            else:
                if prev_match > -1:
                    paint_color = colors[1 - colors.index(paint_color)] #variate between back and front

            x += xd
            if x >= self.width-1 or x < 0:
                x = min(max(x, 0), self.width) #limit to bounds and turn around
                xd = -xd
                y+=1
                if prev_match == -1:
                    paint_color = colors[1 - colors.index(paint_color)] #variate between back and front

            prev_match = current_match

        self.window.draw_image(self.get_style().black_gc, image, 0, 0, 0, 0, -1, -1)


    def bucket_fill(self, image, x, y, old_color, new_color):
        """whoa, a queue based 4-direction bucket fill
           linescan could improve things
        """
        queue = [(x,y)]

        operations = 0
        while queue:
            x, y = queue.pop(0)
            if image.get_pixel(x, y) == new_color:
                operations += 1

            current_color = image.get_pixel(x, y)
            if current_color!= new_color and abs(current_color - old_color) < 4000000:
                image.put_pixel(x, y, new_color)
                if x > 0 and image.get_pixel(x-1, y) != new_color: queue.append((x - 1, y))
                if x < self.width and image.get_pixel(x+1, y) != new_color: queue.append((x + 1, y))
                if y > 0 and image.get_pixel(x, y-1) != new_color: queue.append((x, y - 1))
                if y < self.height and image.get_pixel(x, y+1) != new_color: queue.append((x, y + 1))
        print operations, "operations on fill"


class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(200, 200)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        canvas = Canvas()

        box = gtk.VBox()
        box.pack_start(canvas)


        window.add(box)
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    gtk.main()
