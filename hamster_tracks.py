#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""An attempt to make an overview visualization. Consumes hamster d-bus API"""


import gtk
from lib import graphics

import dbus
import time, datetime as dt
from collections import defaultdict


HAMSTER_DBUS_PATH = "/org/gnome/Hamster"
HAMSTER_DBUS_IFACE = "org.gnome.Hamster"



class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        bus = dbus.SessionBus()
        obj = bus.get_object(HAMSTER_DBUS_IFACE, HAMSTER_DBUS_PATH)
        self.hamster = dbus.Interface(obj, "org.gnome.Hamster")


        self.facts = self.get_facts()

        self.day_counts = defaultdict(list)
        activities, categories = defaultdict(int), defaultdict(int)

        for fact in self.facts:
            self.day_counts[fact['start_time'].date()].append(fact)
            activities[fact['name']] += 1
            categories[fact['category']] += 1

            if fact['end_time'] and fact['start_time'].date() != fact['end_time'].date():
                self.day_counts[fact['end_time'].date()].append(fact)



        self.activities = [activity[0] for activity in sorted(activities.items(), key=lambda item:item[1], reverse=True)]
        self.categories = categories.keys()

        self.connect("on-enter-frame", self.on_enter_frame)

    def get_facts(self):
        facts = []
        start_time = time.mktime(dt.datetime(2009, 1, 1).timetuple())
        for fact in self.hamster.GetFacts(start_time, 0):
            # run through the facts and convert them to python types so it's easier to operate with
            res = {}
            for key in ['name', 'category', 'description']:
                res[key] = str(fact[key])

            for key in ['start_time', 'end_time', 'date']:
                res[key] = dt.datetime.utcfromtimestamp(fact[key]) if fact[key] else None

            res['delta'] = dt.timedelta(days = fact['delta'] / (60 * 60 * 24),
                                        seconds = fact['delta'] % (60 * 60 * 24))

            res['tags'] = [str(tag) for tag in fact['tags']] if fact['tags'] else []

            facts.append(res)

        return facts


    def on_enter_frame(self, scene, context):
        if not self.facts:
            return

        g = graphics.Graphics(context)
        g.set_line_style(width=1)

        start_date = self.facts[0]['start_time'].date()
        end_date = self.facts[-1]['end_time'].date()

        days = (end_date - start_date).days

        day_pixel = self.width / float(days)


        for i in range(0, self.height, 2):
            g.rectangle(0, i * 3, self.width, 3)
        g.fill("#fafafa")


        for day in range(days):
            current_date = start_date + dt.timedelta(days=day)
            cur_x = round(day * day_pixel)
            pixel_width = max(round(day_pixel), 1)

            if not self.day_counts[current_date]:
                g.rectangle(cur_x, 0, day_pixel, self.height)
                g.fill("#fff", 0.5)

            for j, fact in enumerate(self.day_counts[current_date]):

                #bar per category
                g.rectangle(cur_x, 27 + self.categories.index(fact['category']) * 3, pixel_width, 3)

                #bar per activity
                g.rectangle(cur_x, 102 + self.activities.index(fact['name']) * 9, pixel_width, 6)

                #number of activities
                g.rectangle(cur_x, self.height - 3 * j, pixel_width, 3)

            g.fill("#aaa")




class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(600, 300)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()


example = BasicWindow()
gtk.main()
