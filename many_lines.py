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


import gtk
from lib import graphics
from random import random
import collections


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



        self.x = self.x + self.speed_x
        self.y = self.y + self.speed_y

class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        self.connect("on-enter-frame", self.on_enter_frame)
        self.connect("on-mouse-move", self.on_mouse_move)
        self.particles = []
        self.mouse_x, self.mouse_y = 0, 0
        self.paths = collections.deque()

        self.particle_count = 50 # these are the flies
        self.max_path_count = 10   # set this bigger to get longer tails and fry your computer
        self.fade_step = 1         # the smaller is this the "ghostier" it looks (and slower too)



    def on_mouse_move(self, scene, event):
        self.mouse_x, self.mouse_y = event.x, event.y

    def on_enter_frame(self, scene, context):
        g = graphics.Graphics(context)

        if not self.particles:
            for i in range(self.particle_count):
                self.particles.append(Particle(random() * self.width, random() * self.height))

        g.set_line_style(width=0.3)

        for i, path in enumerate(self.paths):
            context.append_path(path)

            if i % self.fade_step == 0:
                g.set_color("#000", i / float(len(self.paths)))
            context.stroke()

        for particle in self.particles:
            particle.update(self.mouse_x, self.mouse_y)
            g.move_to(particle.prev_x, particle.prev_y)
            g.line_to(particle.x, particle.y)

        self.paths.append(context.copy_path())
        if len(self.paths) > self.max_path_count:
            self.paths.popleft()

        g.set_color("#000")
        g.stroke()

        self.redraw()




class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(600, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()

example = BasicWindow()
gtk.main()
