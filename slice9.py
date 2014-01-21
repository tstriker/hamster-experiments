#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Erik Blankinship <jedierikb at gmail.com>
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
 An example of slice9 scaling where the center rows and columns get stretched.
 As seen in CSS3 and all other good frameworks.
 This most probably will go into graphics.py eventually.
"""

from gi.repository import Gtk as gtk
import cairo

from lib import graphics

class Slice9(graphics.Sprite):
    def __init__(self, file_name, x1, x2, y1, y2, width = None, height = None):
        graphics.Sprite.__init__(self)

        image = cairo.ImageSurface.create_from_png(file_name)
        image_width, image_height = image.get_width(), image.get_height()

        self.width = width or image_width
        self.height = height or image_height

        self.left, self.right = x1, image_width - x2
        self.top, self.bottom = y1, image_height - y2

        image_content = image.get_content()
        self.slices = []
        def get_slice(x, y, w, h):
            img = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
            ctx = cairo.Context(img)
            ctx.set_source_surface(image, -x, -y)
            ctx.rectangle(0, 0, w, h)
            ctx.fill()
            return img

        exes = (0, x1, x2, image_width)
        ys = (0, y1, y2, image_height)
        for y1, y2 in zip(ys, ys[1:]):
            for x1, x2 in zip(exes, exes[1:]):
                self.slices.append(get_slice(x1, y1, x2 - x1, y2 - y1))

        self.corners = [
            graphics.BitmapSprite(self.slices[0]),
            graphics.BitmapSprite(self.slices[2]),
            graphics.BitmapSprite(self.slices[6]),
            graphics.BitmapSprite(self.slices[8]),
        ]
        self.add_child(*self.corners)


        self.connect("on-render", self.on_render)

    def get_center_bounds(self):
        return (self.left,
                self.top,
                self.width - self.left - self.right,
                self.height - self.top - self.bottom)

    def on_render(self, sprite):
        def put_pattern(image, x, y, w, h):
            pattern = cairo.SurfacePattern(image)
            pattern.set_extend(cairo.EXTEND_REPEAT)
            self.graphics.save_context()
            self.graphics.translate(x, y)
            self.graphics.set_source(pattern)
            self.graphics.rectangle(0, 0, w, h)
            self.graphics.fill()
            self.graphics.restore_context()

        # top center - repeat width
        put_pattern(self.slices[1],
                    self.left, 0,
                    self.width - self.left - self.right, self.top)

        # top right
        self.corners[1].x = self.width - self.right


        # left - repeat height
        put_pattern(self.slices[3],
                    0, self.top,
                    self.left, self.height - self.top - self.bottom)

        # center - repeat width and height
        put_pattern(self.slices[4],
                    self.left, self.top,
                    self.width - self.left - self.right,
                    self.height - self.top - self.bottom)

        # right - repeat height
        put_pattern(self.slices[5],
                    self.width - self.right, self.top,
                    self.right, self.height - self.top - self.bottom)

        # bottom left
        self.corners[2].y = self.height - self.bottom

        # bottom center - repeat width
        put_pattern(self.slices[7],
                    self.left, self.height - self.bottom,
                    self.width - self.left - self.right, self.bottom)

        # bottom right
        self.corners[3].x = self.width - self.right
        self.corners[3].y = self.height - self.bottom




class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.slice = Slice9('assets/slice9.png', 35, 230, 35, 220)
        self.add_child(self.slice)
        self.connect("on-enter-frame", self.on_enter_frame)

    def on_enter_frame(self, scene, context):
        self.slice.x, self.slice.y = 5, 5
        self.slice.width = self.width - 10
        self.slice.height = self.height - 10

class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_default_size(640, 516)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
