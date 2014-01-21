#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
    Looking into random movement. Specifically looking for something elegant.
    These are just beginnings.
"""


from gi.repository import Gtk as gtk
from lib import graphics
from contrib.euclid import Vector2
import math
from random import random, randint

class Boid(graphics.Sprite):
    def __init__(self):
        graphics.Sprite.__init__(self)
        self.stroke = "#666"
        self.visible = True
        self.radius = 4
        self.acceleration = Vector2()
        self.velocity = Vector2()

        self.location = Vector2(150, 150)
        self.positions = []
        self.message = None # a message that waypoint has set perhaps
        self.flight_angle = 0

        self.connect("on-render", self.on_render)

    def update_position(self, w, h):
        raise TableSpoon # forgot the name of the real exception, so can as well raise a table spoon

    def on_render(self, sprite):
        self.graphics.clear()
        #draw boid triangle
        if self.flight_angle:
            theta = self.flight_angle
        else:
            theta = self.velocity.heading() + math.pi / 2

        self.rotation = theta
        self.x, self.y = self.location.x, self.location.y
        self.graphics.set_line_style(width = 1)

        self.graphics.move_to(0, -self.radius*2)
        self.graphics.line_to(-self.radius, self.radius * 2)
        self.graphics.line_to(self.radius, self.radius * 2)
        self.graphics.line_to(0, -self.radius*2)

        self.graphics.stroke(self.stroke)


class Boid1(Boid):
    """purely random acceleration plus gravitational pull towards the center"""
    def __init__(self):
        Boid.__init__(self)

    def update_position(self, w, h):
        self.acceleration = Vector2(random() * 2 - 1, random() * 2 - 1)

        self.acceleration += (Vector2(w/2, h/2) - self.location) / 4000

        self.velocity += self.acceleration
        self.velocity.limit(2)
        self.location += self.velocity


class Boid2(Boid):
    """acceleration is in slight angular deviation of velocity
       maintaining in screen with the gravitational pull
    """
    def __init__(self):
        Boid.__init__(self)
        self.stroke = "#0f0"

    def update_position(self, w, h):
        acc_angle = self.velocity.heading() + (random() * 2 - 1)

        max_distance = w/2 * w/2 + h/2 * h/2
        current_centre_distance = (Vector2(w/2, h/2) - self.location).magnitude_squared()

        self.acceleration = Vector2(math.cos(acc_angle), math.sin(acc_angle)) * 0.8
        self.acceleration += (Vector2(w/2, h/2) - self.location) / 500 * (1 - (current_centre_distance / float(max_distance)))

        self.velocity += self.acceleration
        self.velocity.limit(5)
        self.location += self.velocity

        self.location.x = max(min(self.location.x, w + 100), -100)
        self.location.y = max(min(self.location.y, h + 100), -100)


class Boid3(Boid):
    """waypoint oriented - once reached, picks another random waypoint
       alternatively another random waypoint is picked, if the boid keeps
       moving away from the current one - this way we can keep the speed constant
       and discard waypoint instead
    """
    def __init__(self):
        Boid.__init__(self)
        self.stroke = "#00f"
        self.target = None
        self.prev_distance = None

    def update_position(self, w, h):
        distance = 0
        if self.target:
            distance = (self.target - self.location).magnitude_squared()

        if not self.target or self.prev_distance and distance > self.prev_distance:
            self.prev_distance = w * w + h * h
            self.target = Vector2(randint(0, w), randint(0, h))

        target = (self.target - self.location)

        self.acceleration = (target - self.velocity).normalize() * 0.25
        self.velocity += self.acceleration

        self.velocity.limit(6)

        self.prev_distance = distance

        self.location += self.velocity


class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        self.boids = [Boid1(), Boid2(), Boid3(), Boid3(), Boid3()]
        self.add_child(*self.boids)
        self.connect("on-enter-frame", self.on_enter_frame)

    def on_enter_frame(self, scene, context):
        for boid in self.boids:
            boid.update_position(self.width, self.height)

        self.redraw()


class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_size_request(600, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()

example = BasicWindow()
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
gtk.main()
