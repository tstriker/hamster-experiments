#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>
""" guilloches, following.  observe how detail grows and your cpu melts.
    move mouse horizontally and vertically to change parameters
    http://ministryoftype.co.uk/words/article/guilloches/
"""

import gtk
from lib import graphics
import colorsys
import math
import cairo


class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        self.a = 1.4191403
        self.b = -2.2841523
        self.c = 2.4275403
        self.d = -2.177196
        self.points = 2000
        self.zoom = 1

        self.x, self.y = 0,0
        self.image = None

        self.connect("mouse-move", self.on_mouse_move)
        self.connect("on-enter-frame", self.on_enter_frame)

    def on_mouse_move(self, area, event):
        self.points = int(event.y / float(self.height) * 30000) + 10000
        self.zoom = abs((event.x / float(self.width)) * 2 - 1)
        self.image = None
        self.x, self.y = 0,0
        self.redraw_canvas()

    def on_enter_frame(self, scene, context):
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

        window.add(Scene())
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    gtk.main()
