#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
 Ported from prefuse (http://prefuse.org/).
 Extra:
   * added node gravitation towards centre
   * buffering node positions and tweening every now and then to avoid stuttering

 Original docu:
 <p>Layout instance implementing the Fruchterman-Reingold algorithm for
 force-directed placement of graph nodes. The computational complexity of
 this algorithm is quadratic [O(n^2)] in the number of nodes, so should
 only be applied for relatively small graphs, particularly in interactive
 situations.</p>

 <p>This implementation was ported from the implementation in the
 <a href="http://jung.sourceforge.net/">JUNG</a> framework.</p>

 @author Scott White, Yan-Biao Boey, Danyel Fisher
 @author <a href="http://jheer.org">jeffrey heer</a>
"""


import gtk
from lib import graphics
from lib.pytweener import Easing

import math
from random import random, randint
from copy import deepcopy

EPSILON = 0.00001
ALPHA = 0.2

class Node(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.fixed = False #to pin down

class DisplayNode(graphics.Circle):
    def __init__(self, x, y, real_node):
        graphics.Circle.__init__(self, 5, fill = "#999")
        self.x = x
        self.y = y
        self.real_node = real_node
        self.pivot_x = 5
        self.pivot_y = 5
        self.interactive = True
        self.draggable = True


class Canvas(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.nodes = []
        self.edges = []

        self.node_buffer = []
        self.edge_buffer = []

        self.max_iterations = 300
        self.iteration = 0
        self.force_constant = 0
        self.connect("on-drag", self.on_drag)
        self.connect("on-mouse-up", self.on_mouse_up)

        self.connect("on-enter-frame", self.on_enter_frame)
        self.connect("on-finish-frame", self.on_finish_frame)

        self.mouse_node = None

    def init_calculations(self):
        self.iteration = 0
        self.force_constant = 0.75 *  math.sqrt(self.height * self.width / len(self.nodes))
        self.temperature = self.width / float(10)

    def cooldown(self):
        self.temperature = self.temperature * (1.0 - self.iteration / float(self.max_iterations))


    def on_finish_frame(self, scene, context):
        context.fill()

    def on_enter_frame(self, scene, context):
        c_graphics = graphics.Graphics(context)

        if not self.nodes:
            for i in range(randint(3, 50)):
                x, y = self.width / 2, self.height / 2
                scale_w = ALPHA * x;
                scale_h = ALPHA * y

                node = Node(x + (random() - 0.5) * 2 * scale_w,
                                       y + (random() - 0.5) * 2 * scale_h)
                self.nodes.append(node)

                display_node = DisplayNode(node.x, node.y, node)
                self.add_child(display_node)


            node_count = len(self.nodes) - 1

            self.edges, self.edge_buffer = [], []
            for i in range(randint(node_count / 2, node_count)):  #connect random nodes
                from_index = randint(0, node_count)
                to_index = randint(0, node_count)

                self.edges.append((self.nodes[from_index], self.nodes[to_index]))
                self.edge_buffer.append((self.sprites[from_index], self.sprites[to_index]))

            self.init_calculations()


        # first draw
        c_graphics.set_line_style(width = 0.5)

        if self.iteration < self.max_iterations:
            c_graphics.set_color("#aaa")
        else:
            c_graphics.set_color("#666")

        for edge in self.edge_buffer:
            context.move_to(edge[0].x, edge[0].y)
            context.line_to(edge[1].x, edge[1].y)
        context.stroke()


        # then recalculate positions
        if self.iteration <= self.max_iterations:
            for node in self.nodes:
                if not node.fixed:
                    self.repulsion(node)
                    self.gravitate(node)

            for edge in self.edges:
                self.atraction(edge)

            for node in self.nodes:
                if not node.fixed:
                    self.position(node)

            self.cooldown()

            # update image every x iterations
            if self.iteration % 10 == 0 or self.iteration == self.max_iterations:
                for i, node in enumerate(self.sprites):
                    self.tweener.killTweensOf(node)
                    self.animate(node, dict(x = self.nodes[i].x,
                                            y = self.nodes[i].y),
                                 easing = Easing.Expo.easeOut,
                                 duration = 1,
                                 instant = False)

            self.iteration +=1
            self.redraw_canvas()



    def repulsion(self, node):
        """calculate repulsion for the node"""
        node.vx, node.vy = 0, 0 # reset velocity back to zero

        for node2 in self.nodes:
            if node is node2 or node2.fixed:
                continue

            dx = node.x - node2.x
            dy = node.y - node2.y

            distance = max(EPSILON, math.sqrt(dx * dx + dy * dy))
            force = self.force_constant * self.force_constant / distance
            node.vx += dx / distance * force
            node.vy += dy / distance * force

    def atraction(self, edge):
        node1, node2 = edge

        dx = node1.x - node2.x
        dy = node1.y - node2.y

        distance = max(EPSILON, math.sqrt(dx * dx + dy * dy))
        force = distance * distance / self.force_constant

        node1.vx -= dx / distance * force
        node1.vy -= dy / distance * force

        node2.vx += dx / distance * force
        node2.vy += dy / distance * force

    def gravitate(self, node):
        dx = node.x - self.width / 2
        dy = node.y - self.height / 2

        distance = max(EPSILON, math.sqrt(dx * dx + dy * dy))
        force = distance * distance / self.force_constant * 0.9

        node.vx -= dx / distance * force
        node.vy -= dy / distance * force


    def position(self, node):
        distance = max(EPSILON, math.sqrt(node.vx * node.vx + node.vy * node.vy))

        node.x += node.vx / distance * min(distance, self.temperature)
        node.y += node.vy / distance * min(distance, self.temperature)

        # don't let nodes leave the display
        margin = self.width / 50.0

        if node.x < margin:
            node.x = margin + random() * margin * 2
        if node.x > self.width - margin:
            node.x = self.width - margin - random() * margin * 2

        if node.y < margin:
            node.y = margin + random() * margin * 2
        if node.y > self.height - margin:
            node.y = self.height - margin - random() * margin * 2



    # just for kicks - mouse events
    def on_drag(self, scene, target, coords):
        self.mouse_node = idx = self.sprites.index(target)
        # dragging around
        self.nodes[idx].fixed = True
        self.nodes[idx].x = coords[0]
        self.nodes[idx].y = coords[1]
        self.init_calculations()
        self.redraw_canvas()

    def on_mouse_up(self, scene):
        if self.mouse_node:
            self.nodes[self.mouse_node].fixed = False
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
            self.canvas.clear()
            self.canvas.nodes = []
            self.canvas.mouse_node = None
            self.canvas.redraw_canvas()
        button.connect("clicked", on_click)
        box.pack_start(button, False)


        window.add(box)
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    gtk.main()
