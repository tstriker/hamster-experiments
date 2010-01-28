#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>
"""
 * Blur.
 *
 * Bluring half of an image by processing it through a
 * low-pass filter.

 Ported from processing (http://processing.org)
 --
 Blur from processing, only million times slower or something in the lines.
 Right now slowness primarily is in getting pixel and determining it's color.
 The get_pixels_array of gtk.Pixbuf does not make things faster either as
 one has to unpack structures, which again is tad expensive.
"""

import gtk
from lib import graphics
import math
import random
import datetime as dt
import collections


class Canvas(graphics.Area):
    def __init__(self):
        graphics.Area.__init__(self)
        self.tile_size = 30
        self.image = None

        self.colormap = {}


    def on_expose(self):
        """here happens all the drawing"""
        if not self.height: return

        self.two_tile_random()
        self.image = self.window.get_image(0, 0, self.width, self.height)
        self.blur()

        self.redraw_canvas()


    def stroke_tile(self, x, y, size, orient):
        # draws a tile, there are just two orientations
        arc_radius = size / 2
        x2, y2 = x + size, y + size

        # i got lost here with all the Pi's
        if orient == 1:
            self.context.move_to(x + arc_radius, y)
            self.context.arc(x, y, arc_radius, 0, math.pi / 2);

            self.context.move_to(x2 - arc_radius, y2)
            self.context.arc(x2, y2, arc_radius, math.pi, math.pi + math.pi / 2);
        elif orient == 2:
            self.context.move_to(x2, y + arc_radius)
            self.context.arc(x2, y, arc_radius, math.pi - math.pi / 2, math.pi);

            self.context.move_to(x, y2 - arc_radius)
            self.context.arc(x, y2, arc_radius, math.pi + math.pi / 2, 0);

    def two_tile_random(self):
        """stroke area with non-filed truchet (since non filed, all match and
           there are just two types"""
        self.set_color("#000")
        self.context.set_line_width(1)

        for y in range(0, self.height, self.tile_size):
            for x in range(0, self.width, self.tile_size):
                self.stroke_tile(x, y, self.tile_size, random.choice([1, 2]))
        self.context.stroke()




    def blur(self):
        t = dt.datetime.now()

        image = self.image
        colormap = self.image.get_colormap()

        blur_pixmap = gtk.gdk.Pixmap(self.window, self.width, self.height)
        blur_pixmap.draw_image(self.get_style().black_gc, image, 0, 0, 0, 0, self.width, self.height)


        v = 1.0 / 9.0
        kernel = ((v, v, v),
                  (v, v, v),
                  (v, v, v))

        kernel_range = range(-1, 2)



        height = self.height


        # we will need all the colors anyway, so let's grab them once
        pixels = (image.get_pixel(x, y) for x in range(0, self.width) for y in range (0, self.height))

        pixel_colors, known_colors = {}, {}
        for i, pixel in enumerate(pixels):
            try:
                pixel_colors[i / height, i % height] = known_colors[pixel]
            except:
                known_colors[pixel] = colormap.query_color(pixel)
                pixel_colors[i / height, i % height] = known_colors[pixel]

        by_color = collections.defaultdict(collections.deque)
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                kernel_sum = 0

                for ky in kernel_range:
                    for kx in kernel_range:
                        kernel_sum += kernel[ky + 1][kx + 1] * pixel_colors[(x + kx), y + ky].red_float

                kernel_sum = int(kernel_sum * 65535) + 1
                if kernel_sum != int(pixel_colors[x, y].red_float * 65535):
                    by_color[kernel_sum].append(x * height + y)


        gc = blur_pixmap.new_gc()
        for color in by_color:
            #print color
            gc.set_foreground(colormap.alloc_color(color, color, color))
            blur_pixmap.draw_points(gc, [(i / height, i % height) for i in by_color[color]])


        self.window.draw_drawable(self.get_style().black_gc, blur_pixmap, 0, 0, 0, 0, -1, -1)

        print "%d x %d," %(self.width, self.height), dt.datetime.now() - t


class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(200, 200)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        canvas = Canvas()

        box = gtk.VBox()
        box.pack_start(canvas)

        button = gtk.Button("Blur")

        def on_blur_clicked(*args):
            canvas.blur()

        button.connect("clicked", on_blur_clicked)
        box.pack_start(button, False)



        window.add(box)
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    gtk.main()
