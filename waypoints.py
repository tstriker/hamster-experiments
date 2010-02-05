#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
 Extending the flocking code with different kinds of waypoints.
 Work in progress.
"""

import gtk

from lib import graphics, pytweener
from lib.pytweener import Easing

import math
import random

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
        self.rotation_angle = 0
        self.radius = 80


    def see_you(self, boid):
        # boid calls waypoint when he sees it
        # normally we just tell it to go on
        if boid not in self.boids:
            self.rotation_angle = (boid.location - self.location).heading()
            self.boids.append(boid)


    def update(self, context):
        if len(self.boids) == self.bucket_size:
            for boid in self.boids:
                self.move_on(boid)

            self.boids = []


        self.rotation_angle += 0.02
        angle_step = math.pi * 2 / (self.bucket_size - 1)
        current_angle = 0

        i = 0

        points = []
        while i < (math.pi * 2):
            x = self.location.x + math.cos(self.rotation_angle + i) * self.radius
            y = self.location.y + math.sin(self.rotation_angle + i) * self.radius

            points.append(Vector2(x,y))

            #context.move_to(self.location.x, self.location.y)
            #context.line_to(x, y)
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
                #context.move_to(boid.location.x, boid.location.y)
                #context.line_to(closest_point.x, closest_point.y)

                boid.seek(closest_point)
                boid.acceleration *= 4
                points.remove(closest_point) # taken
            else:
                boid.velocity *= .9

        context.stroke()

        self.incoming = 0 #reset incoming as it will be updated again in next iter



class CarouselWaypoint(Waypoint):
    """waypoint that will queue our friends until required number
       arrives and then let them go"""
    def __init__(self, x, y, radius):
        Waypoint.__init__(self, x, y)
        self.boids = []
        self.rotation_angle = 0
        self.radius = radius

        self.boid_angles = {}
        self.boid_revolutions = {}

        self.speed = 1
        self.revolutions = 0.1


    def see_you(self, boid):
        if boid not in self.boids:
            if (self.location - boid.location).magnitude_squared() < self.radius * self.radius:
                if not self.boids:
                    self.rotation_angle = (boid.location - self.location).heading()
                self.boids.append(boid)
                self.boid_angles[boid] = (boid.location - self.location).heading()
                self.boid_revolutions[boid] = 0


    def update(self, context):
        poplist = []
        for boid in self.boids:
            if self.boid_revolutions[boid] > self.revolutions:
                angle = self.boid_angles[boid] % (math.pi * 2)
                if math.pi -0.1 < abs((self.location - self.get_next(boid).location).heading() - angle) < math.pi:
                    self.move_on(boid)
                    poplist.append(boid)

        for boid in poplist:
            self.boids.remove(boid)


        if self.boids:
            step = self.speed / 50.0
            for boid in self.boids:
                self.boid_angles[boid] += step
                self.boid_revolutions[boid] += step / math.pi / 2
                boid.location.x = self.location.x + math.cos(self.boid_angles[boid]) * self.radius
                boid.location.y = self.location.y + math.sin(self.boid_angles[boid]) * self.radius
                boid.velocity = (boid.location - self.location) * 0.01



        self.rotation_angle += 0.05 #* math.sqrt(len(self.boids) / float(self.bucket_size))
        self.incoming = 0




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


class Boid(object):
    def __init__(self, location, max_speed = 2.0):
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

        self.data = {}
        self.virus = None

        self.radio = self.radius * 5

        self.target_waypoint = None

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

        #if not self.positions or int(self.location.x) != int(self.positions[-1].x) and int(self.location.y) != int(self.positions[-1].y):
        #    self.positions.append(Vector2(self.location.x, self.location.y))


    def draw(self, context):
        if not self.visible:
            return

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
        self.acceleration += self.steer(target, False)

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



class Canvas(graphics.Area):
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

        for waypoint in self.waypoints:
            waypoint.update(self.context)


        for boid in self.boids:
            # the growing antennae circle
            if self.debug_radius:
                self.set_color("#ddd", 0.3)
                self.context.arc(boid.location.x,
                                 boid.location.y,
                                 boid.radio,
                                 -math.pi, math.pi)
                self.context.fill()


            # obstacle awareness circle
            if self.debug_awareness:
                self.set_color("#ddd", 0.5)
                self.context.arc(boid.location.x,
                                 boid.location.y,
                                 boid.awareness,
                                 -math.pi, math.pi)
                self.context.fill()



        for boid in self.boids:
            neighbours = self.proximities.find_neighbours(boid, 40)

            boid.run(neighbours)

            self.proximities.update_position(boid)


            # debug trail (if enabled)
            self.set_color("#00ff00")
            for position1, position2 in zip(boid.positions, boid.positions[1:]):
                self.context.move_to(position1.x, position1.y)
                self.context.line_to(position2.x, position2.y)
            self.context.stroke()


            # sir boid himself
            self.set_color("#888")
            boid.draw(self.context)

            # line between boid and it's target
            """
            self.context.move_to(boid.location.x, boid.location.y)
            self.context.line_to(boid.target_waypoint.location.x,
                                 boid.target_waypoint.location.y)
            """

            self.context.fill_preserve()
            self.context.stroke()


        self.set_color("#999")
        for i, waypoint in enumerate(self.waypoints):
            self.draw_rect(waypoint.location.x - 4, waypoint.location.y - 4, 8, 8, 2)
            self.register_mouse_region(waypoint.location.x - 4, waypoint.location.y - 4,
                                       waypoint.location.x + 4, waypoint.location.y + 4, i)
            self.context.fill()

        self.redraw_canvas()


    def __init__(self):
        graphics.Area.__init__(self)

        self.connect("mouse-move", self.on_mouse_move)
        self.connect("button-press", self.on_mouse_button_press)
        self.connect("mouse-click", self.on_mouse_click)

        # we should redo the boxes when window gets resized
        box_size = 10
        self.proximities = LQProximityStore(Vector2(0,0), Vector2(600,400), box_size)

        self.waypoints = []
        self.waypoints = [QueueingWaypoint(200, 100, 150),
                          BucketWaypoint(200, 400, 11),
                          ]

        # link them together
        for curr, next in zip(self.waypoints, self.waypoints[1:]):
            curr.next = next
            next.previous = curr

        self.waypoints[0].previous = self.waypoints[-1]
        self.waypoints[-1].next = self.waypoints[0]



        self.boids = [Boid(Vector2(100,100), 2.0) for i in range(10)]

        for i, boid in enumerate(self.boids):
            boid.target(self.waypoints[0])

        self.mouse_node = None

        # some debug variables
        self.debug_radius = False
        self.debug_awareness = False








class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(600, 600)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        canvas = Canvas()

        box = gtk.VBox()
        box.pack_start(canvas)


        window.add(box)
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    gtk.main()
