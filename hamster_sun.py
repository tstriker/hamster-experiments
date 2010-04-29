#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""Base template"""


import gtk
from lib import graphics
import math
import hamster.client
import datetime as dt
from collections import defaultdict
import itertools

class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)


        storage = hamster.client.Storage()

        self.facts = storage.get_facts(dt.date(2007,1,1), dt.date.today())
        print len(self.facts)

        self.day_counts = {}
        categories = defaultdict(int)


        self.years = {}
        for year, facts in itertools.groupby(sorted(self.facts, key=lambda fact:fact['date']), lambda fact:fact['date'].year):
            self.years[year] = defaultdict(list)
            for category, category_facts in itertools.groupby(sorted(facts, key=lambda fact:fact['category']), lambda fact:fact['category']):
                for day, day_facts in itertools.groupby(sorted(category_facts, key=lambda fact:fact['date']), lambda fact:fact['date']):
                    delta = dt.timedelta()
                    for fact in day_facts:
                        delta += fact['delta']
                    delta = delta.seconds / 60 / 60 + delta.days * 24

                    self.years[year][category].append((day, delta))

                categories[category] += 1



        self.categories = categories.keys()


        self.connect("on-enter-frame", self.on_enter_frame)

    def on_enter_frame(self, scene, context):
        g = graphics.Graphics(context)

        g.fill_area(0, 0, self.width, self.height, "#000")

        step = (360.0 / 365) * math.pi / 180.0


        g.set_color("#999")
        g.set_line_style(width = 1)



        colors = ("#ff0000", "#00ff00", "#0000ff", "#aaa000")
        g.set_line_style(width=0.5)



        hour_step = 3
        current_pixel = 30

        for year in sorted(self.years.keys()):
            for category in self.categories:

                ring_height = hour_step * 3

                for day, hours in self.years[year][category]:
                    year_day = day.isocalendar()[1] * 7 + day.weekday()
                    angle = year_day * step - math.pi / 2

                    distance = current_pixel

                    height = ring_height


                    #bar per category
                    g.move_to(math.cos(angle) * distance + self.width / 2,
                              math.sin(angle) * distance + self.height / 2)
                    g.line_to(math.cos(angle) * (distance + height) + self.width / 2 ,
                              math.sin(angle) * (distance + height) + self.height / 2)

                    g.line_to(math.cos(angle+step) * (distance + height) + self.width / 2 ,
                              math.sin(angle+step) * (distance + height) + self.height / 2)

                    g.line_to(math.cos(angle+step) * distance + self.width / 2,
                              math.sin(angle+step) * distance + self.height / 2)
                    g.close_path()

                if self.years[year][category]:
                    current_pixel += ring_height + 7

                color = colors[self.categories.index(category)]
                g.set_color(color)
                g.fill_preserve()
                g.stroke()


            g.set_line_style(width = 1)
            g.circle(self.width/2, self.height/2, current_pixel - 2)
            g.stroke("#fff", 0.1)
            g.set_line_style(width=1)

            current_pixel += 3



        """
        for i, color in enumerate(colors):
            g.move_to(0, i * 20)
            g.set_color(color)
            g.show_text(self.categories[i])
        """



class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(700, 600)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()


example = BasicWindow()
gtk.main()
