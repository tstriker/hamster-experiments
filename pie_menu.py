#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>
""" guilloches, following.  observe how detail grows and your cpu melts.
    move mouse horizontally and vertically to change parameters
    http://ministryoftype.co.uk/words/article/guilloches/
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



class Menu(graphics.Sprite):
    def __init__(self):
        graphics.Sprite.__init__(self, 300, 300, draggable = True)

        self.pivot_x = 10
        self.pivot_y = 10
        self.graphics.arc(0, 0, 10, 0, math.pi * 2)
        self.graphics.fill("#aaa")


        self.menu = []
        self.add_item()

    def on_mouse_over(self, sprite):
        sprite.fill_color = "#ddd"

    def on_mouse_out(self, sprite):
        sprite.fill_color = ""

    def on_click(self, sprite, event):
        self.add_item()

    def add_item(self):
        item = Sector(25, 50, math.pi / 2, 0, stroke = "#aaa", interactive = True)
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

        self.mouse_x, self.mouse_y = None, None
        self.max_width = 50

        self.add_child(Menu())

        self.connect("on-enter-frame", lambda *args: self.redraw_canvas())




class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(1000, 600)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        canvas = Canvas()

        box = gtk.VBox()
        box.pack_start(canvas)


        window.add(box)
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    gtk.main()
