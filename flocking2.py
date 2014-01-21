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

from gi.repository import Gtk as gtk
from lib import graphics

import math
from random import random

from contrib.euclid import Vector2, Point2
from contrib.proximity import LQProximityStore


class Boid(object):
    radius = 2 # boid radius

    # distances are squared to avoid roots (slower)
    neighbour_distance = float(50**2)
    desired_separation = float(25**2)
    braking_distance = float(100**2)

    def __init__(self, location, max_speed, max_force):
        self.acceleration = Vector2()
        self.velocity = Vector2(random() * 2 - 1, random() * 2 - 1)
        self.location = location;
        self.max_speed = max_speed
        self.max_force = max_force


    def run(self, flock_boids):
        self.flock(flock_boids)

        self.velocity += self.acceleration
        self.velocity.limit(self.max_speed)
        self.location += self.velocity

    def flock(self, boids):
        if not boids:
            return

        # We accumulate a new acceleration each time based on three rules
        # and weight them
        separation = self.separate(boids) * 2
        alignment = self.align(boids) * 1
        cohesion = self.cohesion(boids) * 1

        # The sum is the wanted acceleration
        self.acceleration = separation + alignment + cohesion


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

    def align(self, boids):
        sum = Vector2()
        in_zone = 0.0

        for boid, d in boids:
            if 0 < d < self.neighbour_distance:
                sum += boid.velocity
                in_zone += 1

        if in_zone:
            sum = sum / in_zone # weight by neighbour count
            sum.limit(self.max_force)

        return sum

    def cohesion(self, boids,):
        """ For the average location (i.e. center) of all nearby boids,
            calculate steering vector towards that location"""

        sum = Vector2()
        in_zone = 0

        for boid, d in boids:
            if 0 < d < self.neighbour_distance:
                sum = sum + boid.location
                in_zone +=1

        if in_zone:
            sum = sum / float(in_zone)
            return self.steer(sum, True)

        return sum

    def seek(target):
        self.acceleration += self.steer(target, False)

    def arrive(target):
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



class Canvas(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.segments = []

        # we should redo the boxes when window gets resized
        self.proximity_radius = 10
        self.proximities = LQProximityStore(Vector2(0,0), Vector2(600,400), self.proximity_radius)
        self.flock = []
        self.frame = 0

        self.connect("on-click", self.on_mouse_click)
        self.connect("on-enter-frame", self.on_enter_frame)


    def on_enter_frame(self, scene, context):
        c_graphics = graphics.Graphics(context)

        if len(self.flock) < 80:
            for i in range(2):
                self.flock.append(Boid(Vector2(self.width / 2, self.height / 2), 2.0, 0.05))

        # main loop (i should rename this to something more obvious)
        c_graphics.set_line_style(width = 0.8)
        c_graphics.set_color("#666")


        for boid in self.flock:
            neighbours = []
            if self.frame % 2 == 0: #recalculate direction every second frame
                neighbours = self.proximities.find_neighbours(boid, 40)

            boid.run(neighbours)
            self.wrap(boid)
            self.proximities.update_position(boid)

            self.draw_boid(context, boid)


        self.frame +=1

        context.stroke()

        self.redraw()


    def wrap(self, boid):
        "wraps boid around the edges (teleportation)"
        if boid.location.x < -boid.radius:
            boid.location.x = self.width + boid.radius

        if boid.location.y < -boid.radius:
            boid.location.y = self.height + boid.radius

        if boid.location.x > self.width + boid.radius:
            boid.location.x = -boid.radius

        if boid.location.y > self.height + boid.radius:
            boid.location.y = -boid.radius


    def draw_boid(self, context, boid):
        context.save()
        context.translate(boid.location.x, boid.location.y)

        theta = boid.velocity.heading() + math.pi / 2
        context.rotate(theta)

        context.move_to(0, -boid.radius*2)
        context.line_to(-boid.radius, boid.radius*2)
        context.line_to(boid.radius, boid.radius*2)
        context.line_to(0, -boid.radius*2)

        context.restore()


    def on_mouse_click(self, widget, event, target):
        self.flock.append(Boid(Vector2(event.x, event.y), 2.0, 0.05))




class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_size_request(600, 400)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Canvas())
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
