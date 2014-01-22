# - coding: utf-8 -

# Copyright (c) 2011-2012 Media Modifications, Ltd.
# Dual licensed under the MIT or GPL Version 2 licenses.

from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import GdkPixbuf
from gi.repository import GObject as gobject

import cairo
from lib import graphics
from ui import Widget

class Image(Widget):
    """An image widget that can scale smartly. Use slice_* params to control
    how the image scales.
    """


    def __init__(self, path = None, slice_left=0, slice_right=0, slice_top=0, slice_bottom=0, fill = False, **kwargs):
        Widget.__init__(self, fill = fill, **kwargs)

        #: path to the image file
        self.path = path
        self.image_data, self.image_w, self.image_h = None, None, None

        if path:
            self.image_data = cairo.ImageSurface.create_from_png(self.path)
            self.image_w, self.image_h = self.image_data.get_width(), self.image_data.get_height()

        self.min_width, self.min_height = self.min_width or self.image_w, self.min_height or self.image_h

        #: pixels from left that should not be scaled upon image scale
        self.slice_left = slice_left

        #: pixels from right that should not be scaled upon image scale
        self.slice_right = slice_right

        #: pixels from top that should not be scaled upon image scale
        self.slice_top = slice_top

        #: pixels from bottom that should not be scaled upon image scale
        self.slice_bottom = slice_bottom

        self._slices = []
        self._slice()


    def __setattr__(self, name, val):
        Widget.__setattr__(self, name, val)
        if self.__dict__.get(name, "hamster_graphics_no_value_really") == val:
            return

        # reslice when params change
        if name in ("slice_left", "slice_top", "slice_right", "slice_bottom") and hasattr(self, "_slices"):
            self._slice()

        if name == "path" and val and hasattr(self, "image_data"):
            self.image_data = cairo.ImageSurface.create_from_png(val)
            self.image_w, self.image_h = self.image_data.get_width(), self.image_data.get_height()
            self._slice()


    def _slice(self):
        if not self.image_data:
            return

        self._slices = []

        def get_slice(x, y, w, h):
            # we are grabbing bigger area and when painting will crop out to
            # just the actual needed pixels. This is done because otherwise when
            # stretching border, it uses white pixels to blend in
            x, y = x - 1, y - 1
            image = cairo.ImageSurface(cairo.FORMAT_ARGB32, w+2, h+2)
            ctx = cairo.Context(image)
            if isinstance(self.image_data, GdkPixbuf.Pixbuf):
                ctx.set_source_pixbuf(self.image_data, -x, -y)
            else:
                ctx.set_source_surface(self.image_data, -x, -y)

            ctx.rectangle(0, 0, w+2, h+2)
            ctx.fill()
            return image, w, h

        exes = (0, self.slice_left or 0, self.slice_right or self.image_w, self.image_w)
        ys = (0, self.slice_top or 0, self.slice_bottom or self.image_h, self.image_h)
        for y1, y2 in zip(ys, ys[1:]):
            for x1, x2 in zip(exes, exes[1:]):
                self._slices.append(get_slice(x1, y1, x2 - x1, y2 - y1))

    def get_center_bounds(self):
        return (self.slice_left,
                self.slice_top,
                self.width - self.slice_left - (self.image_w - self.slice_right),
                self.height - self.slice_top - (self.image_h - self.slice_bottom))


    def do_render(self):
        if not self.image_data:
            return

        graphics, width, height = self.graphics, self.width, self.height

        def put_pattern(image, x, y, w, h):
            pattern = cairo.SurfacePattern(image[0])

            if w > 0 and h > 0:
                pattern.set_matrix(cairo.Matrix(x0=1, y0=1, xx = (image[1]) / float(w), yy = (image[2]) / float(h)))
                graphics.save_context()
                graphics.translate(x, y)
                graphics.set_source(pattern)
                graphics.rectangle(0, 0, w, h)
                graphics.fill()
                graphics.restore_context()


        # top-left
        put_pattern(self._slices[0], 0, 0, self.slice_left, self.slice_top)


        # top center - repeat width
        put_pattern(self._slices[1],
                    self.slice_left, 0,
                    width - self.slice_left - self.slice_right, self.slice_top)

        # top-right
        put_pattern(self._slices[2], width - self.slice_right, 0, self.slice_left, self.slice_top)


        # left - repeat height
        put_pattern(self._slices[3],
                    0, self.slice_top,
                    self.slice_left, height - self.slice_top - self.slice_bottom)

        # center - repeat width and height
        put_pattern(self._slices[4],
                    self.slice_left, self.slice_top,
                    width - self.slice_left - self.slice_right,
                    height - self.slice_top - self.slice_bottom)

        # right - repeat height
        put_pattern(self._slices[5],
                    width - self.slice_right, self.slice_top,
                    self.slice_right, height - self.slice_top - self.slice_bottom)

        # bottom-left
        put_pattern(self._slices[6], 0, height - self.slice_top, self.slice_left, self.slice_top)

        # bottom center - repeat width
        put_pattern(self._slices[7],
                    self.slice_left, height - self.slice_bottom,
                    width - self.slice_left - self.slice_right, self.slice_bottom)

        # bottom-right
        put_pattern(self._slices[8],
                    width - self.slice_right, height - self.slice_top,
                    self.slice_right, self.slice_top)

        graphics.rectangle(0, 0, width, height)
        graphics.new_path()
