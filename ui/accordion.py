# - coding: utf-8 -

# Copyright (c) 2011-2012 Media Modifications, Ltd.
# Dual licensed under the MIT or GPL Version 2 licenses.

from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import GObject as gobject

from ui import VBox, Button, ScrollArea

from lib.pytweener import Easing

class Accordion(VBox):
    """another way to hide content"""

    def __init__(self, pages = [], spacing = 0, animation_duration = None,
                 easing_function = Easing.Quad.ease_out, **kwargs):
        VBox.__init__(self, spacing=spacing, **kwargs)

        #: currently selected page
        self.current_page = None

        self.reclick_to_close = True

        #: duration of the sliding animation. Defaults to scene's settings.
        #: Set 0 to disable
        self.animation_duration = animation_duration

        #: Tweening method to use for the animation
        self.easing_function = easing_function

        if pages:
            self.add_child(*pages)

    def add_child(self, *pages):
        VBox.add_child(self, *pages)

        for page in pages:
            self.connect_child(page, "on-caption-mouse-down", self.on_caption_mouse_down)


    def on_caption_mouse_down(self, new_page):
        if self.reclick_to_close and new_page == self.current_page:
            new_page = None
        self.select_page(new_page)

    def select_page(self, new_page):
        """show chosen page"""
        if isinstance(new_page, int):
            new_page = self.sprites[new_page]

        if new_page == self.current_page:
            return

        # calculate available space
        taken_by_captions = 0
        for page in self.sprites:
            taken_by_captions += page._caption.height + self.spacing

        if self.current_page:
            taken_by_captions += self.current_page.spacing # this counts too!

        available = self.height - taken_by_captions - self.vertical_padding

        def round_size(container):
            container.min_height = int(container.min_height)

        def hide_container(container):
            container.visible = False

        if self.current_page:
            self.current_page.container.height = available
            self.current_page.container.opacity = 1
            self.current_page.container.scroll_vertical = False
            self.current_page.expand = False
            self.current_page.container.animate(height = 1, opacity=0,
                                                easing = self.easing_function,
                                                duration = self.animation_duration,
                                                on_complete = hide_container,
                                                on_update=round_size)


        def expand_page(container):
            container.parent.expand = True
            container.min_height = None
            container.scroll_vertical = "auto"

        if new_page is not None:
            new_page.container.height = 1
            new_page.container.opacity = 0
            new_page.container.visible = True
            new_page.container.animate(height = available, opacity=1,
                                       easing = self.easing_function,
                                       duration = self.animation_duration,
                                       on_complete = expand_page,
                                       on_update=round_size)


        self.current_page = new_page


        for page in self.sprites:
            page.expanded = page == new_page


class AccordionPageTitle(Button):
    def __init__(self, label="", pressed_offset = 0, expanded = False, **kwargs):
        Button.__init__(self, label=label, pressed_offset = pressed_offset, **kwargs)
        self.expanded = expanded

    def do_render(self):
        state = self.state

        if self.expanded:
            state = "current"

        colors = {
            'normal': ("#eee", "#999"),
            'highlight': ("#fff", "#999"),
            'current': ("#fafafa", "#aaa"),
        }

        color = colors.get(state, colors['normal'])

        self.graphics.set_line_style(1)

        self.graphics.fill_area(0, 0, self.width, self.height, color[0])

        self.graphics.move_to(0, self.height - 0.5)
        self.graphics.line_to(self.width,self.height -  0.5)
        self.graphics.stroke(color[1])


class AccordionPage(VBox):
    __gsignals__ = {
        "on-caption-mouse-down": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }

    caption_class = AccordionPageTitle

    def __init__(self, label = "", contents = [], expand = False, spacing = 0, expanded = False, **kwargs):
        VBox.__init__(self, expand=expand, spacing=spacing, **kwargs)
        self.expanded = expanded
        self._caption = self.caption_class(label, x_align=0, expanded = self.expanded, expand=False)
        self.connect_child(self._caption, "on-click", self.on_caption_mouse_down)

        self.container = ScrollArea(scroll_vertical=False, scroll_horizontal=False, visible=False, border=0)
        self.add_child(self._caption, self.container)
        self.add_child(*contents)

    def add_child(self, *sprites):
        for sprite in sprites:
            if sprite in (self._caption, self.container):
                VBox.add_child(self, sprite)
            else:
                self.container.add_child(sprite)

    def __setattr__(self, name, val):
        if name in ("label", "markup") and hasattr(self, "_caption"):
            setattr(self._caption, name, val)
        else:
            VBox.__setattr__(self, name, val)
            if name == "expanded" and hasattr(self, "_caption"):
                self._caption.expanded = val

    def on_caption_mouse_down(self, sprite, event):
        self.emit("on-caption-mouse-down")
