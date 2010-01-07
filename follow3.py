#!/usr/bin/env python
# - coding: utf-8 -
"""
 * Follow 3. 
 * Based on code from Keith Peters (www.bit-101.com). 
 * 
 * A segmented line follows the mouse. The relative angle from
 * each segment to the next is calculated with atan2() and the
 * position of the next is calculated with sin() and cos().
 *
 Ported from processing by Toms Baugis <toms.baugis@gmail.com>, 2010.
"""
 
import gtk

from hamster import pytweener
from hamster import graphics
from hamster.pytweener import Easing

import math
import colorsys

SEGMENT_LENGTH = 20

class Segment(object):
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.angle = 1
        self.color = color
    
    def draw(self, area):
        area.draw_rect(self.x - 5, self.y - 5, 10, 10, 3)
        
        area.set_color(self.color)
        area.context.fill()
        
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

        parts = 20
        for i in range(parts):
            self.segments.append(Segment(0, 0, "#666666"))

        self.connect("motion_notify_event", self.on_mouse_move)        


    def on_mouse_move(self, widget, event):
        if event.is_hint:
            x, y, state = event.window.get_pointer()
        else:
            x = event.x
            y = event.y
            state = event.state
        
        self.segments[0].drag(x, y)
        
        for prev, segment in zip(self.segments, self.segments[1:]):
            segment.drag(prev.x, prev.y)

        self.redraw_canvas()

    def on_expose(self):
        # on expose is called when we are ready to draw
        for segment in self.segments:
            segment.draw(self)


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

