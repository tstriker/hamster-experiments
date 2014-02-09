#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2014 You <your.email@someplace>

"""Base template"""

import bisect
import cairo
import datetime as dt
import re

from gi.repository import Gdk as gdk
from gi.repository import Gtk as gtk
from gi.repository import GObject as gobject
from gi.repository import PangoCairo as pangocairo
from gi.repository import Pango as pango
from collections import defaultdict

from lib import graphics
import ui

import hamster.client
from hamster.lib import stuff


def looks_like_time(fragment):
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




def extract_fact(text, phase=None):
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
    phases = [
        "start_time",
        "end_time",
        "activity",
        "category",
        "tags"
    ]

    phase = phase or phases[0]
    phases = phases[phases.index(phase):]
    res = {}

    text = text.strip()
    if not text:
        return {}

    fragment = re.split("[\s|#]", text, 1)[0].strip()

    def next_phase(fragment, phase):
        res.update(extract_fact(text[len(fragment):], phase))
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
            res[phase] = dt.datetime.combine(now.date(), dt.datetime.strptime(fragment, "%H:%M").time())
            return next_phase(fragment, phases[phases.index(phase)+1])

        elif time_range_re.match(fragment) and phase == "start_time":
            start, end = fragment.split("-")
            res["start_time"] = dt.datetime.combine(now.date(), dt.datetime.strptime(start, "%H:%M").time())
            res["end_time"] = dt.datetime.combine(now.date(), dt.datetime.strptime(end, "%H:%M").time())
            phase = "activity"
            return next_phase(fragment, "activity")

    if "activity" in phases:
        activity = re.split("[@|#|,]", text, 1)[0]
        if looks_like_time(activity):
            # want meaningful activities
            return res

        res["activity"] = activity
        return next_phase(activity, "category")

    if "category" in phases:
        category = re.split("[#|,]", text, 1)[0]
        if category.lstrip().startswith("@"):
            res["category"] = category.lstrip("@ ")
            return next_phase(category, "tags")

        return next_phase("", "tags")

    if "tags" in phases:
        tags, desc = text.split(",", 1) if "," in text else (text, None)

        tags = [tag.strip() for tag in re.split("[#]", tags) if tag.strip()]
        if tags:
            res["tags"] = tags

        if (desc or "").strip():
            res["description"] = desc.strip()

        return res

    return {}

def extract_search(text):
    fact = extract_fact(text)
    search = fact.get('activity') or ""
    if 'category' in fact:
        search += "@%s" % fact['category']
    if 'tags' in fact:
        search += " #%s" % (" #".join(fact['tags']))
    return search

class DataRow(object):
    """want to split out visible label, description, activity data
      and activity data with time (full_data)"""
    def __init__(self, label, data=None, full_data=None, description=None):
        self.label = label
        self.data = data or label
        self.full_data = full_data or data or label
        self.description = description or ""

class Label(object):
    """a much cheaper label that would be suitable for cellrenderer"""
    def __init__(self, x=0, y=0):
        self.x, self.y = x, y
        self._label_context = cairo.Context(cairo.ImageSurface(cairo.FORMAT_A1, 0, 0))
        self.layout = pangocairo.create_layout(self._label_context)
        self.layout.set_font_description(pango.FontDescription(graphics._font_desc))
        self.layout.set_markup("Hamster") # dummy
        self.height = self.layout.get_pixel_size()[1]

    def show(self, g, text, color=None):
        g.move_to(self.x, self.y)

        self.layout.set_markup(text)
        g.save_context()
        if color:
            g.set_color(color)
        pangocairo.show_layout(g.context, self.layout)
        g.restore_context()


