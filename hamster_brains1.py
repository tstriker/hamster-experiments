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

def minutes(facts):
    time = dt.timedelta()
    for fact in facts:
        time += fact.delta
    return time.total_seconds() / 60.0


class Stats(object):
    def __init__(self, facts, toplevel_group=None):
        self.groups = None # we run top-level groups on first call
        self.toplevel_group = toplevel_group
        self._facts = facts

        self._range_start = None
        self._range_end = None
        self._update_groups()


    @property
    def facts(self):
        return self._facts

    @facts.setter
    def set_facts(self, facts):
        self._facts = facts
        self._update_groups()

    def _update_groups(self):
        for fact in self.facts:
            self._range_start = min(fact.date, self._range_start or fact.date)
            self._range_end = max(fact.date, self._range_end or fact.date)

        if not self.toplevel_group:
            # in case when we have no grouping, we are looking for totals
            self.groups = facts
        else:
            key_func = self.toplevel_group
            self.groups = {key: list(facts) for key, facts in
                               itertools.groupby(sorted(self.facts, key=key_func), key_func)}


    def group(self, key_func):
        # return the nested thing
        res = {}
        for key, facts in self.groups.iteritems():
            res[key] = {nested_key: list(nested_facts) for nested_key, nested_facts in
                         itertools.groupby(sorted(facts, key=key_func), key_func)}
        return res



    def by_week(self):
        """return series by week, fills gaps"""
        year_week = lambda date: (date.year, int(date.strftime("%W")))

        weeks = []
        start, end = self._range_start, self._range_end
        for i in range(0, (end - start).days, 7):
            weeks.append(year_week(start + dt.timedelta(days=i)))

        # group and then fill gaps and turn into a list
        res = self.group(lambda fact: year_week(fact.date))
        for key, group in res.iteritems():
            res[key] = [minutes(group.get(week, [])) for week in weeks]

        return res


    def by_weekday(self):
        """return series by weekday, fills gaps"""
        res = self.group(lambda fact: fact.date.weekday())
        for key, group in res.iteritems():
            res[key] = [minutes(group.get(weekday, [])) for weekday in range(7)]
        return res


    def by_hour(self):
        """return series by hour, stretched for the duration"""


    def sum_durations(self, keys):
        """returns summed durations of the specified keys iterable"""
        res = []
        for key in keys:
            res_delta = dt.timedelta()
            for fact in (facts_dict.get(key) or []):
                res_delta += fact.delta
            res.append(round(res_delta.total_seconds() / 60.0))
        return res


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


        for activity in stats.groups.keys():
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
