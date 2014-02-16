#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2014 Toms Baugis <toms.baugis@gmail.com>

"""Base template"""
import math

from gi.repository import Gtk as gtk
from lib import graphics


class Roller(graphics.Sprite):
    def __init__(self, **kwargs):
        graphics.Sprite.__init__(self, **kwargs)
        self.inner_radius = 60

        self.y = -self.inner_radius
        self.direction = 1

        self.vector = []

        self.connect("on-render", self.on_render)

    def on_render(self, sprite):
        # square has 4 sides, so our waves have to be shorter
        self.graphics.rectangle(-self.inner_radius, -self.inner_radius,
                                self.inner_radius * 2, self.inner_radius * 2)
        self.graphics.stroke("#eee")

        """
        # here's bit of behind the scenes - faking stuff like a boss
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
        # adjust the outer radius here
        self.outer_radius = math.sqrt(2 * ((self.inner_radius) ** 2))
        step = 3

        """
        # based on the phase we can also do a little extra pushing
        step_push = math.cos((self.rotation + math.radians(0)) * 4)
        step += step_push * 1.5
        """
        self.rotation += self.direction * math.radians(step)

        # y has to variate between inner and outer radius based on the phase
        diff = self.outer_radius - self.inner_radius
        self.y = -self.inner_radius - abs(diff * math.sin(self.rotation * 2))



class MovingRoller(Roller):
    def __init__(self, size=100, **kwargs):
        Roller.__init__(self, **kwargs)
        self.size = size
        self._prev_angle = 0

    def roll(self):
        Roller.roll(self)

        angle = math.degrees(self.rotation)
        step = abs(self._prev_angle - angle)
        self._prev_angle = angle

        self.x += self.direction * (math.pi * self.outer_radius) * step / 180.0
        if (self.x > self.size - self.outer_radius and self.direction > 0) or \
           (self.x < self.outer_radius and self.direction < 0):
            self.direction = -self.direction




class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.background_color = "#333"


        self.roller = Roller()
        self.roller_container = graphics.Sprite(y=200, x=300)
        self.roller_container.add_child(self.roller)

        self.roller2 = Roller()
        self.roller_container2 = graphics.Sprite(y=200, x=300, scale_y=-1)
        self.roller_container2.add_child(self.roller2)

        self.add_child(self.roller_container, self.roller_container2)

        self.connect("on-enter-frame", self.on_enter_frame)

    def on_enter_frame(self, scene, context):
        # you could do all your drawing here, or you could add some sprites
        g = graphics.Graphics(context)

        #g.move_to(10, 200)
        #g.line_to(self.width - 10, 200)
        #g.stroke("#eee")

        self.roller_container.rotation += 0.01
        self.roller_container2.rotation += 0.01

        self.roller_container.x = self.roller_container2.x = self.width / 2
        self.roller_container.y = self.roller_container2.y = self.height / 2

        self.roller.size = self.width
        self.roller.roll()

        self.roller2.size = self.width
        self.roller2.roll()

        self.redraw() # this is how to get a constant redraw loop (say, for animation)



class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_default_size(500, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()


if __name__ == '__main__':
    window = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
