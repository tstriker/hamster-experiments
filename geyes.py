#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""Guess what, haha. Oh and the math is way wrong here
   Morale of the story though is that the coordinates are given even when
   outside the window
"""


from gi.repository import Gtk as gtk
from lib import graphics
import math

class Eye(graphics.Sprite):
    def __init__(self, x, y, width, height):
        graphics.Sprite.__init__(self, x=x, y=y, interactive=True, draggable=True)
        self.angle = 0
        self.pupil_distance = 0
        self.width = width
        self.height = height
        self.connect("on-render", self.on_render)

    def update(self, mouse_x, mouse_y):
        distance_x, distance_y = (mouse_x - self.x), (mouse_y - self.y)
        self.pointer_distance = math.sqrt(distance_x**2 + distance_y**2)
        self.pupil_rotation = math.atan2(distance_x, distance_y)

    def on_render(self, sprite):
        width, height = self.width, self.height
        self.graphics.ellipse(-width / 2, -height / 2, width, height)
        self.graphics.fill("#fff")

        rotation = self.pupil_rotation

        pupil_radius = min(width / 4.0, height / 4.0)

        pupil_x = min((width / 2.0 - pupil_radius), self.pointer_distance) * math.sin(rotation)
        pupil_y = min((height / 2.0 - pupil_radius), self.pointer_distance) * math.cos(rotation)


        self.graphics.circle(pupil_x, pupil_y, pupil_radius)
        self.graphics.fill("#000")



class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self, framerate = 20)
        self.eyes = [Eye(50, 100, 70, 100),
                     Eye(150, 100, 70, 100)]
        self.add_child(*self.eyes)
        self.connect("on-enter-frame", self.on_enter_frame)

    def on_enter_frame(self, scene, context):
        for eye in self.eyes:
            eye.update(self.mouse_x, self.mouse_y)

        self.redraw()

class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_size_request(200, 200)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()

example = BasicWindow()
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
gtk.main()
