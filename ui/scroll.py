# - coding: utf-8 -

# Copyright (c) 2011-2012 Media Modifications, Ltd.
# Dual licensed under the MIT or GPL Version 2 licenses.

from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import GObject as gobject

from lib import graphics
from ui import Widget, Table, Box, Viewport, Button
import math

class ScrollArea(Table):
    """Container that will display scroll bars (either horizontal or vertical or
    both) if the space occupied by child is larger than the available.
    """

    #: scroll step size in pixels
    step_size = 30

    def __init__(self, contents=None, border=1, step_size=None,
                 scroll_horizontal="auto", scroll_vertical="auto",
                 **kwargs):
        Table.__init__(self, rows=2, cols=2, padding=[border, 0, 0, border], **kwargs)

        self.viewport = Viewport(x_align=0, y_align=0)
        self.interactive, self.can_focus = True, True

        if step_size:
            self.step_size = step_siz

        #: with of the surrounding border in pixels
        self.border = border

        #: visibility of the horizontal scroll bar. True for always, False for never and "auto" for auto
        self.scroll_horizontal = scroll_horizontal

        #: visibility of the vertical scroll bar. True for always, False for never and "auto" for auto
        self.scroll_vertical = scroll_vertical

        #even if we are don't need the scrollbar, do we reserve space for it?
        self.reserve_space_vertical = False
        self.reserve_space_horizontal = False


        #: vertical scroll bar widget
        self.vscroll = ScrollBar()

        #: horizontal scroll bar widget
        self.hscroll = ScrollBar(horizontal = True)

        self.attach(self.viewport, 0, 1, 0, 1)
        self.attach(self.vscroll, 1, 2, 0, 1)
        self.attach(self.hscroll, 0, 1, 1, 2)


        if contents:
            if isinstance(contents, graphics.Sprite):
                contents = [contents]

            for sprite in contents:
                self.add_child(sprite)

        self.connect("on-mouse-scroll", self.__on_mouse_scroll)
        for bar in (self.vscroll, self.hscroll):
            self.connect_child(bar, "on-scroll", self.on_scroll)
            self.connect_child(bar, "on-scroll-step", self.on_scroll_step)
            self.connect_child(bar, "on-scroll-page", self.on_scroll_page)


    def __setattr__(self, name, val):
        Table.__setattr__(self, name, val)
        if name in ("scroll_horizontal", "scroll_vertical"):
            self.queue_resize()

    def add_child(self, *sprites):
        for sprite in sprites:
            if sprite in (self.viewport, self.vscroll, self.hscroll):
                Table.add_child(self, sprite)
            else:
                self.viewport.add_child(*sprites)

    def get_min_size(self):
        return self.min_width or 0, self.min_height or 0

    def resize_children(self):
        # give viewport all our space
        w, h = self.viewport.alloc_w, self.viewport.alloc_w
        self.viewport.alloc_w = self.width - self.horizontal_padding
        self.viewport.alloc_h = self.height - self.vertical_padding

        # then check if it fits
        area_w, area_h = self.viewport.get_container_size()
        hvis = self.scroll_horizontal is True or (self.scroll_horizontal == "auto" and self.width < area_w)
        if hvis:
            if self.reserve_space_horizontal:
                self.hscroll.opacity = 1
            else:
                self.hscroll.visible = True
        else:
            if self.reserve_space_horizontal:
                self.hscroll.opacity = 0
            else:
                self.hscroll.visible = False
        vvis = self.scroll_vertical is True or (self.scroll_vertical == "auto" and self.height < area_h)
        if vvis:
            if self.reserve_space_vertical:
                self.vscroll.opacity = 1
            else:
                self.vscroll.visible = True
        else:
            if self.reserve_space_vertical:
                self.vscroll.opacity = 0
            else:
                self.vscroll.visible = False

        Table.resize_children(self)


        if self.viewport.child:
            self.scroll_x(self.viewport.child.x)
            self.scroll_y(self.viewport.child.y)


    def _scroll_y(self, y):
        # these are split into two to avoid echoes
        # check if we have anything to scroll
        area_h = self.viewport.get_container_size()[1]
        viewport_h = self.viewport.height

        if y < 0:
            y = max(y, viewport_h - area_h)
        y = min(y, 0)
        self.viewport.child.y = y

    def scroll_y(self, y):
        """scroll to y position"""
        self._scroll_y(y)
        self._update_sliders()

    def _scroll_x(self, x):
        area_w = self.viewport.get_container_size()[0]
        viewport_w = self.viewport.width
        if not viewport_w:
            return

        # when window grows pull in the viewport if it's out of the bounds
        if x < 0:
            x = max(x, viewport_w - area_w)
        x = min(x, 0)

        self.viewport.child.x = x

    def scroll_x(self, x):
        """scroll to x position"""
        self._scroll_x(x)
        self._update_sliders()


    def _update_sliders(self):
        area_w, area_h = self.viewport.get_container_size()
        area_w = area_w or 1 # avoid division by zero
        area_h = area_h or 1

        if self.vscroll.visible:
            v_aspect = min(float(self.viewport.height) / area_h, 1)
            self.vscroll.size = min(float(self.viewport.height) / area_h, 1)

            if v_aspect == 1:
                self.vscroll.offset = 0
            else:
                self.vscroll.offset = -1 * self.viewport.child.y / (area_h * (1 - v_aspect))

        if self.hscroll.visible:
            h_aspect = min(float(self.viewport.width) / area_w, 1)
            self.hscroll.size = min(float(self.viewport.width) / area_w, 1)
            if h_aspect == 1:
                self.hscroll.offset = 0
            else:
                self.hscroll.offset = -1 * self.viewport.child.x / (area_w * (1 - h_aspect))


    """events"""
    def __on_mouse_scroll(self, sprite, event):
        direction  = 1 if event.direction == gdk.ScrollDirection.DOWN else -1
        self.scroll_y(self.viewport.child.y - self.step_size * direction)

    def on_scroll(self, bar, offset):
        area_w, area_h = self.viewport.get_container_size()
        viewport_w, viewport_h = self.viewport.width, self.viewport.height

        if bar == self.vscroll:
            aspect = float(area_h - viewport_h) / area_h
            self._scroll_y(-1 * (area_h * aspect) * offset)
        else:
            aspect = float(area_w - viewport_w) / area_w
            self._scroll_x(-1 * (area_w * aspect) * offset)

    def on_scroll_step(self, bar, direction):
        if bar == self.vscroll:
            self.scroll_y(self.viewport.child.y - self.step_size * direction)
        else:
            self.scroll_x(self.viewport.child.x - self.step_size * direction)

    def on_scroll_page(self, bar, direction):
        if bar == self.vscroll:
            self.scroll_y(self.viewport.child.y - (self.viewport.height + self.step_size) * direction)
        else:
            self.scroll_x(self.viewport.child.y - (self.viewport.width + self.step_size) * direction)


    def do_render(self):
        if self.border:
            self.graphics.rectangle(0.5, 0.5, self.width, self.height)
            self.graphics.set_line_style(width=self.border)
            stroke_color = "#333" if self.focused else "#999"
            self.graphics.fill_stroke("#fff", stroke_color)
        else:
            self.graphics.rectangle(0, 0, self.width, self.height)
            self.graphics.fill("#fff")



