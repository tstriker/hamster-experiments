#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
    Duration picker. Following http://colorhat.com/
"""


import gtk
from lib import graphics
import datetime as dt

class Fact(object):
    def __init__(self, start_time, end_time, name, category):
        self.start_time = start_time
        self.end_time = end_time
        self.name = name
        self.category = category


class Selection(graphics.Shape):
    def __init__(self, start_time = None, end_time = None):
        graphics.Shape.__init__(self, stroke = "#999", fill = "#999")
        self.start_time, self.end_time  = None, None
        self.width, self.height = 0, 0

        self.start_label = graphics.Label("", 8, "#333", visible = False, z_order = 100)
        self.end_label = graphics.Label("", 8, "#333", visible = False, z_order = 100)
        self.duration_label = graphics.Label("", 8, "#FFF", visible = False, z_order = 100)

        self.add_child(self.start_label, self.end_label, self.duration_label)

    def draw_shape(self):
        self.graphics.rectangle(0, 0, self.width, self.height)
        self.graphics.fill(self.fill, 0.5)

        self.graphics.move_to(0, 0)
        self.graphics.line_to(0, self.height)
        self.graphics.move_to(self.width, 0)
        self.graphics.line_to(self.width, self.height)


        # adjust labels
        self.start_label.visible = self.start_time is not None
        if self.start_label.visible:
            self.start_label.text = self.start_time.strftime("%H:%M")
            if self.x - self.start_label.width - 5 > 0:
                self.start_label.x = -self.start_label.width - 5
            else:
                self.start_label.x = 5

            self.start_label.y = self.height - self.start_label.height

        self.end_label.visible = self.end_time is not None
        if self.end_label.visible:
            self.end_label.text = self.end_time.strftime("%H:%M")
            self.end_label.x = self.width + 5



            duration = self.end_time - self.start_time
            duration = int(duration.seconds / 60)
            self.duration_label.text =  "%02d:%02d" % (duration / 60, duration % 60)

            self.duration_label.visible = self.duration_label.width < self.width
            if self.duration_label.visible:
                self.duration_label.y = (self.height - self.duration_label.height) / 2
                self.duration_label.x = (self.width - self.duration_label.width) / 2
        else:
            self.duration_label.visible = False



class Scene(graphics.Scene):
    def __init__(self, start_time = None):
        graphics.Scene.__init__(self)


        self.view_time = start_time or dt.datetime.combine(dt.date.today(), dt.time(5, 30))
        self.start_time = self.view_time - dt.timedelta(hours=12) # we will work with twice the time we will be displaying

        self.fact_bars = []
        self.categories = []



        self.connect("on-enter-frame", self.on_enter_frame)
        self.connect("on-mouse-move", self.on_mouse_move)
        self.connect("on-mouse-down", self.on_mouse_down)
        self.connect("on-mouse-up", self.on_mouse_up)
        self.connect("on-click", self.on_click)


        self.selection = Selection()
        self.selection.z_order = 100

        self.chosen_selection = Selection()
        self.selection.z_order = 100

        self.add_child(self.selection, self.chosen_selection)

        self.drag_start = None
        self.current_x = None


    def add_facts(self, facts):
        for fact in facts:
            fact_bar = graphics.Rectangle(0, 0, fill = "#aaa") # dimensions will depend on screen situation
            fact_bar.fact = fact

            if fact.category in self.categories:
                fact_bar.category = self.categories.index(fact.category)
            else:
                fact_bar.category = len(self.categories)
                self.categories.append(fact.category)

            self.add_child(fact_bar)
            self.fact_bars.append(fact_bar)


    def on_mouse_down(self, scene, event):
        self.drag_start = self.current_x
        if self.chosen_selection in self.sprites:
            self.sprites.remove(self.chosen_selection)

    def on_mouse_up(self, scene):
        if self.drag_start:
            self.drag_start = None
            self.sprites.remove(self.selection)

            self.chosen_selection = self.selection
            self.selection = Selection()
            self.selection.z_order = 100

            self.add_child(self.selection, self.chosen_selection)

    def on_click(self, scene, event, targets):
        print "click"
        self.drag_start = None
        self.redraw()

    def on_mouse_move(self, scene, event):
        if self.current_x:
            active_bar = None
            # find if we are maybe on a bar
            for bar in self.fact_bars:
                if bar.x < self.current_x < bar.x + bar.width:
                    active_bar = bar
                    break

            if active_bar:
                self.set_tooltip_text("%s - %s" % (active_bar.fact.name, active_bar.fact.category))
            else:
                self.set_tooltip_text("")

        self.redraw()


    def on_enter_frame(self, scene, context):
        g = graphics.Graphics(context)

        vertical = 7
        minute_pixel = (24.0 * 60) / self.width

        snap_points = []

        g.fill_area(0, 50, self.width, vertical * 10, "#f6f6f6")
        g.set_line_style(width=1)



        for bar in self.fact_bars:
            bar.y = 50 + vertical * bar.category
            bar.height = vertical


            minutes = (bar.fact.start_time - self.view_time).seconds / 60 + (bar.fact.start_time - self.view_time).days * 24  * 60

            bar.x = round(minutes / minute_pixel) + 0.5
            bar.width = round((bar.fact.end_time - bar.fact.start_time).seconds / 60 / minute_pixel)

            snap_points.append(bar.x)
            snap_points.append(bar.x + bar.width)


        if self.view_time < dt.datetime.now() < self.view_time + dt.timedelta(hours = 24):
            minutes = round((dt.datetime.now() - self.view_time).seconds / 60 / minute_pixel) + 0.5
            g.move_to(minutes, 50)
            g.line_to(minutes, 50 + vertical * 10)
            g.stroke("#f00", 0.4)
            snap_points.append(minutes - 0.5)


        if self.mouse_x:
            start_x = max(min(self.mouse_x, self.width-1), 0) #mouse, but within screen regions

            # check for snap points
            delta, closest_snap = min((abs(start_x - i), i) for i in snap_points)


            if abs(closest_snap - start_x) < 5 and (not self.drag_start or self.drag_start != closest_snap):
                start_x = closest_snap
                minutes = int(start_x * minute_pixel)
            else:
                start_x = start_x + 0.5
                minutes = int(round(start_x * minute_pixel / 15)) * 15


            self.current_x = minutes / minute_pixel


            start_time = self.view_time + dt.timedelta(hours = minutes / 60, minutes = minutes % 60)

            end_time, end_x = None, None
            if self.drag_start:
                minutes = int(self.drag_start * minute_pixel)
                end_time =  self.view_time + dt.timedelta(hours = minutes / 60, minutes = minutes % 60)
                end_x = round(self.drag_start) + 0.5

            if end_time and end_time < start_time:
                start_time, end_time = end_time, start_time
                start_x, end_x = end_x, start_x


            self.selection.start_time = start_time
            self.selection.end_time = end_time

            self.selection.x = start_x
            self.selection.width = 0
            if end_time:
                self.selection.width = end_x - start_x

            self.selection.y = 50
            self.selection.height = vertical * 10





class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(600, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        scene = Scene()

        today = dt.datetime.today()

        scene.add_facts([
            Fact(today.replace(hour=8, minute=45), today.replace(hour=9, minute=45), "hamster", "hacking"),
            Fact(today.replace(hour=10, minute=18), today.replace(hour=11, minute=9), "semlib", "work"),
            Fact(today.replace(hour=11, minute=23), today.replace(hour=13, minute=12), "hamster", "hacking"),
            Fact(today.replace(hour=3, minute=23), today.replace(hour=8, minute=0), "semlib", "work"),
        ])

        window.add(scene)
        window.show_all()

example = BasicWindow()
gtk.main()
