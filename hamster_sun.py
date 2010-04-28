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

class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)


        storage = hamster.client.Storage()

        self.facts = storage.get_facts(dt.date(2007,1,1), dt.date.today())

        self.day_counts = {}
        activities, categories = defaultdict(int), defaultdict(int)

        print len(self.facts)

        for fact in self.facts:
            self.day_counts.setdefault(fact['start_time'].date(), defaultdict(list))
            self.day_counts[fact['start_time'].date()][fact['category']].append(fact)

            activities[fact['name']] += 1
            categories[fact['category']] += 1

            if fact['end_time'] and fact['start_time'].date() != fact['end_time'].date():
                self.day_counts.setdefault(fact['end_time'].date(), defaultdict(list))
                self.day_counts[fact['end_time'].date()][fact['category']].append(fact)



        self.activities = [activity[0] for activity in sorted(activities.items(), key=lambda item:item[1], reverse=True)]
        self.categories = categories.keys()


        self.connect("on-enter-frame", self.on_enter_frame)

    def on_enter_frame(self, scene, context):
        g = graphics.Graphics(context)

        step = (360.0 / 365) * math.pi / 180.0


        g.set_color("#999")
        g.set_line_style(width = 1)

        """
        for i in range(365):
            g.move_to(self.width / 2, self.height / 2)
            g.rel_line_to(math.cos(step * i) * 300,
                          math.sin(step *  i) * 300)

        g.stroke()
        """


        colors = ("#ff0000", "#00ff00", "#0000ff", "#aaa000")

        for day in self.day_counts:

            year_day = day.timetuple().tm_yday
            angle = year_day * step


            for j, category in enumerate(self.day_counts[day]):
                distance = 20 * (day.year - 2005) + self.categories.index(category) * 60 + 30
                color = colors[self.categories.index(category)]

                delta = dt.timedelta()
                for fact in self.day_counts[day][category]:
                    delta += fact['delta']

                hours = delta.seconds / 60 / 60
                height = hours / 16.0 * 20


                g.set_color(color)
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
                #g.fill_preserve()
                g.stroke()


            g.fill("#aaa")


        for i, color in enumerate(colors):
            g.move_to(0, i * 20)
            g.set_color(color)
            g.show_text(self.categories[i])



class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(600, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()


example = BasicWindow()
gtk.main()
