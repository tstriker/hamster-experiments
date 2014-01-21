#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
 Extending the flocking code with different kinds of waypoints.
 Work in progress.
"""

from gi.repository import Gtk as gtk

from lib import graphics

import math
import random

from contrib.euclid import Vector2, Point2
from contrib.proximity import LQProximityStore

class Waypoint(graphics.Sprite):
    def __init__(self, x, y):
        graphics.Sprite.__init__(self, x, y, interactive=True, draggable=True)

        self.graphics.set_color("#999")
        self.graphics.rectangle(-4, -4, 8, 8, 2)
        self.graphics.fill()

        self.connect("on-drag", self.on_drag)

        self.location = Vector2(x, y)
        self.debug = False

    def on_drag(self, sprite, event):
        self.location.x, self.location.y  = event.x, event.y


    def see_you(self, boid):
        # boid calls waypoint when he sees it
        # normally we just tell it to go on
        if boid.data and "reverse" in boid.data:
            boid.target(self.previous)
        else:
            boid.target(self.next)

    def move_on(self, boid):
        boid.visible = True #moves are always visible
        if boid.data and "reverse" in boid.data:
            boid.target(self.previous)
        else:
            boid.target(self.next)

        boid.velocity *= 4

    def update(self, context):
        pass

    def get_next(self, boid):
        if boid.data and "reverse" in boid.data:
            return self.previous
        else:
            return self.next

class QueueingWaypoint(Waypoint):
    """waypoint that eats boids and then releases them after a set period"""
    def __init__(self, x, y, frames):
        Waypoint.__init__(self, x, y)
        self.frames = frames
        self.current_frame = 0
        self.boids = []
        self.boid_scales = {}

    def see_you(self, boid):
        distance = (self.location - boid.location).magnitude_squared()
        if boid not in self.boids and distance < 400:
            if not self.boids:
                self.current_frame = 0

            self.boids.append(boid)
            boid.visible = False


        for boid in self.boids:
            boid.velocity *= 0


    def update(self, context):
        self.current_frame +=1
        if self.current_frame == self.frames:
            self.current_frame = 0
            if self.boids:
                boid = self.boids.pop(0)
                boid.location = Vector2(self.location.x, self.location.y)
                self.move_on(boid)



class BucketWaypoint(Waypoint):
    """waypoint that will queue our friends until required number
       arrives and then let them go"""
    def __init__(self, x, y, bucket_size):
        Waypoint.__init__(self, x, y)
        self.bucket_size = bucket_size
        self.boids = []
        self.boids_out = []
        self.rotation_angle = 0
        self.radius = 80
        self.incremental_angle = False



    def see_you(self, boid):
        # boid calls waypoint when he sees it
        # normally we just tell it to go on
        if boid not in self.boids:
            if (boid.location - self.location).magnitude_squared() < self.radius * self.radius:
                if self.incremental_angle:
                    self.rotation_angle = (boid.location - self.location).heading()
                self.boids.append(boid)


    def update(self, context):
        if len(self.boids) == self.bucket_size:
            self.boids_out = list(self.boids)
            self.boids = []


        self.rotation_angle += 0.02

        if self.incremental_angle:
            nodes = len(self.boids) or 1
        else:
            nodes = self.bucket_size - 1

        angle_step = math.pi * 2 / nodes
        current_angle = 0

        i = 0

        points = []
        while i < (math.pi * 2):
            x = self.location.x + math.cos(self.rotation_angle + i) * self.radius
            y = self.location.y + math.sin(self.rotation_angle + i) * self.radius

            points.append(Vector2(x,y))
            i += angle_step



        context.stroke()

        for boid in self.boids:
            distance = None
            closest_point = None
            for point in points:
                point_distance = (boid.location - point).magnitude_squared()
                if not distance or point_distance < distance:
                    closest_point = point
                    distance = point_distance

            if closest_point:
                target = boid.seek(closest_point)
                #if target.magnitude_squared() < 1:
                #    boid.flight_angle = (self.location - boid.location).cross().heading()

                boid.acceleration *= 8
                points.remove(closest_point) # taken
            else:
                boid.velocity *= .9

        context.stroke()

        if self.boids_out:
            for boid in self.boids_out:
                self.move_on(boid)
                boid.acceleration = -(self.location - boid.location) * 2
                boid.flight_angle = 0

            self.boids_out = []


class RotatingBucketWaypoint(BucketWaypoint):
    def update(self, context):
        BucketWaypoint.update(self, context)
        for boid in self.boids:
            boid.flight_angle += 0.2


class GrowWaypoint(Waypoint):
    """waypoint that will queue our friends until required number
       arrives and then let them go"""
    def __init__(self, x, y, scale):
        Waypoint.__init__(self, x, y)
        self.scale = scale
        self.boid_scales = {}



    def see_you(self, boid):
        # boid calls waypoint when he sees it
        # normally we just tell it to go on
        distance = (self.location - boid.location).magnitude_squared()
        if distance < 400:
            self.move_on(boid)
            del self.boid_scales[boid]
        else: #start braking
            boid.radius = (self.scale * 400 / distance) + (self.boid_scales.setdefault(boid, boid.radius) * (1 - 400 / distance))   #at 400 full scale has been achieved



class ShakyWaypoint(Waypoint):
    def __init__(self, x, y):
        Waypoint.__init__(self, x, y)

    @staticmethod
    def virus(boid, data):
        frame = data.setdefault('frame', 0)
        frame += 1

        if frame > 20:
            seizure = random.random() > 0.4
            if seizure:
                boid.radius = data.setdefault('radius', boid.radius) * (random.random() * 4)
        if frame > 25:
            frame = 0

        data['frame'] = frame


    def see_you(self, boid):

        if boid.virus:
            boid.virus = None
            boid.radius = boid.data['radius']
        else:
            boid.virus = self.virus
        self.move_on(boid)


class Boid(graphics.Sprite):
    def __init__(self, location, max_speed = 2.0):
        graphics.Sprite.__init__(self, snap_to_pixel=False)

        self.visible = True
        self.radius = 3
        self.acceleration = Vector2()
        self.brake = Vector2()
        self.velocity = Vector2(random.random() * 2 - 1, random.random() * 2 - 1)
        self.location = location
        self.max_speed = max_speed
        self.max_force = 0.03
        self.positions = []
        self.message = None # a message that waypoint has set perhaps
        self.flight_angle = 0

        self.data = {}
        self.virus = None

        self.radio = self.radius * 5

        self.target_waypoint = None

        self.connect("on-render", self.on_render)

    def target(self, waypoint):
        self.radio = self.radius * 5
        self.target_waypoint = waypoint

    def run(self, flock_boids):
        if flock_boids:
            self.acceleration += self.separate(flock_boids) * 2

        self.seek(self.target_waypoint.location)

        self.velocity += self.acceleration




        if (self.location - self.target_waypoint.location).magnitude_squared() < self.radio * self.radio:
            self.target_waypoint.see_you(self) #tell waypoint that we see him and hope that he will direct us further

        self.radio += 0.3

        self.velocity.limit(self.max_speed)
        self.location += self.velocity

        self.acceleration *= 0

        if self.virus:
            self.virus(self, self.data)

        self.x, self.y = self.location.x, self.location.y

        #draw boid triangle
        if self.flight_angle:
            self.rotation = self.flight_angle
        else:
            self.rotation = self.velocity.heading() + math.pi / 2



    def on_render(self, context):
        self.graphics.move_to(0, 0)
        self.graphics.line_to(self.acceleration.x * 50, self.acceleration.y * 50)
        self.graphics.stroke()


        self.graphics.move_to(0, -self.radius*2)
        self.graphics.line_to(-self.radius, self.radius * 2)
        self.graphics.line_to(self.radius, self.radius * 2)
        self.graphics.line_to(0, -self.radius*2)

        self.graphics.fill("#aaa")




    def separate(self, boids):
        sum = Vector2()
        in_zone = 0.0

        for boid, d in boids:
            if not boid.visible:
                continue

            if 0 < d < self.radius * 5 * self.radius * 5:
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
        steer_vector = self.steer(target, False)
        self.acceleration += steer_vector
        return steer_vector


    def arrive(self, target):
        self.acceleration += self.steer(target, True)

    def steer(self, target, slow_down):
        desired = target - self.location # A vector pointing from the location to the target

        d = desired.magnitude()
        if d > 0:  # this means that we have a target
            desired.normalize()


            # Two options for desired vector magnitude (1 -- based on distance, 2 -- maxspeed)
            if  slow_down and d < self.radius * 5 * self.radius * 5:
                desired *= self.max_speed * (math.sqrt(d) / self.radius * 5) # This damping is somewhat arbitrary
            else:
                desired *= self.max_speed

            steer = desired - self.velocity # Steering = Desired minus Velocity
            steer.limit(self.max_force) # Limit to maximum steering force
            return steer
        else:
            return Vector2()



class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)


        # we should redo the boxes when window gets resized
        box_size = 10
        self.proximities = LQProximityStore(Vector2(0,0), Vector2(600,400), box_size)

        self.waypoints = []
        self.waypoints = [QueueingWaypoint(100, 100, 70),
                          BucketWaypoint(500, 100, 10),
                          GrowWaypoint(500, 500, 10),
                          QueueingWaypoint(300, 500, 70),
                          BucketWaypoint(100, 500, 10),
                          GrowWaypoint(100, 300, 3),
                          ]

        for waypoint in self.waypoints:
            self.add_child(waypoint)

        # link them together
        for curr, next in zip(self.waypoints, self.waypoints[1:]):
            curr.next = next
            next.previous = curr

        self.waypoints[0].previous = self.waypoints[-1]
        self.waypoints[-1].next = self.waypoints[0]



        self.boids = [Boid(Vector2(100,100), 2.0) for i in range(15)]

        for i, boid in enumerate(self.boids):
            boid.target(self.waypoints[0])
            self.add_child(boid)

        self.mouse_node = None

        # some debug variables
        self.debug_radius = False
        self.debug_awareness = False

        self.connect("on-enter-frame", self.on_enter_frame)




    def on_enter_frame(self, scene, context):
        c_graphics = graphics.Graphics(context)
        c_graphics.set_line_style(width = 0.8)

        for waypoint in self.waypoints:
            waypoint.update(context)

        for boid in self.boids:
            # the growing antennae circle
            if self.debug_radius:
                c_graphics.set_color("#aaa", 0.3)
                context.arc(boid.location.x,
                            boid.location.y,
                            boid.radio,
                            -math.pi, math.pi)
                context.fill()


            # obstacle awareness circle
            if self.debug_awareness:
                c_graphics.set_color("#aaa", 0.5)
                context.arc(boid.location.x,
                            boid.location.y,
                            boid.awareness,
                            -math.pi, math.pi)
                context.fill()



        for boid in self.boids:
            neighbours = self.proximities.find_neighbours(boid, 40)

            boid.run(neighbours)

            self.proximities.update_position(boid)


            # debug trail (if enabled)
            c_graphics.set_color("#0f0")
            for position1, position2 in zip(boid.positions, boid.positions[1:]):
                context.move_to(position1.x, position1.y)
                context.line_to(position2.x, position2.y)
            context.stroke()


            # line between boid and it's target
            """
            c_graphics.set_color("#999")
            context.move_to(boid.location.x, boid.location.y)
            context.line_to(boid.target_waypoint.location.x,
                                 boid.target_waypoint.location.y)
            context.stroke()
            """


        self.redraw()



class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_size_request(600, 600)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        scene = Scene()
        window.add(scene)
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
