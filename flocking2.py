#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
 * Flocking 2 - based on flocking and added the letuce clustering (or something)
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
    __slots__ = ['acceleration', 'velocity', 'location', 'max_speed', 'max_force']

    radius = 3 # boid radius

    def __init__(self, location, max_speed, max_force):
        self.acceleration = Vector2()
        self.velocity = Vector2(random() * 2 - 1, random() * 2 - 1)
        self.location = location;
        self.max_speed = max_speed
        self.max_force = max_force


    def run(self, flock_boids):
        self.flock(flock_boids)
        self.update()

    def draw(self, area):
        area.context.save()
        area.context.translate(self.location.x, self.location.y)
        
        theta = self.velocity.heading() + math.pi / 2
        area.context.rotate(theta)
        
        area.context.move_to(0, -self.radius*2)
        area.context.line_to(-self.radius, self.radius*2)
        area.context.line_to(self.radius, self.radius*2)
        area.context.line_to(0, -self.radius*2)
        
        area.context.restore()
        
        #area.set_color("#FF0000")
        #area.context.move_to(self.location.x, self.location.y)
        #area.context.line_to(self.location.x + self.velocity.x * 20, self.location.y + self.velocity.y * 20)
        #area.context.stroke()



    def flock(self, boids):
        if not boids:
            return
        
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
        desired_separation = 25.0 ** 2
        sum = Vector2()
        in_zone = 0.0
        
        for boid, d in boids:
            if 0 < d < desired_separation:
                diff = self.location - boid.location
                diff.normalize()
                diff = diff / math.sqrt(d)  # Weight by distance
                sum += diff
                in_zone += 1
        
        if in_zone:
            sum = sum / in_zone
        
        return sum

    def align(self, boids):
        neighbour_distance = 50.0 ** 2
        sum = Vector2()
        in_zone = 0.0
        
        for boid,d in boids:
            if 0 < d < neighbour_distance:
                sum += boid.velocity
                in_zone += 1
        
        if in_zone:
            sum = sum / in_zone # weight by neighbour count
            sum.limit(self.max_force)
        
        return sum
    
    def cohesion(self, boids,):
        """ For the average location (i.e. center) of all nearby boids,
            calculate steering vector towards that location"""
        
        neighbour_distance = 50.0 ** 2
        sum = Vector2()
        in_zone = 0.0
        
        for boid, d in boids:
            if 0 < d < neighbour_distance:
                sum += boid.location
                in_zone +=1

        if in_zone:
            sum = sum / in_zone
            return self.steer(sum)
        
        return sum


    def steer(self, target):
        steer = Vector2()
        
        desired = target - self.location # A vector pointing from the location to the target
        
        d = desired.magnitude_squared()
        
        if d > 0:
            desired.normalize()
            
            # Two options for desired vector magnitude (1 -- based on distance, 2 -- maxspeed)
            desired *= self.max_speed

            steer = desired - self.velocity # Steering = Desired minus Velocity
            steer.limit(self.max_force) # Limit to maximum steering force
        else:
            steer = Vector2()
        
        return steer        


class Canvas(graphics.Area):
    def __init__(self):
        graphics.Area.__init__(self)
        self.segments = []

        self.connect("mouse-click", self.on_mouse_click)
        
        self.proximity_radius = 50
        self.proximities = LQProximityStore(Vector2(0,0), Vector2(600,400), self.proximity_radius)

        self.flock = []
        
        self.distances = 0
        
        self.frame = 0


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

    def on_mouse_click(self, widget, coords):
        self.flock.append(Boid(Vector2(*coords), 1, 1))

    def on_expose(self):
        self.context.set_line_width(1)

        if len(self.flock) < 80:
            self.flock.append(Boid(Vector2(100, 100), 2.0, 0.05))
            
        
        self.set_color("#AA00FF")

        for boid in self.flock:
            neighbours = []
            if self.frame % 2 == 0:
                neighbours = self.proximities.find_neighbours(boid, 50)

            #for boid2,d in neighbours:
            #    self.context.move_to(boid.location.x, boid.location.y)
            #    self.context.line_to(boid2.location.x, boid2.location.y)

            boid.run(neighbours)
            self.wrap(boid)


            boid.draw(self)
            

            self.proximities.update_position(boid)

        self.frame +=1
        
        self.context.stroke()

        self.redraw_canvas()

class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_title("Graphics Module")
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

