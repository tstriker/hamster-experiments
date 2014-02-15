#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2014 Toms Baugis <toms.baugis@gmail.com>

"""Base template"""
import math

from gi.repository import Gtk as gtk
from lib import graphics

class Roller(graphics.Sprite):
    def __init__(self, floor=0, **kwargs):
        graphics.Sprite.__init__(self, **kwargs)
        self.floor = floor

        self.inner_radius = 40

        self.y = self.floor - self.inner_radius
        self.direction = 1

        self.connect("on-render", self.on_render)

    def on_render(self, sprite):
        # square has 4 sides, so our waves have to be shorter
        self.graphics.rectangle(-self.inner_radius, -self.inner_radius,
                                self.inner_radius * 2, self.inner_radius * 2)
        self.graphics.fill_stroke("#888", "#eee")

        """
        self.graphics.move_to(self.inner_radius, 0)
        self.graphics.circle(0, 0, self.inner_radius)

        self.graphics.move_to(self.outer_radius, 0)
        self.graphics.circle(0, 0, self.outer_radius)

        self.graphics.move_to(0, 0)
        self.graphics.line_to(math.cos(self.rotation) * self.inner_radius,
                              math.sin(self.rotation) * self.inner_radius)

        self.graphics.stroke("#777")
        """



    def roll(self):
        self.inner_radius = 20 + self.rotation * 2


        self.outer_radius = math.sqrt(2 * ((self.inner_radius) ** 2))

        step = 4
        self.rotation += self.direction * math.radians(step)



        dist = self.inner_radius
        # y has to variate between inner and outer radius based on the phase
        diff = self.outer_radius - self.inner_radius

        rot = self.rotation * 2
        dist += abs(diff * math.sin(rot))

        self.y = self.floor - dist

        # circumference = pi * r
        #
        #* math.pi step  # have to find
        self.x += self.direction * (math.pi * dist) * step / 180.0


        if self.x > 600 - self.outer_radius or self.x < self.outer_radius:
            self.direction = -self.direction





class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.background_color = "#333"

        self.roller = Roller(x = 100, floor = 199)
        self.add_child(self.roller)

        self.connect("on-enter-frame", self.on_enter_frame)

    def on_enter_frame(self, scene, context):
        # you could do all your drawing here, or you could add some sprites
        g = graphics.Graphics(context)

        g.move_to(10, 200)
        g.line_to(self.width - 10, 200)
        g.stroke("#eee")

        self.roller.roll()

        self.redraw() # this is how to get a constant redraw loop (say, for animation)



class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_default_size(600, 250)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()


if __name__ == '__main__':
    window = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
