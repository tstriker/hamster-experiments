#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
 * Bouncy Bubbles.
 * Based on code from Keith Peters (www.bit-101.com).
 *
 * Multiple-object collision.

 Ported from processing (http://processing.org/).
 Also added mass to the ball that is equal to the radius.
"""

from gi.repository import Gtk as gtk
from lib import graphics

import math
from random import randint


SPRING = 0.05;
GRAVITY = 0.1;
FRICTION = -0.3;


class Ball(graphics.Circle):
    def __init__(self, x, y, radius):
        graphics.Circle.__init__(self, radius * 2, radius * 2, fill="#aaa", x = x, y = y)

        self.width = self.height = radius * 2

        self.radius = radius

        # just for kicks add mass, so bigger balls would not bounce as easy as little ones
        self.mass = float(self.radius) * 2

        # velocity
        self.vx = 0
        self.vy = 0

    def move(self, width, height):
        self.vy += GRAVITY
        self.x += self.vx
        self.y += self.vy

        # bounce of the walls
        if self.x - self.width < 0 or self.x + self.width > width:
            self.vx = self.vx * FRICTION

        if self.y - self.height < 0 or self.y + self.height > height:
            self.vy = self.vy * FRICTION

        self.x = max(self.width, min(self.x, width - self.width))
        self.y = max(self.height, min(self.y, height - self.height))


    def colide(self, others):
        for ball in others:
            if ball == self:
                continue

            dx = ball.x - self.x
            dy = ball.y - self.y

            # we are using square as root is bit expensive
            min_distance = (self.radius + ball.radius) * (self.radius + ball.radius)

            if (dx * dx + dy * dy) < min_distance:
                min_distance = self.radius + ball.radius
                angle = math.atan2(dy, dx)
                target_x = self.x + math.cos(angle) * min_distance
                target_y = self.y + math.sin(angle) * min_distance

                ax = (target_x - ball.x) * SPRING
                ay = (target_y - ball.y) * SPRING

                mass_ratio = self.mass / ball.mass

                self.vx -= ax / mass_ratio
                self.vy -= ay / mass_ratio

                # repulse
                ball.vx += ax * mass_ratio
                ball.vy += ay * mass_ratio


class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.balls = []
        self.window_pos = None

        self.connect("on-enter-frame", self.on_enter_frame)

    def on_enter_frame(self, scene, context):
        # render and update positions of the balls
        if not self.balls:
            for i in range(15):
                radius = randint(10, 30)
                ball = Ball(randint(radius, self.width - radius),
                                    randint(radius, self.height - radius),
                                    radius)
                self.balls.append(ball)
                self.add_child(ball)


        for ball in self.balls:
            ball.move(self.width, self.height)
            ball.colide(self.balls)


        window_pos = self.get_toplevel().get_position()
        if self.window_pos and window_pos != self.window_pos:
            dx = window_pos[0] - self.window_pos[0]
            dy = window_pos[1] - self.window_pos[1]
            for ball in self.balls:
                ball.x -= dx
                ball.y -= dy
        self.window_pos = window_pos

        self.redraw()


class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_size_request(700, 300)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    gtk.main()
