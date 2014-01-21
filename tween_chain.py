#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

# This is intentionally slow to test how well the lib behaves on many sprites
# moving.
# It could be easily (and totally appropriately) improved by doing all the
# drawing in on_enter_frame and forgetting about sprites.

import colorsys

from gi.repository import Gtk as gtk
from lib import graphics
from lib.pytweener import Easing
from math import floor


class TailParticle(graphics.Sprite):
    def __init__(self, x, y, color, follow = None):
        graphics.Sprite.__init__(self, x = x, y = y)
        self.follow = follow
        self.color = color
        self.add_child(graphics.Rectangle(20, 20, 3, color, x=-10, y=-10))
        self.graphics.fill(color)


class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        self.tail = []
        parts = 30
        for i in range(parts):
            previous = self.tail[-1] if self.tail else None
            color = colorsys.hls_to_rgb(0.6, i / float(parts), 1)

            self.tail.append(TailParticle(10, 10, color, previous))

        for tail in reversed(self.tail):
            self.add_child(tail) # add them to scene other way round


        self.mouse_moving = False

        self.connect("on-mouse-move", self.on_mouse_move)
        self.connect("on-enter-frame", self.on_enter_frame)


    def on_mouse_move(self, area, event):
        self.redraw()


    def on_enter_frame(self, scene, context):
        g = graphics.Graphics(context)
        for particle in reversed(self.tail):
            if particle.follow:
                new_x, new_y = particle.follow.x, particle.follow.y
                g.move_to(particle.x, particle.y)
                g.line_to(particle.follow.x, particle.follow.y)
                g.stroke(particle.color)
            else:
                new_x, new_y = self.mouse_x, self.mouse_y


            if abs(particle.x - new_x) + abs(particle.y - new_y) > 0.01:
                self.animate(particle, x = new_x, y = new_y, duration = 0.3, easing = Easing.Cubic.ease_out)


        if abs(self.tail[0].x - self.tail[-1].x) + abs(self.tail[0].y - self.tail[-1].y) > 1:
            self.redraw() # redraw if the tail is not on the head


class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_default_size(500, 300)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        scene = Scene()
        window.add(scene)
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
