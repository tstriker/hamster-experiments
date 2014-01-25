#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2012 Toms Bauģis <toms.baugis at gmail.com>

"""Potential edit activities replacement"""

from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import GObject as gobject

from lib import graphics
import hamster.client
from hamster.lib import stuff
from hamster import widgets


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
    __gsignals__ = {
        #: fires when any of the child widgets are clicked
        "on-activate": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
    }

    def __init__(self, width, fact, color, **kwargs):
        graphics.Sprite.__init__(self, **kwargs)
        self.width = width
        self.height = 27
        self.natural_height = 27
        self.fact = fact
        self.color = color

        self.interactive = True
        self.mouse_cursor = gdk.CursorType.XTERM

        self.fact_labels = graphics.Sprite()

        self.start_label = graphics.Label("", color="#333", size=11, x=10, y=5, interactive=True,
                                          mouse_cursor=gdk.CursorType.XTERM)
        self.start_label.text = "%s - " % fact.start_time.strftime("%H:%M")
        self.fact_labels.add_child(self.start_label)

        self.end_label = graphics.Label("", color="#333", size=11, x=65, y=5, interactive=True,
                                        mouse_cursor=gdk.CursorType.XTERM)
        if fact.end_time:
            self.end_label.text = fact.end_time.strftime("%H:%M")
        self.fact_labels.add_child(self.end_label)

        self.activity_label = graphics.Label(fact.activity, color="#333", size=11, x=120, y=5, interactive=True,
                                             mouse_cursor=gdk.CursorType.XTERM)
        self.fact_labels.add_child(self.activity_label)

        self.category_label = graphics.Label("", color="#333", size=9, y=7, interactive=True,
                                             mouse_cursor=gdk.CursorType.XTERM)
        self.category_label.text = stuff.escape_pango(" - %s" % fact.category)
        self.category_label.x = self.activity_label.x + self.activity_label.width
        self.fact_labels.add_child(self.category_label)


        self.duration_label = graphics.Label(stuff.format_duration(fact.delta), size=11, color="#333", interactive=True,
                                             mouse_cursor=gdk.CursorType.XTERM)
        self.duration_label.x = self.width - self.duration_label.width - 5
        self.duration_label.y = 5
        self.fact_labels.add_child(self.duration_label)

        self.add_child(self.fact_labels)

        self.edit_links = graphics.Sprite(x=10, y = 110, opacity=0)

        self.delete_link = graphics.Label("Delete", size=11, color="#555", interactive=True)
        self.save_link = graphics.Label("Save", size=11, x=390, color="#555", interactive=True)
        self.cancel_link = graphics.Label("Cancel", size=11, x=440, color="#555", interactive=True)
        self.edit_links.add_child(self.delete_link, self.save_link, self.cancel_link)

        self.add_child(self.edit_links)

        for sprite in self.fact_labels.sprites:
            sprite.connect("on-click", self.on_sprite_click)

        self.connect("on-render", self.on_render)
        self.connect("on-click", self.on_click)

    def on_sprite_click(self, sprite, event):
        self.emit("on-activate", sprite)

    def on_click(self, sprite, event):
        self.emit("on-activate", self.activity_label)

    def set_edit(self, edit_mode):
        self.edit_mode = edit_mode
        if edit_mode:
            self.fact_labels.animate(opacity=0)
            self.edit_links.animate(opacity=1)
        else:
            self.fact_labels.animate(opacity=1)
            self.edit_links.animate(opacity=0)

    def on_render(self, sprite):
        self.graphics.rectangle(0, 0, self.width, self.height)
        self.graphics.fill_preserve(self.color)
        self.graphics.clip()



