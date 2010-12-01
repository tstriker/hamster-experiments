#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""Base template"""


import gtk
from lib import graphics
import cairo

class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.oxy = graphics.BitmapSprite(cairo.ImageSurface.create_from_png(("assets/oxy.png")), snap_to_pixel=False, draggable=True)

        self.add_child(self.oxy)
        self.connect("on_frame", self.on_frame)
        self.kx, self.ky = 1.5, 1


    def on_frame(self, scene):
        print self.fps



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
