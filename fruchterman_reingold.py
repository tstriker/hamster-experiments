#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
 Ported from prefuse (http://prefuse.org/).
 Extra:
   * added node gravitation towards centre
   * buffering node positions and tweening every 10 frames or so to avoid stuttering

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


class Canvas(graphics.Area):
    def __init__(self):
        graphics.Area.__init__(self)
        self.nodes = []
        self.edges = []
        
        self.node_buffer = []
        self.edge_buffer = []
        
        self.max_iterations = 300
        self.iteration = 0
        self.force_constant = 0
        self.connect("mouse-move", self.on_mouse_move)
        self.connect("button-press", self.on_mouse_button_press)
        
        self.mouse_node = None
        self.prev_mouse_node = None

    def init_calculations(self):
        self.iteration = 0
        self.force_constant = 0.7 *  math.sqrt(self.height * self.width / len(self.nodes))
        self.temperature = self.width / float(10)

    def on_expose(self):
        if not self.nodes:
            for i in range(50):
                x, y = self.width / 2, self.height / 2
                scale_w = ALPHA * x;
                scale_h = ALPHA * y

                self.nodes.append(Node(x + (random() - 0.5) * 2 * scale_w,
                                       y + (random() - 0.5) * 2 * scale_h))

            self.node_buffer = deepcopy(self.nodes) # copy
                
            node_count = len(self.nodes) - 1
            
            for i in range(30):  #connect random nodes
                from_index = randint(0, node_count)
                to_index = randint(0, node_count)

                self.edges.append((self.nodes[from_index], self.nodes[to_index]))
                self.edge_buffer.append((self.node_buffer[from_index], self.node_buffer[to_index]))
            
            self.init_calculations()

        # first draw        
        self.context.set_line_width(0.5)
        if self.iteration < self.max_iterations:
            self.set_color("#aaaaaa")
        else:
            self.set_color("#999999")

        for i, node in enumerate(self.node_buffer):
            self.draw_node(node)
            self.register_mouse_region(node.x - 5, node.y - 5, node.x + 5, node.y + 5, i)
            self.context.fill()

        for edge in self.edge_buffer:
            self.context.move_to(edge[0].x, edge[0].y)
            self.context.line_to(edge[1].x, edge[1].y)

        self.context.stroke()


        # then recalculate positions
        if self.iteration <= self.max_iterations:
            for node in self.nodes:
                if not node.fixed:
                    self.repulsion(node)

            for node in self.nodes:
                if not node.fixed:
                    self.gravitate(node)

            for edge in self.edges:
                self.atraction(edge)
    
            for node in self.nodes:
                if not node.fixed:
                    self.position(node)
    
            self.cooldown()
            
            # update image every x iterations
            if self.iteration % 10 == 0 or self.iteration == self.max_iterations:
                for i, node in enumerate(self.node_buffer):
                    self.tweener.killTweensOf(node)
                    self.animate(node, dict(x = self.nodes[i].x,
                                            y = self.nodes[i].y),
                                 easing = Easing.Expo.easeOut,
                                 duration = 1,
                                 instant = False)

            self.iteration +=1
            self.redraw_canvas()


    def draw_node(self, node):
        self.context.arc(node.x, node.y, 5, 0, 2.0 * math.pi)

        
    def repulsion(self, node):
        """calculate repulsion for the node"""
        node.vx, node.vy = 0, 0 # reset velocity back to zero

        for node2 in self.nodes:
            if node is node2 or node2.fixed:
                continue
            
            dx = node.x - node2.x
            dy = node.y - node2.y
            
            distance = max(EPSILON, math.sqrt(dx**2 + dy**2))
            force = self.force_constant **2 / distance
            node.vx += dx / distance * force
            node.vy += dy / distance * force

    def atraction(self, edge):
        node1, node2 = edge
        
        dx = node1.x - node2.x
        dy = node1.y - node2.y
        
        distance = max(EPSILON, math.sqrt(dx**2 + dy**2))
        force = distance **2 / self.force_constant

        node1.vx -= dx / distance * force
        node1.vy -= dy / distance * force
        
        node2.vx += dx / distance * force
        node2.vy += dy / distance * force

    def gravitate(self, node):
        dx = node.x - self.width / 2
        dy = node.y - self.height / 2
        
        distance = max(EPSILON, math.sqrt(dx**2 + dy**2))
        force = distance **2 / self.force_constant * 0.5

        node.vx -= dx / distance * force
        node.vy -= dy / distance * force


    def position(self, node):
        distance = max(EPSILON, math.sqrt(node.vx**2 + node.vy**2))
        
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
            
        

    def cooldown(self):
        self.temperature = self.temperature * (1.0 - self.iteration / float(self.max_iterations))


    # just for kicks - mouse events
    def on_mouse_button_press(self, area, over_regions):
        if self.prev_mouse_node is not None:
            self.nodes[self.prev_mouse_node].fixed = False
        if over_regions:
            self.mouse_node = over_regions[0]
        else:
            self.mouse_node = None

    def on_mouse_move(self, area, coords, state):
        if self.mouse_node is not None:  #checking for none as there is the node zero
            if gtk.gdk.BUTTON1_MASK & state:
                # dragging around
                self.nodes[self.mouse_node].fixed = True
                self.nodes[self.mouse_node].x = self.node_buffer[self.mouse_node].x = coords[0]
                self.nodes[self.mouse_node].y = self.node_buffer[self.mouse_node].y = coords[1]
                self.init_calculations()
                self.redraw_canvas()
            else:
                # release the node
                if self.mouse_node:
                    self.prev_mouse_node = self.mouse_node
                    
                self.mouse_node = None
    
class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_title("Graphics Module")
        window.set_size_request(600, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())
    
        canvas = Canvas()
        
        box = gtk.VBox()
        box.pack_start(canvas)
        
    
        window.add(box)
        window.show_all()
        
        
if __name__ == "__main__":
    example = BasicWindow()
    gtk.main()

