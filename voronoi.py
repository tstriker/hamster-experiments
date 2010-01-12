#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
 Games with points, implemented following Dr. Mike's Maths
 http://www.dr-mikes-maths.com/
"""


import gtk
from lib import graphics
from lib.pytweener import Easing

import math
from lib.euclid import Vector2, Point2
import itertools


EPSILON = 0.00001

class Node(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.fixed = False #to pin down


class Canvas(graphics.Area):
    def __init__(self):
        graphics.Area.__init__(self)
        self.nodes = [Node(-10000, -10000), Node(10000, -10000), Node(0, 10000)]

        self.connect("mouse-move", self.on_mouse_move)
        self.connect("button-press", self.on_mouse_button_press)
        self.connect("mouse-click", self.on_mouse_click)

        self.mouse_node = None
        self.prev_mouse_node = None
        

    def on_expose(self):

        # voronoi diagram
        segments = list(self.voronoi())
        for node, node2 in segments:
            self.context.move_to(node.x, node.y)
            self.context.line_to(node2.x, node2.y)
        self.context.stroke()

        self.set_color("#999")
        for i, node in enumerate(self.nodes):
            self.draw_node(node)
            self.register_mouse_region(node.x - 5, node.y - 5, node.x + 5, node.y + 5, i)


    def triangle_circumcenter(self, a, b, c):
        """shockingly, the circumcenter math has been taken from wikipedia
           we move the triangle to 0,0 coordinates to simplify math"""
        
        p_a = Vector2(a.x, a.y)
        p_b = Vector2(b.x, b.y) - p_a
        p_c = Vector2(c.x, c.y) - p_a
        
        p_b2 = p_b.magnitude_squared()
        p_c2 = p_c.magnitude_squared()
        
        d = 2 * (p_b.x * p_c.y - p_b.y * p_c.x)
        
        if d < 0:
            d = min(d, EPSILON)
        else:
            d = max(d, EPSILON)
        

        centre_x = (p_c.y * p_b2 - p_b.y * p_c2) / d
        centre_y = (p_b.x * p_c2 - p_c.x * p_b2) / d
        
        centre = p_a + Vector2(centre_x, centre_y)
        return centre
        

    def voronoi(self):
        segments = []
        centres = {}
        for a, b, c in itertools.combinations(self.nodes, 3):
            centre = self.triangle_circumcenter(a, b, c)
            
            distance2 = (Vector2(a.x, a.y) - centre).magnitude_squared()

            smaller_found = False
            for node in self.nodes:
                if node in [a,b,c]:
                    continue
                
                if (Vector2(node.x, node.y) - centre).magnitude_squared() < distance2:
                    smaller_found = True
                    break
            
            if not smaller_found:
                for a1,b1 in itertools.combinations([a,b,c], 2):
                    centres.setdefault((a1,b1), []).append(centre)

        
        #return centres for all points that share more than one
        #centres = set([c[0] for c in centres.values() if len(c) > 1])
        
        res = []
        for key in centres:
            if len(centres[key]) > 1:
                for node, node2 in zip(centres[key], centres[key][1:]):
                    res.append((node, node2))
                    
                if len(centres[key]) > 2:
                    res.append((centres[key][-1], centres[key][0]))


        return res


    def draw_node(self, node):
        radius = 10
        self.draw_rect(node.x - radius / 2, node.y - radius / 2, radius, radius, 3)
        self.context.fill()


    # just for kicks - mouse events
    def on_mouse_button_press(self, area, over_regions):
        if over_regions:
            self.mouse_node = over_regions[0]

    def on_mouse_click(self, area, coords, areas):
        if not areas:
            self.nodes.append(Node(*coords))
            self.redraw_canvas()


    def on_mouse_move(self, area, coords, state):
        if self.mouse_node is not None:  #checking for none as there is the node zero
            if gtk.gdk.BUTTON1_MASK & state:
                # dragging around
                self.nodes[self.mouse_node].x = coords[0]
                self.nodes[self.mouse_node].y = coords[1]
                self.redraw_canvas()
            else:
                self.mouse_node = None

class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(600, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        self.canvas = Canvas()

        box = gtk.VBox()
        box.pack_start(self.canvas)

        button = gtk.Button("Redo")
        def on_click(*args):
            self.canvas.nodes = []
            self.canvas.mouse_node, self.canvas.prev_mouse_node = None, None
            self.canvas.redraw_canvas()

        button.connect("clicked", on_click)
        box.pack_start(button, False)



        window.add(box)
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    gtk.main()