class ScrollBar(Box):
    """A scroll bar.

    **Signals**:

    **on-scroll** *(sprite, current_normalized_position)*
    - fired after scrolling.
    """
    __gsignals__ = {
        "on-scroll": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        "on-scroll-step": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        "on-scroll-page": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
    }

    #: thickness of the bar in pixels
    thickness = 20

    def __init__(self, horizontal = False, thickness = None, size = 0, offset = 0, **kwargs):
        Box.__init__(self, **kwargs)
        self.interactive, self.cursor = True, False

        self.spacing = 0

        self.thickness = thickness if thickness else self.thickness

        #: whether the scroll bar is vertical or horizontal
        self.orient_horizontal = horizontal

        #: width of the bar in pixels
        self.size = size

        #: scroll position in range 0..1
        self.offset = offset

        if horizontal:
            self.expand_vert = False
            self.min_height = thickness
        else:
            self.expand = False
            self.min_width = thickness

        #: slider container
        self.slider_zone = Widget()

        #: slider widget
        self.slider = ScrollBarSlider()
        self.slider_zone.add_child(self.slider)

        #: the scroll up button
        self.up = ScrollBarButton(direction="left" if self.orient_horizontal else "up")

        #: the scroll down button
        self.down = ScrollBarButton(direction="right" if self.orient_horizontal else "down")

        self.add_child(self.up, self.slider_zone, self.down)

        self._timeout = None

        for button in (self.up, self.down):
            self.connect_child(button, "on-mouse-down", self.on_scrollbutton_pressed)
            self.connect_child(button, "on-mouse-up", self.on_scrollbutton_released)
            self.connect_child(button, "on-mouse-out", self.on_scrollbutton_released)

        self.connect_child(self.slider, "on-drag", self.on_slider_drag)
        self.connect("on-click", self.on_click)


    def get_min_size(self):
        return self.thickness, self.thickness

    def resize_children(self):
        Box.resize_children(self)
        self._size_slider()


    def _size_slider(self):
        if self.orient_horizontal:
            self.slider.alloc_h = self.slider_zone.alloc_h
            size = max(self.slider_zone.width * self.size, self.slider_zone.height)
            if self.slider_zone.width < self.slider_zone.height:
                size = self.slider_zone.width
            self.slider.width = round(size)
        else:
            self.slider.alloc_w = self.slider_zone.alloc_w
            size = max(self.slider_zone.height * self.size, self.slider_zone.width)
            if self.slider_zone.height < self.slider_zone.width:
                size = self.slider_zone.height
            self.slider.height = round(size)
        self._position_slider()


    def __setattr__(self, name, val):
        if self.__dict__.get(name, "hamster_graphics_no_value_really") == val:
            return

        Box.__setattr__(self, name, val)

        if name == "orient_horizontal" and hasattr(self, "up"):
            self.up.direction="left" if val else "up"
            self.down.direction="right" if val else "down"
        elif name == "size" and hasattr(self, "slider"):
            self._size_slider()
        elif name == "offset" and hasattr(self, "slider_zone"):
            self._position_slider()

    def _position_slider(self):
        if self.orient_horizontal:
            size = max(self.slider_zone.width - self.slider.width, 1)
            self.slider.x = size * self.offset
        else:
            size = max(self.slider_zone.height - self.slider.height, 1)
            self.slider.y = size * self.offset


    def on_slider_drag(self, slider, event):
        if self.orient_horizontal:
            size = max(self.slider_zone.width - self.slider.width, 0)
            self.slider.y = 0
            self.slider.x = int(max(min(self.slider.x, size), 0))
            self.__dict__['offset'] = self.slider.x / size if size > 0 else 0
        else:
            size = max(self.slider_zone.height - self.slider.height, 0)
            self.slider.x = 0
            self.slider.y = int(max(min(self.slider.y, size), 0))
            self.__dict__['offset'] = self.slider.y / size if size > 0 else 0


        self.emit("on-scroll", self.offset)


    def on_scrollbutton_pressed(self, button, event = None):
        if self._timeout: return  #something's going on already

        # scroll right away and set a timeout to come again after 50 milisecs
        self._emit_scroll(button)
        self._timeout = gobject.timeout_add(100, self._emit_scroll, button)

    def on_scrollbutton_released(self, button, event = None):
        if self._timeout:
            gobject.source_remove(self._timeout)
            self._timeout = None

    def _emit_scroll(self, button):
        direction = -1 if button == self.up else 1
        self.emit("on-scroll-step", direction)
        return True

    def on_click(self, sprite, event):
        direction = -1 if event.y < self.slider.y else 1
        self.emit("on-scroll-page", direction)


    def do_render(self):
        self.graphics.rectangle(0, 0, self.width, self.height)
        if self.enabled:
            self.graphics.fill("#D6D4D2")
        else:
            self.graphics.fill("#eee")


