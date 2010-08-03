#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""Base template"""


import gtk
from lib import graphics
from lib.pytweener import Easing
import random

class Wonky(graphics.Sprite):
    def __init__(self, x, y, radius):
        graphics.Sprite.__init__(self, x=x, y=y, interactive=True)
        self.radius = radius
        self.fill = "#aaa"
        self.connect("on-render", self.on_render)

    def on_render(self, sprite):
        self.graphics.circle(0, 0, self.radius)
        self.graphics.fill_stroke(self.fill, "#222")



class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self, framerate=30)

        self.connect("on-mouse-over", self.on_mouse_over)
        self.connect("on-mouse-out", self.on_mouse_out)
        self.connect("on-click", self.on_click)
        self.connect("on-enter-frame", self.on_enter_frame)

    def on_mouse_over(self, scene, sprite):
        sprite.original_radius = sprite.radius
        self.animate(sprite, radius = sprite.radius * 1.3, easing = Easing.Elastic.ease_out)


    def on_mouse_out(self, scene, sprite):
        self.animate(sprite, radius = sprite.original_radius, easing = Easing.Elastic.ease_out)

    def on_click(self, scene, event, sprite):
        if sprite.fill == "#ff0000":
            self.animate(sprite, fill="#aaa")
        else:
            self.animate(sprite, fill="#f00")

    def on_enter_frame(self, scene, context):
        print self.fps
        if not self.sprites:
            for x in range(30, self.width, 50):
                for y in range(30, self.height, 50):
                    wonky = Wonky(x, y, 20)
                    self.add_child(wonky)
                    self.animate(wonky, radius = wonky.radius * 1.3, easing = Easing.Elastic.ease_out, duration=3)




class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(800, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()

example = BasicWindow()
gtk.main()
