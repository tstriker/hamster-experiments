#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
 * Follow 3.
 * Based on code from Keith Peters (www.bit-101.com).
 *
 * A segmented line follows the mouse. The relative angle from
 * each segment to the next is calculated with atan2() and the
 * position of the next is calculated with sin() and cos().
 *
 Ported from processing (http://processing.org/) examples.
"""

import math
from gi.repository import Gtk as gtk
from lib import graphics

PARTS = 40
SEGMENT_LENGTH = 20

class Segment(graphics.Sprite):
    def __init__(self, x, y, color):
        graphics.Sprite.__init__(self, x, y, interactive = False, snap_to_pixel = False)
        self.angle = 1
        self.color = color

        self.graphics.rectangle(-5, -5, 10, 10, 3)
        self.graphics.move_to(0, 0)
        self.graphics.line_to(SEGMENT_LENGTH, 0)
        self.graphics.set_color("#666")
        self.graphics.fill_preserve()
        self.graphics.stroke_preserve()


    def drag(self, x, y):
        # moves segment towards x, y, keeping the original angle and preset length
        dx = x - self.x
        dy = y - self.y

        self.angle = math.atan2(dy, dx)

        self.x = x - math.cos(self.angle) * SEGMENT_LENGTH
        self.y = y - math.sin(self.angle) * SEGMENT_LENGTH
        self.rotation = self.angle


class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)


        self.segments = []

        for i in range(PARTS):
            # for segment initial positions we use sinus. could as well
            # just set 0,0.
            segment = Segment(500 - (i / float(PARTS)) * 500,
                              math.sin((i / float(PARTS)) * 30) * 150 + 150,
                              "#666666")
            if self.segments:
                segment.drag(self.segments[-1].x, self.segments[-1].y)
            self.segments.append(segment)
            self.add_child(segment)

        self.connect("on-mouse-move", self.on_mouse_move)


    def on_mouse_move(self, scene, event):
        x, y = event.x, event.y

        self.segments[0].drag(x, y)
        for prev, segment in zip(self.segments, self.segments[1:]):
            segment.drag(prev.x, prev.y)

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
