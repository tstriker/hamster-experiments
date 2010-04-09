#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
    Duration picker. Following http://colorhat.com/
"""


import gtk
from lib import graphics
import datetime as dt

class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)

        self.connect("on-enter-frame", self.on_enter_frame)
        self.connect("on-mouse-move", self.on_mouse_move)
        self.connect("on-mouse-down", self.on_mouse_down)
        self.connect("on-mouse-up", self.on_mouse_up)

        self.start_label = graphics.Label("", 8, "#333", visible = False, y = 55)
        self.end_label = graphics.Label("", 8, "#333", visible = False, y = 55)
        self.duration_label = graphics.Label("", 8, "#FFF", visible = False, y = 55)

        self.add_child(self.start_label, self.end_label, self.duration_label)

        self.drag_start = None
        self.current_x = None

    def on_mouse_down(self, scene, event):
        self.drag_start = self.current_x

    def on_mouse_up(self, scene):
        self.drag_start = None


    def on_mouse_move(self, scene, event):
        self.redraw()

    def on_enter_frame(self, scene, context):
        vertical = 7

        horizontal = self.width / 96.0

        g = graphics.Graphics(context)

        g.set_line_style(width=1)

        g.fill_area(0, 50, self.width, vertical * 10, "#f6f6f6")

        snap_points = []

        keys = []
        x = 10
        def add_level(key, length):
            if key in keys:
                idx = keys.index(key)
            else:
                idx = len(keys)
                keys.append(key)

            idx += 3

            w = round(length / 15.0 * horizontal)

            g.rectangle(x + 0.5, 50 + idx * vertical, w, vertical)
            snap_points.append(x + 0.5)
            snap_points.append(x + 0.5 + w)
            return w

        x += add_level(1, 30)
        x += add_level(2, 100)
        x += add_level(3, 50)
        x += add_level(1, 20)
        x += add_level(4, 37)
        x += add_level(5, 70)
        x += add_level(1, 70)

        g.fill("#aaa", 0.5)

        if self.mouse_x:
            start_x = self.mouse_x

            # check for snap points
            delta, closest_snap = min((abs(start_x - i), i) for i in snap_points)

            if abs(closest_snap - start_x) < horizontal - 1 and (not self.drag_start or self.drag_start != closest_snap):
                start_x = closest_snap
            else:
                start_x = start_x + 0.5


            self.current_x = start_x

            minutes = int(start_x / horizontal) * 15
            start_time = dt.time(minutes / 60, minutes % 60)

            g.move_to(start_x, 50)
            g.line_to(start_x, 50 + vertical * 10)
            g.stroke("#999")


            end_time, end_x = None, None
            if self.drag_start:
                minutes = int(self.drag_start / horizontal) * 15
                end_time = dt.time(minutes / 60, minutes % 60)

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
                self.end_label.x = end_x + 5

                if end_x + 5 > self.start_label.x + self.start_label.width:
                    self.end_label.y = 55
                else:
                    self.end_label.y = 55 + self.start_label.height + 5

                duration = (dt.datetime.combine(dt.date.today(), end_time) - dt.datetime.combine(dt.date.today(), start_time))
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
        window.add(Scene())
        window.show_all()

example = BasicWindow()
gtk.main()
