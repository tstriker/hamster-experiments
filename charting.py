#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""Base template"""


import gtk
from lib import graphics
import random

class Bar(graphics.Shape):
    def __init__(self, key, value, normalized, vertical = True):
        graphics.Shape.__init__(self, fill="#999")
        self.key, self.value, self.normalized = key, value, normalized
        self.size = 0
        self.width = 20
        self.vertical = True
        self.interactive = True
        self.connect("on-mouse-over", self.on_mouse_over)
        self.connect("on-mouse-out", self.on_mouse_out)

    def on_mouse_over(self, event):
        self.fill = "#666"

    def on_mouse_out(self, event):
        self.fill = "#999"

    def draw_shape(self):
        if self.vertical:
            self.graphics.rectangle(0, -self.size, self.width, self.size, 5)
            self.graphics.rectangle(0, -min(self.size, 3), self.width, min(self.size, 3))
        else:
            self.graphics.rectangle(0, 0, self.size, self.width, 5)
            self.graphics.rectangle(0, 0, min(self.size, 3), self.width)

class Chart(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        self.bars = []
        self.vertical = True

        self.plot_area = graphics.Sprite(20, 20, interactive = False)
        self.add_child(self.plot_area)

        self.connect("on-enter-frame", self.on_enter_frame)

    def plot(self, keys, data):
        bars = dict([(bar.key, bar.normalized) for bar in self.bars])

        max_val = float(max(data))

        new_bars = []
        for key, value in zip(keys, data):
            normalized = value / max_val
            bar = Bar(key, value, normalized)
            if key in bars:
                bar.normalized = bars[key]
                self.tweener.add_tween(bar, normalized=normalized)
            new_bars.append(bar)

        for bar in self.bars:
            self.plot_area.child_sprites.remove(bar)


        self.bars = new_bars
        self.plot_area.add_child(*self.bars)

        self.redraw()

    def on_enter_frame(self, scene, context):

        self.plot_area.x = round(self.width * 0.1)
        self.plot_area.width = round(self.width * 0.8)
        self.plot_area.y = round(self.height * 0.1)
        self.plot_area.height = round(self.height * 0.8)

        if 1 == 2:
            x = 0
            for i, bar in enumerate(self.bars):
                bar_width = round((self.plot_area.width - x) / (len(self.bars) - i))
                bar.x = x
                bar.y = self.plot_area.height
                bar.width = bar_width
                bar.size = round(self.plot_area.height * 0.8 * bar.normalized)

                x += bar_width + 1
        else:
            #horizontal
            y = 0
            for i, bar in enumerate(self.bars):
                bar_width = round((self.plot_area.height - y) / (len(self.bars) - i))
                bar.x = 0
                bar.y = y
                bar.vertical = False
                bar.width = bar_width
                bar.size = round(self.plot_area.height * 0.8 * bar.normalized)

                y += bar_width + 1


class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(600, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        self.chart = Chart()
        self.chart.plot(['a','b','c'], [random.random() for i in range(3)])

        button = gtk.Button("Random Values")
        button.connect("clicked", self.on_random_clicked)

        vbox = gtk.VBox()
        vbox.pack_start(self.chart)
        vbox.pack_start(button, False)

        window.add(vbox)
        window.show_all()

    def on_random_clicked(self, event):
        self.chart.plot(['a','b','c'], [random.random() for i in range(3)])


example = BasicWindow()
gtk.main()