class ScrollBarSlider(Button):
    def __init__(self, padding = 0, **kwargs):
        Button.__init__(self, padding = padding, **kwargs)
        self.draggable = True
        self.expand = False
        self.connect("on-drag", self.on_drag)

    def on_drag(self, sprite, event):
        if self.enabled == False:
            self.x, self.y = self.drag_x, self.drag_y
            return

    def do_render(self):
        if self.parent.parent.orient_horizontal:
            self.graphics.rectangle(0.5, 1.5, self.width - 1, self.height - 3, 2)
        else:
            self.graphics.rectangle(1.5, 0.5, self.width - 3, self.height - 1, 2)

        self.graphics.fill_stroke("#fff", "#a8aca8")



class ScrollBarButton(Button):
    def __init__(self, padding = 0, direction = "up", **kwargs):
        Button.__init__(self, padding = padding, **kwargs)
        self.expand = False

        #: button direction - one of "up", "down", "left", "right"
        self.direction = direction

    def get_min_size(self):
        # require a square
        dimension = self.alloc_w if self.direction in ("up", "down") else self.alloc_h
        return (dimension, dimension)


    def do_render(self):
        self.graphics.set_line_style(1)

        self.graphics.rectangle(1.5, 1.5, self.width - 3, self.height - 3, 2)
        self.graphics.fill_stroke("#fff", "#a8aca8")


        self.graphics.save_context()
        self.graphics.translate(7.5, 9.5)

        if self.direction == "left":
            self.graphics.rotate(-math.pi / 2)
            self.graphics.translate(-4, 0)
        elif self.direction == "right":
            self.graphics.rotate(math.pi / 2)
            self.graphics.translate(-1, -4)
        elif self.direction == "down":
            self.graphics.rotate(math.pi)
            self.graphics.translate(-6, -3)


        self.graphics.move_to(0, 3)
        self.graphics.line_to(3, 0)
        self.graphics.line_to(6, 3)

        if self.enabled:
            self.graphics.stroke("#333")
        else:
            self.graphics.stroke("#aaa")

        self.graphics.restore_context()
