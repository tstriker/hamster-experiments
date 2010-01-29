#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
 Flocking 2 - based on flocking and added the bin-latice spatial clustering
 with all the optimizations we are still way behind the processing version.
 Help me fixing the slow parts!

 * An implementation of Craig Reynold's Boids program to simulate
 * the flocking behavior of birds. Each boid steers itself based on
 * rules of avoidance, alignment, and coherence.
 *
 Parts of code ported from opensteer (http://sourceforge.net/projects/opensteer/)
 Other parts ported from processing (http://processing.org)
"""

import gtk

from lib import graphics
from lib.pytweener import Easing

import math
from random import random

from lib.euclid import Vector2, Point2
from lib.proximity import LQProximityStore



class Boid(object):
    radius = 3 # boid radius

    # distances are squared to avoid roots (slower)
    neighbour_distance = float(50**2)
    desired_separation = float(25**2)
    awareness = 50
    awareness_square = float(awareness * awareness)


    def __init__(self, location):
        self.acceleration = Vector2()
        self.velocity = Vector2(random() * 2 - 1, random() * 2 - 1)
        self.location = location;
        self.max_speed = 2.0
        self.max_force = 0.05
        self.max_steering_force = 0.005

        self.target_waypoint = None


    def draw(self, context):
        context.save()
        context.translate(self.location.x, self.location.y)

        #draw boid triangle
        theta = self.velocity.heading() + math.pi / 2
        context.rotate(theta)

        # draw awareness circle
        context.arc(0, 0, self.awareness, -math.pi, math.pi)

        context.move_to(0, -self.radius*2)
        context.line_to(-self.radius, self.radius * 2)
        context.line_to(self.radius, self.radius * 2)
        context.line_to(0, -self.radius*2)

        context.restore()


    def run(self, flock_boids, waypoints):
        if not self.target_waypoint:
            self.target_waypoint = waypoints[0]

        self.seek(self.target_waypoint)
        if flock_boids:
            self.acceleration += self.separate(flock_boids) * 2

        self.velocity += self.acceleration
        self.velocity.limit(self.max_speed)
        self.location += self.velocity

        if (self.location - self.target_waypoint).magnitude_squared() < 20 * 20:
            print "check"
            next = waypoints.index(self.target_waypoint) + 1
            if next >= len(waypoints):
                next = 0

            self.target_waypoint = waypoints[next]


    def separate(self, boids):
        sum = Vector2()
        in_zone = 0.0

        for boid, d in boids:
            if 0 < d < self.desired_separation:
                diff = self.location - boid.location
                diff.normalize()
                diff = diff / math.sqrt(d)  # Weight by distance
                sum += diff
                in_zone += 1

        if in_zone:
            sum = sum / in_zone

        return sum


    def seek(self, target):
        self.acceleration += self.steer(target, False)

    def arrive(self, target):
        self.acceleration += self.steer(target, True)

    def steer(self, target, slow_down):
        desired = target - self.location # A vector pointing from the location to the target

        d = desired.magnitude_squared()
        if d > 0:  # this means that we have a target
            desired.normalize()


            # Two options for desired vector magnitude (1 -- based on distance, 2 -- maxspeed)
            if  slow_down and d > self.braking_distance:
                desired *= self.max_speed * d / self.braking_distance # This damping is somewhat arbitrary
            else:
                desired *= self.max_speed

            steer = desired - self.velocity # Steering = Desired minus Velocity
            steer.limit(self.max_force) # Limit to maximum steering force
            return steer
        else:
            return Vector2()



class Canvas(graphics.Area):
    def __init__(self):
        graphics.Area.__init__(self)

        self.connect("mouse-move", self.on_mouse_move)
        self.connect("button-press", self.on_mouse_button_press)
        self.connect("mouse-click", self.on_mouse_click)

        # we should redo the boxes when window gets resized
        box_size = 10
        self.proximities = LQProximityStore(Vector2(0,0), Vector2(600,400), box_size)

        self.waypoints = [Vector2(200, 200), Vector2(300, 300), Vector2(500, 100)]

        self.boids = [Boid(Vector2(120,10))]
        self.mouse_node = None


    # just for kicks - mouse events
    def on_mouse_button_press(self, area, over_regions):
        if over_regions:
            self.mouse_node = over_regions[0]

    def on_mouse_click(self, area, coords, areas):
        if not areas:
            self.waypoints.append(Vector2(*coords))
            self.redraw_canvas()


    def on_mouse_move(self, area, coords, state):
        if self.mouse_node is not None:  #checking for none as there is the node zero
            if gtk.gdk.BUTTON1_MASK & state:
                # dragging around
                self.waypoints[self.mouse_node].x = coords[0]
                self.waypoints[self.mouse_node].y = coords[1]
                self.redraw_canvas()
            else:
                self.mouse_node = None


    def on_expose(self):
        # main loop (i should rename this to something more obvious)
        self.context.set_line_width(0.8)

        for boid in self.boids:
            neighbours = self.proximities.find_neighbours(boid, 40)

            boid.run(neighbours, self.waypoints)

            self.proximities.update_position(boid)

            self.set_color("#ddd")
            self.context.arc(boid.location.x,
                             boid.location.y,
                             boid.awareness,
                             -math.pi, math.pi)
            self.context.fill()
            self.set_color("#666")
            boid.draw(self.context)
            self.context.stroke()


        self.set_color("#999")
        for i, waypoint in enumerate(self.waypoints):
            self.draw_rect(waypoint.x - 4, waypoint.y - 4, 8, 8, 2)
            self.register_mouse_region(waypoint.x - 4, waypoint.y - 4, waypoint.x + 4, waypoint.y + 4, i)
            self.context.fill()

        self.redraw_canvas()








class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(600, 400)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        canvas = Canvas()

        box = gtk.VBox()
        box.pack_start(canvas)


        window.add(box)
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    gtk.main()
