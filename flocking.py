#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
 Move the mouse across the screen to change the position of the rectangles.
 The positions of the mouse are recorded into a list and played back every frame.
 Between each frame, the newest value are added to the start of the list.
 
 Ported from processing.js (http://processingjs.org/learning/basic/storinginput)
"""
 
import gtk

from lib import graphics
from lib.pytweener import Easing

import math
from random import random

from lib.euclid import Vector2, Point2

class Boid(object):
    radius = 3 # boid radius

    def __init__(self, location, max_speed, max_force):
        self.acceleration = Vector2()
        self.velocity = Vector2(random() * 2 - 1, random() * 2 - 1)
        self.location = location;
        self.max_speed = max_speed
        self.max_force = max_force


    def run(self, flock_boids, area):
        self.flock(flock_boids)
        self.update()
        self.borders()
        self.draw(area)


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
        area.context.close_path()
        
        area.context.restore()


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


class Canvas(graphics.Area):
    def __init__(self):
        graphics.Area.__init__(self)
        self.segments = []
        self.connect("motion_notify_event", self.on_mouse_move)

        self.flock = []
        
        for i in range(40):
            self.flock.append(Boid(Vector2(100, 100), 2.0, 0.05))


    def on_mouse_move(self, widget, event):
        if event.is_hint:
            x, y, state = event.window.get_pointer()
        else:
            x = event.x
            y = event.y
            state = event.state


    def on_expose(self):
        self.context.set_line_width(0.5)
        self.set_color("#AA00FF")

        for boid in self.flock:
            boid.run(self.flock, self)

        self.context.stroke()
        self.context.fill()
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

