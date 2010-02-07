#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

import colorsys

import gtk
from lib import graphics
from lib.pytweener import Easing


class TailParticle(graphics.Sprite):
    def __init__(self, x, y, color, follow = None):
        graphics.Sprite.__init__(self, interactive=False)
        self.x = x
        self.y = y
        self.follow = follow

        self.graphics.set_color(color)
        self.graphics.rectangle(-5, -5, 10, 10, 3)
        self.graphics.fill()


class Canvas(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        self.tail = []
        parts = 30
        for i in range(parts):
            previous = self.tail[-1] if self.tail else None
            color = colorsys.hls_to_rgb(0.6, i / float(parts), 1)

            self.tail.append(TailParticle(10, 10, color, previous))

            for tail in reversed(self.tail):
                self.add_child(tail) # add them to scene other way round


        self.mouse_moving = False

        self.connect("mouse-move", self.on_mouse_move)
        self.connect("on-enter-frame", self.on_enter_frame)


    def on_mouse_move(self, area, event):
        # oh i know this should not be performed using tweeners, but hey - a demo!
        x, y = event.x, event.y

        for particle in reversed(self.tail):
            new_x, new_y = x, y
            if particle.follow:
                new_x, new_y = particle.follow.x, particle.follow.y

            self.tweener.killTweensOf(particle)
            self.animate(particle, dict(x=float(new_x), y=float(new_y)), duration = 0.3, easing = Easing.Expo.easeOut, instant = False)

        self.mouse_moving = True
        self.redraw_canvas()


    def on_enter_frame(self, scene, context):
        if self.mouse_moving == False:
            # retract tail when the movement has stopped
            for particle in reversed(self.tail):
                if particle.follow and round(particle.follow.x, 2) != round(particle.x, 2) and round(particle.follow.y, 2) != round(particle.y, 2) :
                    new_x, new_y = particle.follow.x, particle.follow.y
                    self.tweener.killTweensOf(particle)
                    self.animate(particle, dict(x=new_x, y=new_y), duration = 0.3, easing = Easing.Expo.easeOut, instant = False)

        self.mouse_moving = False

        if int(self.tail[0].x) != int(self.tail[-1].x) and int(self.tail[0].y) != int(self.tail[-1].y):
            self.redraw_canvas() # constant redraw (maintaining the requested frame rate)


class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(300, 300)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        canvas = Canvas()

        box = gtk.VBox()
        box.pack_start(canvas)


        window.add(box)
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    gtk.main()
