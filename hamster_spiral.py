#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""Base template"""


from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from lib import graphics, pytweener
import math
import hamster.client
import datetime as dt
from collections import defaultdict
import itertools


class TimeRing(graphics.Sprite):
    def __init__(self, days, start_date, fill):
        graphics.Sprite.__init__(self, interactive = False)
        self.days = days
        self.start_date = start_date

        self.end_date = max([day for day, hours in self.days])

        self.fill = fill

        self.width = 45
        self.height = 15
        self.min_radius = 35

        self.connect("on-render", self.on_render)


    def on_render(self, sprite):
        self.graphics.clear()
        start_date = dt.date(2010, 1, 1) #dt.datetime.today()
        step = (360 / 364.0 / 180 * math.pi)

        height = self.height

        for i in range((self.end_date - self.start_date).days):
            day = i
            angle = day * step - math.pi / 2  # -math.pi is so that we start at 12'o'clock instead of 3
            distance = float(day) / 365 * self.width + self.min_radius

            self.graphics.line_to(math.cos(angle) * (distance + height / 2),
                                  math.sin(angle) * (distance + height / 2))

        self.graphics.set_line_style(width = height * 1)
        self.graphics.stroke(self.fill, 0.05)


        for day, hours in self.days:
            delta_days = (day - self.start_date).days
            if delta_days < 0:
                continue




            angle = delta_days * step - math.pi / 2  # -math.pi is so that we start at 12'o'clock instead of 3

            distance = float(delta_days) / 365 * self.width + self.min_radius

            #self.graphics.move_to(0, 0)
            #height = hours / 12.0 * self.height
            height = self.height

            self.graphics.move_to(math.cos(angle) * distance,
                                  math.sin(angle) * distance)
            self.graphics.line_to(math.cos(angle) * (distance + height),
                                  math.sin(angle) * (distance + height))


            self.graphics.line_to(math.cos(angle+step) * (distance + height),
                                  math.sin(angle+step) * (distance + height))

            self.graphics.line_to(math.cos(angle+step) * distance,
                                  math.sin(angle+step) * distance)
            self.graphics.close_path()

        self.graphics.fill(self.fill)


class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        storage = hamster.client.Storage()

        self.day_counts = {}
        categories = defaultdict(int)

        self.colors = ("#20b6de", "#fff", "#333", "#ff0", "#0ff", "#aaa")

        self.container = graphics.Sprite()
        self.add_child(self.container)

        self.start_date_label = graphics.Label(color = "#000")
        self.add_child(self.start_date_label)


        facts = storage.get_facts(dt.date(2006,1,1), dt.datetime.now())
        facts_per_category = defaultdict(list)
        categories = defaultdict(int)

        #facts = [fact for fact in facts if fact.category in ('work', 'hacking')]

        for category, facts in itertools.groupby(sorted(facts, key=lambda fact:fact.category), lambda fact:fact.category):
            for day, day_facts in itertools.groupby(sorted(facts, key=lambda fact:fact.date), lambda fact:fact.date):
                delta = dt.timedelta()
                for fact in day_facts:
                    delta += fact.delta
                delta = delta.seconds / 60 / 60 + delta.days * 24

                facts_per_category[category].append((day, delta))

            categories[category] += 1


        self.categories = categories.keys()


        self.spirals = []
        self.start_date = dt.date(2006, 1, 1)

        for i, category in enumerate(categories):
            ring = TimeRing(facts_per_category[category],
                            self.start_date,
                            self.colors[i + 1])
            ring.min_radius = i * 20 + 0
            ring.width = len(self.categories) * 30

            #self.animate(ring, 3, width = len(self.categories) * 30, easing = pytweener.Easing.Expo.ease_out)
            self.container.add_child(ring)
            self.spirals.append(ring)

        self.connect("on-enter-frame", self.on_enter_frame)
        self.connect("on-mouse-move", self.on_mouse_move)
        self.connect("on-mouse-scroll", self.on_scroll)


    def on_scroll(self, scene, event):
        if event.direction == gdk.ScrollDirection.UP:
            self.start_date -= dt.timedelta(days = 7)
        elif event.direction == gdk.ScrollDirection.DOWN:
            self.start_date += dt.timedelta(days = 7)
        else:
            print "other scroll"

        for spiral in self.spirals:
            spiral.start_date = self.start_date

        self.redraw()

    def on_mouse_move(self, scene, event):
        self.redraw()

    def on_enter_frame(self, scene, context):
        g = graphics.Graphics(context)
        g.fill_area(0, 0, self.width, self.height, self.colors[0])

        self.container.x = self.width / 2
        self.container.y = self.height / 2

        #print self.start_date.strftime("%d %b, %Y")
        self.start_date_label.text = self.start_date.strftime("%d %b, %Y")
        self.start_date_label.x = self.width / 2 - self.start_date_label.width
        self.start_date_label.y = self.height / 2

        g.move_to(self.width / 2, self.height / 2)
        g.line_to(self.mouse_x, self.mouse_y)
        g.set_line_style(width=0.5)
        g.stroke("#fff")





class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_size_request(700, 600)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()


example = BasicWindow()
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
gtk.main()
