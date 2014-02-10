#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""Base template"""

import math

from gi.repository import Gtk as gtk
from lib import graphics
from lib import layout
from lib.pytweener import Easing


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

        base = layout.VBox()
        self.add_child(base)

        self.fiddly_bits_container = layout.VBox()
        base.add_child(self.fiddly_bits_container)

        button_box = layout.VBox(expand=False, padding=10)
        base.add_child(button_box)

        self.fiddly_bits = [FiddlyBit() for i in range(4)]
        self.populate_fiddlybits()

        self.connect("on-drag", self.on_drag_sprite)


    def on_drag_sprite(self, scene, sprite, event):
        for bit in self.fiddly_bits:
            if bit != sprite:
                bit.animate(x=sprite.x, y=sprite.y,
                            easing=Easing.Expo.ease_out)

    def gimme_mo(self, button):
        self.fiddly_bits.append(FiddlyBit())
        self.populate_fiddlybits()

    def populate_fiddlybits(self):
        self.fiddly_bits_container.clear()
        x, y = tiles(self.fiddly_bits)
        k = 0
        for i in range(y):
            box = layout.HBox()
            self.fiddly_bits_container.add_child(box)
            for j in range(x):
                internal_box = layout.HBox()
                box.add_child(internal_box)

                fixed = layout.Fixed(fill=False)
                internal_box.add_child(fixed)
                bit = self.fiddly_bits[k]
                fixed.add_child(bit)
                bit.x, bit.y = 0, 0 # addchild we do coords recalc

                k += 1
                if k >= len(self.fiddly_bits):
                    break




class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_default_size(600, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        box = gtk.VBox(border_width=10)
        scene = Scene()
        box.pack_start(scene, True, True, 0)

        gimme_mo = gtk.Button("Gimme Mo")
        box.pack_end(gimme_mo, False, True, 0)
        gimme_mo.connect("clicked", scene.gimme_mo)
        window.add(box)

        window.show_all()

if __name__ == '__main__':
    window = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
