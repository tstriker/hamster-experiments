#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>
""" guilloches, following.  observe how detail grows and your cpu melts.
    move mouse horizontally and vertically to change parameters
    http://ministryoftype.co.uk/words/article/guilloches/

    TODO - this is now brokeh, need to find how to get back canvas-like behavior
    which wouldn't repaint at each frame
"""

from gi.repository import Gtk as gtk
from lib import graphics
import colorsys
import math
import cairo


class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.set_double_buffered(False)

        self.a = 1.4191403
        self.b = -2.2841523
        self.c = 2.4275403
        self.d = -2.177196
        self.points = 2000

        self.x, self.y = 0,0
        self.image = None
        self.prev_width, self.prev_height = 0, 0

        self.connect("on-enter-frame", self.on_enter_frame)

    def on_enter_frame(self, scene, context):
        g = graphics.Graphics(context)

        if self.prev_width != self.width or self.prev_height != self.height:
            self.x, self.y = 0,0

        if self.x == 0 and self.y ==0:
            g.fill_area(0,0, self.width, self.height, "#fff")


        for i in range(1000):
            self.x = math.sin(self.a * self.y) - math.cos(self.b * self.x)
            self.y = math.sin(self.c * self.x) - math.cos(self.d * self.y)

            x = int(self.x * self.width * 0.2 + self.width / 2)
            y = int(self.y * self.height * 0.2  + self.height / 2)

            g.rectangle(x, y, 1, 1)

        g.fill("#000", 0.08)

        self.prev_width, self.prev_height = self.width, self.height
        self.redraw()

class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_default_size(800, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        window.add(Scene())
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
