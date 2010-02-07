# - coding: utf-8 -

# Copyright (C) 2008-2009 Toms Bauģis <toms.baugis at gmail.com>

# This file is part of Project Hamster.

# Project Hamster is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Project Hamster is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Project Hamster.  If not, see <http://www.gnu.org/licenses/>.
import math
import time, datetime as dt
import gtk, gobject

import pango, cairo

import pytweener
from pytweener import Easing
import colorsys
from collections import deque

class Colors(object):
    aluminium = [(238, 238, 236), (211, 215, 207), (186, 189, 182),
                 (136, 138, 133), (85, 87, 83), (46, 52, 54)]
    almost_white = (250, 250, 250)

    def parse(self, color):
        assert color is not None

        #parse color into rgb values
        if isinstance(color, str) or isinstance(color, unicode):
            color = gtk.gdk.Color(color)

        if isinstance(color, gtk.gdk.Color):
            color = [color.red / 65535.0, color.green / 65535.0, color.blue / 65535.0]
        else:
            # otherwise we assume we have color components in 0..255 range
            if color[0] > 1 or color[1] > 1 or color[2] > 1:
                color = [c / 255.0 for c in color]

        return color

    def rgb(self, color):
        return [c * 255 for c in self.parse(color)]

    def gdk(self, color):
        c = self.parse(color)
        return gtk.gdk.Color(c[0] * 65535.0, c[1] * 65535.0, c[2] * 65535.0)

    def is_light(self, color):
        # tells you if color is dark or light, so you can up or down the scale for improved contrast
        return colorsys.rgb_to_hls(*self.rgb(color))[1] > 150

    def darker(self, color, step):
        # returns color darker by step (where step is in range 0..255)
        hls = colorsys.rgb_to_hls(*self.rgb(color))
        return colorsys.hls_to_rgb(hls[0], hls[1] - step, hls[2])



class Graphics(object):
    """graphics class accepts instructions, and when draw is called with
       the context, it performs them"""
    def __init__(self):
        self._instructions = deque()
        self.colors = Colors()
        self.extents = (0,0,0,0)

    def clear(self): self._instructions = deque()

    def _stroke(self, context): context.stroke()
    def stroke(self): self._add_instruction(self._stroke,)

    def _fill(self, context): context.fill()
    def fill(self): self._add_instruction(self._fill,)

    def _stroke_preserve(self, context): context.stroke_preserve()
    def stroke_preserve(self): self._add_instruction(self._stroke_preserve,)

    def _fill_preserve(self, context): context.fill_preserve()
    def fill_preserve(self): self._add_instruction(self._fill_preserve,)

    def move_to(self, x, y): self._add_instruction(lambda context, x, y: context.move_to(x, y), x, y)
    def line_to(self, x, y): self._add_instruction(lambda context, x, y: context.line_to(x, y), x, y)
    def curve_to(self, x, y, x2, y2, x3, y3):
        self._add_instruction(lambda context, x, y, x2, y2, x3, y3: context.curve_to(x, y, x2, y2, x3, y3), x, y, x2, y2, x3, y3)
    def close_path(self): self._add_instruction(lambda context: context.close_path(),)

    def set_line_style(self, width = None):
        if width is not None:
            self._add_instruction(lambda context, width: context.set_line_width(width), width)

    def set_color(self, color, a = 1):
        color = self.colors.parse(color) #parse whatever we have there into a normalized triplet
        if len(color) == 4 and a is None:
            a = color[3]
        r,g,b = color[:3]

        if a:
            self._add_instruction(lambda context, r, g, b, a: context.set_source_rgba(r,g,b,a), r, g, b, a)
        else:
            self._add_instruction(lambda context, r, g, b: context.set_source_rgb(r,g,b), r, g, b)

    def arc(self, x, y, radius, start_angle, end_angle):
        self._add_instruction(lambda context, x, y, radius, start_angle, end_angle: context.arc(x, y, radius, start_angle, end_angle),
                                              x, y, radius, start_angle, end_angle)

    def _rounded_rectangle(self, context, x, y, x2, y2, corner_radius):
        half_corner = corner_radius / 2

        context.move_to(x + corner_radius, y)
        context.line_to(x2 - corner_radius, y)
        context.curve_to(x2 - half_corner, y, x2, y + half_corner, x2, y + corner_radius)
        context.line_to(x2, y2 - corner_radius)
        context.curve_to(x2, y2 - half_corner, x2 - half_corner, y2, x2 - corner_radius,y2)
        context.line_to(x + corner_radius, y2)
        context.curve_to(x + half_corner, y2, x, y2 - half_corner, x, y2 - corner_radius)
        context.line_to(x, y + corner_radius)
        context.curve_to(x, y + half_corner, x + half_corner, y, x + corner_radius,y)

    def rectangle(self, x, y, w, h, corner_radius = 0):
        if corner_radius <=0:
            self._add_instruction(lambda context, x, y, w, h: context.rectangle(x, y, w, h), x, y, w, h)
            return

        # make sure that w + h are larger than 2 * corner_radius
        corner_radius = min(corner_radius, min(w, h) / 2)
        x2, y2 = x + w, y + h
        self._add_instruction(self._rounded_rectangle, x, y, x2, y2, corner_radius)

    def fill_area(self, x, y, w, h, color, opacity = 1):
        self.set_color(color, opacity)
        self.rectangle(x, y, w, h)
        self.fill()

    def show_text(self, text, font_desc):
        def do_layout(context, text, font_desc):
            layout = context.create_layout()
            layout.set_font_description(font_desc)
            layout.set_text(text)
            context.move_to(0, 0)
            context.show_layout(layout)
        self._add_instruction(do_layout, text, font_desc)

    def draw(self, context, with_extents = False):
        self.extents = [0,0,0,0]
        for instruction, args in self._instructions:
            if with_extents and instruction in (self._stroke, self._fill,
                                                self._stroke_preserve,
                                                self._fill_preserve):
                # before stroking get extents, for that we have to do something
                # bad to the current transformations matrix
                context.save()
                context.identity_matrix()
                matrix = context.get_matrix()
                self.extents = context.stroke_extents()
                context.restore()

            instruction(context, *args)


    def _add_instruction(self, function, *params):
        self._instructions.append((function, params))



