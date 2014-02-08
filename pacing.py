#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2014 You <your.email@someplace>

"""Base template"""
import math

from gi.repository import Gtk as gtk
from lib import graphics
from lib.pytweener import Easing

class Rect(graphics.Sprite):
    def __init__(self, **kwargs):
        graphics.Sprite.__init__(self, **kwargs)
        self.connect("on-render", self.on_render)

    def on_render(self, sprite):
        self.graphics.rectangle(0, 0, 100, 100)
        self.graphics.fill_stroke("#444", "#444")

class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        pair = graphics.Sprite(x=200, y=200)
        pair.add_child(Rect(),
                       Rect(rotation=math.radians(-90)))
        self.add_child(pair)
        self.kick(pair.sprites[0], 180)


        triplet = graphics.Sprite(x=500, y=200)
        triplet.add_child(Rect(),
                          Rect(rotation=math.radians(-90)),
                          Rect(rotation=math.radians(-180)),
                         )
        self.add_child(triplet)
        self.kick(triplet.sprites[0], 90)


    def kick(self, sprite, angle):
        def kick_next(sprite):
            #sprite.parent.rotation += math.radians(20)
            sprites = sprite.parent.sprites
            next_sprite = sprites[(sprites.index(sprite) + 1) % len(sprites)]
            self.kick(next_sprite, angle)

        def punch_parent(sprite):
            return
            sprite.parent.rotation += math.radians(.2)

        sprite.animate(rotation = sprite.rotation + math.radians(angle),
                       duration=1,
                       #easing=Easing.Expo.ease_in,
                       on_update=punch_parent,
                       on_complete=kick_next)



class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_default_size(700, 400)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()

if __name__ == '__main__':
    window = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
