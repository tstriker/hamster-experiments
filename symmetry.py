#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2014 Toms Baugis <toms.baugis@gmail.com>

"""Exploring symmetry. Feel free to add more handles!"""
import math
from gi.repository import Gtk as gtk
from lib import graphics


class SymmetricalRepeater(graphics.Sprite):
    def __init__(self, sides, master_poly=None, **kwargs):
        graphics.Sprite.__init__(self, **kwargs)
        self.sides = sides #: number of sides this symmetrical dude will have

        self.master_poly = master_poly or []

        # duplicates the poly N times and you can control wether the
        # changes that happen to the master poly are distributed at once
        # or one-by-one

        self.connect("on-render", self.on_render)

    def on_render(self, sprite):
        angle = 360.0 / self.sides

        # debug
        self.graphics.save_context()
        for i in range(self.sides):
            self.graphics.move_to(0, 0)
            self.graphics.line_to(1000, 0)
            self.graphics.rotate(math.radians(angle))
        self.graphics.stroke("#3d3d3d")
        self.graphics.restore_context()


        for i in range(self.sides):
            self.graphics.move_to(*self.master_poly[0])
            for dot in self.master_poly[1:]:
                self.graphics.line_to(*dot)
            self.graphics.rotate(math.radians(angle))
        self.graphics.stroke("#fff")

class Handle(graphics.Sprite):
    def __init__(self, **kwargs):
        graphics.Sprite.__init__(self, **kwargs)
        self.interactive=True
        self.draggable=True

        self.connect("on-render", self.on_render)

    def on_render(self, sprite):
        self.graphics.rectangle(-5, -5, 10, 10, 3)
        self.graphics.fill("#eee")


class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self, background_color="#333")
        self.handles = graphics.Sprite()
        self.add_child(self.handles)
        self.repeater = None
        self.create_repeater(4)

    def create_repeater(self, sides):
        self.clear()
        master_poly = [(100, 0), (150, 0), (200, 0)]
        self.repeater = SymmetricalRepeater(sides, master_poly=master_poly, x=300, y=250)
        self.add_child(self.repeater)

        self.add_child(self.handles)
        self.handles.x, self.handles.y = self.repeater.x, self.repeater.y


        self.handles.clear()
        for dot in master_poly:
            handle = Handle(x=dot[0], y=dot[1])
            self.handles.add_child(handle)
            handle.connect("on-drag", self.adjust_master_poly)

    def adjust_master_poly(self, sprite, event):
        self.repeater.master_poly = [(handle.x, handle.y) for handle in self.handles.sprites]


    def on_enter_frame(self, scene, context):
        # you could do all your drawing here, or you could add some sprites
        g = graphics.Graphics(context)

        # self.redraw() # this is how to get a constant redraw loop (say, for animation)



class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_default_size(600, 550)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        self.scene = Scene()

        box = gtk.VBox()
        box.pack_start(self.scene, True, True, 0)

        hbox = gtk.HBox(spacing=10)
        mo = gtk.Button("More")
        less = gtk.Button("Less")
        for button in (less, mo):
            hbox.add(button)
            button.connect("clicked", self.on_button_click)

        hbox.set_border_width(12)
        box.pack_end(hbox, False, True, 0)

        window.add(box)
        window.show_all()

    def on_button_click(self, button):
        delta = 1 if button.get_label() == "More" else -1
        sides = max(1, self.scene.repeater.sides + delta)
        self.scene.create_repeater(sides)


if __name__ == '__main__':
    window = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