class Sprite(gtk.Object):
    __gsignals__ = {
        "on-mouse-over": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        "on-mouse-out": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        "on-mouse-click": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        "on-drag": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
    }
    def __init__(self, interactive = True):
        gtk.Widget.__init__(self)
        self.graphics = Graphics()
        self.x, self.y = 0, 0
        self.rotation = 0
        self.pivot_x, self.pivot_y = 0, 0 # the anchor and rotation point
        self.interactive = interactive
        self.draggable = False

        self.child_sprites = []
        self.parent = None

    def _draw(self, context):
        context.save()

        if self.x or self.y:
            context.translate(self.x, self.y)

        if self.rotation:
            context.rotate(self.rotation)

        context.translate(-self.pivot_x, -self.pivot_y)
        self.graphics.draw(context, self.interactive)

        for sprite in self.child_sprites:
            sprite._draw(context)

        context.restore()

    def add_child(self, sprite):
        self.child_sprites.append(sprite)
        sprite.parent = self

    def _on_click(self, button_state):
        self.emit("on-mouse-click", button_state)

    def _on_mouse_over(self):
        # scene will call us when there is mouse
        self.emit("on-mouse-over")

    def _on_mouse_out(self):
        # scene will call us when there is mouse
        self.emit("on-mouse-out")

    def _on_drag(self, x, y):
        # scene will call us when there is mouse
        self.emit("on-drag", (x, y))


"""a few primitives"""
class Label(Sprite):
    def __init__(self, text = "", size = 10, color = None):
        Sprite.__init__(self, interactive = False)
        self.text = text
        self.color = color

        self.font_desc = pango.FontDescription(gtk.Style().font_desc.to_string())
        self.font_desc.set_size(size * pango.SCALE)
        self._draw_label()

    def _draw_label(self):
        if self.color:
            self.graphics.set_color(self.color)
        self.graphics.show_text(self.text, self.font_desc)
        self.graphics.stroke()


class Primitive(Sprite):
    def __init__(self, stroke_color = None, fill_color = None):
        Sprite.__init__(self, interactive = False)
        self.stroke_color = stroke_color
        self.fill_color = fill_color


    def _color(self):
        if self.fill_color:
            self.graphics.set_color(self.fill_color)
            if self.stroke_color:
                self.graphics.fill_preserve()
            else:
                self.graphics.fill()

        if self.stroke_color:
            self.graphics.set_color(self.stroke_color)
            self.graphics.stroke()

    def _draw_primitive(self):
        raise UnimplementedException

    def set_color(self, stroke_color = None, fill_color = None):
        if stroke_color is not None: self.stroke_color = stroke_color
        if fill_color is not None: self.fill_color = fill_color
        self.graphics.clear()
        self._draw_primitive()




class Rectangle(Primitive):
    def __init__(self, w, h, corner_radius, stroke_color = None, fill_color = None):
        Primitive.__init__(self, stroke_color, fill_color)
        self.width, self.height, self.corner_radius = w, h, corner_radius
        self._draw_primitive()

    def _draw_primitive(self):
        self.graphics.rectangle(0, 0, self.width, self.height, self.corner_radius)
        self._color()


