#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
    Inspired by Karl Lattimer's perfect ellipse (http://www.qdh.org.uk/wordpress/?p=286)
"""


from gi.repository import Gtk as gtk
from lib import graphics
import math

class Ellipse(graphics.Sprite):
    def __init__(self, x, y, width, height):
        graphics.Sprite.__init__(self, x = x, y = y, snap_to_pixel = False)
        self.width, self.height = width, height
        self.connect("on-render", self.on_render)

    def on_render(self, sprite):
        self.graphics.clear()
        """you can also use graphics.ellipse() here"""
        steps = max((32, self.width, self.height)) / 3

        angle = 0
        step = math.pi * 2 / steps
        points = []
        while angle < math.pi * 2:
            points.append((self.width / 2.0 * math.cos(angle),
                           self.height / 2.0 * math.sin(angle)))
            angle += step

        # move to the top-left corner
        min_x = min((point[0] for point in points))
        min_y = min((point[1] for point in points))

        self.graphics.move_to(points[0][0] - min_x, points[0][1] - min_y)
        for x, y in points:
            self.graphics.line_to(x - min_x, y - min_y)
        self.graphics.line_to(points[0][0] - min_x, points[0][1] - min_y)

        self.graphics.stroke("#666")


class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        self.add_child(graphics.Label("Move mouse to change the size of the ellipse",
                                      12, "#666", x = 5, y = 5))

        self.ellipse = Ellipse(50, 50, 100, 200)
        self.ellipse.pivot_x, self.ellipse.pivot_y = 50, 100 #center
        self.add_child(self.ellipse)


        self.connect("on-enter-frame", self.on_enter_frame)
        self.connect("on-mouse-move", self.on_mouse_move)

    def on_mouse_move(self, scene, event):
        """adjust ellipse dimensions on mouse move"""
        self.ellipse.width = event.x
        self.ellipse.height = event.y
        self.ellipse.pivot_x, self.ellipse.pivot_y = self.ellipse.width / 2, self.ellipse.height / 2


    def on_enter_frame(self, scene, context):
        """on redraw center and rotate"""
        self.ellipse.x, self.ellipse.y = self.width / 2 - self.ellipse.pivot_x, self.height / 2 - self.ellipse.pivot_y
        self.ellipse.rotation += 0.01

        self.redraw()

class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_size_request(600, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()

example = BasicWindow()
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
gtk.main()
