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
from contrib.euclid import Vector2, Point2
import itertools


EPSILON = 0.00001

class Node(graphics.Sprite):
    def __init__(self, x, y):
        graphics.Sprite.__init__(self, x, y, interactive=True, draggable=True)
        self.graphics.rectangle(-5, -5, 10, 10, 3)
        self.graphics.fill("#999")

class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.nodes = [Node(-10000, -10000), Node(10000, -10000), Node(0, 10000)]

        self.connect("on-enter-frame", self.on_enter_frame)
        self.connect("on-click", self.on_mouse_click)
        self.connect("on-drag", self.on_node_drag)

        self.draw_circles = False

    def on_mouse_click(self, area, event, target):
        if not target:
            node = Node(event.x, event.y)
            self.nodes.append(node)
            self.add_child(node)

            self.redraw()


    def on_node_drag(self, scene, node, event):
        self.redraw()


    def on_enter_frame(self, scene, context):

        # voronoi diagram
        context.set_source_rgb(0.7, 0.7, 0.7)
        segments = list(self.voronoi())
        for node, node2 in segments:
            context.move_to(node.x, node.y)
            context.line_to(node2.x, node2.y)
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
                order = sorted([a,b,c], key = lambda node: node.x+node.y)
                for a1,b1 in itertools.combinations(order, 2):
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

        res = set(res)

        return res


class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_size_request(600, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        self.scene = Scene()

        box = gtk.VBox()
        box.pack_start(self.scene, True, True, 0)

        button = gtk.Button("Clear")
        def on_click(*args):
            self.canvas.nodes = []
            self.canvas.mouse_node, self.canvas.prev_mouse_node = None, None
            self.canvas.redraw()

        button.connect("clicked", on_click)
        box.pack_start(button, False, False, 0)



        window.add(box)
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
