#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
    Demo of a a timer based ripple running through nodes and initiating
    sub-animations. Not sure where this could come handy.
"""


import gtk
from lib import graphics
from lib.pytweener import Easing
from random import random
import math

class Node(graphics.Shape):
    def __init__(self, angle, distance):
        graphics.Shape.__init__(self, fill = "#aaa")

        self.angle = angle
        self.distance = distance
        self.radius = 4.0

        self.phase = 0

    def draw_shape(self):
        self.x = math.cos(self.angle) * self.distance
        self.y = math.sin(self.angle) * self.distance

        self.graphics.circle(0, 0, self.radius)
        self.graphics.fill("#aaa")

class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        self.nodes = []
        self.tick = 0
        self.phase = 0
        self.container = graphics.Sprite()
        self.add_child(self.container)
        self.framerate = 30

        self.connect("on-enter-frame", self.on_enter_frame)

    def on_enter_frame(self, scene, context):
        self.container.x = self.width / 2
        self.container.y = self.height / 2

        if not self.nodes:
            for i in range(100):
                angle = random() * math.pi * 2
                distance = random() * 500

                node = Node(angle, distance)
                self.container.add_child(node)
                self.nodes.append(node)

        if not self.tick:
            self.phase +=1
            self.animate(self,
                         tick = 500,
                         duration = 4,
                         on_complete = self.reset_tick,
                         easing = Easing.Expo.ease_out)

        for node in self.nodes:
            if node.phase < self.phase and node.distance < self.tick:
                node.phase = self.phase
                self.tweener.kill_tweens(node)
                self.animate(node,
                             duration = 0.5,
                             radius = 20,
                             easing = Easing.Elastic.ease_in,
                             on_complete = self.slide_back)


    def reset_tick(self, target):
        self.tick = 0

    def slide_back(self, node):
        self.animate(node,
                     radius = 4,
                     duration = 0.5,
                     easing = Easing.Elastic.ease_out)
        self.animate(node,
                     angle = node.angle + ((round(random() * 2) - 1) * random() * math.pi / 8),
                     distance = node.distance + ((round(random() * 2) - 1) * random() * 20),
                     duration = 0.5,
                     easing = Easing.Expo.ease_out)

class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(600, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()

example = BasicWindow()
gtk.main()
