#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
 Games with points, implemented following Dr. Mike's Maths
 http://www.dr-mikes-maths.com/
"""


from gi.repository import Gtk as gtk
from lib import graphics

import math
from contrib.euclid import Vector2
import itertools


EPSILON = 0.00001

class Node(graphics.Sprite):
    def __init__(self, x, y):
        graphics.Sprite.__init__(self, x=x, y=y, interactive=True, draggable=True)
        self.graphics.rectangle(-5, -5, 10, 10, 3)
        self.graphics.fill("#999")

class Canvas(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.nodes = []
        self.centres = []
        self.segments = []

        self.connect("on-enter-frame", self.on_enter_frame)
        self.connect("on-click", self.on_mouse_click)
        self.connect("on-drag", self.on_node_drag)

        self.draw_circles = False

    def on_mouse_click(self, area, event, target):
        if not target:
            node = Node(event.x, event.y)
            self.nodes.append(node)
            self.add_child(node)
            self.centres = []

            self.redraw()


    def on_node_drag(self, scene, node, event):
        self.centres = []
        self.redraw()


    def on_enter_frame(self, scene, context):
        c_graphics = graphics.Graphics(context)
        c_graphics.set_line_style(width = 0.5)

        if not self.centres:  #reset when adding nodes
            self.centres, self.segments = self.delauney()

        c_graphics.set_color("#666")
        for node, node2 in self.segments:
            context.move_to(node.x, node.y)
            context.line_to(node2.x, node2.y)
        context.stroke()

        if self.draw_circles:
            for node, radius in self.centres:
                c_graphics.set_color("#f00", 0.3)
                context.arc(node[0], node[1], radius, 0, 2.0 * math.pi)
                context.fill_preserve()
                context.stroke()

                c_graphics.set_color("#a00")
                context.rectangle(node[0]-1, node[1]-1, 2, 2)
                context.stroke()



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


    def delauney(self):
        segments = []
        centres = []
        combos = list(itertools.combinations(self.nodes, 3))
        print "combinations: ", len(combos)
        for a, b, c in combos:
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
                segments.extend(list(itertools.combinations([a,b,c], 2)))

                if 0 < centre.x < self.width and 0 < centre.y < self.height:
                    centres.append((centre, math.sqrt(distance2)))

        for segment in segments:
            order = sorted(segment, key = lambda node: node.x+node.y)
            segment = (order[0], order[1])

        segments = set(segments)

        return set(centres), segments



class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_size_request(600, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())


        vbox = gtk.VBox()
        window.add(vbox)

        box = gtk.HBox()
        box.set_border_width(10)
        box.add(gtk.Label("Add some points and observe Delauney triangulation"))
        vbox.pack_start(box, False, False, 0)

        self.canvas = Canvas()
        vbox.add(self.canvas)

        box = gtk.HBox(False, 4)
        box.set_border_width(10)

        vbox.pack_start(box, False, False, 0)

        button = gtk.Button("Generate points in centers")
        def on_click(*args):
            for centre, radius in self.canvas.centres:
                if abs(centre) < 2000:
                    node = Node(*centre)
                    self.canvas.nodes.append(node)
                    self.canvas.add_child(node)
            self.canvas.centres = []
            self.canvas.redraw()

        button.connect("clicked", on_click)
        box.pack_end(button, False, False, 0)

        button = gtk.Button("Clear")
        def on_click(*args):
            self.canvas.nodes = []
            self.canvas.mouse_node, self.canvas.prev_mouse_node = None, None
            self.canvas.centres = []
            self.canvas.clear()
            self.canvas.redraw()

        button.connect("clicked", on_click)
        box.pack_end(button, False, False, 0)

        button = gtk.CheckButton("show circumcenter")
        def on_click(button):
            self.canvas.draw_circles = button.get_active()
            self.canvas.redraw()

        button.connect("clicked", on_click)
        box.pack_start(button, False, False, 0)


        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
