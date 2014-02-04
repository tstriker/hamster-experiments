#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2014 You <your.email@someplace>

"""Base template"""

import datetime as dt
import re

from gi.repository import Gtk as gtk
from lib import graphics
import ui

class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        self.box = ui.VBox(expand=False)

        big_box = ui.VBox()
        big_box.add_child(self.box)
        self.add_child(big_box)


        self.phases = [
            "start_time",
            "end_time",
            "activity",
            "tags"
        ]

        self.update_suggestions()


    def extract_fact(self, text, phase=None):
        """tries to extract field and returns field type, value and remaining string on success"""

        # determine what we can look for
        phase = phase or self.phases[0]
        phases = self.phases[self.phases.index(phase):]
        res = []

        text = text.strip()
        if not text:
            return []

        fragment = re.split("[\s|#]", text, 1)[0].strip()

        def next_phase(fragment, phase):
            res.extend(self.extract_fact(text[len(fragment):], phase))
            return res

        print "testing", fragment, "for", phase

        if "start_time" in phases or "end_time" in phases:
            # test for datetime
            delta_re = re.compile("^-[0-9]{1,3}$")
            time_re = re.compile("^([0-1]?[0-9]|[2][0-3]):([0-5][0-9])$")
            time_range_re = re.compile("^([0-1]?[0-9]|[2][0-3]):([0-5][0-9])-([0-1]?[0-9]|[2][0-3]):([0-5][0-9])$")

            if delta_re.match(fragment):
                res.append({"field": phase,
                            "value": dt.timedelta(minutes=int(fragment))})
                return next_phase(fragment, phases[phases.index(phase)+1])

            elif time_re.match(fragment):
                res.append({"field": phase,
                            "value": dt.time(*(int(f) for f in fragment.split(":")))})
                return next_phase(fragment, phases[phases.index(phase)+1])

            elif time_range_re.match(fragment) and phase == "start_time":
                res.append({"field": "start_time",
                            "value": dt.time(*(int(f) for f in fragment.split("-")[0].split(":")))})
                res.append({"field": "end_time",
                            "value": dt.time(*(int(f) for f in fragment.split("-")[1].split(":")))})
                return next_phase(fragment, "activity")

        if "activity" in phases:
            activity, category = fragment.split("@") if "@" in fragment else (fragment, None)
            if len(activity) < 3 or self.looks_like_time(activity):
                # want meaningful activities
                return res

            res.append({"field": "activity", "value": activity})
            if category:
                res.append({"field": "category", "value": category})
            return next_phase(fragment, "tags")

        if "tags" in phases:
            tags = [tag for tag in re.split("[\s|#]", text.strip()) if tag]
            if tags:
                res.append({"field": "tags", "value": tags})

            return res


        return []


    def looks_like_time(self, fragment):
        time_fragment_re = [
            re.compile("^([0-1]?[0-9]?|[2]?[0-3]?)$"),
            re.compile("^([0-1]?[0-9]|[2][0-3]):?([0-5]?[0-9]?)$"),
            re.compile("^([0-1]?[0-9]|[2][0-3]):([0-5][0-9])-?([0-1]?[0-9]?|[2]?[0-3]?)$"),
            re.compile("^([0-1]?[0-9]|[2][0-3]):([0-5][0-9])-([0-1]?[0-9]|[2][0-3]):?([0-5]?[0-9]?)$"),
        ]
        return any((r.match(fragment) for r in time_fragment_re))



    def update_suggestions(self, text=""):
        """
            * from previous activity | set time | minutes ago | start now
            * to ongoing | set time

            * activity
            * [@category]
            * #tags, #tags, #tags

            * we will leave description for later

            all our magic is space separated, strictly, start-end can be just dash

            phases:

            [start_time] | [-end_time] | activity | [@category] | [#tag]
        """
        print "Rrrrr", self.extract_fact(text)

        self.box.clear()

        text = text.lstrip()

        first_chunk = text.split(" ", 1)[0].strip()

        time_re = re.compile("^([0-1]?[0-9]|[2][0-3]):([0-5][0-9])$")
        time_range_re = re.compile("^([0-1]?[0-9]|[2][0-3]):([0-5][0-9])-([0-1]?[0-9]|[2][0-3]):([0-5][0-9])$")
        delta_re = re.compile("^-[0-9]{1,3}$")

        # when the time is filled, we need to make sure that the chunks parse correctly



        delta_fragment_re = re.compile("^-[0-9]{0,3}$")


        templates = {
            "start_time": ("from previous activity 1h 35min ago", "15:39"),
            "start_delta": ("minutes ago", "-"),
            "activity": ("hamster", "start now"),
        }

        variants = []

        if first_chunk == "":
            variants = [templates[name] for name in ("start_time", "start_delta", "activity")]
        else:
            if delta_fragment_re.match(first_chunk):
                #print "delta"
                variants.append(templates["start_delta"])
            elif self.looks_like_time(first_chunk):
                #print "time"
                variants.append(templates["start_time"])
            else:
                #print "something else"
                variants.append(templates["activity"])



        for (description, variant) in variants:
            hbox = ui.HBox()
            hbox.add_child(ui.Label(variant))
            hbox.add_child(ui.Label(description, expand=False, color="#666"))

            self.box.add_child(hbox)



class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_default_size(600, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        self.entry = gtk.Entry()
        self.scene = Scene()

        box = gtk.Box(orientation=gtk.Orientation.VERTICAL)
        box.set_border_width(12)
        box.pack_start(self.entry, False, True, 0)
        box.pack_end(self.scene, True, True, 0)

        self.entry.grab_focus()
        self.entry.connect("changed", self.on_entry_changed)

        window.add(box)
        window.show_all()

    def on_entry_changed(self, entry):
        self.scene.update_suggestions(self.entry.get_text())

if __name__ == '__main__':
    window = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