class Polygon(Primitive):
    def __init__(self, points, stroke_color = None, fill_color = None):
        Primitive.__init__(self, stroke_color, fill_color)
        self.points = points
        self._draw_primitive()

    def _draw_primitive(self):
        if not self.points: return

        self.graphics.move_to(*self.points[0])
        for point in self.points:
            self.graphics.line_to(*point)
        self.graphics.close_path()
        self._color()

class Circle(Primitive):
    def __init__(self, radius, stroke_color = None, fill_color = None):
        Primitive.__init__(self, stroke_color, fill_color)
        self.radius = radius
        self._draw_primitive()

    def _draw_primitive(self):
        self.graphics.move_to(0,0)
        self.graphics.arc(self.radius, self.radius, self.radius, 0, math.pi * 2)
        self._color()



""" the main place where all the action is going on"""
class Scene(gtk.DrawingArea):
    __gsignals__ = {
        "expose-event": "override",
        "configure_event": "override",
        "on-enter-frame": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, )),
        "on-finish-frame": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, )),
        "on-click": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
        "on-drag": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
        "mouse-move": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        "on-mouse-up": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }

    def __init__(self, interactive = True):
        gtk.DrawingArea.__init__(self)
        if interactive:
            self.set_events(gtk.gdk.POINTER_MOTION_MASK | gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK)
            self.connect("motion_notify_event", self.__on_mouse_move)
            self.connect("button_press_event", self.__on_button_press)
            self.connect("button_release_event", self.__on_button_release)

        self.sprites = []
        self.framerate = 80
        self.width, self.height = None, None

        self.tweener = pytweener.Tweener(0.4, pytweener.Easing.Cubic.easeInOut)
        self.last_frame_time = None
        self.__drawing_queued = False

        self._mouse_sprites = set()
        self._mouse_drag = None
        self._drag_sprite = None
        self._drag_x, self._drag_y = None, None
        self._button_press_time = None # to distinguish between click and drag
        self.colors = Colors()


    def add_child(self, sprite):
        self.sprites.append(sprite)

    def clear(self):
        self.sprites = []

    def redraw_canvas(self):
        """Redraw canvas. Triggers also to do all animations"""
        if not self.__drawing_queued: #if we are moving, then there is a timeout somewhere already
            self.__drawing_queued = True
            self.last_frame_time = dt.datetime.now()
            gobject.timeout_add(1000 / self.framerate, self.__interpolate)

    """ animation bits """
    def __interpolate(self):
        if not self.window: #will wait until window comes
            return True

        time_since_last_frame = (dt.datetime.now() - self.last_frame_time).microseconds / 1000000.0
        self.tweener.update(time_since_last_frame)
        self.__drawing_queued = self.tweener.hasTweens()

        self.queue_draw() # this will trigger do_expose_event when the current events have been flushed

        self.last_frame_time = dt.datetime.now()
        return self.__drawing_queued


    def animate(self, object, params = {}, duration = None, easing = None, callback = None, instant = True):
        if duration: params["tweenTime"] = duration  # if none will fallback to tweener default
        if easing: params["tweenType"] = easing    # if none will fallback to tweener default
        if callback: params["onCompleteFunction"] = callback
        self.tweener.addTween(object, **params)

        if instant:
            self.redraw_canvas()


    """ exposure events """
    def do_configure_event(self, event):
        (self.width, self.height) = self.window.get_size()

    def do_expose_event(self, event):
        self.width, self.height = self.window.get_size()
        context = self.window.cairo_create()

        context.rectangle(event.area.x, event.area.y,
                          event.area.width, event.area.height)
        context.clip()

        alloc = self.get_allocation()  #x, y, width, height
        self.width, self.height = alloc.width, alloc.height

        self.emit("on-enter-frame", context)
        for sprite in self.sprites:
            sprite._draw(context)
        self.emit("on-finish-frame", context)


    """ mouse events """
    def all_sprites(self, sprites = None):
        """recursively flatten the tree and return all sprites"""
        sprites = sprites or self.sprites
        res = []
        for sprite in sprites:
            res.append(sprite)
            if sprite.child_sprites:
                res.extend(self.all_sprites(sprite.child_sprites))
        return res

    def __on_mouse_move(self, area, event):
        if event.is_hint:
            mouse_x, mouse_y, state = event.window.get_pointer()
        else:
            mouse_x = event.x
            mouse_y = event.y
            state = event.state

        self.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.ARROW))

        if self._drag_sprite and self._drag_sprite.draggable and gtk.gdk.BUTTON1_MASK & event.state:
            self.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.FLEUR))

            # dragging around
            drag = self._mouse_drag and (self._mouse_drag[0] - event.x) ** 2 + \
                                        (self._mouse_drag[1] - event.y) ** 2 > 5 ** 2
            if drag:
                matrix = cairo.Matrix()
                if self._drag_sprite.parent:
                    # TODO - this currently works only until second level - take all parents into account
                    matrix.rotate(self._drag_sprite.parent.rotation)
                    matrix.invert()

                if not self._drag_x:
                    x1,y1 = matrix.transform_point(self._mouse_drag[0], self._mouse_drag[1])

                    self._drag_x = self._drag_sprite.x - x1
                    self._drag_y = self._drag_sprite.y - y1

                mouse_x, mouse_y = matrix.transform_point(mouse_x, mouse_y)
                new_x = mouse_x + self._drag_x
                new_y = mouse_y + self._drag_y


                self._drag_sprite.x, self._drag_sprite.y = new_x, new_y
                self._drag_sprite._on_drag(new_x, new_y)
                self.emit("on-drag", self._drag_sprite, (new_x, new_y))
                self.redraw_canvas()

                return

        #check if we have a mouse over
        over = set()
        for sprite in self.all_sprites():
            x, y, x2, y2 = sprite.graphics.extents
            if x < mouse_x < x2 and y < mouse_y < y2:
                if sprite.draggable:
                    self.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.FLEUR))
                elif sprite.interactive:
                    self.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND2))

                over.add(sprite)

        for sprite in over - self._mouse_sprites: #new mouse overs
            sprite._on_mouse_over()

        for sprite in self._mouse_sprites - over: #gone mouse overs
            sprite._on_mouse_out()

        self._mouse_sprites = over
        self.emit("mouse-move", event)

    def __on_button_press(self, area, event):
        x = event.x
        y = event.y
        state = event.state
        self._mouse_drag = (x, y)

        over = None
        for sprite in self.all_sprites():
            if sprite.interactive:
                x, y, x2, y2 = sprite.graphics.extents
                if x < event.x < x2 and y < event.y < y2:
                    over = sprite # last one will take precedence
        self._drag_sprite = over
        self._button_press_time = dt.datetime.now()

    def __on_button_release(self, area, event):
        #if the drag is less than 5 pixles, then we have a click
        click = self._button_press_time and (dt.datetime.now() - self._button_press_time) < dt.timedelta(milliseconds = 300)
        self._button_press_time = None
        self._mouse_drag = None
        self._drag_x, self._drag_y = None, None
        self._drag_sprite = None

        if click:
            targets = []
            for sprite in self.all_sprites():
                if sprite.interactive:
                    x, y, x2, y2 = sprite.graphics.extents
                    if x < event.x < x2 and y < event.y < y2:
                        targets.append(sprite)
                        sprite._on_click(event.state)

            self.emit("on-click", event, targets)
        self.emit("on-mouse-up")


