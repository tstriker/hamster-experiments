#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""Base template"""

import math

import gtk
from lib import graphics
from lib.pytweener import Easing
import ui

def tiles(items):
    """looks for the most rectangular grid for the given number of items,
       prefers horizontal"""
    if not items:
        return (0, 0)

    if isinstance(items, list):
        items = len(items)

    y = int(math.sqrt(items))
    x = items / y + (1 if items % y else 0)
    return (x, y)



class FiddlyBit(graphics.Sprite):
    def __init__(self, **kwargs):
        graphics.Sprite.__init__(self, **kwargs)
        self.interactive = True
        self.draggable = True

        self.connect("on-render", self.on_render)

    def on_render(self, sprite):
        self.graphics.fill_area(-10, -10, 20, 20, "#f0f")
        #self.graphics.move_to(0, -50)
        #self.graphics.line_to(0, 50)
        #self.graphics.stroke("#aaa")




class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        base = ui.VBox()
        self.add_child(base)

        self.fiddly_bits_container = ui.VBox()
        base.add_child(self.fiddly_bits_container)

        button_box = ui.VBox(expand=False, padding=10)
        base.add_child(button_box)

        self.mo = ui.Button("Gimme mo")
        self.mo.connect("on-click", self.gimme_mo)
        button_box.add_child(self.mo)

        self.fiddly_bits = [FiddlyBit() for i in range(4)]
        self.populate_fiddlybits()

        self.connect("on-drag", self.on_drag_sprite)


    def on_drag_sprite(self, scene, sprite, event):
        for bit in self.fiddly_bits:
            if bit != sprite:
                bit.animate(x=sprite.x, y=sprite.y,
                            easing=Easing.Expo.ease_out)

    def gimme_mo(self, sprite, event):
        self.fiddly_bits.append(FiddlyBit())
        self.populate_fiddlybits()

    def populate_fiddlybits(self):
        self.fiddly_bits_container.clear()
        x, y = tiles(self.fiddly_bits)
        k = 0
        for i in range(y):
            box = ui.HBox()
            self.fiddly_bits_container.add_child(box)
            for j in range(x):
                internal_box = ui.HBox()
                box.add_child(internal_box)

                fixed = ui.Fixed(fill=False)
                internal_box.add_child(fixed)
                bit = self.fiddly_bits[k]
                fixed.add_child(bit)
                bit.x, bit.y = 0, 0 # addchild we do coords recalc

                k += 1
                if k >= len(self.fiddly_bits):
                    break




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
