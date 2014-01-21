#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>
# Last example from the turorial
# http://wiki.github.com/tbaugis/hamster_experiments/tutorial

from gi.repository import Gtk as gtk
from lib import graphics
from lib.pytweener import Easing


class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        for i in range(14):
            self.add_child(graphics.Rectangle(40, 40, 3,
                                              y = 420, x = i * 45 + 6,
                                              fill = "#999", stroke="#444", interactive = True))

        self.connect("on-mouse-over", self.on_mouse_over)
        #self.connect("on-enter-frame", self.on_enter_frame)

    def on_enter_frame(self, scene, context):
        self.redraw()

    def on_mouse_over(self, scene, sprite):
        if not sprite: return #ignore blank clicks

        if self.tweener.get_tweens(sprite): #must be busy
            return

        def bring_back(sprite):
            self.animate(sprite, y = 420, scale_x = 1, scale_y = 1, x = sprite.original_x, easing = Easing.Bounce.ease_out)

        sprite.original_x = sprite.x
        self.animate(sprite, y = 150, scale_x = 2, x = sprite.x - 20, scale_y = 2, on_complete = bring_back)


window = gtk.Window()
window.set_size_request(640, 480)
window.connect("delete_event", lambda *args: gtk.main_quit())
window.add(Scene())
window.show_all()
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
gtk.main()