class CompleteTree(graphics.Scene):
    """
    ASCII Art

    | Icon | Activity - description |

    """

    __gsignals__ = {
        # enter or double-click, passes in current day and fact
        'on-select-row': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
    }


    def __init__(self):
        graphics.Scene.__init__(self, style_class=gtk.STYLE_CLASS_VIEW)

        self.set_can_focus(False)

        self.row_positions = []

        self.current_row = None
        self.rows = []

        self.style = self._style

        self.label = Label(x=5, y=3)
        self.row_height = self.label.height + 10

        self.connect("on-key-press", self.on_key_press)
        self.connect("on-enter-frame", self.on_enter_frame)
        self.connect("on-mouse-move", self.on_mouse_move)
        self.connect("on-mouse-down", self.on_mouse_down)

    def _get_mouse_row(self, event):
        hover_row = None
        for row, y in zip(self.rows, self.row_positions):
            if y <= event.y <= (y + self.row_height):
                hover_row = row
                break
        return hover_row

    def on_mouse_move(self, scene, event):
        row = self._get_mouse_row(event)
        if row:
            self.current_row = row
            self.redraw()

    def on_mouse_down(self, scene, event):
        row = self._get_mouse_row(event)
        if row:
            self.set_current_row(self.rows.index(row))

    def on_key_press(self, scene, event):
        if event.keyval == gdk.KEY_Up:
            idx = self.rows.index(self.current_row) if self.current_row else 1
            self.set_current_row(idx - 1)

        elif event.keyval == gdk.KEY_Down:
            idx = self.rows.index(self.current_row) if self.current_row else -1
            self.set_current_row(idx + 1)

    def set_current_row(self, idx):
        idx = max(0, min(len(self.rows) - 1, idx))
        row = self.rows[idx]
        self.current_row = row
        self.redraw()
        self.emit("on-select-row", row)

    def set_rows(self, rows):
        self.current_row = None
        self.rows = rows
        self.set_row_positions()

    def set_row_positions(self):
        """creates a list of row positions for simpler manipulation"""
        self.row_positions = [i * self.row_height for i in range(len(self.rows))]
        self.set_size_request(0, self.row_positions[-1] + self.row_height if self.row_positions else 0)

    def on_enter_frame(self, scene, context):
        if not self.height:
            return

        colors = {
            "normal": self.style.get_color(gtk.StateFlags.NORMAL),
            "normal_bg": self.style.get_background_color(gtk.StateFlags.NORMAL),
            "selected": self.style.get_color(gtk.StateFlags.SELECTED),
            "selected_bg": self.style.get_background_color(gtk.StateFlags.SELECTED),
        }

        g = graphics.Graphics(context)
        g.set_line_style(1)
        g.translate(0.5, 0.5)


        for row, y in zip(self.rows, self.row_positions):
            g.save_context()
            g.translate(0, y)

            color, bg = colors["normal"], colors["normal_bg"]
            if row == self.current_row:
                color, bg = colors["selected"], colors["selected_bg"]
                g.fill_area(0, 0, self.width, self.row_height, bg)

            label = row.label
            if row.description:
                description_color = graphics.Colors.contrast(color, 50)
                description_color = graphics.Colors.hex(description_color)

                label += '<span color="%s"> - %s</span>' % (description_color, row.description)

            self.label.show(g, label, color=color)

            g.restore_context()



