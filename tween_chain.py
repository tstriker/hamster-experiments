#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

# This is intentionally slow to test how well the lib behaves on many sprites
# moving.
# It could be easily (and totally appropriately) improved by doing all the
# drawing in on_enter_frame and forgetting about sprites.

import colorsys

import gtk
from lib import graphics
from lib.pytweener import Easing
from math import floor


class TailParticle(graphics.Sprite):
    def __init__(self, x, y, color, follow = None):
        graphics.Sprite.__init__(self, x = x, y = y)
        self.follow = follow
        self.graphics.rectangle(-5, -5, 10, 10, 3)
        self.graphics.fill(color)


class Canvas(graphics.Scene):
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
        for particle in reversed(self.tail):
            if particle.follow:
                new_x, new_y = particle.follow.x, particle.follow.y
            else:
                new_x, new_y = self.mouse_x, self.mouse_y

            if abs(particle.x - new_x) + abs(particle.y - new_y) > 0.01:
                self.animate(particle, x = new_x, y = new_y, duration = 0.3, easing = Easing.Expo.ease_out)


        if abs(self.tail[0].x - self.tail[-1].x) + abs(self.tail[0].y - self.tail[-1].y) > 1:
            self.redraw() # redraw if the tail is not on the head


class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(300, 300)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        canvas = Canvas()

        box = gtk.VBox()
        box.pack_start(canvas)


        window.add(box)
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    gtk.main()
