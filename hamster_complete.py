#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2014 You <your.email@someplace>

"""Base template"""

import bisect
import cairo
import datetime as dt
import re

from gi.repository import GObject as gobject
from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
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
        if looks_like_time(activity):
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








class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        self.box = ui.VBox(expand=False)

        big_box = ui.VBox()
        big_box.add_child(self.box)
        self.add_child(big_box)



    def render_preview(self, text):
        now = dt.datetime.now()

        self.box.clear()

        self.box.add_child(ui.Label("Preview", size=20, color="#333", padding_top=50))
        container = ui.HBox(spacing=5)
        self.box.add_child(container)

        fact = extract_fact(text)
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








class ActionRow(graphics.Sprite):
    def __init__(self):
        graphics.Sprite.__init__(self)
        self.visible = False

        self.restart = graphics.Icon("view-refresh-symbolic", size=18,
                                     interactive=True,
                                     mouse_cursor=gdk.CursorType.HAND1,
                                     y=4)
        self.add_child(self.restart)

        self.width = 50 # Simon says



class Label(object):
    """a much cheaper label that would be suitable for cellrenderer"""
    def __init__(self, x=0, y=0, color=None, use_markup=True):
        self.x = x
        self.y = y
        self.color = color
        self._label_context = cairo.Context(cairo.ImageSurface(cairo.FORMAT_A1, 0, 0))
        self.layout = pangocairo.create_layout(self._label_context)
        self.layout.set_font_description(pango.FontDescription(graphics._font_desc))
        self.layout.set_markup("Hamster") # dummy
        self.height = self.layout.get_pixel_size()[1]
        self.use_markup = use_markup

    def _set_text(self, text):
        if self.use_markup:
            self.layout.set_markup(text)
        else:
            self.layout.set_text(text, -1)

    def _show(self, g, color):
        color = color or self.color
        if color:
            g.set_color(color)
        pangocairo.show_layout(g.context, self.layout)

    def show(self, g, text, color=None, x=0, y=0):
        g.save_context()
        g.move_to(x or self.x, y or self.y)
        self._set_text(text)
        self._show(g, color)
        g.restore_context()


class DataRow(object):
    def __init__(self, label, data=None):
        self.label = label
        self.data = data or label

