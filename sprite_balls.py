#!/usr/bin/env python
# - coding: utf-8 -

from gi.repository import Gtk as gtk
from lib import graphics
from themes import utils

import cairo

class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        self.sprite_sheet = graphics.Image("assets/spritesheet.png")
        self.frame = 0

        self.connect("on-enter-frame", self.on_enter_frame)

        x, y = 0, 0
        step = 60
        self.coords = []
        for i in range(60):
            self.coords.append((x, y))

            self.add_child(utils.SpriteSheetImage(self.sprite_sheet, x, y, 60, 60, x=x, y=y))

            x += step
            if x > 420:
                x = 0
                y += step

        print self.coords

    def on_enter_frame(self, scene, context):
        for (x, y), sprite in zip(self.coords, self.sprites[self.frame:] + self.sprites[:self.frame]):
            sprite.offset_x, sprite.offset_y = x, y


        self.frame +=1
        if self.frame > 59:
            self.frame = 0


        self.redraw()




class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_default_size(800, 600)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        scene = Scene()
        window.add(scene)
        window.show_all()

if __name__ == '__main__':
    window = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
