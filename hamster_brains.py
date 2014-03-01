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
    def __init__(self, items=None, **kwargs):
        layout.Widget.__init__(self, **kwargs)

        self.width = 100
        self.height = 20
        self.bar_width = 10
        self.fill_color = "#777"
        self.items = items or []

        self.connect("on-render", self.on_render)
        self.fill=False


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

            self.graphics.fill_area(0, 0,
                                    width, -height,
                                    self.fill_color)
            self.graphics.translate(width + gap, 0)

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

        self.connect("on-enter-frame", self.on_enter_frame)
        gobject.timeout_add(10, self.load_facts)


    def load_facts(self):
        end = self._load_end_date
        start = end - dt.timedelta(days=300)
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


        self.clear()
        main = layout.VBox(padding=10, spacing=10)
        self.add_child(main)

        first_row = layout.HBox(spacing=10, expand=False)
        main.add_child(first_row)

        # add sparkbars of activity by weekday
        activity_weekdays = layout.HBox([layout.VBox(spacing=5),
                                         layout.VBox(spacing=5)], expand=False, spacing=20)
        first_row.add_child(activity_weekdays)

        by_activity = self.get_workday_pattern(by_activity)
        for activity, stats in by_activity.iteritems():
            hours = [stats["by_weekday"].get(i, {}).get("total", 0) for i in range(7)]

            activity_weekdays[0].add_child(layout.Label(activity, color="#333", size=12, x_align=0, y_align=0.5))
            activity_weekdays[1].add_child(SparkBars(hours))


    def get_workday_pattern(self, facts_by_activity):
        activity_days = {}

        for activity, rec in facts_by_activity.iteritems():
            stats = activity_days.setdefault(activity,
                                             {"by_weekday": {},
                                              "workday_sums": {"count": 0, "total": 0},
                                              "weekend_sums": {"count": 0, "total": 0},
                                             })

            for fact in rec['facts']:
                weekday_rec = stats["by_weekday"].setdefault(fact.date.weekday(),
                                                             {"facts": [],
                                                              "total": 0})
                weekday_rec["facts"].append(fact)
                weekday_rec["total"] += minutes(fact.delta)

                if fact.date.weekday() in  (5, 6):
                    stats["weekend_sums"]["count"] += 1
                    stats["weekend_sums"]["total"] += minutes(fact.delta)
                else:
                    stats["workday_sums"]["count"] += 1
                    stats["workday_sums"]["total"] += minutes(fact.delta)


        # reduce down to simple workday/weekday pattern
        for activity, stats in activity_days.iteritems():
            work, weekend = stats["workday_sums"], stats["weekend_sums"]

            total = (work["total"] + weekend["total"])


            pattern = "workday" if work["total"] / total > 0.8 and work["count"] > 10 else "other"
            stats["pattern"] = pattern

        return activity_days


    def on_enter_frame(self, scene, context):
        # you could do all your drawing here, or you could add some sprites
        g = graphics.Graphics(context)

        # self.redraw() # this is how to get a constant redraw loop (say, for animation)



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
