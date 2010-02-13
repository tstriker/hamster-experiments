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
        self.cluster = None
        self.neighbours = []

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
        self.edge_buffer = []
        self.clusters = []

        self.iteration = 0
        self.force_constant = 0
        self.connect("on-drag", self.on_drag)
        self.connect("on-mouse-up", self.on_mouse_up)

        self.connect("on-enter-frame", self.on_enter_frame)
        self.connect("on-finish-frame", self.on_finish_frame)

        self.mouse_node = None

    def init_calculations(self):
        self.force_constant = math.sqrt(self.height * self.width / float(len(self.nodes)))
        self.temperature = len(self.nodes) + math.floor(math.sqrt(len(self.edges)))
        self.minimum_temperature = 1
        self.initial_temperature = self.temperature
        self.iteration = 0

    def on_finish_frame(self, scene, context):
        context.fill()


    def populate_nodes(self):
        self.nodes, self.edges, self.clusters = [], [], []
        self.edge_buffer = []

        # nodes
        for i in range(randint(5, 30)):
            x, y = self.width / 2, self.height / 2
            scale_w = ALPHA * x;
            scale_h = ALPHA * y

            node = Node(x + (random() - 0.5) * 2 * scale_w,
                                   y + (random() - 0.5) * 2 * scale_h)
            self.nodes.append(node)

            display_node = DisplayNode(node.x, node.y, node)
            self.add_child(display_node)

        # edges
        node_count = len(self.nodes) - 1

        for i in range(randint(node_count / 3, node_count)):  #connect random nodes
            idx1, idx2 = randint(0, node_count), randint(0, node_count)
            node1 = self.nodes[idx1]
            node2 = self.nodes[idx2]
            if node1 == node2:
                continue

            self.edges.append((node1, node2))
            self.edge_buffer.append((self.sprites[idx1], self.sprites[idx2]))
            node1.neighbours.append(node2)
            node2.neighbours.append(node1)

        # clusters
        all_nodes = list(self.nodes)

        def set_cluster(node, cluster):
            if not node.cluster:
                node.cluster = cluster
                cluster.append(node)
                all_nodes.remove(node)
                for node2 in node.neighbours:
                    set_cluster(node2, cluster)

        while all_nodes:
            node = all_nodes[0]
            if not node.cluster:
                new_cluster = []
                self.clusters.append(new_cluster)
                set_cluster(node, new_cluster)


    def on_enter_frame(self, scene, context):
        c_graphics = graphics.Graphics(context)

        if not self.nodes:
            self.populate_nodes()
            self.init_calculations()


        # first draw
        c_graphics.set_line_style(width = 0.5)

        done = abs(self.minimum_temperature - self.temperature) < 0.05


        if not done:
            c_graphics.set_color("#aaa")
        else:
            c_graphics.set_color("#666")

        for edge in self.edge_buffer:
            context.move_to(edge[0].x, edge[0].y)
            context.line_to(edge[1].x, edge[1].y)
        context.stroke()


        # then recalculate positions
        if not done:
            self.node_repulsion()
            self.atraction()
            self.cluster_repulsion()
            self.position()

            self.iteration +=1
            self.temperature = max(self.temperature - (self.initial_temperature / 100), self.minimum_temperature)


            # update image every x iterations
            if self.iteration % 10 == 0:
                self.is_layout_done()

                # find bounds
                min_x, min_y, max_x, max_y = self.bounds(self.nodes)

                factor_x = float(self.width) / (max_x - min_x)
                factor_y = float(self.height) / (max_y - min_y)
                factor = min(factor_x, factor_y) * 0.9
                start_x = (self.width - (max_x - min_x) * factor) / 2
                start_y = (self.height - (max_y - min_y) * factor) / 2

                """
                for i, node in enumerate(self.sprites):
                    adjusted_x = (self.nodes[i].x - min_x) * factor
                    adjusted_y = (self.nodes[i].y - min_y) * factor
                    node.x = adjusted_x
                    node.y = adjusted_y
                """

                for i, node in enumerate(self.sprites):
                    self.tweener.killTweensOf(node)
                    self.animate(node, dict(x = (self.nodes[i].x - min_x) * factor + start_x,
                                            y = (self.nodes[i].y - min_y) * factor + start_y),
                                 easing = Easing.Expo.easeOut,
                                 duration = 1,
                                 instant = False)

            self.redraw_canvas()

    def bounds(self, nodes):
        x1, y1, x2, y2 = 1000, 1000, -1000, -1000
        for node in nodes:
            x1, y1 = min(x1, node.x), min(y1, node.y)
            x2, y2 = max(x2, node.x), max(y2, node.y)

        return (x1, y1, x2, y2)


    def cluster_repulsion(self):
        """push around unconnected nodes on overlap"""
        for cluster in self.clusters:
            ax1, ay1, ax2, ay2 = self.bounds(cluster)

            for cluster2 in self.clusters:
                if cluster == cluster2:
                    continue

                bx1, by1, bx2, by2 = self.bounds(cluster2)

                if (bx1 <= ax1 <= bx2 or bx1 <= ax2 <= bx2) \
                and (by1 <= ay1 <= by2 or by1 <= ay2 <= by2):

                    dx = (ax1 + ax2) / 2 - (bx1 + bx2) / 2
                    dy = (ay1 + ay2) / 2 - (by1 + by2) / 2

                    max_d = float(max(abs(dx), abs(dy)))

                    dx, dy = dx / max_d, dy / max_d

                    force_x = dx * random() * 100
                    force_y = dy * random() * 100

                    for node in cluster:
                        node.x += force_x
                        node.y += force_y

                    for node in cluster2:
                        node.x -= force_x
                        node.y -= force_y

    def node_repulsion(self):
        """calculate repulsion for the node"""

        for node in self.nodes:
            node.vx, node.vy = 0, 0 # reset velocity back to zero

            for node2 in node.cluster:
                if node == node2: continue

                dx = node.x - node2.x
                dy = node.y - node2.y

                magnitude = math.sqrt(dx * dx + dy * dy)


                if magnitude:
                    force = self.force_constant * self.force_constant / magnitude
                    node.vx += dx / magnitude * force
                    node.vy += dy / magnitude * force



    def atraction(self):
        for edge in self.edges:
            node1, node2 = edge

            dx = node1.x - node2.x
            dy = node1.y - node2.y

            distance = math.sqrt(dx * dx + dy * dy)
            if distance:
                force = distance * distance / self.force_constant

                node1.vx -= dx / distance * force
                node1.vy -= dy / distance * force

                node2.vx += dx / distance * force
                node2.vy += dy / distance * force



    def is_layout_done(self):
        totalChange = 0

        min_x, min_y, max_x, max_y = 10000, 10000, -10000, -10000
        for node in self.nodes:
            min_x, min_y = min(min_x, node.x), min(min_y, node.y)
            max_x, max_y = max(max_x, node.x), max(max_y, node.y)


        graph_w, graph_h = max_x - min_x, max_y - min_y
        graph_magnitude = math.sqrt(graph_w * graph_w + graph_h * graph_h)
        canvas_magnitude = math.sqrt(self.width * self.width + self.height * self.height)

        self.minimum_temperature = graph_magnitude / canvas_magnitude



    def position(self):
        biggest_move = -1

        for node in self.nodes:
            distance = math.sqrt(node.vx * node.vx + node.vy * node.vy)

            if distance:
                node.x += node.vx / distance * min(abs(node.vx), self.temperature)
                node.y += node.vy / distance * min(abs(node.vy), self.temperature)



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
            self.canvas.populate_nodes()
            self.canvas.init_calculations()
            self.canvas.redraw_canvas()
        button.connect("clicked", on_click)
        box.pack_start(button, False)

        button = gtk.Button("Repeat Layout")
        def on_click(*args):
            self.canvas.init_calculations()
            self.canvas.redraw_canvas()
        button.connect("clicked", on_click)
        box.pack_start(button, False)

        window.add(box)
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    gtk.main()
