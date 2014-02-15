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
        self.label.text = "Done!"

        def minutes(delta):
            return delta.total_seconds() / 60.0

        by_activity = defaultdict(list)
        for fact in self.facts:
            by_activity["%s@%s" % (fact.activity, fact.category or "")].append(fact)

        activity_weekday = {}
        for activity, facts in by_activity.iteritems():
            by_activity[activity] = {"activity": activity,
                                     "facts": facts,
                                     "by_weekday": {},
                                     "workday_sums": {"count": 0, "total": 0},
                                     "weekend_sums": {"count": 0, "total": 0}}

            rec = by_activity[activity]

            for fact in facts:
                weekday_rec = rec["by_weekday"].setdefault(fact.date.weekday(),
                                                           {"facts": [],
                                                            "total": 0})
                weekday_rec["facts"].append(fact)
                weekday_rec["total"] += minutes(fact.delta)

                if fact.date.weekday() in  (5, 6):
                    rec["weekend_sums"]["count"] += 1
                    rec["weekend_sums"]["total"] += minutes(fact.delta)
                else:
                    rec["workday_sums"]["count"] += 1
                    rec["workday_sums"]["total"] += minutes(fact.delta)


        # reduce down to simple workday/weekday pattern
        for activity in by_activity.itervalues():
            work, weekend = activity["workday_sums"], activity["weekend_sums"]

            total = (work["total"] + weekend["total"])


            pattern = "workday" if work["total"] / total > 0.8 and work["count"] > 10 else "other"
            activity["pattern"] = pattern

            print activity["activity"]
            print ["%.1d" % rec[1]["total"] for rec in sorted(activity["by_weekday"].iteritems())]


        print "workday activities", [activity["activity"]
                                     for activity in by_activity.itervalues() if activity["pattern"] == "workday"]


        print len(by_activity)


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
