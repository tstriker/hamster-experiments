#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2014 Toms Baugis <toms.baugis@gmail.com>

"""Base template"""
import math

from gi.repository import Gtk as gtk
from lib import graphics


class Roller(graphics.Sprite):
    def __init__(self, poly=[], **kwargs):
        graphics.Sprite.__init__(self, **kwargs)

        # the inner radius of the square
        self.inner_radius = 20

        self.poly = poly or [(10, 250), (500, 150)]

        self.vector = self.poly[:2]

        self.snap_to_pixel = False


        # roll directoin - clockwise or counter-clockwise
        self.direction = 1
        self.outside = False # if outside is set to true, will flip to the other side of the vector

        self._abs_distance_to_b = 0

        self.roller = graphics.Sprite()
        self.add_child(self.roller)
        self.roller.connect("on-render", self.on_render_roller)

        self.connect("on-render", self.on_render)

    def on_render(self, sprite):
        if not self.debug:
            return

        self.graphics.move_to(0, 0)
        self.graphics.line_to(self.roller.x, self.roller.y)
        self.graphics.stroke("#eee")

        self.graphics.move_to(-self.outer_radius, 0)
        self.graphics.line_to(self.outer_radius, 0)
        self.graphics.stroke("#f00")

    def on_render_roller(self, roller):
        # square has 4 sides, so our waves have to be shorter
        roller.graphics.rectangle(-self.inner_radius, -self.inner_radius,
                                self.inner_radius * 2, self.inner_radius * 2)
        roller.graphics.stroke("#eee")


    def roll(self, base_angle=0):
        # adjust the outer radius here
        self.outer_radius = math.sqrt(2 * ((self.inner_radius) ** 2))
        step = 3


        rotation_step = self.direction * math.radians(step) * (-1 if self.outside else 1)

        # no point going over 360 degrees
        self.roller.rotation = (self.roller.rotation + rotation_step) % (math.pi * 2)

        # y has to variate between inner and outer radius based on the phase
        diff = self.outer_radius - self.inner_radius
        distance = self.inner_radius + abs(diff * math.sin((self.roller.rotation) * 2))
        self.roller.y = -distance * (-1 if self.outside else 1)


        # determine base tilt on the vector we are sitting
        a, b = self.vector
        dx, dy = b[0] - a[0], b[1] - a[1]
        base_tilt = math.atan2(dy, dx)
        self.rotation = base_tilt

        x_step = (math.pi * self.outer_radius) * step / 180.0
        self.x += self.direction * x_step * math.cos(base_tilt)

        # adjust our position
        y_step = (math.pi * self.outer_radius) * step / 180.0
        self.y += self.direction * y_step * math.sin(base_tilt)


        # are we there yet?
        remaining = abs(b[0] - self.x - abs(distance) * math.cos(base_tilt))
        remaining += abs(b[1] - self.y - abs(distance) * math.sin(base_tilt))
        if self._abs_distance_to_b and self._abs_distance_to_b < remaining:
            self._abs_distance_to_b = 0
            next_dot = self.poly.index(self.vector[1])

            self.vector = self.poly[next_dot:next_dot+2]

            # the whole approach has issues - it might be cheaper to actually
            # immitate physics than to do all these calcs. alas, not impossible

            # there are two cardinal - cases - whether we go inside of the next
            # turn or on the outside

            # if it is inside, we have to stop our traverse as soon as we are
            # crossing the next line

            # if it's outside, we do our animation till the very last point and
            # then we do a rather magical switch
            self.x, self.y = self.vector[0]
        else:
            self._abs_distance_to_b = remaining



class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.background_color = "#333"

        self.poly = [
            (100, 100), (250, 50), (500, 100), (500, 500), (100, 500), (100, 100)
        ]


        self.roller = Roller(self.poly)
        self.roller2 = Roller(list(reversed(self.poly)))
        #self.roller2.outside=True

        self.add_child(self.roller, self.roller2)

        # distance from the surface
        self.roller.x, self.roller.y = self.roller.vector[0]
        self.roller2.x, self.roller2.y = self.roller.vector[0]

        self.connect("on-enter-frame", self.on_enter_frame)

    def on_enter_frame(self, scene, context):
        self.roller.roll()
        self.roller2.roll()

        g = graphics.Graphics(context)
        g.move_to(*self.poly[0])

        for dot in self.poly[1:]:
            g.line_to(*dot)

        g.stroke("#f0f")

        self.redraw() # this is how to get a constant redraw loop (say, for animation)



class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_default_size(600, 600)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()


if __name__ == '__main__':
    window = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
