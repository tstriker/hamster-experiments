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

from gi.repository import Gtk as gtk
from lib import graphics
import math
import random
import datetime as dt
import cairo
import struct

class Canvas(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.tile_size = 30

        self.connect("on-enter-frame", self.on_enter_frame)


    def on_enter_frame(self, scene, context):
        g = graphics.Graphics(context)

        self.two_tile_random(context)

        g.move_to(0,0)
        g.show_label("Hello", size=48, color="#33a")

        # creating a in-memory image of current context
        image_surface = cairo.ImageSurface(cairo.FORMAT_RGB24, self.width, self.height)
        image_context = cairo.Context(image_surface)

        # copying
        image_context.set_source_surface(context.get_target())
        image_context.paint()

        # buffer allows us to manipulate the pixels directly
        buffer = image_surface.get_data()

        # blur
        self.blur(buffer)

        # and paint it back
        context.set_source_surface(image_surface)
        context.paint()


        self.redraw()



    def blur(self, buffer):
        t = dt.datetime.now()

        def get_pixel(x, y):
            pos = (x * self.height + y) * 4
            (b, g, r, a) = struct.unpack('BBBB', buffer[pos:pos+4])
            return (r, g, b, a)

        v = 1.0 / 9.0
        kernel = ((v, v, v),
                  (v, v, v),
                  (v, v, v))

        kernel_range = range(-1, 2) # surrounding the pixel



        height, width = self.height, self.width


        # we will need all the pixel colors anyway, so let's grab them once
        pixel_colors = struct.unpack_from('BBBB' * width * height, buffer)

        new_pixels = [0] * width * height * 4 # target matrix

        for x in range(1, width - 1):
            for y in range(1, height - 1):
                r,g,b = 0,0,0
                pos = (x * height + y) * 4

                for ky in kernel_range:
                    for kx in kernel_range:
                        k = kernel[kx][ky]
                        k_pos = pos + kx * height * 4 + ky * 4

                        pixel_r,pixel_g,pixel_b = pixel_colors[k_pos:k_pos + 3]

                        r += k * pixel_r
                        g += k * pixel_g
                        b += k * pixel_b

                new_pixels[pos:pos+3] = (r,g,b)

        struct.pack_into('BBBB' * self.width * self.height, buffer, 0, *new_pixels)
        print "%d x %d," %(self.width, self.height), dt.datetime.now() - t



    def two_tile_random(self, context):
        """stroke area with non-filed truchet (since non filed, all match and
           there are just two types"""
        context.set_source_rgb(0,0,0)
        context.set_line_width(1)

        for y in range(0, self.height, self.tile_size):
            for x in range(0, self.width, self.tile_size):
                self.stroke_tile(context, x, y, self.tile_size, random.choice([1, 2]))
        context.stroke()


    def stroke_tile(self, context, x, y, size, orient):
        # draws a tile, there are just two orientations
        arc_radius = size / 2
        x2, y2 = x + size, y + size

        # i got lost here with all the Pi's
        if orient == 1:
            context.move_to(x + arc_radius, y)
            context.arc(x, y, arc_radius, 0, math.pi / 2);

            context.move_to(x2 - arc_radius, y2)
            context.arc(x2, y2, arc_radius, math.pi, math.pi + math.pi / 2);
        elif orient == 2:
            context.move_to(x2, y + arc_radius)
            context.arc(x2, y, arc_radius, math.pi - math.pi / 2, math.pi);

            context.move_to(x, y2 - arc_radius)
            context.arc(x, y2, arc_radius, math.pi + math.pi / 2, 0);


class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_size_request(200, 200)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Canvas())
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
