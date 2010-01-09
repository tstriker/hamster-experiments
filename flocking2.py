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

 Ported from processing (http://processing.org/) examples.
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

    def __init__(self, location, max_speed, max_force):
        self.acceleration = Vector2()
        self.velocity = Vector2(random() * 2 - 1, random() * 2 - 1)
        self.location = location;
        self.max_speed = max_speed
        self.max_force = max_force


    def run(self, flock_boids):
        self.flock(flock_boids)
        self.update()
        self.borders()


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
        self.connect("motion_notify_event", self.on_mouse_move)
        
        self.proximity_radius = 50
        self.proximities = LQProximityStore(Vector2(0,0), Vector2(600,400), self.proximity_radius)

        self.flock = []
        
        self.distances = 0
        
        for i in range(100):
            self.flock.append(Boid(Vector2(100, 100), 2.0, 0.05))
            
        self.special = self.flock[0] # our favourite boid
        
        self.frame = 0


    def on_mouse_move(self, widget, event):
        if event.is_hint:
            x, y, state = event.window.get_pointer()
        else:
            x = event.x
            y = event.y
            state = event.state


    def on_expose(self):
        self.context.set_line_width(0.5)
        
        """
        #highlight quadrants
        from bisect import bisect
        point = self.special
        radius = 40
        min_x = bisect(self.proximities.grid_x, point.location.x - radius)
        min_y = bisect(self.proximities.grid_y, point.location.y - radius)
        max_x = bisect(self.proximities.grid_x, point.location.x + radius)
        max_y = bisect(self.proximities.grid_y, point.location.y + radius)
        

        radius = self.proximity_radius
        for x in range(min_x, max_x+1):
            for y in range(min_y, max_y+1):
                if self.proximities.positions.get((x, y)):
                    self.fill_area(x * radius-radius, y * radius-radius, radius, radius, "#FF00FF")
                else:
                    self.fill_area(x * radius-radius, y * radius-radius, radius, radius, "#AAAAAA")

        #print len(self.proximities.find_neighbours(self.special, 40))
        """
        

        #draw the grid
        self.set_color("#FFFFFF")
        for x in range(self.proximities.point1.x, self.proximities.point2.x, self.proximities.stride):
            self.context.move_to(x+0.5, self.proximities.point1.y)
            self.context.line_to(x+0.5, self.proximities.point2.y)

        for y in range(self.proximities.point1.y, self.proximities.point2.y, self.proximities.stride):
            self.context.move_to(self.proximities.point1.x, y + 0.5)
            self.context.line_to(self.proximities.point2.x, y + 0.5)
        self.context.stroke()

        

                
        
        self.set_color("#AA00FF")

        

        for boid in self.flock:
            neighbours = []
            if self.frame % 1 == 0:
                neighbours = self.proximities.find_neighbours(boid, 50)

            #for boid2,d in neighbours:
            #    self.context.move_to(boid.location.x, boid.location.y)
            #    self.context.line_to(boid2.location.x, boid2.location.y)

            boid.run(neighbours)
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

