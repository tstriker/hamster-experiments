#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
 Nothing, but wiggly seconds (especially when it gets to the top-right quarter).
"""

import math
import datetime as dt

import gtk
from lib import graphics

SEGMENT_LENGTH = 15
SEGMENTS = 10

class Segment(object):
    def __init__(self, x, y, color, width):
        self.x = x
        self.y = y
        self.angle = 1
        self.color = color
        self.width = width

    def draw(self, area):
        area.set_color(self.color)


        area.context.set_line_width(self.width)
        area.context.move_to(self.x, self.y)
        area.context.line_to(self.x + math.cos(self.angle) * SEGMENT_LENGTH,
                             self.y + math.sin(self.angle) * SEGMENT_LENGTH)
        area.context.stroke()

    def drag(self, x, y):
        # moves segment towards x, y, keeping the original angle and preset length
        dx = x - self.x
        dy = y - self.y

        self.angle = math.atan2(dy, dx)

        self.x = x - math.cos(self.angle) * SEGMENT_LENGTH
        self.y = y - math.sin(self.angle) * SEGMENT_LENGTH


class Canvas(graphics.Area):
    def __init__(self):
        graphics.Area.__init__(self)


        self.segments = []

        for i in range(SEGMENTS):
            self.segments.append(Segment(0, 0, "#666666", i))

        #self.connect("motion_notify_event", self.on_mouse_move)

        self.last_second = None


    def on_mouse_move(self, widget, event):
        if event.is_hint:
            x, y, state = event.window.get_pointer()
        else:
            x = event.x
            y = event.y
            state = event.state

        self.drag_hand(x, y)

    def drag_hand(self, x, y):
        def get_angle(segment, x, y):
            dx = x - segment.x
            dy = y - segment.y
            return math.atan2(dy, dx)

        # point each segment to it's predecessor
        for segment in self.segments:
            angle = get_angle(segment, x, y)
            segment.angle = angle

            x = x - math.cos(angle) * SEGMENT_LENGTH
            y = y - math.sin(angle) * SEGMENT_LENGTH

        # and now move the pointed nodes, starting from the last one
        # (that is the beginning of the arm)
        for prev, segment in reversed(list(zip(self.segments, self.segments[1:]))):
            prev.x = segment.x + math.cos(segment.angle) * SEGMENT_LENGTH
            prev.y = segment.y + math.sin(segment.angle) * SEGMENT_LENGTH

        self.redraw_canvas()

    def on_expose(self):
        self.segments[-1].y = self.height / 2
        self.segments[-1].x = self.width / 2

        # on expose is called when we are ready to draw
        for segment in self.segments:
            segment.draw(self)


        sec_degrees = dt.datetime.now().second / 60.0 * math.pi * 2
        msec_degrees = dt.datetime.now().microsecond / 1000000.0 * math.pi

        x = math.sin(sec_degrees) * 150 + self.width / 2 + math.sin(msec_degrees) * 5
        y = -math.cos(sec_degrees) * 150 + self.height / 2 + math.cos(msec_degrees) * 5

        self.drag_hand(x, y)

        self.redraw_canvas()



class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(600, 400)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        canvas = Canvas()

        box = gtk.VBox()
        box.pack_start(canvas)


        window.add(box)
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    gtk.main()

