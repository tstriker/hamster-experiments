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

class Waypoint(object):
    def __init__(self, x, y):
        self.location = Vector2(x, y)

    def see_you(self, boid):
        # boid calls waypoint when he sees it
        # normally we just tell it to go on
        if boid.data and "reverse" in boid.data:
            boid.target(self.previous)
        else:
            boid.target(self.next)

class BucketWaypoint(Waypoint):
    """waypoint that will queue our friends until required number
       arrives and then let them go"""
    def __init__(self, x, y, bucket_size):
        Waypoint.__init__(self, x, y)
        self.bucket_size = bucket_size
        self.boids = []
        self.rotation_angle = 0


    def see_you(self, boid):
        # boid calls waypoint when he sees it
        # normally we just tell it to go on
        if boid not in self.boids and (self.location - boid.location).magnitude_squared() < 400:
            print "got one"
            self.boids.append(boid)
        else: #start braking
            boid.velocity *= 0.9

        if len(self.boids) == self.bucket_size:
            for boid in self.boids:
                self.move_on(boid)

            self.boids = []

        self.rotation_angle += 0.02
        angle_step = math.pi * 2 / (self.bucket_size - 1)
        current_angle = 0
        for boid in self.boids:
            current_angle += angle_step
            boid.location.x = self.location.x + math.cos(self.rotation_angle + current_angle) * 20
            boid.location.y = self.location.y + math.sin(self.rotation_angle + current_angle) * 20
            boid.velocity = (self.location - boid.location) * 0.01


    def move_on(self, boid):
        if boid.data and "reverse" in boid.data:
            boid.target(self.previous)
        else:
            boid.target(self.next)



