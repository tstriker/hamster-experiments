#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

import colorsys

import gtk
from lib import graphics
from lib.pytweener import Easing


class TailParticle(object):
    def __init__(self, x, y, color, follow = None):
        self.x = x
        self.y = y
        self.follow = follow
        self.color = color

    def draw(self, area):
        area.draw_rect(self.x - 5, self.y - 5, 10, 10, 3)


        area.set_color(self.color)
        area.context.fill()
        if self.follow:
            area.context.move_to(self.x, self.y)
            area.context.line_to(self.follow.x, self.follow.y)
            area.context.stroke()

class Canvas(graphics.Area):
    def __init__(self):
        graphics.Area.__init__(self)

        self.tail = []
        parts = 30
        for i in range(parts):
            previous = self.tail[-1] if self.tail else None
            color = colorsys.hls_to_rgb(0.6, i / float(parts), 1)

            self.tail.append(TailParticle(10, 10, color, previous))

        self.connect("mouse-move", self.on_mouse_move)
        self.mouse_moving = False


    def on_mouse_move(self, area, coords, state):
        # oh i know this should not be performed using tweeners, but hey - a demo!
        x, y = coords

        for particle in reversed(self.tail):
            new_x, new_y = x, y
            if particle.follow:
                new_x, new_y = particle.follow.x, particle.follow.y

            self.tweener.killTweensOf(particle)

            self.animate(particle, dict(x=float(new_x), y=float(new_y)), duration = 0.3, easing = Easing.Expo.easeOut)

        self.mouse_moving = True


    def on_expose(self):
        # on expose is called when we are ready to draw
        for tail in reversed(self.tail):
            tail.draw(self)

        if self.mouse_moving == False:
            # retract tail when the movement has stopped
            for particle in reversed(self.tail):
                if particle.follow and round(particle.follow.x, 2) != round(particle.x, 2) and round(particle.follow.y, 2) != round(particle.y, 2) :
                    new_x, new_y = particle.follow.x, particle.follow.y
                    self.tweener.killTweensOf(particle)
                    self.animate(particle, dict(x=new_x, y=new_y), duration = 0.3, easing = Easing.Expo.easeOut, instant = False)

        self.mouse_moving = False
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

