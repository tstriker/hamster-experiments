#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
 * Reach 2.
 * Based on code from Keith Peters (www.bit-101.com).
 *
 * The arm follows the position of the mouse by
 * calculating the angles with atan2().
 *
 Ported from processing (http://processing.org/) examples.
"""

import gtk
from lib import graphics



class Canvas(graphics.Area):
    def __init__(self):
        graphics.Area.__init__(self)
        self.segments = []

    def on_expose(self):
        states = [("Normal", gtk.STATE_NORMAL),
                  ("Active", gtk.STATE_ACTIVE),
                  ("Prelight", gtk.STATE_PRELIGHT),
                  ("Selected", gtk.STATE_SELECTED),
                  ("Insensitive", gtk.STATE_INSENSITIVE)]
        

        style = self.get_style()

        self.set_color(style.fg[gtk.STATE_NORMAL].to_string())
        self.layout.set_text("Text")
        self.context.move_to(100, 30)
        self.context.show_layout(self.layout)

        self.layout.set_text("Base")
        self.context.move_to(200, 30)
        self.context.show_layout(self.layout)

        self.layout.set_text("fg")
        self.context.move_to(300, 30)
        self.context.show_layout(self.layout)


        self.layout.set_text("bg")
        self.context.move_to(400, 30)
        self.context.show_layout(self.layout)

        for i, state in enumerate(states):
            label, state = state
            
            self.set_color(style.fg[gtk.STATE_NORMAL].to_string())
            self.layout.set_text(label)
            self.context.move_to(20, i * 50 + 60)
            self.context.show_layout(self.layout)
            
            self.context.rectangle(100, i * 50 + 50, 50, 30)
            self.set_color(style.text[state].to_string())
            self.context.fill_preserve()
            self.set_color("#999")
            self.context.stroke()

            self.context.rectangle(200, i * 50 + 50, 50, 30)
            self.set_color(style.base[state].to_string())
            self.context.fill_preserve()
            self.set_color("#999")
            self.context.stroke()
            
            self.context.rectangle(300, i * 50 + 50, 50, 30)
            self.set_color(style.fg[state].to_string())
            self.context.fill_preserve()
            self.set_color("#999")
            self.context.stroke()

            self.context.rectangle(400, i * 50 + 50, 50, 30)
            self.set_color(style.bg[state].to_string())
            self.context.fill_preserve()
            self.set_color("#999")
            self.context.stroke()




class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(500, 300)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        canvas = Canvas()

        box = gtk.VBox()
        box.pack_start(canvas)


        window.add(box)
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    gtk.main()

