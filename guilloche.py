#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

import gtk
from lib import graphics
from lib.pytweener import Easing

import math


class Canvas(graphics.Area):
    def __init__(self):
        graphics.Area.__init__(self)


    def on_expose(self):
        R = 50
        r = 0.08
        p = 55

        theta = 0

        self.set_color("#000")
        self.context.set_line_width(0.2)

        first = True
        while theta < 2 * math.pi:
            theta += 0.0001
            x = (R + r) * math.cos(theta) + (r + p) * math.cos((R+r)/r * theta)
            y = (R + r) * math.sin(theta) + (r + p) * math.sin((R+r)/r * theta)

            x = x * 4 + self.width / 2
            y = y * 4 + self.height / 2
            if first:
                self.context.move_to(x, y)
                first = False

            self.context.line_to(x, y)

        self.context.stroke()



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
