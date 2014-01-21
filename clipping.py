#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
Clipping demo - two labels in different colors are put on each other
but before painting the area is clipped so that first label gets 0 -> mouse_x
width and the other mouse_x -> window width
"""


from gi.repository import Gtk as gtk
from lib import graphics


class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self, framerate=30)
        self.connect("on-enter-frame", self.on_enter_frame)

    def on_enter_frame(self, scene, context):
        g = graphics.Graphics(context)

        g.save_context()


        g.rectangle(0, 0, self.mouse_x, self.height)
        g.clip()
        g.move_to(20, 100)
        g.show_label("Hello", font_desc="Sans Serif 150", color="#fff")

        g.restore_context()

        g.save_context()
        g.rectangle(self.mouse_x, 0, self.width, self.height)
        g.clip()
        g.move_to(20, 100)
        g.show_label("Hello", font_desc="Sans Serif 150", color="#000")
        g.restore_context()

        self.redraw()






class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_default_size(600, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()

if __name__ == '__main__':
    window = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
