#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2012 Toms Bauģis <toms.baugis at gmail.com>

"""Potential edit activities replacement"""


import gtk
from lib import graphics
import hamster.client
from hamster.lib import stuff
import datetime as dt

colors = ["#95CACF", "#A2CFB6", "#D1DEA1", "#E4C384", "#DE9F7B"]
connector_colors = ["#51868C", "#76A68B", "#ADBF69", "#D9A648", "#BF6A39"]
entry_colors = ["#95CACF", "#A2CFB6", "#D1DEA1", "#E4C384", "#DE9F7B"]

fact_names = []


def delta_minutes(start, end):
    end = end or dt.datetime.now()
    return (end - start).days * 24 * 60 + (end - start).seconds / 60

class Container(graphics.Sprite):
    def __init__(self, width = 100, **kwargs):
        graphics.Sprite.__init__(self, **kwargs)
        self.width = width

        self.connect("on-render", self.on_render)

    def on_render(self, sprite):
        self.graphics.rectangle(0, 0, self.width, 500)
        self.graphics.fill("#fff")


class Entry(graphics.Sprite):
    def __init__(self, width, fact, color, **kwargs):
        graphics.Sprite.__init__(self, **kwargs)
        self.width = width
        self.height = 27
        self.natural_height = 27
        self.fact = fact
        self.color = color

        self.interactive = True
        self.mouse_cursor = gtk.gdk.XTERM

        time_label = graphics.Label("", color="#333", size=11, x=15, y = 5)
        time_label.text = "%s - " % fact.start_time.strftime("%H:%M")
        if fact.end_time:
            time_label.text += fact.end_time.strftime("%H:%M")
        self.add_child(time_label)

        activity_label = graphics.Label(fact.activity, color="#333", size=11, x=110, y = 5)
        self.add_child(activity_label)

        category_label = graphics.Label("", color="#333", size=9, y = 7)
        category_label.text = stuff.escape_pango(" - %s" % fact.category)
        category_label.x = activity_label.x + activity_label.width
        self.add_child(category_label)


        duration_label = graphics.Label(stuff.format_duration(fact.delta), size=11, color="#333")
        duration_label.x = self.width - duration_label.width - 5
        duration_label.y = 5
        self.add_child(duration_label)

        self.connect("on-render", self.on_render)

    def on_render(self, sprite):
        self.graphics.fill_area(0, 0, self.width, self.height, self.color)



