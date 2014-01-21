#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
 Games with points, implemented following Dr. Mike's Maths
 http://www.dr-mikes-maths.com/

 Also this is an example how to handle mouse
"""

from gi.repository import Gtk as gtk
from lib import graphics

import math
from contrib.euclid import Point2

class Node(graphics.Rectangle):
    def __init__(self, x, y):
        graphics.Rectangle.__init__(self, 10, 10, x=x, y=y,
                                    fill = "#999",
                                    corner_radius = 3,
                                    pivot_x = 5, pivot_y = 5,
                                    interactive=True,
                                    draggable = True)

        # TODO - remember how the drag model has changed and fix the math
        #self.connect("on-drag-start", self.on_drag_start)
        #self.connect("on-drag-finish", self.on_drag_finish)

    def on_drag_start(self, sprite, event):
        self.animate(width=50, height=50,
                     pivot_x = 25, pivot_y = 25,
                     drag_x = sprite.x - 25, drag_y = sprite.y - 25)

    def on_drag_finish(self, sprite, event):
        self.animate(width=10, height=10, pivot_x = 5, pivot_y = 5)

class Canvas(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.nodes = []
        self.connect("on-click", self.on_mouse_click)
        self.connect("on-enter-frame", self.on_enter_frame)

    def on_mouse_click(self, area, event, target):
        if not target:
            node = Node(event.x, event.y)

            self.nodes.append(node)
            self.add_child(node)
        else:
            target.fill = "#f00"

    def on_enter_frame(self, scene, context):
        g = graphics.Graphics(context)
        g.set_color("#999")

        for node, node2 in self.convex_hull():
            g.move_to(node.x + node.pivot_x, node.y + node.pivot_y)
            g.line_to(node2.x + node2.pivot_x, node2.y + node2.pivot_y)

            node.rotation += 0.01

        g.stroke()
        self.redraw()




    def convex_hull(self):
        """self brewn lame algorithm to find hull, following dr mike's math.
           Basically we find the topmost edge and from there go looking
           for line that would form the smallest angle
        """

        if len(self.nodes) < 2: return []

        # grab the topmost node (the one with the least y)
        topmost = sorted(self.nodes, key=lambda node:node.y)[0]

        segments = []
        # initially the current line is looking upwards
        current_line = Point2(topmost.x, topmost.y) - Point2(topmost.x, topmost.y - 1)
        current_node = topmost
        smallest = None

        node_list = list(self.nodes)

        while current_node and smallest != topmost:
            # calculate angles between current line
            angles = [(node, current_line.angle(current_node - Point2(node.x, node.y))) for node in node_list if node != current_node]

            if angles:
                smallest = sorted(angles, key = lambda x: x[1])[0][0]
                segments.append((current_node, smallest)) # add to the results

                # now we will be looking for next connection
                current_line = Point2(current_node.x, current_node.y) - Point2(smallest.x, smallest.y)
                current_node = smallest
                node_list.remove(smallest) # tiny optimization
            else:
                current_node = None


        return segments




class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_size_request(600, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        self.canvas = Canvas()

        box = gtk.VBox()
        box.add(self.canvas)

        button = gtk.Button("Redo")
        def on_click(*args):
            self.canvas.nodes = []
            self.canvas.clear()
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
