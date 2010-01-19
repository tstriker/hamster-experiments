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

import math


class Canvas(graphics.Area):
    def __init__(self):
        graphics.Area.__init__(self)

        self.connect("mouse-move", self.on_mouse_move)
        self.mouse_x, self.mouse_y = None, None
        self.max_width = 50



    def on_mouse_move(self, area, coords, mouse_areas):
        self.mouse_x, self.mouse_y = coords
        self.redraw_canvas()


    def on_expose(self):
        self.set_color("#444")
        self.context.set_line_width(0.6)

        exes = range(1, self.width, self.max_width)
        whys = range(250, 350, 10)

        for i,x in enumerate(exes):
            if self.mouse_x:
                distance = abs(x - self.mouse_x)
                rel_distance = 1 - distance / float(self.width)

                if rel_distance < 0:
                    print rel_distance
                rel_distance = rel_distance ** 2

                distance = rel_distance * self.max_width
                if x < self.mouse_x:
                    corrected_x = max(x + distance, i)
                else:
                    corrected_x = min(x - distance, self.width - len(exes) + i)

                width = max(abs(x - corrected_x), 10)

                self.draw_rect(x, 100, width, 50, 5)

                self.draw_rect(x, 150 + width * 2, 50, width * 2, 5)

        self.set_color("#444")
        self.context.fill_preserve()
        self.set_color("#fff")
        self.context.stroke()



class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(1000, 600)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        canvas = Canvas()

        box = gtk.VBox()
        box.pack_start(canvas)


        window.add(box)
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    gtk.main()
