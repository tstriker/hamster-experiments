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
    
    def draw(self, area):
        area.set_color(self.color, 0.5)

        area.draw_rect(self.x - self.width / 2.0, self.y - self.width / 2.0, self.width, self.width, 3)
        area.context.fill()

            

class Canvas(graphics.Area):
    def __init__(self):
        graphics.Area.__init__(self)
        self.segments = []
        self.connect("mouse-move", self.on_mouse_move)        


    def on_mouse_move(self, widget, coords):
        x, y = coords

        segment = Segment(x, y, "#666666", 50)
        self.tweener.addTween(segment, tweenType = Easing.Cubic.easeOut, tweenTime=1.5, width = 0)
        self.segments.insert(0, segment)

    def on_expose(self):
        # on expose is called when we are ready to draw
        for i, segment in reversed(list(enumerate(self.segments))):
            if segment.width:
                segment.draw(self)
            else:
                del self.segments[i]

        self.redraw_canvas()


class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_title("Graphics Module")
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

