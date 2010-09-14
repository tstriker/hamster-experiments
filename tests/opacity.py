#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""Base template"""


import gtk

# adjust python path so we can use lib that is in sibling folder
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..')))
from lib import graphics

class OverlappingChildren(graphics.Sprite):
    def __init__(self, x, y, **kwargs):
        graphics.Sprite.__init__(self, x=x, y=y, **kwargs)
        self.add_child(graphics.Rectangle(50, 200, fill="#f00", opacity=0.5))
        self.add_child(graphics.Rectangle(50, 200, fill="#0f0", opacity=0.5, y=50))

class OnRender(graphics.Sprite):
    def __init__(self, x, y, **kwargs):
        graphics.Sprite.__init__(self, x=x, y=y, **kwargs)
        self.connect("on-render", self.on_render)

    def on_render(self, sprite):
        self.graphics.rectangle(0, 0, 50, 200)
        self.graphics.fill("#f00", 0.5)
        self.graphics.rectangle(0, 50, 50, 200)
        self.graphics.fill("#0f0", 0.5)

class ChildParent(graphics.Sprite):
    def __init__(self, x, y, **kwargs):
        graphics.Sprite.__init__(self, x=x, y=y, opacity=0.5, **kwargs)
        self.graphics.fill_area(0, 0, 50, 200, "#f00")

        self.add_child(graphics.Rectangle(50, 200, fill="#0f0", y=50))

class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        self.add_child(OverlappingChildren(110, 50, cache_as_bitmap = False))
        self.add_child(OverlappingChildren(161, 50, cache_as_bitmap = True))

        self.add_child(OnRender(220, 50, cache_as_bitmap = False))
        self.add_child(OnRender(271, 50, cache_as_bitmap = True))

        self.add_child(ChildParent(330, 50, cache_as_bitmap = False))
        self.add_child(ChildParent(381, 50, cache_as_bitmap = True))

        self.add_child(graphics.Image("../assets/oxy.png", x=430, y=50, opacity=0.5, cache_as_bitmap=False))
        self.add_child(graphics.Image("../assets/oxy.png", x=455, y=75, opacity=0.5, cache_as_bitmap=True))

        self.connect("on-enter-frame", self.on_enter_frame)

    def on_enter_frame(self, scene, context):
        g = graphics.Graphics(context)

        g.rectangle(50, 50, 50, 200)
        g.fill("#f00", 0.5)
        g.rectangle(50, 100, 50, 200)
        g.fill("#0f0", 0.5)

        self.redraw()



class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_default_size(1100, 400)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()

if __name__ == '__main__':
    window = BasicWindow()
    gtk.main()
