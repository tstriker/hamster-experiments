#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>
"""
    Draws initial canvas to play flood filling on (based on truchet.py).
    Then on mouse click performs queue-based flood fill.
    We are combining cairo with gdk.Image here to operate on pixel level (yay!)
"""

import gtk
from lib import graphics
import math
import random
import datetime as dt
import collections


class Canvas(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.tile_size = 60
        self.image = None

        self.connect("on-click", self.on_mouse_click)
        self.connect("on-enter-frame", self.on_enter_frame)

        # don't care about anything but spraycan
        self.connect("on-mouse-move", lambda *args: self.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.SPRAYCAN)))

    def on_mouse_click(self, area, event, target):
        x, y = event.x, event.y

        colormap = self.image.get_colormap()
        color1 = colormap.alloc_color(self.colors.gdk("#ff0000"))

        self.flood_fill(self.image, x, y, color1.pixel)
        self.redraw()


    def stroke_tile(self, context, x, y, size, orient):
        # draws a tile, there are just two orientations
        arc_radius = size / 2
        x2, y2 = x + size, y + size

        # i got lost here with all the Pi's
        if orient == 1:
            context.move_to(x + arc_radius, y)
            context.arc(x, y, arc_radius, 0, math.pi / 2);

            context.move_to(x2 - arc_radius, y2)
            context.arc(x2, y2, arc_radius, math.pi, math.pi + math.pi / 2);
        elif orient == 2:
            context.move_to(x2, y + arc_radius)
            context.arc(x2, y, arc_radius, math.pi - math.pi / 2, math.pi);

            context.move_to(x, y2 - arc_radius)
            context.arc(x, y2, arc_radius, math.pi + math.pi / 2, 0);

    def on_enter_frame(self, scene, context):
        """here happens all the drawing"""
        if not self.height: return

        if not self.image:
            self.two_tile_random(context)
            self.image = self.window.get_image(0, 0, self.width, self.height)

        self.window.draw_image(self.get_style().black_gc, self.image, 0, 0, 0, 0, -1, -1)



    def two_tile_random(self, context):
        """stroke area with non-filed truchet (since non filed, all match and
           there are just two types"""
        context.set_source_rgb(0,0,0)
        context.set_line_width(1)

        for y in range(0, self.height, self.tile_size):
            for x in range(0, self.width, self.tile_size):
                self.stroke_tile(context, x, y, self.tile_size, random.choice([1, 2]))
        context.stroke()

    @staticmethod
    def paint_check(color1, color2):
        return color1 != color2 and abs(color1 - color2) < 3000000


    def flood_fill(self, image, x, y, new_color, old_color = None):
        """from starting point finds left and right bounds, paint them all
           and adds any point above and below the line that is in the old color
           to the queue
        """
        x, y = int(x), int(y)
        old_color = old_color or image.get_pixel(x, y)

        queue = collections.deque()
        queue.append((x, y))

        pixels, longest_queue = 0, 0
        paint_check = self.paint_check


        t = dt.datetime.now()
        while queue:
            longest_queue = max(longest_queue, len(queue))
            x, y = queue.popleft()
            if image.get_pixel(x, y) != old_color:
                continue

            west, east = x,x  #up and down

            # find bounds
            while west > 0 and paint_check(image.get_pixel(west - 1, y), new_color):
                west -= 1

            while east < self.width - 1 and paint_check(image.get_pixel(east + 1, y), new_color):
                east += 1

            for x in range(west, east):
                pixels +=1
                image.put_pixel(x, y, new_color)
                if y > 0 and paint_check(image.get_pixel(x, y - 1), new_color):
                    queue.append((x, y - 1))

                if y < self.height - 1 and paint_check(image.get_pixel(x, y + 1), new_color):
                    queue.append((x, y + 1))


        delta = dt.datetime.now() - t
        delta_ms = delta.seconds * 1000000 + delta.microseconds
        print "%d pixels in %.2f (%.2f/s). Longest queue: %d" % \
                                          (pixels,
                                           delta_ms / 1000000.0,
                                           float(pixels) / delta_ms * 1000000.0,
                                           longest_queue)


class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(500, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        canvas = Canvas()

        box = gtk.VBox()
        box.pack_start(canvas)


        window.add(box)
        window.show_all()


if __name__ == "__main__":
    example = BasicWindow()
    gtk.main()
