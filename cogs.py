#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2014 You <your.email@someplace>

"""Base template"""

import math
from gi.repository import Gtk as gtk
from lib import graphics

class Cog(graphics.Sprite):
    def __init__(self, radius=None, teeth=None, axis_distance = None, tooth_height=None,
                 tooth_width=None, inset=None, fill=None, **kwargs):
        graphics.Sprite.__init__(self, **kwargs)
        self.connect("on-render", self.on_render)

        self.radius = radius

        self.teeth = teeth or int(radius / 5)

        self.fill = fill or "#999"

        self.tooth_width = tooth_width or int(radius / 8)
        self.tooth_height = tooth_height or self.tooth_width * 1.5

        self.axis_distance = axis_distance or 20
        self.inset = inset or False

        self.interactive = True

    def on_render(self, sprite):
        direction = -1 if self.inset else 1

        radius = self.radius - direction * self.tooth_height / 2


        self.graphics.move_to(100, 0)

        steps = int(self.teeth)
        degrees = 360 * 1.0 / self.teeth

        if self.inset:
            self.graphics.move_to(radius - direction * self.axis_distance, 0)
            self.graphics.circle(0, 0, radius - direction * self.axis_distance)
            self.graphics.fill_stroke("#fafafa", "#333")

        self.graphics.save_context()
        for i in range(steps):
            self.graphics.rotate(math.radians(degrees))


            if i == 0:
                self.graphics.move_to(-self.tooth_width/2, -radius)
            self.graphics.line_to(-self.tooth_width/2, -radius)

            self.graphics.line_to(-self.tooth_width/2 + self.tooth_width/3,
                                  -radius - direction * self.tooth_height)

            self.graphics.line_to(self.tooth_width/2 - self.tooth_width/3,
                                  -radius - direction * self.tooth_height)

            self.graphics.line_to(self.tooth_width/2, -radius)

        self.graphics.set_line_style(width=1)
        self.graphics.rotate(math.radians(degrees))
        self.graphics.line_to(-self.tooth_width/2, -radius)
        self.graphics.restore_context()
        self.graphics.fill_stroke(self.fill, "#666")

        if not self.inset:
            self.graphics.circle(0, 0, radius - direction * self.axis_distance)
            self.graphics.fill_stroke("#fafafa", "#333")




class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        self.container = graphics.Sprite(x=300, y=250)
        self.add_child(self.container)

        width, height = 10, 10

        self.inner = Cog(radius=40, teeth=20, rotation=-0.114,
                         fill="#D5C439",
                         tooth_width=width, tooth_height=height)
        self.outer = Cog(radius=200, teeth=100,
                         fill="#CEE2A6",
                         inset=True, tooth_height=height, tooth_width=width, axis_distance=10)

        radius, teeth = 75, 37


        self.middles = []
        distance, angle = -120, 0
        for i in range(3):
            angle += 120
            x, y = (math.sin(math.radians(angle)) * distance,
                    math.cos(math.radians(angle)) * distance)
            middle = Cog(x=x, y=y, rotation=-0.114,
                         radius=75, teeth=37,
                         fill="#3D699B",
                         tooth_width=width, tooth_height=height,
                         axis_distance=50)
            self.middles.append(middle)


        self.container.add_child(self.outer, self.inner)
        self.container.add_child(*self.middles)

        self.reference_point = None
        self.connect("on-click", self.on_click)

        self.connect("on-enter-frame", self.on_enter_frame)

    def on_click(self, scene, event, sprite):
        self.reference_point = sprite

    def on_enter_frame(self, scene, context):
        speed = 0.005

        self.inner.rotation += speed * 5
        self.outer.rotation -= speed

        for middle in self.middles:
            middle.rotation -= speed * 2.7

        if self.reference_point:
            self.container.rotation = -self.reference_point.rotation
        else:
            self.container.rotation = 0

        self.redraw()



class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_default_size(600, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()

if __name__ == '__main__':
    window = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
