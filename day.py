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

class InfoBubble(graphics.Sprite):
    def __init__(self):
        graphics.Sprite.__init__(self, opacity = 0, interactive = False)

        self.graphics.rectangle(0, 0.5, 100, 30, 4)
        self.graphics.fill_preserve("#eee", 0.5)
        self.graphics.stroke("#999", 0.5)
        self.fact = None

    def update_info(self, fact):
        self.fact = fact


class Scene(graphics.Scene):
    def __init__(self, start_time = None):
        graphics.Scene.__init__(self)


        self.view_time = start_time or dt.datetime.combine(dt.date.today(), dt.time(5, 30))
        self.start_time = self.view_time - dt.timedelta(hours=12) # we will work with twice the time we will be displaying

        self.view_minutes = 12 * 60

        self.fact_bars = []
        self.categories = []



        self.connect("on-enter-frame", self.on_enter_frame)
        self.connect("on-mouse-move", self.on_mouse_move)
        self.connect("on-mouse-down", self.on_mouse_down)
        self.connect("on-mouse-up", self.on_mouse_up)

        self.connect("on-mouse-over", self.on_mouse_over)
        self.connect("on-mouse-out", self.on_mouse_out)

        self.start_label = graphics.Label("", 8, "#333", visible = False, y = 100, z_order = 100)
        self.end_label = graphics.Label("", 8, "#333", visible = False, y = 100, z_order = 100)
        self.duration_label = graphics.Label("", 8, "#FFF", visible = False, y = 55, z_order = 100)

        self.info_bubble = InfoBubble()

        self.add_child(self.start_label, self.end_label, self.duration_label, self.info_bubble)

        self.drag_start = None
        self.current_x = None

    def add_facts(self, facts):
        for fact in facts:
            fact_bar = graphics.Rectangle(0, 0, fill = "#aaa", interactive = True) # dimensions will depend on screen situation
            fact_bar.fact = fact

            if fact.category in self.categories:
                fact_bar.category = self.categories.index(fact.category)
            else:
                fact_bar.category = len(self.categories)
                self.categories.append(fact.category)

            self.add_child(fact_bar)
            self.fact_bars.append(fact_bar)

    def on_mouse_over(self, scene, targets):
        bar = targets[0]
        pass

    def on_mouse_out(self, scene, event):
        pass


    def on_mouse_down(self, scene, event):
        self.drag_start = self.current_x

    def on_mouse_up(self, scene):
        self.drag_start = None


    def on_mouse_move(self, scene, event):
        if self.current_x:
            active_bar = None
            # find if we are maybe on a bar
            for bar in self.fact_bars:
                if bar.x < self.current_x < bar.x + bar.width:
                    active_bar = bar
                    break

            if active_bar:
                if active_bar.fact != self.info_bubble.fact:
                    self.info_bubble.update_info(active_bar.fact)

                    self.tweener.kill_tweens(self.info_bubble)
                    self.animate(self.info_bubble,
                                 opacity = 1,
                                 x = active_bar.x + active_bar.width + 5,
                                 y = active_bar.y + 5,
                                 duration = 0.3
                                 )
            else:
                self.tweener.kill_tweens(self.info_bubble)
                self.animate(self.info_bubble, opacity = 0)
                self.info_bubble.fact = None

        self.redraw()

    def on_enter_frame(self, scene, context):
        g = graphics.Graphics(context)

        vertical = 7
        minute_pixel = (24.0 * 60) / self.width

        snap_points = []

        g.fill_area(0, 50, self.width, vertical * 10, "#f6f6f6")
        g.set_line_style(width=1)


        self.view_time = self.start_time + dt.timedelta(minutes = self.view_minutes)
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
            start_x = self.mouse_x

            # check for snap points
            delta, closest_snap = min((abs(start_x - i), i) for i in snap_points)

            start_x = max(min(start_x, self.width-1), 0)

            if abs(closest_snap - start_x) < 5 and (not self.drag_start or self.drag_start != closest_snap):
                start_x = closest_snap
                minutes = int(start_x * minute_pixel)
            else:
                start_x = start_x + 0.5
                minutes = int(round(start_x * minute_pixel / 15)) * 15


            self.current_x = minutes / minute_pixel


            start_time = self.view_time + dt.timedelta(hours = minutes / 60, minutes = minutes % 60)

            g.move_to(start_x, 50)
            g.line_to(start_x, 50 + vertical * 10)
            g.stroke("#999")


            end_time, end_x = None, None
            if self.drag_start:
                minutes = int(self.drag_start * minute_pixel)
                end_time =  self.view_time + dt.timedelta(hours = minutes / 60, minutes = minutes % 60)

                end_x = self.drag_start


                x, x2 = min(self.drag_start, start_x), max(self.drag_start, start_x)
                g.rectangle(x, 50, x2-x, vertical * 10)
                g.set_color("#999", 0.5)
                g.fill()

            if end_time and end_time < start_time:
                start_time, end_time = end_time, start_time
                start_x, end_x = end_x, start_x

            self.start_label.text = start_time.strftime("%H:%M")

            if start_x - self.start_label.width - 5 > 0:
                self.start_label.x = start_x - self.start_label.width - 5
            else:
                self.start_label.x = start_x + 5
            self.start_label.visible = True

            if end_time:
                self.end_label.text = end_time.strftime("%H:%M")

                if end_x + 5 + self.end_label.width < self.width:
                    self.end_label.x = end_x + 5
                else:
                    self.end_label.x = end_x - self.end_label.width - 5


                if self.end_label.x > self.start_label.x + self.start_label.width:
                    self.end_label.y = 55
                else:
                    self.end_label.y = 55 + self.start_label.height + 5

                duration = end_time - start_time
                duration = int(duration.seconds / 60)
                self.duration_label.text =  "%02d:%02d" % (duration / 60, duration % 60)

                self.end_label.visible = True

                if self.duration_label.width < end_x - start_x:
                    self.duration_label.y = 80
                    self.duration_label.visible = True
                    self.duration_label.x = start_x + (end_x - start_x - self.duration_label.width) / 2
                    self.duration_label.visible = True
                else:
                    self.duration_label.visible = False
            else:
                self.end_label.visible = False
                self.duration_label.visible = False

        else:
            self.start_label.visible = False
            self.end_label.visible = False


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
