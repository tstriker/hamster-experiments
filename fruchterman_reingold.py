#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
 Frankensteined together from everywhere, including prefuse (http://prefuse.org/),
 heygraph (http://www.heychinaski.com/blog/?p=288) and this monstrosity
 (http://www.mathiasbader.de/studium/bioinformatics/)
"""


from gi.repository import Gtk as gtk
from lib import graphics
from lib.pytweener import Easing

import math
from random import random, randint
from copy import deepcopy

class Node(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.fixed = False #to pin down
        self.cluster = None
        self.neighbours = []


class Graph(object):
    """graph lives on it's own, separated from display"""
    def __init__(self, area_w, area_h):
        self.nodes = []
        self.edges = []
        self.clusters = []
        self.iteration = 0
        self.force_constant = 0
        self.init_layout(area_w, area_h)
        self.graph_bounds = None

    def populate_nodes(self, area_w, area_h):
        self.nodes, self.edges, self.clusters = [], [], []

        # nodes
        for i in range(randint(5, 30)):
            x, y = area_w / 2, area_h / 2
            scale_w = x * 0.2;
            scale_h = y * 0.2

            node = Node(x + (random() - 0.5) * 2 * scale_w,
                        y + (random() - 0.5) * 2 * scale_h)
            self.nodes.append(node)

        # edges
        node_count = len(self.nodes) - 1

        for i in range(randint(node_count / 3, node_count)):  #connect random nodes
            idx1, idx2 = randint(0, node_count), randint(0, node_count)
            node1 = self.nodes[idx1]
            node2 = self.nodes[idx2]

            self.add_edge(node1, node2)

    def add_edge(self, node, node2):
        if node == node2 or (node, node2) in self.edges or (node2, node) in self.edges:
            return

        self.edges.append((node, node2))
        node.neighbours.append(node2)
        node2.neighbours.append(node)

    def remove_edge(self, node, node2):
        if (node, node2) in self.edges:
            self.edges.remove((node, node2))
            node.neighbours.remove(node2)
            node2.neighbours.remove(node)

    def init_layout(self, area_w, area_h):
        if not self.nodes:
            self.nodes.append(Node(area_w / 2, area_h / 2))

        # cluster
        self.clusters = []
        for node in self.nodes:
            node.cluster = None

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
        # init forces
        self.force_constant = math.sqrt(area_h * area_w / float(len(self.nodes)))
        self.temperature = len(self.nodes) + math.floor(math.sqrt(len(self.edges)))
        self.minimum_temperature = 1
        self.initial_temperature = self.temperature
        self.iteration = 0


    def update(self, area_w, area_h):
        self.node_repulsion()
        self.atraction()
        self.cluster_repulsion()
        self.position()

        self.iteration +=1
        self.temperature = max(self.temperature - (self.initial_temperature / 100), self.minimum_temperature)


        # update temperature every ten iterations
        if self.iteration % 10 == 0:
            min_x, min_y, max_x, max_y = self.graph_bounds

            graph_w, graph_h = max_x - min_x, max_y - min_y
            graph_magnitude = math.sqrt(graph_w * graph_w + graph_h * graph_h)
            canvas_magnitude = math.sqrt(area_w * area_w + area_h * area_h)

            self.minimum_temperature = graph_magnitude / canvas_magnitude

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



    def position(self):
        biggest_move = -1

        x1, y1, x2, y2 = 100000, 100000, -100000, -100000

        for node in self.nodes:
            if node.fixed:
                node.fixed = False
                continue

            distance = math.sqrt(node.vx * node.vx + node.vy * node.vy)

            if distance:
                node.x += node.vx / distance * min(abs(node.vx), self.temperature)
                node.y += node.vy / distance * min(abs(node.vy), self.temperature)

            x1, y1 = min(x1, node.x), min(y1, node.y)
            x2, y2 = max(x2, node.x), max(y2, node.y)

        self.graph_bounds = (x1,y1,x2,y2)

    def bounds(self, nodes):
        x1, y1, x2, y2 = 100000, 100000, -100000, -100000
        for node in nodes:
            x1, y1 = min(x1, node.x), min(y1, node.y)
            x2, y2 = max(x2, node.x), max(y2, node.y)

        return (x1, y1, x2, y2)



class DisplayNode(graphics.Sprite):
    def __init__(self, x, y, real_node):
        graphics.Sprite.__init__(self, x=x, y=y, interactive=True, draggable=True)
        self.real_node = real_node
        self.fill = "#999"

        self.connect("on-mouse-over", self.on_mouse_over)
        self.connect("on-mouse-out", self.on_mouse_out)
        self.connect("on-render", self.on_render)

    def on_mouse_over(self, sprite):
        self.fill = "#000"

    def on_mouse_out(self, sprite):
        self.fill = "#999"

    def on_render(self, sprite):
        self.graphics.clear()
        self.graphics.arc(0, 0, 5, 0, math.pi * 2)
        self.graphics.fill(self.fill)

        # adding invisible circle with bigger radius for easier targeting
        self.graphics.arc(0, 0, 10, 0, math.pi * 2)
        self.graphics.stroke("#000", 0)



class Canvas(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.edge_buffer = []
        self.clusters = []

        self.connect("on-enter-frame", self.on_enter_frame)
        self.connect("on-finish-frame", self.on_finish_frame)
        self.connect("on-click", self.on_node_click)
        self.connect("on-drag", self.on_node_drag)
        self.connect("on-mouse-move", self.on_mouse_move)

        self.mouse_node = None
        self.mouse = None
        self.graph = None
        self.redo_layout = False
        self.display_nodes = []


    def on_node_click(self, scene, event,  sprite):

        mouse_node = sprite

        if mouse_node:
            if self.mouse_node:
                if mouse_node == self.mouse_node:
                    self.mouse_node = None
                    return


                #check if maybe there is an edge already - in that case remove it
                if (self.mouse_node.real_node, mouse_node.real_node) in self.graph.edges:
                    self.graph.remove_edge(self.mouse_node.real_node, mouse_node.real_node)

                elif (mouse_node.real_node, self.mouse_node.real_node) in self.graph.edges:
                    self.graph.remove_edge(mouse_node.real_node, self.mouse_node.real_node)

                else:
                    self.graph.add_edge(self.mouse_node.real_node, mouse_node.real_node)

                self.update_buffer()

                if event.button != 3:
                    self.mouse_node = mouse_node
                else:
                    self.mouse_node = None

                self.queue_relayout()
            else:
                self.mouse_node = mouse_node
        else:
            if event.button == 3:
                self.mouse_node = None
            else:
                new_node = Node(*self.screen_to_graph(event.x, event.y))
                self.graph.nodes.append(new_node)
                display_node = self.add_node(event.x, event.y, new_node)

                if self.mouse_node:
                    self.graph.add_edge(self.mouse_node.real_node, new_node)
                    self.update_buffer()

                self.mouse_node = display_node


            self.queue_relayout()

    def on_node_drag(self, scene, node, event):
        node.real_node.x, node.real_node.y = self.screen_to_graph(event.x, event.y)
        node.real_node.fixed = True
        self.redraw()


    def on_mouse_move(self, scene, event):
        self.mouse = (event.x, event.y)
        self.queue_relayout()


    def delauney(self):
        pass

    def add_node(self, x, y, real_node):
        display_node = DisplayNode(x, y, real_node)
        self.add_child(display_node)
        self.display_nodes.append(display_node)
        return display_node


    def new_graph(self):
        self.clear()
        self.display_nodes = []
        self.add_child(graphics.Label("Click on screen to add node. Right-click to stop the thread from going on", color="#666", x=10, y=10))


        self.edge_buffer = []

        if not self.graph:
            self.graph = Graph(self.width, self.height)
        else:
            self.graph.populate_nodes(self.width, self.height)
            self.queue_relayout()

        for node in self.graph.nodes:
            self.add_node(node.x, node.y, node)

        self.update_buffer()

        self.redraw()

    def queue_relayout(self):
        self.redo_layout = True
        self.redraw()

    def update_buffer(self):
        self.edge_buffer = []

        for edge in self.graph.edges:
            self.edge_buffer.append((
                self.display_nodes[self.graph.nodes.index(edge[0])],
                self.display_nodes[self.graph.nodes.index(edge[1])],
            ))


    def on_finish_frame(self, scene, context):
        if self.mouse_node and self.mouse:
            c_graphics = graphics.Graphics(context)
            c_graphics.set_color("#666")
            c_graphics.move_to(self.mouse_node.x, self.mouse_node.y)
            c_graphics.line_to(*self.mouse)
            c_graphics.stroke()


    def on_enter_frame(self, scene, context):
        c_graphics = graphics.Graphics(context)

        if not self.graph:
            self.new_graph()
            self.graph.update(self.width, self.height)


        if self.redo_layout:
            self.redo_layout = False
            self.graph.init_layout(self.width, self.height)


        # first draw
        c_graphics.set_line_style(width = 0.5)

        done = abs(self.graph.minimum_temperature - self.graph.temperature) < 0.05


        if not done:
            c_graphics.set_color("#aaa")
        else:
            c_graphics.set_color("#666")

        for edge in self.edge_buffer:
            context.move_to(edge[0].x, edge[0].y)
            context.line_to(edge[1].x, edge[1].y)
        context.stroke()


        if not done:
            # then recalculate positions
            self.graph.update(self.width, self.height)

            # find bounds
            min_x, min_y, max_x, max_y = self.graph.graph_bounds
            graph_w, graph_h = max_x - min_x, max_y - min_y

            factor_x = self.width / float(graph_w)
            factor_y = self.height / float(graph_h)
            graph_mid_x = (min_x + max_x) / 2.0
            graph_mid_y = (min_y + max_y) / 2.0

            mid_x, mid_y = self.width / 2.0, self.height / 2.0

            factor = min(factor_x, factor_y) * 0.9 # just have the smaller scale, avoid deformations

            for i, node in enumerate(self.display_nodes):
                self.tweener.kill_tweens(node)
                self.animate(node,
                             x = mid_x + (self.graph.nodes[i].x - graph_mid_x) * factor,
                             y = mid_y + (self.graph.nodes[i].y - graph_mid_y) * factor,
                             easing = Easing.Expo.ease_out,
                             duration = 3)


            self.redraw()

    def screen_to_graph(self,x, y):
        if len(self.graph.nodes) <= 1:
            return x, y



        min_x, min_y, max_x, max_y = self.graph.graph_bounds
        graph_w, graph_h = max_x - min_x, max_y - min_y

        factor_x = self.width / float(graph_w)
        factor_y = self.height / float(graph_h)
        graph_mid_x = (min_x + max_x) / 2.0
        graph_mid_y = (min_y + max_y) / 2.0

        mid_x, mid_y = self.width / 2.0, self.height / 2.0

        factor = min(factor_x, factor_y) * 0.9 # just have the smaller scale, avoid deformations

        graph_x = (x - mid_x) / factor + graph_mid_x
        graph_y = (y - mid_y) / factor + graph_mid_y

        return graph_x, graph_y


    def graph_to_screen(self,x, y):
        pass


class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_size_request(600, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        self.canvas = Canvas()

        box = gtk.VBox()
        box.add(self.canvas)

        """
        hbox = gtk.HBox(False, 5)
        hbox.set_border_width(12)

        box.pack_start(hbox, False)

        hbox.pack_start(gtk.HBox()) # filler
        button = gtk.Button("Random Nodes")
        button.connect("clicked", lambda *args: self.canvas.new_graph())
        hbox.pack_start(button, False)
        """

        window.add(box)
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