class CompleteTree(graphics.Scene, gtk.Scrollable):
    """
    ASCII Art

    | Icon | Activity - description |

    """

    __gsignals__ = {
        # enter or double-click, passes in current day and fact
        'on-activate-row': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
        'on-change-row': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
    }



    hadjustment = gobject.property(type=gtk.Adjustment, default=None)
    hscroll_policy = gobject.property(type=gtk.ScrollablePolicy, default=gtk.ScrollablePolicy.MINIMUM)
    vadjustment = gobject.property(type=gtk.Adjustment, default=None)
    vscroll_policy = gobject.property(type=gtk.ScrollablePolicy, default=gtk.ScrollablePolicy.MINIMUM)

    def __init__(self):
        graphics.Scene.__init__(self, style_class=gtk.STYLE_CLASS_VIEW)

        self.row_positions = []
        self.row_heights = []

        self.y = 0

        self.hover_row = None
        self.current_row = None
        self.rows = []

        self.style = self._style

        self.label = Label()

        self.visible_range = None

        self.connect("on-mouse-scroll", self.on_scroll)
        self.connect("on-mouse-move", self.on_mouse_move)
        self.connect("on-mouse-down", self.on_mouse_down)

        self.connect("on-resize", self.on_resize)
        self.connect("on-key-press", self.on_key_press)
        self.connect("notify::vadjustment", self._on_vadjustment_change)
        self.connect("on-enter-frame", self.on_enter_frame)
        self.connect("on-double-click", self.on_double_click)


    def on_mouse_down(self, scene, event):
        self.grab_focus()
        if self.hover_row:
            self.set_current_row(self.rows.index(self.hover_row))


    def activate_row(self, day, fact):
        self.emit("on-activate-row", day, fact)


    def on_double_click(self, scene, event):
        if self.hover_row:
            self.activate_row(self.hover_day, self.hover_row)

    def on_key_press(self, scene, event):
        if event.keyval == gdk.KEY_Up:
            idx = self.rows.index(self.current_row) if self.current_row else 1
            self.set_current_row(idx - 1)

        elif event.keyval == gdk.KEY_Down:
            idx = self.rows.index(self.current_row) if self.current_row else -1
            self.set_current_row(idx + 1)

        elif event.keyval == gdk.KEY_Page_Down:
            self.y += self.height * 0.8
            self.on_scroll()

        elif event.keyval == gdk.KEY_Page_Up:
            self.y -= self.height * 0.8
            self.on_scroll()

        elif event.keyval == gdk.KEY_Return:
            self.activate_row(self.hover_day, self.current_row)


    def set_current_row(self, idx):
        idx = max(0, min(len(self.rows) - 1, idx))
        row = self.rows[idx]
        self.current_row = row

        if row.y < self.y:
            self.y = row.y
        if (row.y + 15) > (self.y + self.height):
            self.y = row.y - self.height + 25

        self.emit("on-change-row", self.current_row)
        self.on_scroll()


    def get_visible_range(self):
        start, end = (bisect.bisect(self.row_positions, self.y) - 1,
                      bisect.bisect(self.row_positions, self.y + self.height))

        y = self.y
        return [{"i": start + i, "y": pos - y, "h": height, "row": row}
                    for i, (pos, height, row) in enumerate(zip(self.row_positions[start:end],
                                                               self.row_heights[start:end],
                                                               self.rows[start:end]))]


    def on_mouse_move(self, tree, event):
        hover_day, hover_row = None, None

        for rec in self.visible_range:
            if rec['y'] <= event.y <= (rec['y'] + rec['h']):
                hover_row = rec
                break

        if hover_row != self.hover_row:
            self.hover_row = hover_row


    def _on_vadjustment_change(self, scene, vadjustment):
        if not self.vadjustment:
            return
        self.vadjustment.connect("value_changed", self.on_scroll_value_changed)


    def set_rows(self, rows):
        self.y = 0
        self.current_row = self.hover_row = None

        if self.vadjustment:
            self.vadjustment.set_value(0)


        self.rows = []
        for row in rows:
            self.rows.append(DataRow(*row))

        self.set_row_heights()

        if self.height is not None:
            self.on_scroll()


    def set_row_heights(self):
        """
            the row height is defined by following factors:
                * how many facts are there in the day
                * does the fact have description / tags

            This func creates a list of row start positions to be able to
            quickly determine what to display
        """
        if self.height is None:
            return

        y, pos, heights = 0, [], []

        for row in self.rows:
            row_height = 25
            row.y = y
            row.height = row_height

            pos.append(y)
            heights.append(row_height)
            y += row_height


        self.row_positions, self.row_heights = pos, heights

        maxy = max(y, 1)

        if self.vadjustment:
            self.vadjustment.set_lower(0)
            self.vadjustment.set_upper(max(maxy, self.height))
            self.vadjustment.set_page_size(self.height)

        self.set_size_request(10, maxy)

    def on_resize(self, scene, event):
        self.set_row_heights()
        self.on_scroll()


    def on_scroll_value_changed(self, scroll):
        self.y = int(scroll.get_value())
        self.on_scroll()


    def on_scroll(self, scene=None, event=None):
        y_pos = self.y
        direction = 0
        if event and event.direction == gdk.ScrollDirection.UP:
            direction = -1
        elif event and event.direction == gdk.ScrollDirection.DOWN:
            direction = 1

        if self.vadjustment:
            y_pos += 15 * direction
            y_pos = max(0, min(self.vadjustment.get_upper() - self.height, y_pos))
            self.vadjustment.set_value(y_pos)
            self.y = y_pos

        self.redraw()

        self.visible_range = self.get_visible_range()


    def on_enter_frame(self, scene, context):
        if not self.height:
            return


        has_focus = self.get_toplevel().has_toplevel_focus()
        if has_focus:
            colors = {
                "normal": self.style.get_color(gtk.StateFlags.NORMAL),
                "normal_bg": self.style.get_background_color(gtk.StateFlags.NORMAL),
                "selected": self.style.get_color(gtk.StateFlags.SELECTED),
                "selected_bg": self.style.get_background_color(gtk.StateFlags.SELECTED),
            }
        else:
            colors = {
                "normal": self.style.get_color(gtk.StateFlags.BACKDROP),
                "normal_bg": self.style.get_background_color(gtk.StateFlags.BACKDROP),
                "selected": self.style.get_color(gtk.StateFlags.BACKDROP),
                "selected_bg": self.style.get_background_color(gtk.StateFlags.BACKDROP),
            }

        g = graphics.Graphics(context)
        g.set_line_style(1)
        g.translate(0.5, 0.5)

        for rec in self.visible_range:
            g.save_context()
            g.translate(0, rec['y'])


            color, bg = colors["normal"], colors["normal_bg"]
            if rec['row'] == self.current_row:
                color, bg = colors["selected"], colors["selected_bg"]
                g.fill_area(0, 0, self.width, 25, bg)

            self.label.show(g, rec['row'].label, color=color)

            g.restore_context()




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
        self.entry_checker = self.entry.connect("changed", self.on_entry_changed)
        self.entry.connect("key-press-event", self.on_key_press)

        self.complete_tree = CompleteTree()
        box.pack_end(self.complete_tree, False, False, 0)
        self.complete_tree.connect("on-change-row", self.on_complete_changed)



        self.storage = hamster.client.Storage()
        self.todays_facts = self.storage.get_todays_facts()

        # list of all activities
        self.activities = self.storage.get_activities()

        # list of facts of last month
        now = dt.datetime.now()
        last_month = self.storage.get_facts(now - dt.timedelta(days=30), now)

        # naive recency and frequency rank
        # score is as simple as you get 30-days_ago points for each occurence
        activity_category = defaultdict(int)
        for fact in last_month:
            days = 30 - (now - dt.datetime.combine(fact.date, dt.time())).total_seconds() / 60 / 60 / 24
            activity_category["%s@%s" % (fact.activity, fact.category or "Unsorted")] += days

        activity_category = sorted(activity_category.iteritems(), key=lambda x: x[1], reverse=True)


        self.ignore_stroke = False

        window.add(box)
        window.show_all()
        self.update_suggestions()

    def on_entry_changed(self, entry):
        text = self.entry.get_text()
        self.update_suggestions(text)
        if self.complete_tree.rows:
            self.complete_tree.set_current_row(0)

        if self.ignore_stroke:
            self.ignore_stroke = False
            return



        def complete():
            text, suffix = self.complete_current()
            if suffix:
                #self.ignore_stroke = True
                with self.entry.handler_block(self.entry_checker):
                    self.entry.set_text("%s%s" % (text, suffix))
                    self.entry.select_region(len(text), -1)
        gobject.timeout_add(0, complete)


    def on_key_press(self, entry, event=None):
        if event.keyval in (gdk.KEY_BackSpace, gdk.KEY_Delete):
            self.ignore_stroke = True


    def on_complete_changed(self, tree, current_row):
        pass
        #self.complete_current()


    def complete_current(self):
        current_text = self.entry.get_text()

        current_row = self.complete_tree.current_row
        if not current_row:
            return current_text, None

        last_word = current_text.split(" ")[-1]

        current_label = current_row.data

        res = current_label[len(last_word):]

        return current_text, res



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
            res.append(['%s <span color="#666">- %s</span>' % (variant, description),
                        variant])

        # regular activity
        now = dt.datetime.now()

        if (looking_for in ("start_time", "end_time") and not looks_like_time(text.split(" ")[-1])) or \
           looking_for in ("activity", "category"):
            activities = self.storage.get_activities(current_fragment.strip() if looking_for in("activity", "category") else "")
            for activity in activities:
                label = (fact.get('start_time') or now).strftime("%H:%M-")
                if fact.get('end_time'):
                    label += fact['end_time'].strftime("%H:%M")

                label += " " + activity['name']
                if activity['category']:
                    label += "@%s" % activity['category']




                res.append([label, "%s@%s" % (activity['name'], activity['category'] or "")])




        self.complete_tree.set_rows(res)

        self.scene.render_preview(text)



if __name__ == '__main__':
    window = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
