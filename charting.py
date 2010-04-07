#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""Base template"""


import gtk
from lib import graphics
import random
import pango

class Bar(graphics.Shape):
    def __init__(self, key, value, normalized, bar_color, label_color):
        graphics.Shape.__init__(self, fill = bar_color)
        self.key, self.value, self.normalized = key, value, normalized

        self.height = 0
        self.width = 20
        self.vertical = True
        self.interactive = True

        self.label = graphics.Label(value, size=8, color=label_color)

        self.add_child(self.label)

    def draw_shape(self):
        self.label.text = self.value


        # invisible rectangle for the mouse
        self.graphics.set_color("#000", 0)
        self.graphics.rectangle(0, 0, self.width, self.height)
        self.graphics.stroke()


        if self.vertical:
            size = round(self.height * self.normalized)

            # actual shape (rounded corners)
            self.graphics.rectangle(0, self.height - size, self.width, size, 5)
            self.graphics.rectangle(0, self.height - min(size, 3), self.width, min(size, 3))

            # adjust label
            self.label.x = (self.width - self.label.width) / 2
            vert_offset = min(10, self.label.x * 2)

            if self.label.height < size - vert_offset:
                self.label.y = -size + vert_offset
            else:
                self.label.y = -size - self.label.height - 3

        else:
            size = round(self.width * self.normalized)

            self.graphics.rectangle(0, 0, size, self.height, 3)
            self.graphics.rectangle(0, 0, min(size, 3), self.height)

            self.label.y = (self.height - self.label.height) / 2

            horiz_offset = min(10, self.label.y * 2)

            if self.label.width < size - horiz_offset:
                #if it fits in the bar
                self.label.x = size - self.label.width - horiz_offset
            else:
                self.label.x = size + 3




class Chart(graphics.Scene):
    def __init__(self, max_bar_width = 20, legend_width = 70, value_format = "%.2f", interactive = True):
        graphics.Scene.__init__(self)

        self.bars = []
        self.labels = []

        self.max_width = max_bar_width
        self.legend_width = legend_width
        self.value_format = value_format
        self.graph_interactive = interactive

        self.vertical = True
        self.plot_area = graphics.Sprite(interactive = False)
        self.add_child(self.plot_area)

        self.bar_color, self.label_color = None, None
        self.find_colors()

        self.connect("on-enter-frame", self.on_enter_frame)



    def find_colors(self):
        bg_color = self.get_style().bg[gtk.STATE_NORMAL].to_string()
        if self.colors.is_light(bg_color):
            self.bar_color = self.colors.darker(bg_color,  30)
        else:
            self.bar_color = self.colors.darker(bg_color,  -30)


        # now for the text - we want reduced contrast for relaxed visuals
        fg_color = self.get_style().fg[gtk.STATE_NORMAL].to_string()
        if self.colors.is_light(fg_color):
            self.label_color = self.colors.darker(fg_color,  80)
        else:
            self.label_color = self.colors.darker(fg_color,  -80)


    def on_mouse_over(self, bar):
        bar.fill = self.get_style().base[gtk.STATE_PRELIGHT].to_string()

    def on_mouse_out(self, bar):
        bar.fill = self.bar_color



    def plot(self, keys, data):
        bars = dict([(bar.key, bar.normalized) for bar in self.bars])

        max_val = float(max(data))

        new_bars, new_labels = [], []
        for key, value in zip(keys, data):
            normalized = value / max_val
            bar = Bar(key, self.value_format % value, normalized, self.bar_color, self.label_color)

            bar.connect("on-mouse-over", self.on_mouse_over)
            bar.connect("on-mouse-out", self.on_mouse_out)


            if key in bars:
                bar.normalized = bars[key]
                self.tweener.add_tween(bar, normalized=normalized)
            new_bars.append(bar)
            new_labels.append(graphics.Label(key, size = 8, color = self.label_color))

        for sprite in self.bars:
            self.plot_area.sprites.remove(sprite)

        for sprite in self.labels:
            self.sprites.remove(sprite)

        self.bars, self.labels = new_bars, new_labels
        self.add_child(*self.labels)
        self.plot_area.add_child(*self.bars)

        self.redraw()

    def on_enter_frame(self, scene, context):
        if 1 == 2:
            self.plot_area.y = 5
            self.plot_area.height = self.height - self.plot_area.y - 20
            self.plot_area.x = 0
            self.plot_area.width = self.width - self.plot_area.x

            x = 0
            for i, (label, bar) in enumerate(zip(self.labels, self.bars)):
                bar_width = min(round((self.plot_area.width - x) / (len(self.bars) - i)), self.max_width)
                bar.x = x
                bar.width = bar_width
                bar.height = self.plot_area.height

                label.y = self.plot_area.y + self.plot_area.height + 3
                label.x = x + (bar_width - label.width) / 2 + self.plot_area.x

                x += bar_width + 1


        else:
            self.plot_area.y = 0
            self.plot_area.height = self.height - self.plot_area.y
            self.plot_area.x = 80
            self.plot_area.width = self.width - self.plot_area.x

            #horizontal
            y = 0
            for i, (label, bar) in enumerate(zip(self.labels, self.bars)):
                bar_width = min(round((self.plot_area.height - y) / (len(self.bars) - i)), self.max_width)
                bar.y = y
                bar.vertical = False
                bar.height = bar_width
                bar.width = self.plot_area.width


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
