#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""Base template"""


import gtk
# adjust python path so we can use lib that is in sibling folder
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..')))

from lib import graphics
from lib.pytweener import Easing
from tests.old_pytweener import Easing as EasingOld

class OldTweenGraph(graphics.Sprite):
    def __init__(self, easing, **kwargs):
        graphics.Sprite.__init__(self, **kwargs)
        self.easing = easing

        self.graphics.set_line_style(width=1)

        start, end = 50, 0  #going upside down - from y=50 to y=0

        self.graphics.move_to(0, 50)
        for x in range(101):
            y = self.easing.ease_in(x, start, end - start, 100.0)
            self.graphics.line_to(x, y)

        self.graphics.move_to(110, 50)
        for x in range(101):
            y = self.easing.ease_out(x, start, end - start, 100.0)
            self.graphics.line_to(x + 110, y)

        self.graphics.move_to(220, 50)
        for x in range(101):
            y = self.easing.ease_in_out(x, start, end - start, 100.0)
            self.graphics.line_to(x + 220, y)

        self.graphics.stroke("#f00")

class TweenGraph(graphics.Sprite):
    def __init__(self, easing, **kwargs):
        graphics.Sprite.__init__(self, **kwargs)
        self.easing = easing

        self.graphics.set_line_style(width=1)

        start, end = 50, 0  #going upside down - from y=50 to y=0

        self.graphics.move_to(0, 50)
        for x in range(101):
            y = start + (end - start) * self.easing.ease_in(x / 100.0)
            self.graphics.line_to(x, y)

        self.graphics.move_to(110, 50)
        for x in range(101):
            y = start + (end - start) * self.easing.ease_out(x / 100.0)
            self.graphics.line_to(x + 110, y)

        self.graphics.move_to(220, 50)
        for x in range(101):
            y = start + (end - start) * self.easing.ease_in_out(x / 100.0)
            self.graphics.line_to(x + 220, y)

        self.graphics.stroke("#00f")



class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        self.add_child(OldTweenGraph(EasingOld.Sine, y = 50, x = 50))
        self.add_child(TweenGraph(Easing.Sine, y = 50, x = 50, opacity=0.1))


class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_default_size(600, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()

if __name__ == '__main__':
    window = BasicWindow()
    gtk.main()
