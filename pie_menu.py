#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>
"""
    Bit of pie in progress.
"""

import gtk
from lib import graphics
from lib.pytweener import Easing
from lib.euclid import Vector2
import math

class Sector(graphics.Shape):
    def __init__(self, inner_radius, outer_radius, start_angle = 0, end_angle = 0, **kwargs):
        self.inner_radius = inner_radius
        self.outer_radius = outer_radius
        self.start_angle = start_angle
        self.end_angle = end_angle

        graphics.Shape.__init__(self, rotation = start_angle, **kwargs)

    def draw_shape(self):
        self.rotation = self.start_angle
        angle = self.start_angle - self.end_angle # we will transform matrix to do the drawing, so we are interested in delta

        self.graphics.arc(0, 0, self.inner_radius, angle, 0)
        if abs(angle) >= math.pi * 2:
            self.graphics.move_to(self.outer_radius, 0)
        else:
            self.graphics.line_to(self.outer_radius, 0)
        self.graphics.arc_negative(0, 0, self.outer_radius, 0, angle)
        self.graphics.close_path()

        self.graphics.move_to(150, -15)
        self.graphics.rectangle(150,-15,10,10)



class Menu(graphics.Sprite):
    def __init__(self, x, y):
        graphics.Sprite.__init__(self, x, y, draggable = True)

        self.graphics.arc(0, 0, 10, 0, math.pi * 2)
        self.graphics.fill("#aaa")
        #self.graphics.set_line_style(width=1)

        self.menu = []
        for i in range(20):
            self.add_item()

    def on_mouse_over(self, sprite):
        sprite.fill_color = "#ddd"

    def on_mouse_out(self, sprite):
        sprite.fill_color = ""

    def on_click(self, sprite, event):
        self.add_item()

    def add_item(self):
        item = Sector(25, 50, math.pi / 2, 0, interactive = True, stroke = "#aaa")
        item.connect("on-mouse-over", self.on_mouse_over)
        item.connect("on-mouse-out", self.on_mouse_out)
        item.connect("on-mouse-click", self.on_click)


        self.menu.append(item)
        self.add_child(item)


        current_angle = 0
        angle = math.pi * 2 / len(self.menu)

        for i, item in enumerate(self.menu):
            item.start_angle = current_angle
            item.end_angle = current_angle + angle
            item.inner_radius = 25 + len(self.menu) / 2.0
            item.outer_radius = 50 + len(self.menu) * 2

            current_angle += angle





class Canvas(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.max_width = 50
        self.menu = Menu(200, 200)
        self.add_child(self.menu)
        #self._debug_bounds = True

        # on all mouse actions we redraw canvas
        self.connect("on-mouse-over", lambda *args: self.redraw_canvas())
        self.connect("on-mouse-out", lambda *args: self.redraw_canvas())
        self.connect("on-click", lambda *args: self.redraw_canvas())

        # uncomment for continuous redraw
        self.connect("on-enter-frame", self.on_enter_frame)
        self.connect("on-finish-frame", self.on_finish_frame)
        #self.framerate = 30

    def on_enter_frame(self, scene, context):
        self.menu.rotation += 0.002

    def on_finish_frame(self, scene, context):
        self.redraw_canvas()


class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(400, 400)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        canvas = Canvas()

        box = gtk.VBox()
        box.pack_start(canvas)


        window.add(box)
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    gtk.main()
