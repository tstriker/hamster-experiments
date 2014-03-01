#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2014 Toms Baugis <toms.baugis@gmail.com>

"""Base template"""
import datetime as dt
import itertools

from gi.repository import Gtk as gtk
from gi.repository import GObject as gobject

from collections import defaultdict

from lib import graphics
from lib import layout

from hamster.client import Storage

def minutes(delta):
    return delta.total_seconds() / 60.0

class SparkBars(layout.Widget):
    def __init__(self, items=None, width = None, height=None, **kwargs):
        layout.Widget.__init__(self, **kwargs)

        self.width = width or 100
        self.height = height or 20
        self.bar_width = 10
        self.fill_color = "#777"
        self.items = items or []

        self.connect("on-render", self.on_render)


    def on_render(self, sprite):
        # simplify math by rolling down to the bottom
        self.graphics.save_context()
        self.graphics.translate(0, self.height)

        gap = 1

        max_width = min(self.width, len(self.items) * (self.bar_width + gap))
        pixels = graphics.full_pixels(max_width, [1] * len(self.items), gap)

        max_val = max(self.items)

        for val, width in zip(self.items, pixels):
            height = max(1, round(val * 1.0 / max_val * self.height))

            self.graphics.rectangle(0, 0, width, -height)
            self.graphics.translate(width + gap, 0)
        self.graphics.fill(self.fill_color)

        self.graphics.restore_context()


class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.storage = Storage()

        self._load_end_date = dt.datetime.now()
        self.facts = []

        self.label = layout.Label("Loading...", y=100,
                                    color="#666",
                                    size=50)
        self.add_child(layout.VBox(self.label))

        gobject.timeout_add(10, self.load_facts)


    def load_facts(self):
        end = self._load_end_date
        start = end - dt.timedelta(days=365)
        self.facts = self.storage.get_facts(start, end) + self.facts

        self._load_end_date = start - dt.timedelta(days=1)
        if end > dt.datetime(2013, 1, 1):
            self.label.text = "Loading %d..." % len(self.facts)
            gobject.timeout_add(10, self.load_facts)
        else:
            self.on_facts_loaded()


    def on_facts_loaded(self):
        by_activity = {}
        for fact in self.facts:
            activity = "%s@%s" % (fact.activity, fact.category)
            rec = by_activity.setdefault(activity,
                                         {"activity": fact.activity,
                                          "category": fact.category,
                                          "facts": []})
            rec['facts'].append(fact)



        by_activity_hour = defaultdict(lambda: defaultdict(float))
        for activity, stats in by_activity.iteritems():
            for fact in stats["facts"]:
                minutes = fact.delta.total_seconds() / 60.0
                hours = int(minutes // 60)
                minutes = round(minutes - hours * 60)

                for i in range(hours):
                    by_activity_hour[activity][(fact.start_time + dt.timedelta(hours=i)).hour] += 1

                by_activity_hour[activity][(fact.start_time + dt.timedelta(hours=hours)).hour] += minutes / 60.0

        hours = range(24)
        hours = hours[6:] + hours[:6]
        for activity in by_activity_hour.keys():
            by_activity_hour[activity] = [by_activity_hour[activity][i] for i in hours]



        self.clear()
        main = layout.VBox(padding=10, spacing=10)
        self.add_child(main)

        first_row = layout.HBox(spacing=10, expand=False)
        main.add_child(first_row)

        activity_weekdays = layout.HBox([layout.VBox(spacing=15, expand=False),
                                         layout.VBox(spacing=15, expand=False),
                                         layout.VBox(spacing=15)
                                        ], spacing=20)
        first_row.add_child(activity_weekdays)

        activity_weekdays[0].add_child(layout.Label("Activity", expand=False, x_align=0))
        activity_weekdays[1].add_child(layout.Label("Hour of the day", expand=False, x_align=0))


        for activity in sorted([(rec["category"], rec["activity"]) for rec in by_activity.itervalues()]):
            activity = "%s@%s" % (activity[1], activity[0])

            label = layout.Label(activity, color="#333", size=12, x_align=0, y_align=0.5)
            label.max_width = 150
            activity_weekdays[0].add_child(label)
            activity_weekdays[1].add_child(SparkBars(by_activity_hour[activity], 150))


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