class ActivityEntry(gtk.Entry):
    def __init__(self, **kwargs):
        gtk.Entry.__init__(self)

        self.popup = gtk.Window(type = gtk.WindowType.POPUP)
        box = gtk.Frame()
        box.set_shadow_type(gtk.ShadowType.IN)
        self.popup.add(box)

        self.complete_tree = CompleteTree()
        self.tree_checker = self.complete_tree.connect("on-select-row", self.on_tree_select_row)
        box.add(self.complete_tree)

        self.storage = hamster.client.Storage()
        self.load_suggestions()
        self.ignore_stroke = False

        self.set_icon_from_icon_name(gtk.EntryIconPosition.SECONDARY, "go-down-symbolic")

        self.checker = self.connect("changed", self.on_changed)
        self.connect("key-press-event", self.on_key_press)
        self.connect("focus-out-event", self.on_focus_out)
        self.connect("icon-press", self.on_icon_press)



    def on_changed(self, entry):
        text = self.get_text()

        with self.complete_tree.handler_block(self.tree_checker):
            self.show_suggestions(text)
            if self.complete_tree.rows:
                self.complete_tree.set_current_row(0)

        if self.ignore_stroke:
            self.ignore_stroke = False
            return

        def complete():
            text, suffix = self.complete_first()
            if suffix:
                #self.ignore_stroke = True
                with self.handler_block(self.checker):
                    self.update_entry("%s%s" % (text, suffix))
                    self.select_region(len(text), -1)
        gobject.timeout_add(0, complete)

    def on_focus_out(self, entry, event):
        self.popup.hide()

    def on_icon_press(self, entry, icon, event):
        self.show_suggestions("")

    def on_key_press(self, entry, event=None):
        if event.keyval in (gdk.KEY_BackSpace, gdk.KEY_Delete):
            self.ignore_stroke = True
        elif event.keyval == gdk.KEY_Escape:
            with self.handler_block(self.checker):
                self.set_text("")
                self.popup.hide()

        elif event.keyval == gdk.KEY_Return:
            self.popup.hide()
            self.set_position(-1)


        elif event.keyval in (gdk.KEY_Up, gdk.KEY_Down):
            if not self.popup.get_visible():
                self.show_suggestions(self.get_text())
            self.complete_tree.on_key_press(self, event)
            return True

    def on_tree_select_row(self, tree, row):
        with self.handler_block(self.checker):
            label = row.full_data
            self.update_entry(label)
            self.set_position(-1)

    def load_suggestions(self):
        self.todays_facts = self.storage.get_todays_facts()

        # list of facts of last month
        now = dt.datetime.now()
        last_month = self.storage.get_facts(now - dt.timedelta(days=30), now)

        # naive recency and frequency rank
        # score is as simple as you get 30-days_ago points for each occurence
        suggestions = defaultdict(int)
        for fact in last_month:
            days = 30 - (now - dt.datetime.combine(fact.date, dt.time())).total_seconds() / 60 / 60 / 24
            label = fact.activity
            if fact.category:
                label += "@%s" % fact.category

            suggestions[label] += days

            if fact.tags:
                label += " #%s" % (" #".join(fact.tags))
                suggestions[label] += days

        for rec in self.storage.get_activities():
            label = rec["name"]
            if rec["category"]:
                label += "@%s" % rec["category"]
            suggestions[label] += 0

        self.suggestions = sorted(suggestions.iteritems(), key=lambda x: x[1], reverse=True)

    def complete_first(self):
        text = self.get_text()
        fact, search = extract_fact(text), extract_search(text)
        if not self.complete_tree.rows or "activity" not in fact:
            return text, None



        label = self.complete_tree.rows[0].data
        if label.startswith(search):
            return text, label[len(search):]

        return text, None


    def update_entry(self, text):
        self.set_text(text or "")


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
        now = dt.datetime.now()

        text = text.lstrip()

        time_re = re.compile("^([0-1]?[0-9]|[2][0-3]):([0-5][0-9])$")
        time_range_re = re.compile("^([0-1]?[0-9]|[2][0-3]):([0-5][0-9])-([0-1]?[0-9]|[2][0-3]):([0-5][0-9])$")
        delta_re = re.compile("^-[0-9]{1,3}$")

        # when the time is filled, we need to make sure that the chunks parse correctly



        delta_fragment_re = re.compile("^-[0-9]{0,3}$")


        templates = {
            "start_time": "",
            "start_delta": ("start activity -n minutes ago", "-"),
        }

        # need to set the start_time template before
        prev_fact = self.todays_facts[-1] if self.todays_facts else None
        if prev_fact and prev_fact.end_time:
            templates["start_time"] = ("from previous activity %s ago" % stuff.format_duration(now - prev_fact.end_time),
                                       prev_fact.end_time.strftime("%H:%M "))

        variants = []

        fact = extract_fact(text)

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


        res = []
        for (description, variant) in variants:
            res.append(DataRow(variant, description=description))

        # regular activity
        if (looking_for in ("start_time", "end_time") and not looks_like_time(text.split(" ")[-1])) or \
            looking_for in ("activity", "category"):

            search = extract_search(text)

            matches = []
            for match, score in self.suggestions:
                if search in match:
                    if match.startswith(search):
                        score += 10**8 # boost beginnings
                    matches.append((match, score))

            matches = sorted(matches, key=lambda x: x[1], reverse=True)[:7] # need to limit these guys, sorry

            for match, score in matches:
                label = (fact.get('start_time') or now).strftime("%H:%M")
                if fact.get('end_time'):
                    label += fact['end_time'].strftime("-%H:%M")

                markup_label = label + " " + (match.replace(search, "<b>%s</b>" % search) if search else match)
                label += " " + match

                res.append(DataRow(markup_label, match, label))

        if not res:
            # in case of nothing to show, add preview so that the user doesn't
            # think they are lost
            label = (fact.get('start_time') or now).strftime("%H:%M")
            if fact.get('end_time'):
                label += fact['end_time'].strftime("-%H:%M")

            if 'activity' in fact:
                label += " " + fact['activity']
            if 'category' in fact:
                label += "@" + fact['category']

            if 'tags' in fact:
                label += " #" + " #".join(fact['tags'])

            res.append(DataRow(label, description="Start tracking"))

        self.complete_tree.set_rows(res)


    def show_suggestions(self, text):
        entry_alloc = self.get_allocation()
        entry_x, entry_y = self.get_window().get_origin()[1:]
        x, y = entry_x + entry_alloc.x, entry_y + entry_alloc.y + entry_alloc.height

        self.popup.show_all()

        self.update_suggestions(text)

        tree_w, tree_h = self.complete_tree.get_size_request()

        self.popup.move(x, y)
        self.popup.resize(entry_alloc.width, tree_h)
        self.popup.show_all()





class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_default_size(600, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        self.entry = ActivityEntry()
        box = gtk.Box(orientation=gtk.Orientation.VERTICAL)
        box.set_border_width(12)
        box.pack_start(self.entry, False, True, 0)
        window.add(box)

        self.entry.grab_focus()
        window.show_all()


if __name__ == '__main__':
    window = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
