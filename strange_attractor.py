#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>
""" guilloches, following.  observe how detail grows and your cpu melts.
    move mouse horizontally and vertically to change parameters
    http://ministryoftype.co.uk/words/article/guilloches/
"""

import gtk
from lib import graphics
from lib.pytweener import Easing
import colorsys
import math
import cairo


class Canvas(graphics.Area):
    def __init__(self):
        graphics.Area.__init__(self)
        self.connect("mouse-move", self.on_mouse_move)

        self.a = 1.4191403
        self.b = -2.2841523
        self.c = 2.4275403
        self.d = -2.177196
        self.points = 2000
        self.zoom = 1

        self.x, self.y = 0,0

        self.image = None

    def on_mouse_move(self, area, coords, mouse_areas):
        self.points = int(coords[1] / float(self.height) * 30000) + 10000
        self.zoom = abs((coords[0] / float(self.width)) * 2 - 1)
        self.image = None
        self.x, self.y = 0,0
        self.redraw_canvas()

    def on_expose(self):
        if not self.image:
            self.image = self.window.get_image(0, 0, self.width, self.height)

        colormap = self.image.get_colormap()
        color1 = colormap.alloc_color(self.colors.gdk("#000000")).pixel

        for i in range(1000):
            self.x = math.sin(self.a * self.y) - math.cos(self.b * self.x)
            self.y = math.sin(self.c * self.x) - math.cos(self.d * self.y)

            self.image.put_pixel(int(self.x * self.width * self.zoom + self.width / 2),
                                 int(self.y * self.height * self.zoom + self.height / 2),
                                 color1)

        self.window.draw_image(self.get_style().black_gc, self.image, 0, 0, 0, 0, -1, -1)
        self.redraw_canvas()

class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(800, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        canvas = Canvas()

        box = gtk.VBox()
        box.pack_start(canvas)


        window.add(box)
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    gtk.main()
