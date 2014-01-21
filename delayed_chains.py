#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2014 Toms Bauģis <toms.baugis at gmail.com>

"""
    The delayed chains makes an animation where each next sprite animates a
    fraction later.
    Play with get_delay and get_duration functions to get very different effects.
"""

import math

from gi.repository import Gtk as gtk
from lib import graphics
from lib.pytweener import Easing

class FiddlyBit(graphics.Sprite):
    def __init__(self, **kwargs):
        graphics.Sprite.__init__(self, **kwargs)
        self.connect("on-render", self.on_render)

    def on_render(self, sprite):
        self.graphics.set_line_style(width=1)
        self.graphics.move_to(0.5, -150)
        self.graphics.line_to(0.5, 150)
        self.graphics.stroke("#999")




class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.fiddly_bits = []
        self.fiddly_bits_container = graphics.Sprite(interactive=True)
        self.add_child(self.fiddly_bits_container)

        self.current_angle, self.current_reverse = math.pi, True

        self.fiddly_bits_container.connect("on-mouse-over", self.on_fiddly_over)
        self.fiddly_bits_container.connect("on-mouse-out", self.on_fiddly_out)
        self.fiddly_bits_container.connect("on-mouse-move", self.on_fiddly_mouse_move)

        self.connect("on-resize", self.on_resize)
        self.connect("on-enter-frame", self.on_enter_frame)

    def on_fiddly_over(self, sprite):
        self.stop_animation(self.fiddly_bits)

    def on_fiddly_out(self, sprite):
        self.roll(self.current_angle, self.current_reverse)

    def on_fiddly_mouse_move(self, sprite, event):
        width = self.width
        def normalized(x):
            return (x - 50) * 1.0 / 600

        # find position in range 0..1
        pos = normalized(event.x)
        for bit in self.fiddly_bits:
            bit_pos = normalized(bit.x)
            bit.rotation = (bit_pos - pos - 0.5) * math.pi

    def on_resize(self, scene, event):
        self.stop_animation(self.fiddly_bits)
        self.populate_fiddlybits()
        self.current_angle = math.pi
        self.roll(self.current_angle, self.current_reverse)

    def populate_fiddlybits(self):
        self.fiddly_bits_container.clear()

        width = self.width
        self.fiddly_bits = [FiddlyBit() for i in range(width / 10)]

        step = (width - 100) *1.0 / len(self.fiddly_bits)



        x, y = 50, self.height / 2
        self.fiddly_bits_container.graphics.fill_area(0, y-150, width, 300, "#000", 0)


        delay = 0
        for i, bit in enumerate(self.fiddly_bits):
            self.fiddly_bits_container.add_child(bit)
            bit.x, bit.y, bit.rotation = int(x), y, 0
            x += step

    def get_duration(self, i, elems):
        # 1..0 - duration shrinks as we go towards the end
        return 2 + 2.0 * (1 - i * 1.0 / elems)

    def get_delay(self, i, elems):
        # 0..1 - delay grows as we go towards the end
        return 3.0 * i * 1.0 / elems

    def roll(self, angle, reverse=True):
        self.current_angle, self.current_reverse = angle, reverse

        delay = 0
        bits = self.fiddly_bits
        if reverse:
            bits = reversed(bits)

        for i, bit in enumerate(bits):
            on_complete = None
            if i == len(self.fiddly_bits) - 1:
                next_angle = math.pi - angle
                next_reverse = next_angle == math.pi
                on_complete = lambda sprite: sprite.get_scene().roll(next_angle, next_reverse)

            delay = self.get_delay(i, len(self.fiddly_bits))
            duration = self.get_duration(i, len(self.fiddly_bits))

            bit.animate(rotation=angle,
                        duration=duration,
                        delay=delay,
                        easing=Easing.Sine.ease_in_out,
                        on_complete=on_complete)


    def on_enter_frame(self, scene, context):
        if not self.fiddly_bits:
            self.populate_fiddlybits()
            self.roll(self.current_angle, self.current_reverse)


class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_default_size(600, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()

if __name__ == '__main__':
    window = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
