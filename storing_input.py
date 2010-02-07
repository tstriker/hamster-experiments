#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
 Move the mouse across the screen to change the position of the rectangles.
 The positions of the mouse are recorded into a list and played back every frame.
 Between each frame, the newest value are added to the start of the list.

 Ported from processing.js (http://processingjs.org/learning/basic/storinginput)
"""

import gtk
from lib import graphics
from lib.pytweener import Easing

import math


class Segment(object):
    def __init__(self, x, y, color, width):
        self.x = x
        self.y = y
        self.color = color
        self.width = width

    def draw(self, scene, context):
        color = scene.colors.parse(self.color)
        context.set_source_rgba(color[0], color[1], color[2], 0.5)

        context.rectangle(self.x - self.width / 2.0, self.y - self.width / 2.0, self.width, self.width)
        context.fill()



class Canvas(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.segments = []
        self.connect("mouse-move", self.on_mouse_move)
        self.connect("on-enter-frame", self.on_enter_frame)


    def on_mouse_move(self, widget, event):
        x, y = event.x, event.y

        segment = Segment(x, y, "#666666", 50)
        self.tweener.addTween(segment, tweenType = Easing.Cubic.easeOut, tweenTime=1.5, width = 0)
        self.segments.insert(0, segment)

    def on_enter_frame(self, scene, context):
        # on expose is called when we are ready to draw
        for i, segment in reversed(list(enumerate(self.segments))):
            if segment.width:
                segment.draw(self, context)
            else:
                del self.segments[i]

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
