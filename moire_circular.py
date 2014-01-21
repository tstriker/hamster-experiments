#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2014 Toms Bauģis <toms.baugis at gmail.com>

"""Circular moire, epilepse your heart out!
   Move mouse left and right to adjust the circle disposition
   and up and down to increase and decrease the number of circles and line
   thickness
"""
import math

from gi.repository import Gtk as gtk
from lib import graphics

class Circles(graphics.Sprite):
    def __init__(self, color, **kwargs):
        graphics.Sprite.__init__(self, **kwargs)
        self.color = color
        self.connect("on-render", self.on_render)
        self.cache_as_bitmap = True
        self.distance = 5

    def on_render(self, sprite):
        self.graphics.set_line_style(width=1)

        circles = 500 / self.distance
        line_width = max(self.distance / 2, 1)

        for i in range(circles):
            radius = i * self.distance + 1
            self.graphics.move_to(radius, 0)
            self.graphics.circle(0, 0, radius)
        self.graphics.set_line_style(width = line_width)
        self.graphics.stroke(self.color)


class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        self.base = Circles("#f00", x=400, y=300)
        self.sattelite = Circles("#00f", x=500, y=300)
        self.add_child(self.base, self.sattelite)

        self.distance = 20

        self.connect("on-enter-frame", self.on_enter_frame)
        self.connect("on-mouse-move", self.on_mouse_move)

    def on_mouse_move(self, sprite, event):
        middle = self.width / 2.0
        distance = (event.x - middle) * 1.0 / middle
        self.distance = int(distance * 250)

        middle = self.height / 2.0
        circle_distance = abs((event.y - middle) * 1.0 / middle)
        circle_distance = circle_distance * 20 + 5
        for circle in (self.base, self.sattelite):
            circle.distance = int(circle_distance)


        self.redraw()

    def on_enter_frame(self, scene, context):
        self.base.x, self.base.y = self.width / 2, self.height / 2

        distance = self.distance
        self.sattelite.x, self.sattelite.y = self.base.x + distance, self.base.y



class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_default_size(800, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()

if __name__ == '__main__':
    window = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
