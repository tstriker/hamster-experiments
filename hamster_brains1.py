#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2014 Toms Baugis <toms.baugis@gmail.com>

"""Base template"""
import datetime as dt

from gi.repository import Gtk as gtk
from gi.repository import GObject as gobject

from collections import defaultdict

from lib import graphics
from lib import layout

from hamster.client import Storage
from hamster_stats import Stats, minutes


class SparkBars(layout.Widget):
    def __init__(self, items=None, width = None, height=None, color=None, gap=1, **kwargs):
        layout.Widget.__init__(self, **kwargs)

        self.width = width or 100
        self.height = height or 20
        self.bar_width = 10
        self.gap = gap
        self.color = color or "#777"
        self.items = items or []

        self.connect("on-render", self.on_render)


    def on_render(self, sprite):
        # simplify math by rolling down to the bottom
        self.graphics.save_context()
        self.graphics.translate(0, self.height)

        max_width = min(self.width, len(self.items) * (self.bar_width + self.gap))
        pixels = graphics.full_pixels(max_width, [1] * len(self.items), self.gap)

        max_val = max(self.items)

        for val, width in zip(self.items, pixels):
            height = max(1, round(val * 1.0 / max_val * self.height))

            self.graphics.rectangle(0, 0, width, -height)
            self.graphics.translate(width + self.gap, 0)
        self.graphics.fill(self.color)

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
        # chunk size
        end = self._load_end_date
        start = end - dt.timedelta(days=30)
        self.facts = self.storage.get_facts(start, end) + self.facts

        self._load_end_date = start - dt.timedelta(days=1)

        # limiter
        if end > dt.datetime.now() - dt.timedelta(days=365):
            self.label.text = "Loading %d..." % len(self.facts)
            gobject.timeout_add(10, self.load_facts)
        else:
            self.on_facts_loaded()


    def on_facts_loaded(self):
        stats = Stats(self.facts, lambda fact: (fact.category, fact.activity))
        by_week = stats.by_week()

        # group by weekday
        by_weekday = stats.by_weekday()

        # group by workday / holiday
        by_work_hobby = stats.group(lambda fact: "weekend" if fact.date.weekday() in  (5, 6) else "workday")
        for activity, group in by_work_hobby.iteritems():
            work, non_work = group.get("workday", []), group.get("weekend", [])
            total = minutes(work) + minutes(non_work)
            by_work_hobby[activity] = "workday" if minutes(work) / total > 0.8 and len(work) > 10 else "other"




        self.clear()
        main = layout.VBox(padding=10, spacing=10)
        self.add_child(main)

        first_row = layout.HBox(spacing=10, expand=False)
        main.add_child(first_row)

        # add sparkbars of activity by weekday
        activity_weekdays = layout.HBox([layout.VBox(spacing=15, expand=False),
                                         layout.VBox(spacing=15, expand=False),
                                         layout.VBox(spacing=15)
                                        ], spacing=20)
        first_row.add_child(activity_weekdays)

        activity_weekdays[0].add_child(layout.Label("Activity", expand=False, x_align=0))
        activity_weekdays[1].add_child(layout.Label("Weekdays", expand=False, x_align=0))
        activity_weekdays[2].add_child(layout.Label("By week", expand=False, x_align=0))


        for activity in sorted(stats.groups.keys()):
            label = layout.Label("%s@%s" % (activity[1], activity[0]),
                                 color="#333",
                                 size=12, x_align=0, y_align=0.5)
            label.max_width = 150
            activity_weekdays[0].add_child(label)

            if by_work_hobby[activity] == "workday":
                color = graphics.Colors.category10[0]
            else:
                color = graphics.Colors.category10[2]

            hours = [rec for rec in by_weekday[activity]]
            activity_weekdays[1].add_child(SparkBars(hours, color=color))

            weeks = by_week[activity]
            activity_weekdays[2].add_child(SparkBars(weeks, width=200, color=color))


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
