#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2014 Toms Baugis <toms.baugis@gmail.com>

"""Base template"""
import math
import random

from gi.repository import Gtk as gtk
from lib import graphics
from lib import layout
from lib.pytweener import Easing

class Rattle(graphics.Sprite):
    def __init__(self, **kwargs):
        graphics.Sprite.__init__(self, **kwargs)
        self.connect("on-render", self.on_render)
        self.snap_to_pixel = False

        self._intensity = 0

        self.shake_range = 10
        self.easing = Easing.Sine
        self.duration = 1.3
        self.fill = "#ddd"


    def buzz(self, sprite=None):
        graphics.chain([
            [self, {"_intensity": self.shake_range,
                    "duration": self.duration,
                    "easing": self.easing.ease_in,
                    "on_update": self._update_buzz}],
            [self, {"_intensity": 0,
                    "duration": self.duration,
                    "easing": self.easing.ease_out,
                    "on_update": self._update_buzz,
                    "on_complete": self.buzz}]
        ])


    def _update_buzz(self, sprite):
        self.update_buzz()

    def rattle(self):
        pass

    def on_render(self, sprite):
        self.graphics.rectangle(-25, -25, 50, 50)
        self.graphics.fill(self.fill)

class RattleRandomXY(Rattle):
    def update_buzz(self):
        shake_range = self._intensity
        self.x = (1 - 2 * random.random()) * shake_range
        self.y = (1 - 2 * random.random()) * shake_range


class RattleRandomAngle(Rattle):
    def update_buzz(self):
        shake_range = self._intensity
        angle = random.randint(0, 360)
        self.x = math.cos(math.radians(angle)) * shake_range
        self.y = math.sin(math.radians(angle)) * shake_range


class RattleRandomAngleShadow(RattleRandomAngle):
    def __init__(self, **kwargs):
        RattleRandomAngle.__init__(self, **kwargs)
        self.prev_x, self.prev_y = 0, 0

    def update_buzz(self):
        self.prev_x, self.prev_y = self.x, self.y
        RattleRandomAngle.update_buzz(self)

    def on_render(self, sprite):
        self.graphics.rectangle(-25 - self.prev_x + self.x, -25 - self.prev_y + self.y, 50, 50)
        self.graphics.fill(self.fill, 0.3)

        self.graphics.rectangle(-25, -25, 50, 50)
        self.graphics.fill(self.fill)

class RattleRandomAngle2Shadow(RattleRandomAngleShadow):
    def on_render(self, sprite):
        self.graphics.rectangle(-25 + self.prev_x - self.x, -25 + self.prev_y - self.y, 50, 50)
        self.graphics.fill(self.fill, 0.3)

        self.graphics.rectangle(-25 - self.prev_x + self.x, -25 - self.prev_y + self.y, 50, 50)
        self.graphics.fill(self.fill, 0.3)

        self.graphics.rectangle(-25, -25, 50, 50)
        self.graphics.fill(self.fill)


class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self, background_color="#333")


        self.rattles = [
            RattleRandomXY(),
            RattleRandomAngle(),
            RattleRandomAngleShadow(),
            RattleRandomAngle2Shadow(),
        ]

        box = layout.HBox()
        self.add_child(box)

        for rattle in self.rattles:
            container = layout.VBox(
                rattle,
                fill=False
            )
            box.add_child(container)

        self.rattling = False
        self.connect("on-first-frame", self.on_first_frame)

    def on_first_frame(self, scene, context):
        for rattle in self.rattles:
            rattle.buzz()



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