class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        self.total_hours = 24
        self.height = 500
        self.pixels_in_minute =  float(self.height) / (self.total_hours * 60)

        self.spacing = 1

        self.fact_list = graphics.Sprite(x=40, y=50)
        self.add_child(self.fact_list)

        self.fragments = Container(70)
        self.connectors = graphics.Sprite(x=self.fragments.x + self.fragments.width)
        self.connectors.width = 30

        self.entries = Container(500, x=self.connectors.x + self.connectors.width)

        self.fact_list.add_child(self.fragments, self.connectors, self.entries)

        self.storage = hamster.client.Storage()

        start_date = dt.date(2012, 2, 7)
        self.date = dt.datetime.combine(start_date, dt.time()) + dt.timedelta(hours=5)

        self.date_label = graphics.Label("", size=18, y = 10, color="#444")
        self.add_child(self.date_label)


        self.entry_positions = []
        self.render_facts()

        self.connect("on-enter-frame", self.on_enter_frame)



    def render_facts(self):
        facts = self.storage.get_facts(self.date)
        self.fragments.sprites = []
        self.connectors.sprites = []
        self.entries.sprites = []

        self.date_label.text = self.date.strftime("%d. %b %Y")

        entry_y = 0
        for i, fact in enumerate(facts):
            if fact.activity not in fact_names:
                fact_names.append(fact.activity)

            color_index = fact_names.index(fact.activity) % len(colors)
            color = colors[color_index]

            #fragments are simple
            fragment_y = int(delta_minutes(self.date, fact.start_time) * self.pixels_in_minute)
            fragment_height = int(delta_minutes(fact.start_time, fact.end_time) * self.pixels_in_minute)
            self.fragments.add_child(graphics.Rectangle(self.fragments.width, fragment_height, fill=color, y=fragment_y))


            entry = Entry(self.entries.width, fact, entry_colors[color_index], y=entry_y)
            self.entries.add_child(entry)
            entry.connect("on-click", self.on_entry_click)
            entry_y += entry.height

        # now move entries
        # first move them all to the top
        entry_y = 0
        for entry in self.entries.sprites:
            entry.y = entry_y
            entry_y = entry.y + entry.height

        # then try centering them with the fragments
        for entry in reversed(self.entries.sprites):
            idx = self.entries.sprites.index(entry)
            fragment = self.fragments.sprites[idx]

            min_y = 0
            if idx > 0:
                prev_sprite = self.entries.sprites[idx-1]
                min_y = prev_sprite.y + prev_sprite.height + 1

            entry.y = fragment.y + (fragment.height - entry.height) / 2
            entry.y = max(entry.y, min_y)

            if idx < len(self.entries.sprites) - 1:
                next_sprite = self.entries.sprites[idx+1]
                max_y = next_sprite.y - entry.height - self.spacing

                entry.y = min(entry.y, max_y)

        self.entry_positions = [entry.y for entry in self.entries.sprites]
        self.draw_connectors()



    def on_entry_click(self, clicked_entry, event):
        idx = self.entries.sprites.index(clicked_entry)

        def grow_parent(sprite):
            self.draw_connectors()


        for entry in self.entries.sprites:
            if entry != clicked_entry and entry.height != entry.natural_height:
                entry.animate(height = entry.natural_height)


        target_height = 80
        fragment = self.fragments.sprites[idx]
        y = fragment.y + (fragment.height - target_height) / 2
        clicked_entry.animate(height=target_height, y = y, on_update=grow_parent)


        # entries above current move upwards when necessary
        prev_entries = self.entries.sprites[:idx]
        max_y = y - 1
        for entry in reversed(prev_entries):
            pos = self.entry_positions[self.entries.sprites.index(entry)]
            target_y = min(pos, max_y - entry.natural_height)
            entry.animate(y=target_y)
            max_y = max_y - entry.natural_height - 1


        # entries below current move down when necessary
        next_entries = self.entries.sprites[idx+1:]
        min_y = y + target_height + 1
        for entry in next_entries:
            pos = self.entry_positions[self.entries.sprites.index(entry)]
            target_y = max(pos, min_y)
            entry.animate(y = target_y)
            min_y += entry.natural_height + 1




    def draw_connectors(self):
        # draw connectors
        g = self.connectors.graphics
        g.clear()
        g.set_line_style(width=1)
        g.clear()

        for fragment, entry in zip(self.fragments.sprites, self.entries.sprites):
            x2 = self.connectors.width

            g.move_to(0, fragment.y)
            g.line_to([(x2, entry.y),
                       (x2, entry.y + entry.height),
                       (0, fragment.y + fragment.height),
                       (0, fragment.y)])
            g.fill(connector_colors[colors.index(fragment.fill)])



    def on_enter_frame(self, scene, context):
        g = graphics.Graphics(context)
        for i in range (self.total_hours):
            hour = self.date + dt.timedelta(hours=i)
            y = delta_minutes(self.date, hour) * self.pixels_in_minute
            g.move_to(0, self.fact_list.y + y)
            g.show_label(hour.strftime("%H:%M"), 10, "#666")




class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_default_size(700, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        vbox = gtk.VBox(spacing=10)
        vbox.set_border_width(12)
        self.scene = Scene()
        vbox.pack_start(self.scene)

        button_box = gtk.HBox(spacing=5)
        vbox.pack_start(button_box, False)
        window.add(vbox)

        prev_day = gtk.Button("Previous day")
        next_day = gtk.Button("Next day")
        button_box.pack_start(gtk.HBox())
        button_box.pack_start(prev_day, False)
        button_box.pack_start(next_day, False)

        prev_day.connect("clicked", self.on_prev_day_click)
        next_day.connect("clicked", self.on_next_day_click)

        window.show_all()

    def on_prev_day_click(self, button):
        self.scene.date -= dt.timedelta(days=1)
        self.scene.render_facts()

    def on_next_day_click(self, button):
        self.scene.date += dt.timedelta(days=1)
        self.scene.render_facts()

if __name__ == '__main__':
    from hamster.lib import i18n
    i18n.setup_i18n()

    window = BasicWindow()
    gtk.main()
