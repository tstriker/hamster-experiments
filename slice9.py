#!/usr/bin/env python

import gtk, cairo

from lib import graphics

class Slice9(graphics.Sprite):
    def __init__(self, file_name, x1, x2, y1, y2):
        graphics.Sprite.__init__(self)

        self.cols = (x1, x2)
        self.rows = (y1, y2)

        img = cairo.ImageSurface.create_from_png(file_name)
        img_w, img_h = img.get_width(), img.get_height()

        img_content = img.get_content()

        self.support_alpha = False
        if img_content in (cairo.CONTENT_ALPHA, cairo.CONTENT_COLOR_ALPHA):
            self.support_alpha = True


        def get_slice(x, y, w, h):
            image = self._get_blank_image(w, h)
            ctx = cairo.Context(image)
            ctx.set_source_surface(img, -x, -y)
            ctx.rectangle(0, 0, w, h)
            ctx.fill()
            return image

        self.slices = []
        exes = (0, x1, x2, img_w)
        ys = (0, y1, y2, img_h)

        for y1, y2 in zip(ys, ys[1:]):
            for x1, x2 in zip(exes, exes[1:]):
                x, y, w, h = x1, y1, x2 - x1, y2 - y1
                slice = get_slice(x, y, w, h)
                self.slices.append(dict(image=slice, x=x, y=y, w=w, h=h))

        self.width = 500
        self.height = 100

        self.center_graphics_style = "pattern"
        self.center_color = None
        self.center_bitmap = None

        self.connect("on-render", self.on_render)


    #todo: get feedback on this bug from Toms
    def _get_blank_image(self, width, height):
        return cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        """
        if (self.support_alpha):
            return cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        else:
            return cairo.ImageSurface(cairo.FORMAT_RGB24, width, height)
        """

    def on_render(self, sprite):
        def put_image(image, x, y):
            self.graphics.save_context()
            self.graphics.translate(x, y)
            self.graphics.set_source_surface(image)
            self.graphics.paint()
            self.graphics.restore_context()

        def put_pattern(image, x, y, w, h):
            pattern = cairo.SurfacePattern(image)
            pattern.set_extend(cairo.EXTEND_REPEAT)
            self.graphics.save_context()
            self.graphics.translate(x, y)
            self.graphics.set_source(pattern)
            self.graphics.rectangle(0, 0, w, h)
            self.graphics.fill()
            self.graphics.restore_context()


        # top left
        put_image(self.slices[0]['image'], 0, 0)

        # top center - repeat width
        put_pattern(self.slices[1]['image'],
                    self.slices[1]['x'],
                    self.slices[1]['y'],
                    self.width - self.slices[2]['w'] - self.slices[1]['x'],
                    self.slices[1]['h'])

        # top right
        put_image(self.slices[2]['image'],
                  self.width - self.slices[2]['w'],
                  0)

        # left - repeat height
        put_pattern(self.slices[3]['image'],
                    self.slices[3]['x'],
                    self.slices[3]['y'],
                    self.slices[3]['w'],
                    self.height - self.slices[6]['h'] - self.slices[3]['y'])

        # center - repeat width and height
        put_pattern(self.slices[4]['image'],
                    self.slices[4]['x'],
                    self.slices[4]['y'],
                    self.width - self.slices[5]['w'] - self.slices[4]['x'],
                    self.height - self.slices[7]['h'] - self.slices[4]['y'])

        # right - repeat height
        put_pattern(self.slices[5]['image'],
                    self.width - self.slices[5]['w'],
                    self.slices[5]['y'],
                    self.slices[5]['w'],
                    self.height - self.slices[8]['h'] - self.slices[5]['y'])

        # bottom left
        put_image(self.slices[6]['image'], 0, self.height - self.slices[6]['h'])

        # bottom center - repeat width
        put_pattern(self.slices[7]['image'],
                    self.slices[7]['x'],
                    self.height - self.slices[7]['h'],
                    self.width - self.slices[8]['w'] - self.slices[7]['x'],
                    self.slices[7]['h'])

        # bottom right
        put_image(self.slices[8]['image'], self.width - self.slices[8]['w'], self.height - self.slices[8]['h'])



class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.slice = Slice9('assets/slice9.png', 35, 230, 35, 220)
        self.add_child(self.slice)
        self.connect("on-enter-frame", self.on_enter_frame)

    def on_enter_frame(self, scene, context):
        self.slice.width = self.width
        self.slice.height = self.height

class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(640, 516)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    gtk.main()
