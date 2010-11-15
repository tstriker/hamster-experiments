#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""Base template"""


import gtk
from lib import graphics

class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        sides = ["tl", "br", "tl2", "br2"]
        for side in sides:
            rect = graphics.Rectangle(10, 10, 3, "#aaa", draggable = True)
            setattr(self, side, rect)
            self.add_child(rect)

        self.tl.x, self.tl.y = 100, 100
        self.br.x, self.br.y = 150, 150

        self.tl2.x, self.tl2.y = 200, 200
        self.br2.x, self.br2.y = 250, 250

        self.rect = graphics.geom.Rectangle()
        self.rect2 = graphics.geom.Rectangle()

        self.connect("on-enter-frame", self.on_enter_frame)

    def on_enter_frame(self, scene, context):
        g = graphics.Graphics(context)

        self.rect.left = self.tl.x + 5
        self.rect.top = self.tl.y + 5
        self.rect.right = self.br.x + 5
        self.rect.bottom = self.br.y + 5
        g.rectangle(self.rect.x, self.rect.y, self.rect.w, self.rect.h)

        self.rect2.left = self.tl2.x + 5
        self.rect2.top = self.tl2.y + 5
        self.rect2.right = self.br2.x + 5
        self.rect2.bottom = self.br2.y + 5
        g.rectangle(self.rect2.x, self.rect2.y, self.rect2.w, self.rect2.h)
        g.stroke("#666")

        union = self.rect.union(self.rect2)
        g.rectangle(union.x, union.y, union.w, union.h)
        g.fill("#fff000", 0.3)

        inter = self.rect.intersection(self.rect2)
        if inter:
            g.rectangle(inter.x, inter.y, inter.w, inter.h)
            g.fill("#000fff", 0.3)


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
