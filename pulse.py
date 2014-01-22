#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
    Demo of a a timer based ripple running through nodes and initiating
    sub-animations. Not sure where this could come handy.
"""


from gi.repository import Gtk as gtk
from lib import graphics
from lib.pytweener import Easing
from random import random
import math

class Node(graphics.Sprite):
    def __init__(self, angle, distance):
        graphics.Sprite.__init__(self)

        self.angle = angle
        self.distance = distance
        self.base_angle = 0
        self.distance_scale = 1
        self.radius = 4.0
        self.phase = 0
        self.connect("on-render", self.on_render)

    def on_render(self, sprite):
        self.graphics.clear()
        self.x = math.cos(self.angle + self.base_angle) * self.distance * self.distance_scale
        self.y = math.sin(self.angle + self.base_angle) * self.distance * self.distance_scale

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
        self.connect("on-mouse-move", self.on_mouse_move)

    def on_mouse_move(self, scene, event):
        if gdk.ModifierType.BUTTON1_MASK & event.state:
            # rotate and scale on mouse
            base_angle = math.pi * 2 * ((self.width / 2 - event.x) / self.width) / 3
            distance_scale = math.sqrt((self.width / 2 - event.x) ** 2 + (self.height / 2 - event.y) ** 2) \
                             / math.sqrt((self.width / 2) ** 2 + (self.height / 2) ** 2)

            for node in self.nodes:
                node.base_angle = base_angle
                node.distance_scale = distance_scale

    def on_enter_frame(self, scene, context):
        self.container.x = self.width / 2
        self.container.y = self.height / 2

        if len(self.nodes) < 100:
            for i in range(100 - len(self.nodes)):
                angle = random() * math.pi * 2
                distance = random() * 500

                node = Node(angle, distance)
                node.phase = self.phase
                self.container.add_child(node)
                self.nodes.append(node)

        if not self.tick:
            self.phase +=1
            self.animate(self,
                         tick = 550,
                         duration = 3,
                         on_complete = self.reset_tick,
                         easing = Easing.Expo.ease_in_out)

        for node in self.nodes:
            if node.phase < self.phase and node.distance < self.tick:
                node.phase = self.phase
                self.tweener.kill_tweens(node)
                self.animate(node,
                             duration = 0.5,
                             radius = 20,
                             easing = Easing.Expo.ease_in,
                             on_complete = self.slide_back)


    def reset_tick(self, target):
        self.tick = 0

    def slide_back(self, node):
        self.animate(node,
                     radius = 4,
                     duration = 0.5,
                     easing = Easing.Expo.ease_out)

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
