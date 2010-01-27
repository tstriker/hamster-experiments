#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>
"""
 Blur from processing, only 4 times slower or something in the lines.

 * Blur.
 *
 * Bluring half of an image by processing it through a
 * low-pass filter.

 Ported from processing (http://processing.org)
"""

import gtk
from lib import graphics
import math
import random
import datetime as dt


class Canvas(graphics.Area):
    def __init__(self):
        graphics.Area.__init__(self)
        self.tile_size = 30
        self.image = None


    def on_expose(self):
        """here happens all the drawing"""
        if not self.height: return

        if not self.image:
            self.two_tile_random()

            self.image = self.window.get_image(0, 0, self.width, self.height)
        else:
            self.window.draw_image(self.get_style().black_gc, self.image, 0, 0, 0, 0, -1, -1)

        self.image = self.window.get_image(0, 0, self.width, self.height)

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




    @staticmethod
    def paint_check(color1, color2):
        return color1 != color2 and abs(color1 - color2) < 3000000




    def blur(self):
        image = self.image

        blur_image = gtk.gdk.Image(gtk.gdk.IMAGE_FASTEST, self.get_visual(), self.width, self.height)
        blur_colormap = gtk.gdk.Colormap(self.get_visual(), True)
        blur_image.set_colormap(blur_colormap)

        v = 1.0 / 9.0
        kernel = ((v, v, v),
                  (v, v, v),
                  (v, v, v))



        colormap = self.image.get_colormap()
        #color1 = colormap.alloc_color(self.colors.gdk("#ff0000"))
        kernel_range = range(-1, 2)

        pixel_colors = []
        for i in range(self.width * self.height):
            pixel_colors.append(0)


        t = dt.datetime.now()
        height = self.height
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                kernel_sum = 0

                for ky in kernel_range:
                    for kx in kernel_range:
                        color = pixel_colors[(x + kx) * height + y + ky]
                        if not color:
                            color = colormap.query_color(image.get_pixel(x + kx, y + ky)).red_float
                            pixel_colors[(x + kx) * height + y + ky] = color

                        kernel_sum += kernel[ky + 1][kx + 1] * color

                new_color = blur_colormap.alloc_color(int(kernel_sum * 65535),
                                                 int(kernel_sum * 65535),
                                                 int(kernel_sum * 65535))
                blur_image.put_pixel(x, y, new_color.pixel)

        self.image = blur_image


        print dt.datetime.now() - t

        self.redraw_canvas()

class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(300, 300)
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
