#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""Base template"""


import gtk
from lib import graphics

class Entry(graphics.Sprite):
    """a sprite that can wrap around any gtk interactive element
       and make it move on a canvas etc"""

    def __init__(self, **kwargs):
        graphics.Sprite.__init__(self, **kwargs)
        self.entry = gtk.Entry()
        self.entry.set_has_frame(False)
        self.entry.set_text("Edit me and drag the circle around too")
        self.fixed = None
        self.connect("on-render", self.on_render)
        self.width, self.height = -1, -1

    def __setattr__(self, name, value):
        if name in ('width', 'height') and value is None:
            value = -1

        graphics.Sprite.__setattr__(self, name, value)

    def _draw(self, context, opacity=1, *args, **kwargs):
        graphics.Sprite._draw(self, context, opacity)
        matrix = self.get_matrix()
        x, y = int(matrix[4]), int(matrix[5])

        self.fixed.move(self.entry, x, y)

    def on_render(self, sprite):
        self.fixed = self.get_scene().parent
        if self.entry.parent != self.fixed:
            self.fixed.put(self.entry, 100, 100)
            self.entry.show()

        self.entry.set_size_request(self.width, self.height)


class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.background_color = "#fafafa"

        self.circle = graphics.Circle(100, 100, "#6ee", x=100, y=100,
                                      interactive=True, draggable=True)

        self.entry = Entry(x=40, y=40)
        self.circle.add_child(self.entry)

        self.entry.width = 300

        self.add_child(self.circle)
        self.connect("on-enter-frame", self.on_enter_frame)

    def on_enter_frame(self,  scene, context):
        pass


class FixedScene(gtk.Fixed):
    def __init__(self):
        gtk.Fixed.__init__(self)
        self.scene = Scene()

        self.put(self.scene, 0, 0)
        self.scene.set_size_request(600, 500)

        #self.put(gtk.Label("yohoho"), 100, 10)

        #self.put(gtk.Entry(), 130, 135)

    def put(self, object, x, y):
        gtk.Fixed.put(self, object, x, y)


class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_default_size(600, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        fixed = FixedScene()

        viewport = gtk.Viewport()
        viewport.add(fixed)
        viewport.set_size_request(600,500)

        window.add(viewport)
        window.show_all()

if __name__ == '__main__':
    window = BasicWindow()
    gtk.main()
