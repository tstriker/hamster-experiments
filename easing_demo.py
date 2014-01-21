#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

import colorsys

from gi.repository import Gtk as gtk
from lib import graphics
from lib.pytweener import Easing
from random import randint
import datetime as dt


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

                label = graphics.Label(easing_class, color = "#333", x = 10, y = i * 49 + 40)
                self.add_child(label)

                box = EasingBox(easing_class, 90, i * 49 + 30, the_class)
                self.add_child(box)
                self.boxes.append(box)

                label = graphics.Label(easing_class, color = "#333", x = 350, y = i * 49 + 40)
                self.add_child(label)


        self.connect("on-click", self.on_click)


    def on_click(self, area, event, clicked):
        if not clicked:
            return

        easing = clicked.easing_method

        if clicked.left_side:
            self.animate(clicked, x = 300, easing = easing.__getattribute__("ease_out"), fill="#0f0")
        else:
            self.animate(clicked, x = 90, easing = easing.__getattribute__("ease_in"), fill="#aaa")

        clicked.left_side = not clicked.left_side



class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_size_request(450, 630)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
