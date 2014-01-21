#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>
"""
    this was an attempt to achieve motion blur
    hoping that fading out will do the job.
    this is not quite motion blur - to see what i mean, try moving the mouse
    around for a longer while - instead of motion blur what you get is motion
    tail, which is unwanted.
    still this example teaches something too.
"""

from gi.repository import Gtk as gtk
from lib import graphics

class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.mouse_cursor = False

        self.coords = []
        self.x, self.y = 0, 0
        self.radius = 30
        self.connect("on-mouse-move", self.on_mouse_move)
        self.connect("on-enter-frame", self.on_enter_frame)
        self.fade_tick = 0


    def on_mouse_move(self, area, event):
        # oh i know this should not be performed using tweeners, but hey - a demo!
        self.coords.insert(0, (event.x, event.y))
        self.coords = self.coords[:10]  # limit trail length

    def on_enter_frame(self, scene, context):
        g = graphics.Graphics(context)

        for i, coords in enumerate(reversed(self.coords)):
            x, y = coords

            if i == len(self.coords) - 1:
                alpha = 1
            else:
                alpha = float(i+1) / len(self.coords) / 2

            g.rectangle(x - self.radius,
                            y - self.radius,
                            self.radius * 2,
                            self.radius * 2, 3)
            #print alpha
            g.fill("#999", alpha)

        self.fade_tick += 1
        if len(self.coords) > 1 and self.fade_tick > 2:
            self.fade_tick = 0
            self.coords.pop(-1)

        self.redraw() # constant redraw (maintaining the requested frame rate)


class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_default_size(300, 300)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        window.add(Scene())
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
