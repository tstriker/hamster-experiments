#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

from gi.repository import Gtk as gtk
from lib import graphics
import math

class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.connect("on-finish-frame", self.on_enter_frame)
        self.start_angle = 0
        self.framerate = 120

    def on_enter_frame(self, scene, context):
        self.start_angle += 0.01 * 60 / self.framerate # good way to keep the speed constant when overriding frame rate

        g = graphics.Graphics(context)

        g.fill_area(0, 0, self.width, self.height, "#f00")
        g.set_line_style(width = 0.5)
        g.set_color("#fff")

        x, y = self.width / 2, self.height / 2

        x = x + math.sin(self.start_angle * 0.3) * self.width / 4

        center_distance = math.cos(self.start_angle) * self.width / 8

        angle = self.start_angle
        step = math.pi * 2 / 64

        distance = max(self.width, self.height)

        while angle < self.start_angle + math.pi * 2:
            g.move_to(x + math.cos(angle) * center_distance, y + math.sin(angle) * center_distance)
            g.line_to(x + math.cos(angle) * distance, y + math.sin(angle) * distance)
            g.line_to(x + math.cos(angle+step) * distance, y + math.sin(angle+step) * distance)
            g.line_to(x + math.cos(angle) * center_distance,y + math.sin(angle) * center_distance)

            angle += step * 2

        g.fill()
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
