#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""Base template"""


from gi.repository import Gtk as gtk
from lib import graphics
import math
import hamster.client
import datetime as dt
from collections import defaultdict
import itertools


class Chart(graphics.Sprite):
    def __init__(self):
        graphics.Sprite.__init__(self, interactive = False)

    def do_stuff(self, years, categories):
        step = (360.0 / 365) * math.pi / 180.0

        g = self.graphics


        g.set_color("#999")
        g.set_line_style(width = 1)


        # em
        colors = ["#009966", "#33cc00", "#9933cc", "#aaaaaa", "#ff9999", "#99cccc"]
        colors.reverse()

        # em contrast
        colors = ["#00a05f", "#1ee100", "#a0a000", "#ffa000", "#a01ee1", "#a0a0a0", "#ffa0a0", "#a0e1e1"]
        colors.reverse()


        # tango light
        colors = ["#fce94f", "#89e034", "#fcaf3e", "#729fcf", "#ad7fa8", "#e9b96e", "#ef2929", "#eeeeec", "#888a85"]

        # tango medium
        colors =["#edd400", "#73d216", "#f57900", "#3465a4", "#75507b", "#c17d11", "#cc0000", "#d3d7cf", "#555753"]
        #colors = colors[1:]


        #colors = ("#ff0000", "#00ff00", "#0000ff", "#aaa000")


        hour_step = 15
        spacing = 20
        current_pixel = 1220

        g.set_line_style(width = 1)
        g.circle(0, 0, current_pixel - 2)
        g.stroke("#fff", 0.2)
        g.set_line_style(width=1)

        for year in sorted(years.keys()):
            for category in categories:
                ring_height = hour_step * 3

                for day, hours in years[year][category]:
                    year_day = day.isocalendar()[1] * 7 + day.weekday()
                    angle = year_day * step - math.pi / 2

                    distance = current_pixel

                    height = ring_height


                    #bar per category
                    g.move_to(math.cos(angle) * distance + 0,
                              math.sin(angle) * distance + 0)
                    g.line_to(math.cos(angle) * (distance + height),
                              math.sin(angle) * (distance + height))

                    g.line_to(math.cos(angle+step) * (distance + height),
                              math.sin(angle+step) * (distance + height))

                    g.line_to(math.cos(angle+step) * distance,
                              math.sin(angle+step) * distance)
                    g.close_path()

                if years[year][category]:
                    current_pixel += ring_height + 7 + spacing

                color = "#fff" #colors[categories.index(category)]
                g.set_color(color)
                g.fill()

            current_pixel += spacing * 3


            g.set_line_style(width = 4)
            g.circle(0, 0, current_pixel - spacing * 2)
            g.stroke("#fff", 0.5)

            current_pixel += 3





class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)


        storage = hamster.client.Storage()

        self.facts = storage.get_facts(dt.date(2009,1,1), dt.date(2009,12,31))
        print len(self.facts)

        self.day_counts = {}
        categories = defaultdict(int)


        self.years = {}
        for year, facts in itertools.groupby(sorted(self.facts, key=lambda fact:fact.date), lambda fact:fact.date.year):
            self.years[year] = defaultdict(list)
            for category, category_facts in itertools.groupby(sorted(facts, key=lambda fact:fact.category), lambda fact:fact.category):
                for day, day_facts in itertools.groupby(sorted(category_facts, key=lambda fact:fact.date), lambda fact:fact.date):
                    delta = dt.timedelta()
                    for fact in day_facts:
                        delta += fact.delta
                    delta = delta.seconds / 60 / 60 + delta.days * 24

                    self.years[year][category].append((day, delta))

                categories[category] += 1

        self.categories = categories.keys()


        self.chart = Chart()

        self.add_child(self.chart)

        self.chart.do_stuff(self.years, self.categories)

        self.connect("on-enter-frame", self.on_enter_frame)
        self.connect("on-mouse-move", self.on_mouse_move)

        #self.animate(self.chart, rotation=math.pi * 2, duration = 3)

    def on_mouse_move(self, scene, event):
        x, y = self.width / 2, self.height / 2

        max_distance = math.sqrt((self.width / 2) ** 2 + (self.height / 2) ** 2)

        distance = math.sqrt((x - event.x) ** 2 + (y - event.y) ** 2)

        #self.chart.scale_x = 2 - 2 * (distance / float(max_distance))
        #self.chart.scale_y = 2 - 2 * (distance / float(max_distance))
        #self.redraw()

    def on_enter_frame(self, scene, context):
        g = graphics.Graphics(context)
        g.fill_area(0, 0, self.width, self.height, "#20b6de")

        self.chart.x = self.width / 2
        self.chart.y = self.height / 2
        self.chart.scale_x = 0.18
        self.chart.scale_y = 0.18





class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_size_request(700, 600)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()


example = BasicWindow()
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
gtk.main()
