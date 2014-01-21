#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
  Ported from javascript via chrome experiments.
  Most addictive. There are some params to adjust in the Scene class.
  Color and number of particles reduced due to performance
  Without fadeout this becomes a mess soon, drawing/storing whole window seems
  to be bit expensive though. Although scales lineary. Check earlier code of this
  same file for some snippets, if you want to go that way.

  Super Simple Particle System
  Eric Ishii Eckhardt for Adapted
  http://adaptedstudio.com
"""


from gi.repository import Gtk as gtk
from lib import graphics
from contrib.euclid import Vector2
from random import random, randint
import collections

class Boid(object):
    def __init__(self):
        self.acceleration = Vector2()
        self.velocity = Vector2()
        self.location = Vector2(150, 150)

class Boid3(Boid):
    """Sir Boid from random_movement.py"""
    def __init__(self):
        Boid.__init__(self)
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

        self.acceleration = (target - self.velocity).normalize() * 2
        self.velocity += self.acceleration

        self.velocity.limit(20)

        self.prev_distance = distance

        self.location += self.velocity

class Particle(object):
    def __init__(self, x, y):
        self.x, self.y = x, y


        self.prev_x, self.prev_y = x, y

        # bouncyness - set to 1 to disable
        self.speed_mod_x = random() * 20 + 8
        self.speed_mod_y = random() * 20 + 8

        # random force of atraction towards target (0.1 .. 0.5)
        self.accel_mod_x = random() * 0.5 + 0.2
        self.accel_mod_y = random() * 0.5 + 0.2

        self.speed_x, self.speed_y = 0, 0

    def update(self, mouse_x, mouse_y):
        self.prev_x, self.prev_y = self.x, self.y

        target_accel_x = (mouse_x - self.x) * self.accel_mod_x
        target_accel_y = (mouse_y - self.y) * self.accel_mod_y


        self.speed_x = self.speed_x + (target_accel_x - self.speed_x) / self.speed_mod_x
        self.speed_y = self.speed_y + (target_accel_y - self.speed_y) / self.speed_mod_y



        self.x = self.x + self.speed_x * 0.1
        self.y = self.y + self.speed_y * 0.1

class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        self.connect("on-enter-frame", self.on_enter_frame)
        #self.set_double_buffered(False) # cheap way how to get to continuous draw!

        self.particles = []

        self.particle_count = 40 # these are the flies
        self.fade_step = 2         # the smaller is this the "ghostier" it looks (and slower too)

        self.target = Boid3()



    def on_enter_frame(self, scene, context):
        g = graphics.Graphics(context)
        g.fill_area(0, 0, self.width, self.height, "#fff", 0.08)

        if not self.particles:
            for i in range(self.particle_count):
                self.particles.append(Particle(random() * self.width, random() * self.height))

        self.target.update_position(self.width, self.height)

        g.set_line_style(width=0.3)

        for particle in self.particles:
            particle.update(self.target.location.x, self.target.location.y)
            g.move_to(particle.prev_x, particle.prev_y)
            g.line_to(particle.x, particle.y)

        g.set_color("#000")
        g.stroke()

        self.redraw()




class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_size_request(1000, 650)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()

example = BasicWindow()
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
gtk.main()
