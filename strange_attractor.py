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

    def on_mouse_move(self, area, coords, mouse_areas):
        self.points = int(coords[1] / float(self.height) * 20000)
        self.zoom = abs((coords[0] / float(self.width)) * 2 - 1)
        self.redraw_canvas()



    def on_expose(self):

        #new_x = a0 + (a1 * x) + (a2 * x * x) + (a3 * x * y) + (a4 * y) + (a5 * y * y)
        #new_y = b0 + (b1 * x) + (b2 * x * x) + (b3 * x * y) + (b4 * y) + (b5 * y * y)

        x, y = 0,0
        self.set_color((0.5,0.5,0.5))
        self.context.set_antialias(cairo.ANTIALIAS_NONE)
        for i in range(self.points):
            x = math.sin(self.a * y) - math.cos(self.b * x)
            y = math.sin(self.c * x) - math.cos(self.d * y)


            self.draw_rect(int(x * self.width * self.zoom + self.width / 2),
                           int(y * self.height * self.zoom + self.height / 2),
                           1, 1)

        self.context.fill()

        #pixbuf = gtk.gdk.Pixbuf(gtk.gdk.colormap_get_system(), False, 8, self.width, self.height)
        #self.image = pixbuf.get_from_drawable(self)

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
