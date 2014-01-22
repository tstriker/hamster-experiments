# - coding: utf-8 -

# Copyright (c) 2011-2012 Media Modifications, Ltd.
# Dual licensed under the MIT or GPL Version 2 licenses.

from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import GObject as gobject

from lib import graphics

from ui import Widget, Container, Bin, Table, Box, HBox, VBox, Fixed, Viewport, Group, TreeModel
import math
from gi.repository import Pango as pango

class _DisplayLabel(graphics.Label):
    cache_attrs = Box.cache_attrs | set(('_cached_w', '_cached_h'))

    def __init__(self, text="", **kwargs):
        graphics.Label.__init__(self, text, **kwargs)
        self._cached_w, self._cached_h = None, None
        self._cached_wh_w, self._cached_wh_h = None, None

    def __setattr__(self, name, val):
        graphics.Label.__setattr__(self, name, val)

        if name in ("text", "markup", "size", "wrap", "ellipsize", "max_width"):
            if name != "max_width":
                self._cached_w, self._cached_h = None, None
            self._cached_wh_w, self._cached_wh_h = None, None


    def get_min_size(self):
        if self._cached_w:
            return self._cached_w, self._cached_h

        text = self.markup or self.text
        escape = len(self.markup) == 0

        if self.wrap is not None or self.ellipsize is not None:
            self._cached_w = self.measure(text, escape, 1)[0]
            self._cached_h = self.measure(text, escape, -1)[1]
        else:
            self._cached_w, self._cached_h = self.measure(text, escape, -1)
        return self._cached_w, self._cached_h

    def get_weight_for_width_size(self):
        if self._cached_wh_w:
            return self._cached_wh_w, self._cached_wh_h

        text = self.markup or self.text
        escape = len(self.markup) == 0
        self._cached_wh_w, self._cached_wh_h = self.measure(text, escape, self.max_width)

        return self._cached_wh_w, self._cached_wh_h

class Label(Bin):
    """a widget that displays a limited amount of read-only text"""
    #: pango.FontDescription to use for the label
    font_desc = "Sans Serif 10"

    #: image attachment. one of top, right, bottom, left
    image_position = "left"

    #: font size
    size = None

    fill = False
    padding = 0
    x_align = 0

    def __init__(self, text = "", markup = "", spacing = 5, image = None,
                 image_position = None, size = None, font_desc = None,
                 overflow = False,
                 color = "#000", background_color = None, **kwargs):

        # TODO - am initiating table with fill = false but that yields suboptimal label placement and the 0,0 points to whatever parent gave us
        Bin.__init__(self, **kwargs)

        #: image to put next to the label
        self.image = image

        # the actual container that contains the label and/or image
        self.container = Box(spacing = spacing, fill = False,
                             x_align = self.x_align, y_align = self.y_align)

        if image_position is not None:
            self.image_position = image_position

        self.display_label = _DisplayLabel(text = text, markup = markup, color=color, size = size)
        self.display_label.x_align = 0 # the default is 0.5 which makes label align incorrectly on wrapping

        if font_desc or self.font_desc:
            self.display_label.font_desc = font_desc or self.font_desc

        self.display_label.size = size or self.size

        self.background_color = background_color

        #: either the pango `wrap <http://www.pygtk.org/pygtk2reference/pango-constants.html#pango-wrap-mode-constants>`_
        #: or `ellipsize <http://www.pygtk.org/pygtk2reference/pango-constants.html#pango-ellipsize-mode-constants>`_ constant.
        #: if set to False will refuse to become smaller
        self.overflow = overflow

        self.add_child(self.container)

        self._position_contents()
        self.connect_after("on-render", self.__on_render)

    def get_mouse_sprites(self):
        return None

    @property
    def text(self):
        """label text. This attribute and :attr:`markup` are mutually exclusive."""
        return self.display_label.text

    @property
    def markup(self):
        """pango markup to use in the label.
        This attribute and :attr:`text` are mutually exclusive."""
        return self.display_label.markup

    @property
    def color(self):
        """label color"""
        return self.display_label.color

    def __setattr__(self, name, val):
        if name in ("text", "markup", "color", "size"):
            if self.display_label.__dict__.get(name, "hamster_graphics_no_value_really") == val:
                return
            setattr(self.display_label, name, val)
        elif name in ("spacing"):
            setattr(self.container, name, val)
        else:
            if self.__dict__.get(name, "hamster_graphics_no_value_really") == val:
                return
            Bin.__setattr__(self, name, val)


        if name in ('x_align', 'y_align') and hasattr(self, "container"):
            setattr(self.container, name, val)

        elif name == "alloc_w" and hasattr(self, "display_label") and getattr(self, "overflow") is not False:
            self._update_max_width()

        elif name == "min_width" and hasattr(self, "display_label"):
            self.display_label.width = val - self.horizontal_padding

        elif name == "overflow" and hasattr(self, "display_label"):
            if val is False:
                self.display_label.wrap = None
                self.display_label.ellipsize = None
            elif isinstance(val, pango.WrapMode) and val in (pango.WrapMode.WORD, pango.WrapMode.WORD_CHAR, pango.WrapMode.CHAR):
                self.display_label.wrap = val
                self.display_label.ellipsize = None
            elif isinstance(val, pango.EllipsizeMode) and val in (pango.EllipsizeMode.START, pango.EllipsizeMode.MIDDLE, pango.EllipsizeMode.END):
                self.display_label.wrap = None
                self.display_label.ellipsize = val

            self._update_max_width()
        elif name in ("font_desc", "size"):
            setattr(self.display_label, name, val)

        if name in ("text", "markup", "image", "image_position", "overflow", "size"):
            if hasattr(self, "overflow"):
                self._position_contents()
                self.container.queue_resize()


    def _update_max_width(self):
        # updates labels max width, respecting image and spacing
        if self.overflow is False:
            self.display_label.max_width = -1
        else:
            w = (self.alloc_w or 0) - self.horizontal_padding - self.container.spacing
            if self.image and self.image_position in ("left", "right"):
                w -= self.image.width - self.container.spacing
            self.display_label.max_width = w

        self.container.queue_resize()


    def _position_contents(self):
        if self.image and (self.text or self.markup):
            self.image.expand = False
            self.container.orient_horizontal = self.image_position in ("left", "right")

            if self.image_position in ("top", "left"):
                if self.container.sprites != [self.image, self.display_label]:
                    self.container.clear()
                    self.container.add_child(self.image, self.display_label)
            else:
                if self.container.sprites != [self.display_label, self.image]:
                    self.container.clear()
                    self.container.add_child(self.display_label, self.image)
        elif self.image or (self.text or self.markup):
            sprite = self.image or self.display_label
            if self.container.sprites != [sprite]:
                self.container.clear()
                self.container.add_child(sprite)


    def __on_render(self, sprite):
        w, h = self.width, self.height
        w2, h2 = self.get_height_for_width_size()
        w, h = max(w, w2), max(h, h2)
        self.graphics.rectangle(0, 0, w, h)

        if self.background_color:
            self.graphics.fill(self.background_color)
        else:
            self.graphics.new_path()



