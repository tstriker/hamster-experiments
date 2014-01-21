#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""Base template"""


from gi.repository import Gtk as gtk
from lib import graphics
import cairo
import struct

class DropShadow(graphics.Sprite):
    def __init__(self, sprite):
        graphics.Sprite.__init__(self)
        self.original_sprite = sprite
        self.us = False
        #self.original_sprite.connect("on-render", self.on_prev_sprite_render)


    def render(self):
        if self.us:
            return

        if self.original_sprite.graphics.extents:
            x, y, x2, y2 = self.original_sprite.graphics.extents
            print x, y, x2, y2


        self.us = True

        # first we will measure extents (lame)
        image_surface = cairo.ImageSurface(cairo.FORMAT_A1, 0, 0)
        image_context = cairo.Context(image_surface)
        self.original_sprite._draw(image_context)

        extents = self.original_sprite.get_extents()
        width  = int(extents.width) + 10
        height = int(extents.height) + 10


        # creating a in-memory image of current context
        image_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        image_context = cairo.Context(image_surface)


        self.original_sprite._draw(image_context)

        self.us = False

        # now create shadow
        self.blur(image_surface)

        self.graphics.clear()
        self.graphics.set_source_surface(image_surface)
        self.graphics.paint()



    def blur(self, surface):
        buffer = surface.get_data()

        v = 1.0 / 9.0
        kernel = ((v, v, v),
                  (v, v, v),
                  (v, v, v))

        kernel_range = range(-1, 2) # surrounding the pixel


        extents = self.original_sprite.get_extents()
        width  = int(extents.width) + 10
        height = int(extents.height) + 10



        # we will need all the pixel colors anyway, so let's grab them once
        pixel_colors = struct.unpack_from('BBBB' * width * height, buffer)

        new_pixels = [0] * width * height * 4 # target matrix

        for x in range(1, width - 1):
            for y in range(1, height - 1):
                r,g,b,a = 0,0,0,0
                pos = (y * width + x) * 4

                for ky in kernel_range:
                    for kx in kernel_range:
                        k = kernel[kx][ky]
                        k_pos = pos + ky * width * 4 + kx * 4

                        pixel_r,pixel_g,pixel_b,pixel_a = pixel_colors[k_pos:k_pos + 4]

                        r += k * pixel_r
                        g += k * pixel_g
                        b += k * pixel_b
                        a += k * pixel_a

                avg = min((r + g + b) / 3.0 * 0.6, 255)
                new_pixels[pos:pos+4] = (avg, avg, avg, a)

        struct.pack_into('BBBB' * width * height, buffer, 0, *new_pixels)

class SomeShape(graphics.Sprite):
    def __init__(self):
        graphics.Sprite.__init__(self, interactive=True, draggable=True)

        #self.graphics.circle(25, 25, 15)
        label = graphics.Label("", 24, "#fff")
        label.markup = "<b>Drag me around!</b>"
        self.add_child(label)

        self.graphics.rectangle(0, 0, label.width, label.height)
        self.graphics.new_path()

        #self.graphics.fill_area(5, 5, 80, 80, "#fff")

        self.connect("on-render", self.on_render)

    def on_render(self, sprite):
        self.shadow.render()

class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        self.shape = SomeShape()

        shadow = DropShadow(self.shape)
        shadow.x, shadow.y = -4, -4

        self.shape.shadow = shadow

        self.add_child(shadow)
        self.add_child(self.shape)

        self.connect("on-drag", self.on_sprite_drag)
        #self.animate(self.shape, opacity=1, duration=1.0)
        self.redraw()

    def on_sprite_drag(self, scene, sprite, event):
        extents = sprite.get_extents()
        width, height = extents.width, extents.height

        sprite.shadow.x = sprite.x + (sprite.x + (width - self.width) / 2.0) / float(self.width) * 8
        sprite.shadow.y = sprite.y + (sprite.y + (height - self.height) / 2.0) / float(self.height) * 8



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
