#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>
""" guilloches, following.  observe how detail grows and your cpu melts.
    move mouse horizontally and vertically to change parameters
    http://ministryoftype.co.uk/words/article/guilloches/
"""

from gi.repository import Gtk as gtk
from lib import graphics
from contrib.euclid import Vector2

import math

class CenteredCircle(graphics.Sprite):
    """we don't have alignment yet and the pivot model is such that it does not
       alter anchor so the positioning would be predictable"""
    def __init__(self, x, y, radius):
        graphics.Sprite.__init__(self, x, y, interactive=True,draggable=True)
        self.radius = radius

        self.graphics.circle(0, 0, self.radius)
        self.graphics.fill_stroke("#ccc", "#999", 1)

class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        self.circle1 = CenteredCircle(100, 300, 90)
        self.circle2 = CenteredCircle(350, 300, 50)

        self.add_child(self.circle1)
        self.add_child(self.circle2)

        self.tangent = graphics.Sprite(interactive = False)
        self.add_child(self.tangent)

        self.draw_tangent()

        self.connect("on-drag", self.on_drag_circle)


    def on_drag_circle(self, scene, drag_sprite, event):
        self.draw_tangent()

    def draw_tangent(self):
        tangent = self.tangent
        tangent.graphics.clear()

        tangent.graphics.set_line_style(width = 0.5)

        band_radius = 30

        v1 = Vector2(self.circle1.x, self.circle1.y)
        v2 = Vector2(self.circle2.x, self.circle2.y)

        distance = abs(v1 - v2)



        tangent.graphics.set_color("#000")
        #tangent.graphics.move_to(v1.x, v1.y)
        #tangent.graphics.line_to(v2.x, v2.y)

        c = distance
        distance = 100

        a = distance + self.circle2.radius
        b = distance + self.circle1.radius


        orientation = (v2-v1).heading()

        # errrm, well, basically the one is in the other
        if (b**2 + c**2 - a**2) / (2.0 * b * c) >= 1:
            tangent.graphics.arc(v1.x, v1.y, max(self.circle1.radius, self.circle2.radius) + band_radius, 0, math.pi * 2)
            tangent.graphics.stroke()
            return


        # we have to figure out the angle for the vector that is pointing
        # towards the point C (which will help as to draw that tangent)
        left_angle = math.acos((b**2 + c**2 - a**2) / (2.0 * b * c))
        arc_angle = math.acos((a**2 + b**2 - c**2) / (2.0 * a * b))

        # arc on the one side
        a1 = left_angle + orientation
        x, y = math.cos(a1) * b, math.sin(a1) * b

        v3_1 = Vector2(v1.x+x, v1.y+y)
        tangent.graphics.arc(v3_1.x, v3_1.y, distance - band_radius, (v1 - v3_1).heading(), (v2 - v3_1).heading())
        tangent.graphics.stroke()



        # arc on the other side (could as well flip at the orientation axis, too dumb to do that though)
        a2 = -left_angle + orientation
        x, y = math.cos(a2) * b, math.sin(a2) * b
        v3_2 = Vector2(v1.x+x, v1.y+y)

        tangent.graphics.arc(v3_2.x, v3_2.y, distance - band_radius, (v2 - v3_2).heading(), (v1 - v3_2).heading())
        tangent.graphics.stroke()



        # the rest of the circle
        tangent.graphics.arc(v1.x, v1.y, self.circle1.radius + band_radius, (v3_1-v1).heading(), (v3_2-v1).heading())
        tangent.graphics.stroke()

        tangent.graphics.arc_negative(v2.x, v2.y, self.circle2.radius + band_radius, (v3_1-v2).heading(), (v3_2-v2).heading())
        tangent.graphics.stroke()


class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_size_request(800, 600)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
