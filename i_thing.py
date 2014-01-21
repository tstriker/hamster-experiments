#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""Emulating the wheel from apple products"""


from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from lib import graphics
from contrib import euclid

import cairo
import math

class Scene(graphics.Scene):
    def __init__(self, progress):
        graphics.Scene.__init__(self, scale=True, keep_aspect=True)
        self.progress = progress


        self.wheel = graphics.Circle(200, 200, "#aaa", x = 20, y=20, interactive=True, pivot_x=100, pivot_y=100)
        self.add_child(self.wheel)
        self.add_child(graphics.Circle(50, 50, "#fafafa", x=95, y=95, interactive=True))

        self.ticker = graphics.Label("*tick*", size=24, color="#000", x=5, y=220, opacity=0)
        self.ticker.last_degrees = 0
        self.add_child(self.ticker)

        self.connect("on-mouse-move", self.on_mouse_move)
        self.connect("on-mouse-down", self.on_mouse_down)
        self.connect("on-mouse-up", self.on_mouse_up)

        self.drag_point = None
        self.start_rotation = None

    def on_mouse_down(self, scene, event):
        sprite = self.get_sprite_at_position(event.x, event.y)
        if sprite == self.wheel:
            self.drag_point = euclid.Point2(event.x, event.y)
            self.start_rotation = self.wheel.rotation

    def on_mouse_up(self, scene, event):
        self.drag_point = None
        self.start_rotation = None


    def flash_tick(self):
        if self.ticker.opacity < 0.5:
            self.ticker.opacity = 1
            self.ticker.animate(opacity=0, duration=0.2)

    def on_mouse_move(self, scene, event):
        mouse_down = gdk.ModifierType.BUTTON1_MASK & event.state
        if not mouse_down:
            return
        sprite = self.get_sprite_at_position(event.x, event.y)

        if sprite == self.wheel:
            if not self.drag_point:
                self.on_mouse_down(scene, event)

            pivot_x, pivot_y = self.wheel.get_matrix().transform_point(self.wheel.pivot_x, self.wheel.pivot_y)

            pivot_point = euclid.Point2(pivot_x, pivot_y)
            drag_vector = euclid.Point2(event.x, event.y) - pivot_point

            start_vector = self.drag_point - pivot_point

            angle = math.atan2(start_vector.y, start_vector.x) - math.atan2(drag_vector.y, drag_vector.x)


            delta = (self.start_rotation - angle) - self.wheel.rotation

            # full revolution jumps from -180 to 180 degrees
            if abs(delta) >= math.pi:
                delta = 0
            else:
                degrees = int(math.degrees(self.wheel.rotation))
                self.ticker.last_degrees = self.ticker.last_degrees or degrees
                if abs(self.ticker.last_degrees - degrees) >= 30:
                    self.ticker.last_degrees = degrees
                    self.flash_tick()


            progress = min(1, max(0, self.progress.get_fraction() + delta / (math.pi * 2 * 10)))
            self.progress.set_fraction(progress)

            self.wheel.rotation = self.start_rotation - angle

        else:
            self.drag_point = None




class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_default_size(240, 280)
        window.set_title("iThing")
        window.connect("delete_event", lambda *args: gtk.main_quit())
        vbox = gtk.VBox()

        progress_bar = gtk.ProgressBar()
        vbox.pack_start(Scene(progress_bar), True, True, 0)
        vbox.pack_start(progress_bar, False, False, 0)
        window.add(vbox)
        window.show_all()

if __name__ == '__main__':
    window = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