class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        self.tweener.default_duration = 0.1

        self.total_hours = 24
        self.height = 500
        self.pixels_in_minute =  float(self.height) / (self.total_hours * 60)

        self.spacing = 1

        self.fact_list = graphics.Sprite(x=40, y=50)
        self.add_child(self.fact_list)

        self.fragments = Container(30)

        self.connectors = graphics.Sprite(x=self.fragments.x + self.fragments.width)
        self.connectors.width = 30

        self.entries = Container(500, x=self.connectors.x + self.connectors.width)

        self.fact_list.add_child(self.fragments, self.connectors, self.entries)

        self.storage = hamster.client.Storage()

        self._date = dt.datetime.combine(dt.date.today(), dt.time()) + dt.timedelta(hours=5)


        self.date_label = graphics.Label("", size=18, y = 10, color="#444")
        self.add_child(self.date_label)


        self.entry_positions = []

        self.set_size_request(610, 500)

        self.current_entry = None

        self.connect("on-enter-frame", self.on_enter_frame)


    def render_facts(self, date = None):
        date = date or self._date

        self.container.edit_box.hide()
        facts = self.storage.get_facts(date)
        self.fragments.sprites = []
        self.connectors.sprites = []
        self.entries.sprites = []

        self.date_label.text = date.strftime("%d. %b %Y")

        for i, fact in enumerate(facts):
            if fact.activity not in fact_names:
                fact_names.append(fact.activity)

            color_index = fact_names.index(fact.activity) % len(colors)
            color = colors[color_index]

            fragment_height = int(delta_minutes(fact.start_time, fact.end_time) * self.pixels_in_minute)
            self.fragments.add_child(graphics.Rectangle(self.fragments.width, fragment_height, fill=color))

            entry = Entry(self.entries.width, fact, entry_colors[color_index])
            self.entries.add_child(entry)
            entry.connect("on-activate", self.on_entry_click)

        self.position_entries(date)


    def position_entries(self, date):
        entry_y = 0

        for fragment, entry in zip(self.fragments.sprites, self.entries.sprites):
            fragment.y = int(delta_minutes(date, entry.fact.start_time) * self.pixels_in_minute)

            entry.y = entry_y
            entry_y += entry.height


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


    def on_entry_click(self, clicked_entry, target):
        self.select(clicked_entry, target)

    def select(self, clicked_entry, target):
        prev_entry = None
        #self.container.edit_box.hide()
        idx = self.entries.sprites.index(clicked_entry)

        def get(widget_name):
            return getattr(self.container, widget_name)


        def on_update(sprite):
            self.draw_connectors()

            if sprite.height < 65 and prev_entry:
                sprite = prev_entry
            else:
                if self.current_entry != clicked_entry:
                    self.current_entry = clicked_entry
                    clicked_entry.set_edit(True)
                    if prev_entry:
                        prev_entry.set_edit(False)


                show_edit(clicked_entry)


            scene_y = int(sprite.parent.to_scene_coords(0, sprite.y)[1])
            self.container.fixed.move(self.container.edit_box, 100, scene_y)
            self.container.edit_box.set_size_request(int(sprite.width - 10), int(sprite.height))

            get("edit_box").set_visible(sprite.height > 35)
            get("description_entry").set_visible(sprite.height > 65)


        def on_complete(sprite):
            self.draw_connectors()

            clicks = {clicked_entry.start_label: "start_entry",
                      clicked_entry.end_label: "end_entry",
                      clicked_entry.activity_label: "activity_entry",
                      clicked_entry.category_label: "activity_entry",
                      clicked_entry.duration_label: "activity_entry",
            }
            get(clicks[target]).grab_focus()



        def show_edit(entry):
            get("start_entry").set_time(entry.fact.start_time)
            get("end_entry").set_start_time(entry.fact.start_time)
            if entry.fact.end_time:
                get("end_entry").set_time(entry.fact.end_time)
            get("activity_entry").set_text("%s@%s" % (entry.fact.activity, entry.fact.category))
            get("tags_entry").set_text(", ".join(entry.fact.tags))
            get("description_entry").set_text(entry.fact.description or "")

            scene_y = int(clicked_entry.parent.to_scene_coords(0, clicked_entry.y)[1])
            self.container.fixed.move(self.container.edit_box, 100, scene_y)



        for entry in self.entries.sprites:
            if entry != clicked_entry and entry.height != entry.natural_height:
                prev_entry = entry
                entry.animate(height = entry.natural_height)


        target_height = 135
        fragment = self.fragments.sprites[idx]
        y = fragment.y + (fragment.height - target_height) / 2




        clicked_entry.animate(height=target_height, y=y,
                              on_update=on_update,
                              on_complete=on_complete)

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
            hour = self._date + dt.timedelta(hours=i)
            y = delta_minutes(self._date, hour) * self.pixels_in_minute
            g.move_to(0, self.fact_list.y + y)
            g.show_label(hour.strftime("%H:%M"), 10, "#666")




class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_default_size(600, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        vbox = gtk.VBox(spacing=10)
        vbox.set_border_width(12)
        self.scene = Scene()

        self.fixed = gtk.Fixed()
        self.fixed.put(self.scene, 0, 0)

        self.scene.container = self


        self.edit_box = gtk.HBox()
        self.edit_box.set_border_width(6)
        self.fixed.put(self.edit_box, 100, 0)


        container = gtk.HBox(spacing=5)
        self.edit_box.add(container)

        start_entry = widgets.TimeInput()
        self.start_entry = start_entry
        box = gtk.VBox()
        box.add(start_entry)
        container.add(box)

        end_entry = widgets.TimeInput()
        self.end_entry = end_entry
        box = gtk.VBox()
        box.add(end_entry)
        container.add(box)

        entry_box = gtk.VBox(spacing=5)
        container.add(entry_box)

        activity_entry = widgets.ActivityEntry()
        activity_entry.set_width_chars(35)
        self.activity_entry = activity_entry
        entry_box.add(activity_entry)

        tags_entry = widgets.TagsEntry()
        self.tags_entry = tags_entry
        entry_box.add(tags_entry)

        description_entry = gtk.Entry()
        description_entry.set_width_chars(35)
        self.description_entry = description_entry
        entry_box.add(description_entry)

        save_button = gtk.Button("Save")
        entry_box.add(save_button)


        container.add(gtk.HBox())
        vbox.add(self.fixed)

        button_box = gtk.HBox(spacing=5)
        vbox.add(button_box)
        window.add(vbox)

        prev_day = gtk.Button("Previous day")
        next_day = gtk.Button("Next day")
        button_box.add(gtk.HBox())
        button_box.add(prev_day)
        button_box.add(next_day)

        prev_day.connect("clicked", self.on_prev_day_click)
        next_day.connect("clicked", self.on_next_day_click)

        self.scene.render_facts()

        window.show_all()
        self.edit_box.hide()

    def on_prev_day_click(self, button):
        self.scene._date -= dt.timedelta(days=1)
        self.scene.render_facts()

    def on_next_day_click(self, button):
        self.scene._date += dt.timedelta(days=1)
        self.scene.render_facts()

if __name__ == '__main__':
    from hamster.lib import i18n
    i18n.setup_i18n()

    window = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