class Boid(object):
    radius = 3 # boid radius

    # distances are squared to avoid roots (slower)
    separation = 15.0 # separation from other objects
    awareness = 30.0  # the sense field
    separation_squared = separation * separation
    awareness_squared = awareness * awareness


    def __init__(self, location):
        self.acceleration = Vector2()
        self.brake = Vector2()
        self.velocity = Vector2(random() * 2 - 1, random() * 2 - 1)
        self.location = location
        self.max_speed = 2.0
        self.max_force = 0.03
        self.positions = []
        self.message = None # a message that waypoint has set perhaps
        self.data = None

        self.radio = self.awareness

        self.target_waypoint = None

    def target(self, waypoint):
        self.target_waypoint = waypoint

    def run(self, flock_boids):
        if flock_boids:
            self.acceleration += self.separate(flock_boids) * 2

        self.seek(self.target_waypoint.location)

        self.velocity += self.acceleration




        if (self.location - self.target_waypoint.location).magnitude_squared() < self.radio * self.radio:
            self.target_waypoint.see_you(self) #tell waypoint that we see him and hope that he will direct us further
            self.radio = self.awareness

        self.radio += 0.3

        self.velocity.limit(self.max_speed)
        self.location += self.velocity

        self.acceleration *= 0
        #if not self.positions or int(self.location.x) != int(self.positions[-1].x) and int(self.location.y) != int(self.positions[-1].y):
        #    self.positions.append(Vector2(self.location.x, self.location.y))


    def draw(self, context):
        context.save()

        context.translate(self.location.x, self.location.y)


        context.move_to(0, 0)
        context.line_to(self.acceleration.x * 50, self.acceleration.y * 50)
        context.stroke()

        #draw boid triangle
        theta = self.velocity.heading() + math.pi / 2
        context.rotate(theta)

        context.move_to(0, -self.radius*2)
        context.line_to(-self.radius, self.radius * 2)
        context.line_to(self.radius, self.radius * 2)
        context.line_to(0, -self.radius*2)



        context.restore()



    def separate(self, boids):
        sum = Vector2()
        in_zone = 0.0

        for boid, d in boids:
            if 0 < d < self.separation_squared:
                diff = self.location - boid.location
                diff.normalize()
                diff = diff / math.sqrt(d)  # Weight by distance
                sum += diff
                in_zone += 1

        if in_zone:
            sum = sum / in_zone

        sum.limit(self.max_force)
        return sum


    def seek(self, target):
        self.acceleration += self.steer(target, False)

    def arrive(self, target):
        self.acceleration += self.steer(target, True)

    def steer(self, target, slow_down):
        desired = target - self.location # A vector pointing from the location to the target

        d = desired.magnitude()
        if d > 0:  # this means that we have a target
            desired.normalize()


            # Two options for desired vector magnitude (1 -- based on distance, 2 -- maxspeed)
            if  slow_down and d < self.awareness_squared:
                desired *= self.max_speed * (math.sqrt(d) / self.awareness) # This damping is somewhat arbitrary
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

        self.waypoints = []
        self.waypoints = [Waypoint(200, 200),
                          BucketWaypoint(150, 300, 3),
                          Waypoint(300, 300),
                          BucketWaypoint(100, 400, 2),
                          Waypoint(500, 100)]

        # link them together
        for curr, next in zip(self.waypoints, self.waypoints[1:]):
            curr.next = next
            next.previous = curr

        self.waypoints[0].previous = self.waypoints[-1]
        self.waypoints[-1].next = self.waypoints[0]



        self.boids = [Boid(Vector2(120,10)),
                      Boid(Vector2(150,10)),
                      Boid(Vector2(160,200)),
                      Boid(Vector2(350,100)),
                      Boid(Vector2(150,10))
                      ]
        for i, boid in enumerate(self.boids):
            boid.target(self.waypoints[i])

        self.mouse_node = None


    # just for kicks - mouse events
    def on_mouse_button_press(self, area, over_regions):
        if over_regions:
            self.mouse_node = over_regions[0]

    def on_mouse_click(self, area, coords, areas):
        if not areas:
            self.waypoints.append(Waypoint(*coords))
            self.redraw_canvas()


    def on_mouse_move(self, area, coords, state):
        if self.mouse_node is not None:  #checking for none as there is the node zero
            if gtk.gdk.BUTTON1_MASK & state:
                # dragging around
                self.waypoints[self.mouse_node].location.x = coords[0]
                self.waypoints[self.mouse_node].location.y = coords[1]
                self.redraw_canvas()
            else:
                self.mouse_node = None


    def on_expose(self):
        # main loop (i should rename this to something more obvious)
        self.context.set_line_width(0.8)

        for boid in self.boids:
            neighbours = self.proximities.find_neighbours(boid, 40)

            boid.run(neighbours)

            self.proximities.update_position(boid)

            # the growing antennae circle
            self.set_color("#ddd", 0.3)
            self.context.arc(boid.location.x,
                             boid.location.y,
                             boid.radio,
                             -math.pi, math.pi)
            self.context.fill()

            #awareness circle
            """
            self.set_color("#aaa", 0.5)
            self.context.arc(boid.location.x,
                             boid.location.y,
                             boid.awareness,
                             -math.pi, math.pi)
            self.context.fill()
            """


            # debug trail (if enabled)
            self.set_color("#00ff00")
            for position1, position2 in zip(boid.positions, boid.positions[1:]):
                self.context.move_to(position1.x, position1.y)
                self.context.line_to(position2.x, position2.y)
            self.context.stroke()


            # sir boid himself
            self.set_color("#666")
            boid.draw(self.context)

            # line between boid and it's target
            self.context.move_to(boid.location.x, boid.location.y)
            self.context.line_to(boid.target_waypoint.location.x,
                                 boid.target_waypoint.location.y)

            self.context.stroke()


        self.set_color("#999")
        for i, waypoint in enumerate(self.waypoints):
            self.draw_rect(waypoint.location.x - 4, waypoint.location.y - 4, 8, 8, 2)
            self.register_mouse_region(waypoint.location.x - 4, waypoint.location.y - 4,
                                       waypoint.location.x + 4, waypoint.location.y + 4, i)
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
