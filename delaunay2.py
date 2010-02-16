#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
 This one is based on code by Geoff Leach <gl@cs.rmit.edu.au> (29/3/96)
 Same delauney triangulation, just much more efficient.
 See here for original source and description:
 http://goanna.cs.rmit.edu.au/~gl/research/comp_geom/delaunay/delaunay.html
"""


import gtk
from lib import graphics
from lib.euclid import Point2, Vector2

import math
import itertools

EPSILON = 0.00001

class Node(graphics.Sprite):
    def __init__(self, x, y, point):
        graphics.Sprite.__init__(self, x, y)

        self.draw_node()
        self.point = point
        self.connect("on-drag", self.on_drag)
        self.draggable = True

    def on_drag(self, event, targets):
        self.point.x = event.x
        self.point.y = event.y
        self.draw_node()

    def draw_node(self):
        self.graphics.clear()
        self.graphics.set_color("#000")
        self.graphics.show_text("%d, %d" % (self.x, self.y))
        self.graphics.set_color("#000", 0)
        self.graphics.rectangle(0,0, 50, 20)
        self.graphics.stroke()


class Edge(object):
    def __init__(self, point1, point2):
        self.point1 = point1
        self.point2 = point2
        self.left_face = None
        self.right_face = None

    def update_left_face(self, point1, point2):
        if  (self.point1 != point1 and self.point2 != point2) \
        and (self.point2 != point1 and self.point1 != point2):
            return

        if (self.point1 == point1 and self.point2 == point2) and not self.left_face:
            self.left_face = 1
        elif (self.point2 == point1 and self.point1 == point2) and not self.right_face:
            self.right_face = 1
        else:
            pass
            #print "attempt to overwrite edge info", self.point1, self.point2, self.left_face, self.right_face



class Circle(Point2):
    def __init__(self, x = 0, y = 0, radius = 0):
        Point2.__init__(self, x, y)
        self.radius = radius

    def inside(self, point):
        return (self - point).magnitude_squared() < self.radius * self.radius


    def circumcircle(self, p1, p2, p3):
        v1 = p2 - p1
        v2 = p3 - p1

        cross = (p2 - p1).product(p3 - p1)

        if cross != 0:
            p1_sq = p1.magnitude_squared()
            p2_sq = p2.magnitude_squared()
            p3_sq = p3.magnitude_squared()

            num = p1_sq * (p2.y - p3.y) + p2_sq * (p3.y - p1.y) + p3_sq * (p1.y - p2.y)
            cx = num / (2.0 * cross)

            num = p1_sq * (p3.x - p2.x) + p2_sq * (p1.x - p3.x) + p3_sq * (p2.x - p1.x)
            cy = num / (2.0 * cross);

            self.x, self.y = cx, cy

        self.radius = (self - p1).magnitude()

        return self


class Canvas(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.nodes = []
        self.centres = []
        self.segments = []

        self.edges = []

        self.edge_dict = {}

        self.points = [] # [Vector2(-10000, -10000), Vector2(10000, -10000), Vector2(0, 10000)]



        self.connect("on-enter-frame", self.on_enter_frame)
        self.connect("on-click", self.on_mouse_click)
        self.connect("on-drag", self.on_node_drag)

        self.draw_circles = False

    def get_edge(self, point1, point2):
        return self.edge_dict.get((point1, point2), self.edge_dict.get((point2, point1)))

    def add_edge(self, p1, p2, left_face, right_face):
        exists = self.get_edge(p1, p2)
        if not exists:
            if p1 < p2:
                edge = Edge(p1, p2)
                edge.left_face = left_face
                edge.right_face = right_face
            else:
                edge = Edge(p2, p1)


            self.edges.append(edge)
            self.edge_dict[(p1, p2)] = edge
            return edge
        else:
            return exists

    def on_mouse_click(self, area, event, targets):
        if not targets:
            point = Vector2(event.x, event.y)
            self.points.append(point)

            node = Node(event.x, event.y, point)
            self.nodes.append(node)
            self.add_child(node)
            self.centres = []

            self.redraw_canvas()


    def on_node_drag(self, scene, node, coords):
        self.centres = []
        self.redraw_canvas()


    def on_enter_frame(self, scene, context):
        c_graphics = graphics.Graphics(context)
        c_graphics.set_line_style(width = 0.5)

        self.centres, self.segments = self.delauney()

        c_graphics.set_color("#666")
        for edge in self.segments:
            context.move_to(edge.point1.x, edge.point1.y)
            context.line_to(edge.point2.x, edge.point2.y)
        context.stroke()

        if self.draw_circles:
            for centre in self.centres:
                c_graphics.set_color("#f00", 0.1)
                context.arc(centre.x, centre.y, centre.radius, 0, 2.0 * math.pi)
                context.fill_preserve()
                context.stroke()

                c_graphics.set_color("#a00")
                context.rectangle(centre.x-1, centre.y-1, 2, 2)
                context.stroke()

    def add_triangle(self, p1, p2, p3):
        self.add_edge(p1, p2, None, None)
        self.add_edge(p2, p3, None, None)
        self.add_edge(p3, p1, None, None)


    def find_closest_neighbours(self):
        """finds two closest points on the screen"""
        res1, res2 = None, None
        min_distance = None

        for p1 in self.points:
            for p2 in self.points:
                if p1 == p2:
                    continue

                d = (p1 - p2).magnitude_squared()
                if not min_distance or d < min_distance:
                    res1, res2 = p1, p2
                    min_distance = d

        return res1, res2


    def delauney(self):
        self.edges = []
        self.edge_dict = {}
        self.centres = []

        p1, p2 = self.find_closest_neighbours()

        if not p1 or not p2:
            return [], []

        self.add_edge(p1, p2, None, None)


        current_edge = 0

        while current_edge < len(self.edges):
            current = self.edges[current_edge]
            if not current.left_face:
                self.complete_facet(current, current.point1, current.point2)
            if not current.right_face:
                self.complete_facet(current, current.point2, current.point1)

            current_edge += 1

        return self.centres, self.edges


    def complete_facet(self, edge, point1, point2):
        """
         * Complete a facet by looking for the circle free point to the left
         * of the edge "e_i".  Add the facet to the triangulation.
         *
         * This function is a bit long and may be better split.
        """


        # Find a point on left of edge.
        left_edge_point = None
        for point in self.points:
            if point in (point1, point2):
                continue

            if (point2 - point1).product(point - point1) > 0:
                left_edge_point = point
                break

        # Find best point on left of edge.
        best_point = left_edge_point

        if not best_point: # if there is nothing - update and go home
            edge.update_left_face(point1, point2)
            return

        if self.points.index(best_point) < len(self.points):
            best_point_centre = Circle()
            best_point_centre.circumcircle(point1, point2, best_point)


            for point_u in self.points:
                if point_u in (point1, point2, best_point):
                    continue

                product = (point2 - point1).dot((point_u - point1).cross())
                if product > 0 and best_point_centre.inside(point_u):
                    best_point = point_u
                    # move centre
                    best_point_centre.circumcircle(point1, point2, best_point)

            if best_point_centre not in self.centres:
                self.centres.append(best_point_centre)


        # Add new triangle or update edge info if s-t is on hull.
        # Update face information of edge being completed.
        edge.update_left_face(point1, point2)

        best_edge = self.get_edge(best_point, point1)
        if not best_edge:
            best_edge = self.add_edge(best_point, point1, 1, None)
        else:
            best_edge.update_left_face(best_point, point1)



        best_edge = self.get_edge(point2, best_point)
        if not best_edge:
            best_edge = self.add_edge(point2, best_point, 1, None)
        else:
            best_edge.update_left_face(point2, best_point)





class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(600, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())


        vbox = gtk.VBox()
        window.add(vbox)

        box = gtk.HBox()
        box.set_border_width(10)
        box.pack_start(gtk.Label("Add some points and observe Delauney triangulation"))
        vbox.pack_start(box, False)

        self.canvas = Canvas()
        vbox.pack_start(self.canvas)

        box = gtk.HBox(False, 4)
        box.set_border_width(10)

        vbox.pack_start(box, False)

        button = gtk.Button("Generate points in centers")
        def on_click(*args):
            for centre in self.canvas.centres:
                point = Vector2(centre.x, centre.y)
                self.canvas.points.append(point)
                node = Node(point.x, point.y, point)
                self.canvas.nodes.append(node)
                self.canvas.add_child(node)
            self.canvas.centres = []
            self.canvas.redraw_canvas()


        button.connect("clicked", on_click)
        box.pack_end(button, False)

        button = gtk.Button("Clear")
        def on_click(*args):
            self.canvas.nodes = []
            self.canvas.mouse_node, self.canvas.prev_mouse_node = None, None
            self.canvas.centres = []
            self.canvas.clear()
            self.canvas.redraw_canvas()

        button.connect("clicked", on_click)
        box.pack_end(button, False)




        button = gtk.CheckButton("show circumcenter")
        def on_click(button):
            self.canvas.draw_circles = button.get_active()
            self.canvas.redraw_canvas()

        button.connect("clicked", on_click)
        box.pack_start(button, False)


        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    gtk.main()
