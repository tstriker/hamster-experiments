#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""Demonstrating pivot_x and pivot_y"""


from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from lib import graphics
from contrib import euclid

import cairo
import math

class Rotator(graphics.Sprite):
    def __init__(self, x=100, y=100, radius=10):
        graphics.Sprite.__init__(self, x, y, interactive=True, draggable=True)
        self.radius = radius

        self.graphics.circle(0, 0, radius)
        self.graphics.fill("#aaa")

        def sector():
            self.graphics.move_to(radius, 0)
            self.graphics.line_to(0, 0)
            self.graphics.line_to(0, -radius)
            self.graphics.arc(0, 0, radius, -math.pi / 2, 0)

        self.graphics.save_context()
        sector()
        self.graphics.rotate(math.pi)
        sector()
        self.graphics.fill("#f6f6f6")
        self.graphics.restore_context()

        self.graphics.circle(0, 0, radius)
        self.graphics.move_to(-radius, 0.5)
        self.graphics.line_to(radius, 0.5)
        self.graphics.move_to(-0.5, -radius)
        self.graphics.line_to(-0.5, radius)

        self.graphics.set_line_style(width = 1)
        self.graphics.stroke("#333")

class Thing(graphics.Sprite):
    def __init__(self):
        graphics.Sprite.__init__(self, 200, 200, pivot_x=100, pivot_y=25, snap_to_pixel=False, interactive=True)

        # add some shapes
        self.graphics.rectangle(0.5, 0.5, 200, 50, 5)
        self.graphics.stroke("#000")

        self.rotator = Rotator(x=self.pivot_x, y=self.pivot_y)
        self.add_child(self.rotator)

        self.rotator.connect("on-drag", self.on_drag)

    def on_drag(self, sprite, event):
        matrix = cairo.Matrix()

        # the pivot point change causes the sprite to be at different location after
        # rotation so we are compensating that
        # this is bit lame as i could not figure out how to properly
        # transform the matrix so that it would give me back the new delta
        matrix.translate(self.x + self.rotator.x, self.y + self.rotator.y)
        matrix.rotate(self.rotation)
        matrix.translate(-self.rotator.x, -self.rotator.y)
        new_x, new_y =  matrix.transform_point(0,0)

        prev_x, prev_y = self.get_matrix().transform_point(0,0)

        self.x -= new_x - prev_x
        self.y -= new_y - prev_y

        # setting the pivot point
        self.pivot_x, self.pivot_y = self.rotator.x, self.rotator.y


class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        self.thing = Thing()
        self.rotator = Rotator(x=self.thing.pivot_x, y=self.thing.pivot_y)

        self.add_child(self.thing)

        self.add_child(graphics.Label("Drag to rotate", size=24, color="#999"))
        self.rotating = True

        self.connect("on-drag-start", self.on_drag_start)
        self.connect("on-drag-finish", self.on_drag_finish)

        self.connect("on-mouse-move", self.on_mouse_move)
        self.connect("on-mouse-down", self.on_mouse_down)
        self.connect("on-mouse-up", self.on_mouse_up)

        self.drag_point = None
        self.start_rotation = None

    def on_mouse_down(self, scene, event):
        sprite = self.get_sprite_at_position(event.x, event.y)
        if sprite == self.thing:
            self.drag_point = euclid.Point2(event.x, event.y)
            self.start_rotation = self.thing.rotation

    def on_mouse_up(self, scene, event):
        self.drag_point = None
        self.start_rotation = None

    def on_mouse_move(self, scene, event):
        mouse_down = gdk.ModifierType.BUTTON1_MASK & event.state
        if mouse_down and self.drag_point:
            pivot_x, pivot_y = self.thing.get_matrix().transform_point(self.thing.pivot_x, self.thing.pivot_y)

            pivot_point = euclid.Point2(pivot_x, pivot_y)
            drag_vector = euclid.Point2(event.x, event.y) - pivot_point

            start_vector = self.drag_point - pivot_point

            angle = math.atan2(start_vector.y, start_vector.x) - math.atan2(drag_vector.y, drag_vector.x)


            delta = (self.start_rotation - angle) - self.thing.rotation

            # full revolution jumps from -180 to 180 degrees
            if abs(delta) >= math.pi:
                delta = 0

            self.thing.rotation = self.start_rotation - angle


    def on_drag_start(self, scene, sprite, event):
        self.rotating = False

    def on_drag_finish(self, scene, sprite, event):
        self.rotating = True




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
