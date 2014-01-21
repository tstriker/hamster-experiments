#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>
""" guilloches, following.  observe how detail grows and your cpu melts.
    move mouse horizontally and vertically to change parameters
    http://ministryoftype.co.uk/words/article/guilloches/
"""

from gi.repository import Gtk as gtk
from lib import graphics

import math


class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        self.theta_step = 0.01
        self.R = 60 # big steps
        self.r = 0.08 # little steps
        self.p = 35 # size of the ring
        self.connect("on-mouse-move", self.on_mouse_move)
        self.connect("on-enter-frame", self.on_enter_frame)

    def on_mouse_move(self, area, event):
        self.R = event.x / float(self.width) * 50
        self.r = event.y / float(self.height) * 0.08


    def on_enter_frame(self, scene, context):
        R, r, p = self.R, self.r, self.p

        theta = 0

        context.set_source_rgb(0, 0, 0)
        context.set_line_width(0.2)

        first = True
        while theta < 2 * math.pi:
            theta += self.theta_step
            x = (R + r) * math.cos(theta) + (r + p) * math.cos((R+r)/r * theta)
            y = (R + r) * math.sin(theta) + (r + p) * math.sin((R+r)/r * theta)

            x = x * 4 + self.width / 2
            y = y * 4 + self.height / 2
            if first:
                context.move_to(x, y)
                first = False

            context.line_to(x, y)

        context.stroke()

        self.theta_step = self.theta_step - 0.0000002
        self.redraw()



class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_size_request(600, 600)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        window.add(Scene())
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