""" simple example """
class SampleScene(Scene):
    def __init__(self):
        Scene.__init__(self)

        self.rectangle = Rectangle(90, 90, 10, "#666", "#ff00ff") # one of the primitives
        self.rectangle.interactive = True           # interactive means that the sprite will get mouse events
        self.rectangle.draggable = True             # draggable enables automatic dragging, which can be handy sometimes
        self.rectangle.x, self.rectangle.y = 50, 50 #
        self.add_child(self.rectangle)

        self.label = Label("Hello world", 30, "#000")
        self.label.x, self.label.y = 10, -100 # setting y to -100 so it will fall "from the sky"

        self.add_child(self.label)


class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_title("Project Hamster Graphics Module")
        window.set_size_request(300, 300)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        self.scene = SampleScene()
        box = gtk.VBox()
        box.pack_start(self.scene)

        button = gtk.Button("Hello")
        button.connect("clicked", self.on_go_clicked)

        box.add_with_properties(button, "expand", False)

        window.add(box)
        window.show_all()

        # drop the hello on init
        self.scene.animate(self.scene.label,
                           dict(y = 120),
                           duration = 0.7,
                           easing = Easing.Bounce.easeOut)


    def on_go_clicked(self, widget):
        """ when button clicked, we just throw the scene's rectangle
            object to some other random place, using tweens for smoother animation"""
        import random

        # set x and y to random position within the drawing area
        x = round(min(random.random() * self.scene.width,
                      self.scene.width - 90))
        y = round(min(random.random() * self.scene.height,
                      self.scene.height - 90))

        # here we call the animate function with parameters we would like to change
        # the easing functions outside graphics module can be accessed via
        # graphics.Easing
        self.scene.tweener.killTweensOf(self.scene.rectangle)
        self.scene.animate(self.scene.rectangle,
                           dict(x = x, y = y),
                           duration = 0.8,
                           easing = Easing.Expo.easeOut)


if __name__ == "__main__":
   example = BasicWindow()
   gtk.main()
