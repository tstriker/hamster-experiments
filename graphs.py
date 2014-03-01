#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2014 Toms Baugis <toms.baugis@gmail.com>

"""Base template"""

from gi.repository import Gtk as gtk
from lib import graphics
from lib.pytweener import Easing

import datetime
import datetime as dt


def full_pixels(space, data, gap_pixels=1):
    """returns the given data distributed in the space ensuring it's full pixels
    and with the given gap.
    this will result in minor sub-pixel inaccuracies.
    """
    available = space - (len(data) - 1) * gap_pixels # 8 recs 7 gaps

    res = []
    for i, val in enumerate(data):
        # convert data to 0..1 scale so we deal with fractions
        data_sum = sum(data[i:])
        norm = val * 1.0 / data_sum


        w = max(int(round(available * norm)), 1)
        res.append(w)
        available -= w
    return res


class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.connect("on-enter-frame", self.on_enter_frame)
        self.background_color = "#333"

    def time_volume(self, g, data):
        total_claimed = sum((rec['claimed'] for rec in data))
        max_claimed = max((rec['claimed'] for rec in data))

        total_duration = dt.timedelta()
        for rec in data:
            total_duration += rec['time']
        total_duration = total_duration.total_seconds()

        h = 100
        w = (self.width - 50) / 100.0 * total_claimed

        colors = {
            "slow": "#63623F",
            "fast": "#3F5B63",
        }

        g.move_to(0, h / 2)
        g.line_to(w, h / 2)
        g.stroke("#eee")

        for rec in data:
            rec_x = w * rec['time'].total_seconds() / total_duration
            rec_h = int(h / 2.0 * (rec['claimed'] / max_claimed))
            rec_h = max(rec_h, 1)

            g.circle(rec_x, h / 2, rec_h)
            g.fill(graphics.Colors.contrast(colors[rec['speed']], 50), 0.5)
            """
            g.fill_area(0, h-rec_h,
                        int(rec_w), rec_h,
                        graphics.Colors.contrast(colors[rec['speed']], 50))
            """

            g.translate(rec_x, 0)

    def just_volume(self, g, data):
        """a stacked bar of just volumes up to claimed"""
        total_claimed = sum((rec['claimed'] for rec in data))

        h = 50
        w = int(self.width / 100.0 * total_claimed)

        colors = {
            "slow": "#63623F",
            "fast": "#3F5B63",
        }

        g.save_context()

        gap = 3
        widths = full_pixels(w, [rec['claimed'] for rec in data], gap)
        for rec_w, rec in zip(widths, data):
            g.fill_area(-0.5, -0.5,
                        rec_w, h + 1,
                        graphics.Colors.contrast(colors[rec['speed']], 50))

            g.translate(rec_w + gap, 0)

            g.move_to(-gap+1, -0.5)
            g.line_to(-gap+1, h + 1)
            g.stroke(graphics.Colors.contrast(colors[rec['speed']], 0))
        g.restore_context()


        g.rectangle(-2, -2, self.width-14, h+4)
        g.move_to(int(w), -20)
        g.line_to(int(w), h + 20)
        g.stroke("#eee")



    def duration_vs_volume(self, g, data):
        """a scatterplot of claim patterns"""
        total_claimed = sum((rec['claimed'] for rec in data))
        max_claimed = max((rec['claimed'] for rec in data))



        durations = [data[0]["time"]]
        max_duration = durations[0]
        for prev, next in zip(data, data[1:]):
            durations.append(next['time']-prev['time'])
            max_duration = max(max_duration, durations[-1])

        max_duration = max_duration.total_seconds()

        h = 200
        w = self.width - 20

        colors = {
            "slow": "#63623F",
            "fast": "#3F5B63",
        }

        g.move_to(0, 0)
        g.line_to([(0, h), (w, h)])
        g.stroke("#aaa")

        for rec, duration in zip(data, durations):
            x = w * 0.8 * duration.total_seconds() / max_duration
            y = h - h * 0.8 * rec['claimed'] / max_claimed

            g.fill_area(x-5, y-5,
                        10, 10,
                        graphics.Colors.contrast(colors[rec['speed']], 50))





    def on_enter_frame(self, scene, context):
        g = graphics.Graphics(context)

        data = [{'claimed': 0.7466666666666667, 'speed': 'fast', 'time': datetime.timedelta(0, 2, 52537)},
                {'claimed': 1.7813333333333334, 'speed': 'fast', 'time': datetime.timedelta(0, 4, 449440)}, {'claimed': 2.965333333333333, 'speed': 'fast', 'time': datetime.timedelta(0, 9, 171014)}, {'claimed': 45.424, 'speed': 'slow', 'time': datetime.timedelta(0, 16, 733329)}, {'claimed': 0.8, 'speed': 'fast', 'time': datetime.timedelta(0, 19, 697931)}, {'claimed': 1.44, 'speed': 'fast', 'time': datetime.timedelta(0, 21, 693617)}, {'claimed': 0.4053333333333333, 'speed': 'fast', 'time': datetime.timedelta(0, 23, 404403)}, {'claimed': 0.6453333333333333, 'speed': 'fast', 'time': datetime.timedelta(0, 25, 592150)}, {'claimed': 13.530666666666667, 'speed': 'slow', 'time': datetime.timedelta(0, 28, 753307)}, {'claimed': 0.7253333333333334, 'speed': 'fast', 'time': datetime.timedelta(0, 30, 684011)}, {'claimed': 0.192, 'speed': 'fast', 'time': datetime.timedelta(0, 32, 345738)}, {'claimed': 1.2906666666666666, 'speed': 'fast', 'time': datetime.timedelta(0, 34, 676201)}, {'claimed': 24.528, 'speed': 'slow', 'time': datetime.timedelta(0, 39, 406208)}]
        #data = [{'claimed': 0.21333333333333335, 'speed': 'fast', 'time': datetime.timedelta(0, 0, 873499)}, {'claimed': 0.4, 'speed': 'fast', 'time': datetime.timedelta(0, 2, 281331)}, {'claimed': 1.3226666666666667, 'speed': 'fast', 'time': datetime.timedelta(0, 4, 116499)}, {'claimed': 3.008, 'speed': 'fast', 'time': datetime.timedelta(0, 6, 930709)}, {'claimed': 0.896, 'speed': 'fast', 'time': datetime.timedelta(0, 8, 921856)}, {'claimed': 0.608, 'speed': 'fast', 'time': datetime.timedelta(0, 9, 936559)}, {'claimed': 51.19466666666667, 'speed': 'fast', 'time': datetime.timedelta(0, 17, 55576)}, {'claimed': 15.829333333333333, 'speed': 'fast', 'time': datetime.timedelta(0, 20, 666332)}, {'claimed': 3.8026666666666666, 'speed': 'fast', 'time': datetime.timedelta(0, 24, 745785)}]

        g.set_line_style(3)
        g.translate(0.5, 0.5)

        g.translate(10, 50)
        g.save_context()
        self.time_volume(g, data)
        g.restore_context()

        g.translate(0, 150)
        g.save_context()
        self.just_volume(g, data)
        g.restore_context()

        g.translate(0, 100)
        g.save_context()
        self.duration_vs_volume(g, data)
        g.restore_context()


class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_default_size(600, 600)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()


if __name__ == '__main__':
    window = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