class Spinner(Container):
    """an indeterminate progress indicator"""
    def __init__(self, active = True, **kwargs):
        Container.__init__(self, **kwargs)

        #: whether the spinner is spinning or not
        self.active = active

        self._scene = None
        self.expose_handler = None

        #: number of beams in the progress indicator
        self.edges = 11

        self.inner_radius = 6
        self.outer_radius = 13
        self.tick_thickness = 3

        #: motion speed. the higher the number the slower the redraw is performed
        self.speed = 2
        self._frame = 0

        self._spinner = graphics.Sprite(cache_as_bitmap = False)
        self.connect_child(self._spinner, "on-render", self.on_spinner_render)
        self.add_child(self._spinner)


    def get_min_size(self):
        need = max(self.min_height or 20, self.min_width or 20)
        return need, need

    def resize_children(self):
        self.outer_radius = min(self.alloc_h / 2.0, self.alloc_w / 2.0)
        self.inner_radius = self.outer_radius * 0.3
        self.tick_thickness = self.inner_radius * 0.5
        self._spinner.x, self._spinner.y = self.outer_radius / 2.0 + (self.width - self.outer_radius) * self.x_align, \
                                         self.outer_radius / 2.0 + (self.height - self.outer_radius) * self.y_align

    def on_finish_frame(self, scene, context):
        if self.active:
            if self._frame % self.speed == 0:
                self._spinner.rotation += math.pi * 2 / self.edges

            self._frame +=1
            scene.redraw()

    def on_spinner_render(self, spinner):
        spinner.graphics.save_context()
        if not self.expose_handler:
            self._scene = self.get_scene()
            self.expose_handler = self._scene.connect("on-finish-frame", self.on_finish_frame)

        spinner.graphics.rectangle(-self.outer_radius, -self.outer_radius, self.outer_radius * 2, self.outer_radius * 2)
        spinner.graphics.new_path()
        for i in range(self.edges):
            spinner.graphics.rectangle(-self.tick_thickness / 2, self.inner_radius, self.tick_thickness, self.outer_radius - self.inner_radius, 4)
            spinner.graphics.fill(graphics.Colors.darker("#fff", i * 15))
            spinner.graphics.rotate(math.pi * 2 / self.edges)

        spinner.graphics.restore_context()
