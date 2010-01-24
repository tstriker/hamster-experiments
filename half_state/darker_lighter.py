#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
 * Reach 2.
 * Based on code from Keith Peters (www.bit-101.com).
 *
 * The arm follows the position of the mouse by
 * calculating the angles with atan2().
 *
 Ported from processing (http://processing.org/) examples.
"""

import gtk
from lib import graphics



class Canvas(graphics.Area):
    def __init__(self):
        graphics.Area.__init__(self)
        self.segments = []

    def on_expose(self):
        steps = 20
        for i in range(steps):
            color = self.colors.darker("#000", -i * 255 / (steps - 1))
            
            self.context.rectangle(i * 30 + 30, 100, 30, 30)
            self.set_color(color)
            self.context.fill_preserve()
            
            if self.colors.is_light(color):
                self.set_color("#000")
            else:
                self.set_color("#fff")

            self.context.stroke()


class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(700, 200)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        canvas = Canvas()

        box = gtk.VBox()
        box.pack_start(canvas)


        window.add(box)
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    gtk.main()

