#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2014 Toms Baugis <toms.baugis@gmail.com>

"""Base template"""


from gi.repository import Gtk as gtk
from lib import graphics
import random


class FlatMap(object):
    def paint(self, g, w, h):
        numbers = self.norm(0)

        for depth, normalized in enumerate(numbers):
            # we will split the dimension where we have more space
            x, y = round(w * normalized), round(h * normalized)
            y = 0 if x >= y else y
            x = 0 if y > x else x

            g.fill_area(0, 0, x or w, y or h, graphics.Colors.category20c[depth % 20])
            g.translate(x, y)
            w = w - x
            h = h - y


class Fibonacci(FlatMap):
    description = "Fibonacci"
    def __init__(self):
        self.numbers = [] # generate numbers

        # don't drink and math
        j, k = 0, 1
        for i in range(1, 20):
            res = j + k
            self.numbers.append(res)
            j, k = k, k + j

        self.numbers = sorted(self.numbers, reverse=True)



    def norm(self, depth):
        numbers = self.numbers[depth:]
        if len(numbers) < 2:
            return []

        top = numbers[0] * 1.0 / (numbers[1] + numbers[0])
        return [top] + self.norm(depth+1)




class Sum2D(FlatMap):
    description = "Current against the remaining sum"

    def __init__(self):
        self.numbers = [random.randint(1, 900) for i in range(10)]
        #self.numbers = [i for i in range(10, 100, 30)]
        self.numbers = sorted(self.numbers, reverse=True)

    def norm(self, depth):
        """we will find out how much space we have and then start dividing
        up the area accordingly"""
        numbers = self.numbers[depth:]
        if not numbers:
            return []

        total = sum(numbers) * 1.0
        top = numbers[0] * 1.0 / total
        return [top] + self.norm(depth+1)


class Max2D(FlatMap):
    description = "Current against max value"

    def __init__(self):
        self.numbers = [random.randint(10, 100) for i in range(50)]
        self.numbers = sorted(self.numbers, reverse=True)

    def norm(self, depth):
        """we will find out how much space we have and then start dividing
        up the area accordingly"""
        numbers = self.numbers
        if depth == len(self.numbers):
            return []

        total = max(numbers) * 1.0
        top = numbers[0] * 1.0 / total * 0.5
        return [top] + self.norm(depth+1)



class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.experiments = [
            Fibonacci(),
            Sum2D(),
            Max2D(),
        ]

        self.current_experiment = self.experiments[0]

        self.connect("on-enter-frame", self.on_enter_frame)

    def toggles(self):
        idx = self.experiments.index(self.current_experiment)
        self.current_experiment = self.experiments[(idx + 1) % len(self.experiments)]
        self.redraw()

    def on_enter_frame(self, scene, context):
        # you could do all your drawing here, or you could add some sprites
        g = graphics.Graphics(context)
        self.current_experiment.paint(g, self.width, self.height)



class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_default_size(600, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        box = gtk.VBox(border_width=10, spacing=10)
        window.add(box)

        self.scene = Scene()
        box.pack_start(self.scene, True, True, 0)

        button = gtk.Button("Toggles")
        box.pack_end(button, False, True, 0)
        button.connect("clicked", self.on_button_clicked)
        self.on_button_clicked(button)

        window.show_all()

        print "The morale of the story is that flat treemaps are boring with a simplified layout algo"


    def on_button_clicked(self, button):
        self.scene.toggles()
        button.set_label(self.scene.current_experiment.description + ". Click for Next")

if __name__ == '__main__':
    window = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
