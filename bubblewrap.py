#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""Punishing cairo for expensive non-pixel-aligned stroking"""


from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from lib import graphics
from lib.pytweener import Easing
import random

class Wonky(graphics.Sprite):
    def __init__(self, x, y, radius, cache_as_bitmap):
        graphics.Sprite.__init__(self, x=x, y=y, interactive=True, cache_as_bitmap = cache_as_bitmap)
        self.radius = radius
        self.fill = "#aaa"
        self.connect("on-render", self.on_render)

    def on_render(self, sprite):
        self.graphics.circle(0, 0, self.radius)
        self.graphics.fill_stroke(self.fill, "#222")



class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        self.connect("on-mouse-over", self.on_mouse_over)
        self.connect("on-mouse-out", self.on_mouse_out)
        self.connect("on-mouse-up", self.on_mouse_up)
        self.connect("on-mouse-move", self.on_mouse_move)
        self.connect("on-enter-frame", self.on_enter_frame)
        self.cache_as_bitmap = True
        self.paint_color = None
        self.add_child(graphics.Rectangle(600, 40, 4, "#666", opacity = 0.8, z_order = 999998))
        self.fps_label = graphics.Label(size = 20, color = "#fff", z_order=999999, x = 10, y = 4)
        self.add_child(self.fps_label)
        self.bubbles = []
        self.max_zorder = 1

    def on_mouse_move(self, scene, event):
        sprite = self.get_sprite_at_position(event.x, event.y)

        if sprite and gdk.ModifierType.BUTTON1_MASK & event.state:
            if self.paint_color is None:
                if sprite.fill == "#f00":
                    self.paint_color =  "#aaa"
                elif sprite.fill == "#aaa":
                    self.paint_color = "#f00"
            self.animate(sprite, fill=self.paint_color)

    def on_mouse_up(self, scene, event):
        self.paint_color = None

    def on_mouse_over(self, scene, sprite):
        sprite.original_radius = sprite.radius
        self.animate(sprite, radius = sprite.radius * 1.3, easing = Easing.Elastic.ease_out, duration = 1)
        self.max_zorder +=1
        sprite.z_order = self.max_zorder


    def on_mouse_out(self, scene, sprite):
        self.animate(sprite, radius = sprite.original_radius, easing = Easing.Elastic.ease_out)

    def on_enter_frame(self, scene, context):
        self.fps_label.text = "Hold mouse down and drag to paint. FPS: %.2f" % self.fps

        if not self.bubbles:
            for x in range(30, self.width, 50):
                for y in range(30, self.height, 50):
                    wonky = Wonky(x, y, 20, self.cache_as_bitmap)
                    self.bubbles.append(wonky)
                    self.add_child(wonky)
                    self.animate(wonky,
                                 radius = wonky.radius * 1.3,
                                 easing = Easing.Elastic.ease_out,
                                 duration=2)




class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_size_request(800, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        vbox = gtk.VBox()

        self.scene = Scene()
        vbox.pack_start(self.scene, True, True, 0)

        self.button = gtk.Button("Cache as bitmap = True")

        def on_click(event):
            self.scene.cache_as_bitmap = not self.scene.cache_as_bitmap
            self.scene.remove_child(*self.scene.bubbles)
            self.scene.bubbles = []
            self.button.set_label("Cache as bitmap = %s" % str(self.scene.cache_as_bitmap))
            self.scene.redraw()


        self.button.connect("clicked", on_click)
        vbox.pack_start(self.button, False, False, 0)

        window.add(vbox)
        window.show_all()

example = BasicWindow()
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
gtk.main()
