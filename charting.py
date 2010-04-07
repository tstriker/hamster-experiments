#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""Base template"""


import gtk
from lib import graphics
import random
import pango

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

        self.label = graphics.Label(str(value), size=8, color="#000")

        self.add_child(self.label)


    def on_mouse_over(self, event):
        self.fill = "#666"

    def on_mouse_out(self, event):
        self.fill = "#999"

    def draw_shape(self):
        self.label.text = str(self.value)

        if self.vertical:
            self.graphics.rectangle(0, -self.size, self.width, self.size, 5)
            self.graphics.rectangle(0, -min(self.size, 3), self.width, min(self.size, 3))

            self.label.x = (self.width - self.label.width) / 2
            vert_offset = min(10, self.label.x * 2)

            if self.label.height < self.size - vert_offset:
                self.label.y = -self.size + vert_offset
            else:
                self.label.y = -self.size - self.label.height - 3

        else:
            self.graphics.rectangle(0, 0, self.size, self.width, 5)
            self.graphics.rectangle(0, 0, min(self.size, 3), self.width)

            self.label.y = (self.width - self.label.height) / 2

            horiz_offset = min(10, self.label.y * 2)

            if self.label.width < self.size - horiz_offset:
                #if it fits in the bar
                self.label.x = self.size - self.label.width - horiz_offset
            else:
                self.label.x = self.size + 3






class Chart(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        self.bars = []
        self.labels = []
        self.vertical = True

        self.plot_area = graphics.Sprite(20, 20, interactive = False)
        self.add_child(self.plot_area)

        self.connect("on-enter-frame", self.on_enter_frame)

        self.max_width = 200

    def plot(self, keys, data):
        bars = dict([(bar.key, bar.normalized) for bar in self.bars])

        max_val = float(max(data))

        new_bars, new_labels = [], []
        for key, value in zip(keys, data):
            normalized = value / max_val
            bar = Bar(key, value, normalized)
            if key in bars:
                bar.normalized = bars[key]
                self.tweener.add_tween(bar, normalized=normalized)
            new_bars.append(bar)
            new_labels.append(graphics.Label(key, size = 8, color = "#000"))

        for sprite in self.bars:
            self.plot_area.sprites.remove(sprite)

        for sprite in self.labels:
            self.sprites.remove(sprite)

        self.bars, self.labels = new_bars, new_labels
        self.add_child(*self.labels)
        self.plot_area.add_child(*self.bars)

        self.redraw()

    def on_enter_frame(self, scene, context):

        self.plot_area.x = 80
        self.plot_area.width = self.width - self.plot_area.x
        self.plot_area.y = round(self.height * 0.1)
        self.plot_area.height = round(self.height * 0.8)

        if 1 == 1:
            x = 0
            for i, (label, bar) in enumerate(zip(self.labels, self.bars)):
                bar_width = min(round((self.plot_area.width - x) / (len(self.bars) - i)), self.max_width)
                bar.x = x
                bar.y = self.plot_area.height
                bar.width = bar_width
                bar.size = round(self.plot_area.height * 0.9 * bar.normalized)

                label.y = self.plot_area.y + self.plot_area.height + 3
                label.x = x + (bar_width - label.width) / 2 + self.plot_area.x

                x += bar_width + 1


        else:
            #horizontal
            y = 0
            for i, (label, bar) in enumerate(zip(self.labels, self.bars)):
                bar_width = min(round((self.plot_area.height - y) / (len(self.bars) - i)), self.max_width)
                bar.x = 0
                bar.y = y
                bar.vertical = False
                bar.width = bar_width
                bar.size = round(self.plot_area.width * 0.9 * bar.normalized)


                label.y = y + (bar_width - label.height) / 2 + self.plot_area.y
                label.x = 10
                label.width = 70

                y += bar_width + 1


class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(400, 200)
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
        self.chart.plot(['Bananas and apples','Other fruits','Chocolate smoothy'], [random.random() for i in range(3)])


example = BasicWindow()
gtk.main()
