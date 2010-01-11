#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

import colorsys

import gtk
from lib import graphics
from lib.pytweener import Easing
from random import randint


class EasingBox(object):
    def __init__(self, name, x, y, easing_method):
        self.name = name
        self.x = x
        self.y = y
        self.easing_method = easing_method

        self.left_side = True


class Canvas(graphics.Area):
    def __init__(self):
        graphics.Area.__init__(self)

        self.boxes = []

        def get_next_y():
            y = y + 30
            return y

        classes = Easing()
        for i, easing_class in enumerate(dir(Easing)):
            if easing_class.startswith("__") == False:
                the_class = classes.__getattribute__(easing_class)

                self.boxes.append(EasingBox(easing_class, 90, i * 49 + 30, the_class))


        self.connect("button-release", self.on_mouse_click)

    def draw_boxes(self):
        for i, box in enumerate(self.boxes):
            self.set_color("#333333")
            self.layout.set_text("%s out" % box.name)
            self.context.move_to(20, box.y + 10)
            self.context.show_layout(self.layout)

            self.draw_rect(box.x, box.y, 30, 30, 5)
            self.set_color("#aaaaaa")
            self.context.fill()

            self.set_color("#333333")
            self.layout.set_text("%s in" % box.name)
            self.context.move_to(350, box.y + 10)
            self.context.show_layout(self.layout)

            self.register_mouse_region(box.x, box.y, box.x + 30, box.y + 30, i)

    def on_mouse_click(self, area, regions):
        if not regions:
            return

        clicked = self.boxes[regions[0]]
        easing = clicked.easing_method()

        if clicked.left_side:
            self.animate(clicked, dict(x = 300), easing = easing.__getattribute__("easeOut"))
        else:
            self.animate(clicked, dict(x = 90), easing = easing.__getattribute__("easeIn"))

        clicked.left_side = not clicked.left_side

    def on_expose(self):
        self.draw_boxes()


class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(450, 630)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        canvas = Canvas()

        box = gtk.VBox()
        box.pack_start(canvas)


        window.add(box)
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    gtk.main()

