#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
 This one is based on code by Geoff Leach <gl@cs.rmit.edu.au> (29/3/96)
 Same delaunay triangulation, just much more efficient.
 See here for original source and description:
 http://goanna.cs.rmit.edu.au/~gl/research/comp_geom/delaunay/delaunay.html
"""


from gi.repository import Gtk as gtk
from lib import graphics
from contrib.euclid import Point2, Vector2

import math
import itertools
import collections

EPSILON = 0.00001

class Node(graphics.Sprite):
    def __init__(self, x, y, point):
        graphics.Sprite.__init__(self, x, y, interactive=True, draggable=True)

        self.draw_node()
        self.point = point
        self.connect("on-drag", self.on_drag)

    def on_drag(self, sprite, event):
        self.point.x = event.x
        self.point.y = event.y
        self.draw_node()

    def draw_node(self):
        self.graphics.clear()
        self.graphics.set_color("#999")
        self.graphics.rectangle(-5,-5, 10, 10, 3)
        self.graphics.fill()


class Edge(object):
    def __init__(self, point1, point2):
        self.point1 = point1
        self.point2 = point2
        self.left_face = None
        self.right_face = None

    def update_left_face(self, point1, point2, face):
        if set((self.point1, self.point2)) - set((point1, point2)):
            return # have been asked to update, but these are not our points

        if point1 == self.point1 and self.left_face is None:
            self.left_face = face
        elif point1 == self.point2 and self.right_face is None:
            self.right_face = face




class Circle(Point2):
    def __init__(self, x = 0, y = 0, radius = 0):
        Point2.__init__(self, x, y)
        self.radius = radius

    def covers(self, point):
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

        self.edges = []

        self.edge_dict = {}

        self.points = [] # [Vector2(-10000, -10000), Vector2(10000, -10000), Vector2(0, 10000)]



        self.connect("on-enter-frame", self.on_enter_frame)
        self.connect("on-click", self.on_mouse_click)
        self.connect("on-drag", self.on_node_drag)


        self.add_child(graphics.Label("Add some points and observe Delaunay triangulation", x = 5, y = 5, color = "#666"))

        self.draw_circles = False


    def add_edge(self, p1, p2):
        exists = self.edge_dict.get((p1, p2), self.edge_dict.get((p2, p1)))
        if not exists:
            edge = Edge(p1, p2)

            self.edges.append(edge)
            self.edge_dict[(p1, p2)] = edge
            return edge, True
        else:
            return exists, False


    def find_triangles(self):
        # run through edges and detect triangles
        for edge in self.edges:
            pass

    def triangulate(self):
        self.edges = []
        self.edge_dict = {}
        self.centres = []

        # find closest neighbours for the seed
        neighbours = None
        min_distance = None

        for p1 in self.points:
            for p2 in self.points:
                if p1 == p2: continue

                d = (p1 - p2).magnitude_squared()
                if not min_distance or d < min_distance:
                    neighbours = p1, p2
                    min_distance = d

        if not neighbours:
            return

        seed, new = self.add_edge(*neighbours)


        edges = collections.deque([seed])
        self.face_num = 0
        while edges:
            current = edges.popleft()

            if not current.left_face:
                edges.extend(self.check_edge(current, current.point1, current.point2))

            if not current.right_face:
                edges.extend(self.check_edge(current, current.point2, current.point1))


    def check_edge(self, edge, point1, point2):
        """
         * Complete a facet by looking for the circle free point to the left
         * of the edge.  Add the facet to the triangulation.
        """

        positive_products = (point for point in self.points if point not in (point1, point2) \
                                                           and (point2 - point1).product(point - point1) > 0)

        # Find a point on left of edge.
        try:
            left_point = positive_products.next()
            left_point_circumcentre = Circle()
            left_point_circumcentre.circumcircle(point1, point2, left_point)
        except StopIteration:
            edge.update_left_face(point1, point2, 0)
            return [] #did not find anything

        # now from all the left side points find the one that is circle-free
        for point in positive_products:
            if left_point_circumcentre.covers(point):
                # move centre
                left_point_circumcentre.circumcircle(point1, point2, point)
                left_point = point

        # now that we are done, add our successful candidate to the centres
        if left_point_circumcentre not in self.centres:
            self.centres.append(left_point_circumcentre)
            self.face_num +=1


        # Add new triangle or update edge info if s-t is on hull.
        # Update face information of edge being completed.
        edge.update_left_face(point1, point2, self.face_num)

        # connect the dots
        res = []

        edge1, new = self.add_edge(left_point, point1)
        edge1.update_left_face(left_point, point1, self.face_num)
        if new: res.append(edge1)


        edge2, new = self.add_edge(point2, left_point)
        edge2.update_left_face(point2, left_point, self.face_num)
        if new: res.append(edge2)


        return res


    def on_mouse_click(self, area, event, target):
        if not target:
            point = Vector2(event.x, event.y)
            self.points.append(point)

            node = Node(event.x, event.y, point)
            self.nodes.append(node)
            self.add_child(node)
            self.centres = []

            self.triangulate()

            self.redraw()

    def on_node_drag(self, scene, node, event):
        self.centres = []
        self.redraw()


    def on_enter_frame(self, scene, context):
        g = graphics.Graphics(context)
        g.set_line_style(width = 0.5)

        self.triangulate()

        g.set_color("#666")
        for edge in self.edges:
            context.move_to(edge.point1.x, edge.point1.y)
            context.line_to(edge.point2.x, edge.point2.y)

            context.save()
            context.translate((edge.point1.x + edge.point2.x) / 2, (edge.point1.y + edge.point2.y) / 2)
            context.save()
            context.rotate((edge.point2 - edge.point1).heading())
            context.move_to(-5, 0)
            g.show_label(str(edge.left_face))
            context.restore()

            context.save()
            context.rotate((edge.point1 - edge.point2).heading())
            context.move_to(-5, 0)
            g.show_label(str(edge.right_face))
            context.restore()

            context.restore()

        context.stroke()

        if self.draw_circles:
            for centre in self.centres:
                g.set_color("#f00", 0.1)
                context.arc(centre.x, centre.y, centre.radius, 0, 2.0 * math.pi)
                context.fill_preserve()
                context.stroke()

                g.set_color("#a00")
                context.rectangle(centre.x-1, centre.y-1, 2, 2)
                context.stroke()



class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_default_size(600, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())


        vbox = gtk.VBox()
        window.add(vbox)

        box = gtk.HBox()
        vbox.pack_start(box, False, False, 0)

        self.canvas = Canvas()
        vbox.add(self.canvas)

        box = gtk.HBox(False, 4)

        vbox.pack_start(box, False, False, 0)

        button = gtk.Button("Generate points in centers")
        def on_click(*args):
            for centre in self.canvas.centres:
                if abs(centre) < 2000:
                    point = Vector2(centre.x, centre.y)
                    self.canvas.points.append(point)
                    node = Node(point.x, point.y, point)
                    self.canvas.nodes.append(node)
                    self.canvas.add_child(node)
            self.canvas.centres = []
            self.canvas.redraw()


        button.connect("clicked", on_click)
        box.pack_end(button, False, False, 0)

        button = gtk.Button("Clear")
        def on_click(*args):
            self.canvas.points = []
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
