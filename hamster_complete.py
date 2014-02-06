#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2014 You <your.email@someplace>

"""Base template"""

import datetime as dt
import re

from gi.repository import Gtk as gtk
from lib import graphics
import ui

import hamster.client
from hamster.lib import stuff


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

        self.storage = hamster.client.Storage()
        self.todays_facts = self.storage.get_todays_facts()

        self.update_suggestions()


    def extract_fact(self, text, phase=None):
        """tries to extract fact fields from the string
            the optional arguments in the syntax makes us actually try parsing
            values and fallback to next phase
            start -> [end] -> activity[@category] -> tags

            Returns dict for the fact and achieved phase

            TODO - While we are now bit cooler and going recursively, this code
            still looks rather awfully spaghetterian. What is the real solution?
        """
        now = dt.datetime.now()

        # determine what we can look for
        phase = phase or self.phases[0]
        phases = self.phases[self.phases.index(phase):]
        res = {}

        text = text.strip()
        if not text:
            return {}

        fragment = re.split("[\s|#]", text, 1)[0].strip()

        def next_phase(fragment, phase):
            res.update(self.extract_fact(text[len(fragment):], phase))
            return res

        if "start_time" in phases or "end_time" in phases:
            # looking for start or end time

            delta_re = re.compile("^-[0-9]{1,3}$")
            time_re = re.compile("^([0-1]?[0-9]|[2][0-3]):([0-5][0-9])$")
            time_range_re = re.compile("^([0-1]?[0-9]|[2][0-3]):([0-5][0-9])-([0-1]?[0-9]|[2][0-3]):([0-5][0-9])$")

            if delta_re.match(fragment):
                res[phase] = now + dt.timedelta(minutes=int(fragment))
                return next_phase(fragment, phases[phases.index(phase)+1])

            elif time_re.match(fragment):
                res[phase] = dt.datetime.strptime(fragment, "%H:%M")
                return next_phase(fragment, phases[phases.index(phase)+1])

            elif time_range_re.match(fragment) and phase == "start_time":
                start, end = fragment.split("-")
                res["start_time"] = dt.datetime.strptime(start, "%H:%M")
                res["end_time"] = dt.datetime.strptime(end, "%H:%M")
                phase = "activity"
                return next_phase(fragment, "activity")

        if "activity" in phases:
            activity, category = fragment.split("@") if "@" in fragment else (fragment, None)
            if self.looks_like_time(activity):
                # want meaningful activities
                return res

            res["activity"] = activity
            if category:
                res["category"] = category
            return next_phase(fragment, "tags")

        if "tags" in phases:
            tags, desc = text.split(",", 1) if "," in text else (text, None)

            tags = [tag for tag in re.split("[\s|#]", tags.strip()) if tag]
            if tags:
                res["tags"] = tags

            if (desc or "").strip():
                res["description"] = desc.strip()

            return res

        return {}


    def looks_like_time(self, fragment):
        if not fragment:
            return False
        time_fragment_re = [
            re.compile("^-$"),
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

        self.box.clear()

        text = text.lstrip()

        time_re = re.compile("^([0-1]?[0-9]|[2][0-3]):([0-5][0-9])$")
        time_range_re = re.compile("^([0-1]?[0-9]|[2][0-3]):([0-5][0-9])-([0-1]?[0-9]|[2][0-3]):([0-5][0-9])$")
        delta_re = re.compile("^-[0-9]{1,3}$")

        # when the time is filled, we need to make sure that the chunks parse correctly



        delta_fragment_re = re.compile("^-[0-9]{0,3}$")


        templates = {
            "start_time": "",
            "start_delta": ("minutes ago", "-"),
            "activity": ("start now", "hamster"),
        }

        # need to set the start_time template before
        prev_fact = self.todays_facts[-1] if self.todays_facts else None
        if prev_fact and prev_fact.end_time:
            templates["start_time"] = ("from previous activity %s ago" % stuff.format_duration(prev_fact.delta),
                                       prev_fact.end_time.strftime("%H:%M"))

        variants = []

        fact = self.extract_fact(text)

        # figure out what we are looking for
        # time -> activity[@category] -> tags -> description
        # presence of each next attribute means that we are not looking for the previous one
        # we still might be looking for the current one though
        looking_for = "start_time"
        fields = ["start_time", "end_time", "activity", "category", "tags",
                  "description", "done"]
        for field in reversed(fields):
            if fact.get(field):
                looking_for = field
                if text[-1] == " ":
                    looking_for = fields[fields.index(field)+1]
                break


        fragments = [f for f in re.split("[\s|#]", text)]
        current_fragment = fragments[-1] if fragments else ""


        if not text.strip():
            variants = [templates[name] for name in ("start_time",
                                                     "start_delta") if templates[name]]
        elif looking_for == "start_time" and text == "-":
            if len(current_fragment) > 1: # avoid blank "-"
                templates["start_delta"] = ("%s minutes ago" % (-int(current_fragment)), current_fragment)
            variants.append(templates["start_delta"])


        # regular activity
        now = dt.datetime.now()

        if (looking_for in ("start_time", "end_time") and not self.looks_like_time(text.split(" ")[-1])) or \
           looking_for in ("activity", "category"):
            activities = self.storage.get_activities(current_fragment.strip() if looking_for in("activity", "category") else "")
            for activity in activities:
                label = (fact.get('start_time') or now).strftime("%H:%M-")
                if fact.get('end_time'):
                    label += fact['end_time'].strftime("%H:%M")

                label += " " + activity['name']
                if activity['category']:
                    label += "@%s" % activity['category']


                variants.append(("", label))




        for (description, variant) in variants:
            hbox = ui.HBox()
            hbox.add_child(ui.Label(variant))
            hbox.add_child(ui.Label(description, expand=False, color="#666"))

            self.box.add_child(hbox)


        self.render_preview(text)


    def render_preview(self, text):
        now = dt.datetime.now()

        self.box.add_child(ui.Label("Preview", size=20, color="#333", padding_top=50))
        container = ui.HBox(spacing=5)
        self.box.add_child(container)

        fact = self.extract_fact(text)
        start_time = fact.get('start_time') or now
        container.add_child(ui.Label(start_time.strftime("%H:%M - "),
                                     expand=False, y_align=0))

        if fact.get('end_time'):
            container.add_child(ui.Label(fact['end_time'].strftime("%H:%M"),
                                         expand=False, y_align=0))

        nested = ui.VBox()
        nested.add_child(ui.HBox([
            ui.Label(fact.get('activity', ""), expand=False),
            ui.Label((" - %s" % fact['category']) if fact.get('category') else "", size=12, color="#888")
        ]))
        container.add_child(nested)
        if fact.get('tags'):
            nested.add_child(ui.Label(", ".join(fact['tags'])))
        if fact.get('description'):
            nested.add_child(ui.Label(markup = "<i>%s</i>" % fact['description']))

        end_time = fact.get('end_time') or now

        if start_time != end_time:
            minutes = (end_time - start_time).total_seconds() / 60
            hours, minutes = minutes // 60, minutes % 60
            label = ("%dh %dmin" % (hours, minutes)) if hours else "%dmin" % minutes
            container.add_child(ui.Label(label, expand=False, y_align=0))


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
