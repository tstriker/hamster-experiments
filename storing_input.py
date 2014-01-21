#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
 Move the mouse across the screen to change the position of the rectangles.
 The positions of the mouse are recorded into a list and played back every frame.
 Between each frame, the newest value are added to the start of the list.

 Ported from processing.js (http://processingjs.org/learning/basic/storinginput)
"""

from gi.repository import Gtk as gtk
from lib import graphics
from lib.pytweener import Easing

import math


class Segment(object):
    def __init__(self, x, y, color, width):
        self.x = x
        self.y = y
        self.color = color
        self.width = width


class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.segments = []
        self.connect("on-mouse-move", self.on_mouse_move)
        self.connect("on-enter-frame", self.on_enter_frame)


    def on_mouse_move(self, widget, event):
        x, y = event.x, event.y

        segment = Segment(x, y, "#666666", 50)
        self.tweener.add_tween(segment, easing = Easing.Cubic.ease_out, duration=1.5, width = 0)
        self.segments.insert(0, segment)

    def on_enter_frame(self, scene, context):
        g = graphics.Graphics(context)


        # on expose is called when we are ready to draw
        for i, segment in reversed(list(enumerate(self.segments))):
            if segment.width:
                g.rectangle(segment.x - segment.width / 2.0,
                            segment.y - segment.width / 2.0,
                            segment.width,
                            segment.width, 3)
                g.fill(segment.color, 0.5)

            else:
                del self.segments[i]

        self.redraw()


class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_size_request(600, 400)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        window.add(Scene())
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
