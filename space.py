#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2014 Toms Baugis <toms.baugis@gmail.com>

"""Base template"""
import math

from gi.repository import Gtk as gtk
from gi.repository import GObject as gobject
from lib import graphics

"""wanna look into the third dimensions
 * can't use scale_x, scale_y as those will mess up the stroke
 * should be operating with points in 3d
 * assuming horizon at specific coordinates (middle)
 * at depth 0, x=screen_x, y=screen_y
"""

class Point3D(gobject.GObject):
    __gsignals__ = {
        "on-point-changed": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }
    def __init__(self, x=0, y=0, depth=0, perspective_skew=0):
        gobject.GObject.__init__(self)
        self.perspective_skew = perspective_skew or 0
        self.max_depth = 1000.0

        self._x = x
        self._y = y
        self.z = 1

    @property
    def z_skew(self):
        skew = (self.z / self.max_depth)
        return skew ** 0.3 if skew > 0 else 0

    @property
    def angle(self):
        return math.atan2(self._x, self._y) - math.radians(90)

    @property
    def from_center(self):
        return math.sqrt(self._x ** 2 + self._y ** 2)

    @property
    def x(self):
        x = math.cos(self.angle) * self.from_center
        return x - x * self.z_skew * self.perspective_skew

    @x.setter
    def x(self, val):
        self._x = val
        self.emit("on-point-changed")

    @property
    def y(self):
        y = math.sin(self.angle) * self.from_center
        return -y + y * self.z_skew

    @y.setter
    def y(self, val):
        self._y = val
        self.emit("on-point-changed")


    def __setattr__(self, name, val):
        if isinstance(getattr(type(self), name, None), property) and \
           getattr(type(self), name).fset is not None:
            getattr(type(self), name).fset(self, val)
            return
        gobject.GObject.__setattr__(self, name, val)


    def __iter__(self):
        yield self.x
        yield self.y

    def __repr__(self):
        return "<%s x=%d, y=%d, z=%d>" % (self.__class__.__name__, self.x, self.y, self.z)



class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self, background_color="#333")
        self.a, self.b = Point3D(-800, 500), Point3D(800, 500)

        self.viewport_depth = 0

        self.connect("on-enter-frame", self.on_enter_frame)
        self.connect("on-mouse-move", self.on_mouse_move)

    def on_mouse_move(self, scene, event):
        x = event.x * 1.0 / scene.width
        self.a.perspective_skew = 1 - x
        self.b.perspective_skew = 1 - x

    def on_enter_frame(self, scene, context):
        # you could do all your drawing here, or you could add some sprites
        g = graphics.Graphics(context)

        g.translate(self.width / 2, self.height / 2 - 100)

        g.move_to(-500, 0)
        g.line_to(500, 0)
        g.stroke("#33F2F0", 0.2)

        for z in range(-10, 1000, 50):
            for dot in (self.a, self.b):
                dot.z = z - self.viewport_depth

            g.move_to(*self.a)
            g.line_to(*self.b)

            #g.set_line_style(int(30 * (1 - z / 1000.0)))
            g.stroke("#33F2F0", 1 - z / 1000.0 * 0.8)

        self.viewport_depth += 1
        if self.viewport_depth > 50:
            self.viewport_depth = 0

        self.redraw()
        #self.a.z += 0.01
        #self.b.z += 0.01


        #self.redraw()



class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_default_size(700, 600)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()


if __name__ == '__main__':
    window = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
