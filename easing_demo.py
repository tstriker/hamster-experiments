#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

import colorsys

import gtk
from lib import graphics
from lib.pytweener import Easing
from random import randint


class EasingBox(graphics.Rectangle):
    def __init__(self, name, x, y, easing_method):
        graphics.Rectangle.__init__(self, 40, 40, 3, fill = "#aaa")
        self.name = name
        self.x = x
        self.y = y
        self.easing_method = easing_method
        self.left_side = True
        self.interactive = True


class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        self.boxes = []

        classes = Easing()
        for i, easing_class in enumerate(dir(Easing)):
            if easing_class.startswith("__") == False:
                the_class = classes.__getattribute__(easing_class)

                label = graphics.Label(easing_class, color = "#333")
                label.x, label.y = 10, i * 49 + 40
                self.add_child(label)

                box = EasingBox(easing_class, 90, i * 49 + 30, the_class)
                self.add_child(box)
                self.boxes.append(box)

                label = graphics.Label(easing_class, color = "#333")
                label.x, label.y = 350, i * 49 + 40
                self.add_child(label)


        self.connect("on-click", self.on_click)


    def on_click(self, area, event, targets):
        if not targets:
            return

        clicked = targets[0]
        easing = clicked.easing_method()

        if clicked.left_side:
            self.animate(clicked, dict(x = 300), easing = easing.__getattribute__("easeOut"))
        else:
            self.animate(clicked, dict(x = 90), easing = easing.__getattribute__("easeIn"))

        clicked.left_side = not clicked.left_side



class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(450, 630)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    gtk.main()
