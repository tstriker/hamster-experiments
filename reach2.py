#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
 * Reach 2.
 * Based on code from Keith Peters (www.bit-101.com).
 *
 * The arm follows the position of the mouse by
 * calculating the angles with atan2().
 *
 Ported from processing (http://processing.org/) examples.
"""

import math
from gi.repository import Gtk as gtk
from lib import graphics

SEGMENT_LENGTH = 25

class Segment(graphics.Sprite):
    def __init__(self, x, y, width):
        graphics.Sprite.__init__(self, x, y, snap_to_pixel = False)

        self.graphics.move_to(0, 0)
        self.graphics.line_to(SEGMENT_LENGTH, 0)

        self.graphics.set_color("#999")
        self.graphics.set_line_style(width = width)
        self.graphics.stroke()


class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)


        self.segments = []

        parts = 20
        for i in range(parts):
            segment = Segment(0, 0, i)
            self.segments.append(segment)
            self.add_child(segment)

        self.connect("on-mouse-move", self.on_mouse_move)
        self.connect("on-enter-frame", self.on_enter_frame)


    def on_mouse_move(self, scene, event):
        x, y = event.x, event.y

        def get_angle(segment, x, y):
            dx = x - segment.x
            dy = y - segment.y
            return math.atan2(dy, dx)

        # point each segment to it's predecessor
        for segment in self.segments:
            angle = get_angle(segment, x, y)
            segment.angle = angle
            segment.rotation = angle

            x = x - math.cos(angle) * SEGMENT_LENGTH
            y = y - math.sin(angle) * SEGMENT_LENGTH

        # and now move the pointed nodes, starting from the last one
        # (that is the beginning of the arm)
        for prev, segment in reversed(list(zip(self.segments, self.segments[1:]))):
            prev.x = segment.x + math.cos(segment.angle) * SEGMENT_LENGTH
            prev.y = segment.y + math.sin(segment.angle) * SEGMENT_LENGTH


        self.redraw()

    def on_enter_frame(self, scene, context):
        self.segments[-1].y = self.height



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
