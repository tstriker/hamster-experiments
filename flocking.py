#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
 * Flocking
 * by Daniel Shiffman.
 *
 * An implementation of Craig Reynold's Boids program to simulate
 * the flocking behavior of birds. Each boid steers itself based on
 * rules of avoidance, alignment, and coherence.

    See flocking2 for better performance.
"""

from gi.repository import Gtk as gtk
from lib import graphics

import math
from random import random

from contrib.euclid import Vector2, Point2

class Boid(object):
    radius = 3 # boid radius

    def __init__(self, location, max_speed, max_force):
        self.acceleration = Vector2()
        self.velocity = Vector2(random() * 2 - 1, random() * 2 - 1)
        self.location = location;
        self.max_speed = max_speed
        self.max_force = max_force


    def run(self, flock_boids, context):
        self.flock(flock_boids)
        self.update()
        self.borders()
        self.draw(context)


    def borders(self):
        # wrapping around
        if self.location.x < -self.radius:
            self.location.x = 600 + self.radius

        if self.location.y < -self.radius:
            self.location.y = 400 + self.radius

        if self.location.x > 600 + self.radius:
            self.location.x = -self.radius

        if self.location.y > 400 + self.radius:
            self.location.y = -self.radius



    def draw(self, context):
        context.save()
        context.translate(self.location.x, self.location.y)

        theta = self.velocity.heading() + math.pi / 2
        context.rotate(theta)

        context.move_to(0, -self.radius*2)
        context.line_to(-self.radius, self.radius*2)
        context.line_to(self.radius, self.radius*2)
        context.close_path()

        context.restore()


    def flock(self, boids):
        # We accumulate a new acceleration each time based on three rules

        separation = self.separate(boids)
        alignment = self.align(boids)
        cohesion = self.cohesion(boids)

        # Arbitrarily weight these forces
        separation = separation * 2
        alignment = alignment * 1
        cohesion = cohesion * 1

        # Add the force vectors to acceleration
        self.acceleration += separation
        self.acceleration += alignment
        self.acceleration += cohesion


    def update(self):
        self.velocity += self.acceleration
        self.velocity.limit(self.max_speed)

        self.location += self.velocity
        # Reset accelertion to 0 each cycle
        self.acceleration *= 0

    def separate(self, boids):
        desired_separation = 25.0
        sum = Vector2()
        in_zone = 0.0

        for boid in boids:
            d = (self.location - boid.location).magnitude()

            if 0 < d < desired_separation:
                diff = self.location - boid.location
                diff.normalize()
                diff = diff / d  # Weight by distance
                sum += diff
                in_zone += 1

        if in_zone:
            sum = sum / in_zone

        return sum

    def align(self, boids):
        neighbour_distance = 50.0
        sum = Vector2()
        in_zone = 0.0

        for boid in boids:
            d = (self.location - boid.location).magnitude()
            if 0 < d < neighbour_distance:
                sum += boid.velocity
                in_zone += 1

        if in_zone:
            sum = sum / in_zone # weight by neighbour count
            sum.limit(self.max_force)

        return sum

    def cohesion(self, boids):
        """ For the average location (i.e. center) of all nearby boids,
            calculate steering vector towards that location"""

        neighbour_distance = 50.0
        sum = Vector2()
        in_zone = 0.0

        for boid in boids:
            d = (self.location - boid.location).magnitude()

            if 0 < d < neighbour_distance:
                sum += boid.location
                in_zone +=1

        if in_zone:
            sum = sum / in_zone
            return self.steer(sum, False)

        return sum


    def steer(self, target, slow_down):
        steer = Vector2()

        desired = target - self.location # A vector pointing from the location to the target

        d = desired.magnitude()

        if d > 0:
            desired.normalize()

            # Two options for desired vector magnitude (1 -- based on distance, 2 -- maxspeed)
            if slow_down and d < 100:
                desired *= self.max_speed * (d / 100.0) # This damping is somewhat arbitrary
            else:
                desired *= self.max_speed

            steer = desired - self.velocity # Steering = Desired minus Velocity
            steer.limit(self.max_force) # Limit to maximum steering force
        else:
            steer = Vector2()

        return steer


class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.flock = []
        self.connect("on-enter-frame", self.on_enter_frame)

    def on_enter_frame(self, scene, context):
        c_graphics = graphics.Graphics(context)
        c_graphics.set_line_style(width = 0.5)
        c_graphics.set_color("#AA00FF")


        if len(self.flock) < 40:
            self.flock.append(Boid(Vector2(100, 100), 2.0, 0.05))

        for boid in self.flock:
            boid.run(self.flock, context)

        context.stroke()
        context.fill()
        self.redraw()


class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_size_request(600, 400)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
