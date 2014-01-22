# - coding: utf-8 -

# Copyright (c) 2011-2012 Media Modifications, Ltd.
# Dual licensed under the MIT or GPL Version 2 licenses.

import math

import cairo
from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import GObject as gobject

from lib import graphics
from ui import Label, Container, Table, Box, HBox, Viewport, ToggleButton, Group, ScrollButton, Bin

class Notebook(Box):
    """Container that allows grouping children in tab pages"""

    __gsignals__ = {
        "on-tab-change": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
    }

    #: class to use for constructing the overflow buttons that appear on overflow
    scroll_buttons_class = ScrollButton

    #: class for the wrapping container
    tabbox_class = HBox

    #: class for the pages container
    pages_container_class = Container


    def __init__(self, labels = None, tab_position="top", tab_spacing = 0,
                 scroll_position = None, show_scroll = "auto", scroll_selects_tab = True, **kwargs):
        Box.__init__(self, horizontal=False, spacing=0, **kwargs)

        #: list of tabs in the order of appearance
        self.tabs = []

        #: list of pages in the order of appearance
        self.pages = []

        #: container of the pages
        self.pages_container = self.pages_container_class(padding=1)

        #: container of tabs. useful if you want to adjust padding/placement
        self.tabs_container = Group(fill=False, spacing=tab_spacing)
        self.tabs_container.on_mouse_over = lambda button: False  # ignore select-on-drag

        # viewport so that tabs don't go out of their area
        self._tabs_viewport = Viewport()
        self._tabs_viewport.get_min_size = self._tabs_viewport_get_min_size
        self._tabs_viewport.resize_children = self._tabs_viewport_resize_children
        self._tabs_viewport.add_child(self.tabs_container)

        #: wether scroll buttons should select next/previos tab or show the
        #: next/previos tab out of the view
        self.scroll_selects_tab = scroll_selects_tab

        #: container for custom content before tabs
        self.before_tabs = HBox(expand=False)

        #: container for custom content after tabs
        self.after_tabs = HBox(expand=False)

        #: button to scroll tabs back
        self.tabs_back = self.scroll_buttons_class("left",
                                                   expand=False,
                                                   visible=False,
                                                   enabled=False,
                                                   repeat_down_delay = 150)
        self.tabs_back.connect("on-mouse-down", self.on_back_press)

        #: button to scroll tabs forward
        self.tabs_forward = self.scroll_buttons_class("right",
                                                      expand=False,
                                                      visible=False,
                                                      enabled=False,
                                                      repeat_down_delay = 150)
        self.tabs_forward.connect("on-mouse-down", self.on_forward_press)


        #: the wrapping container that holds also the scroll buttons and everyting
        self.tabbox = self.tabbox_class(expand = False, expand_vert = False)
        self.tabbox.get_min_size = self.tabbox_get_min_size
        self.tabbox.get_height_for_width_size = self.tabbox_get_height_for_width_size


        self.tabbox.add_child(self.before_tabs, self.tabs_back,
                              self._tabs_viewport,
                              self.tabs_forward, self.after_tabs)

        #: current page
        self.current_page = 0

        #: tab position: top, right, bottom, left and combinations: "top-right", "left-bottom", etc.
        self.tab_position = tab_position


        for label in labels or []:
            self.add_page(label)

        #: where to place the scroll buttons on tab overflow. one of "start"
        #: (both at the start), "end" (both at the end) or "around" (on left
        #: and right of the tabs)
        self.scroll_position = scroll_position

        #: determines when to show scroll buttons. True for always, False for
        #: never, "auto" for auto appearing and disappearing, and
        #: "auto_invisible" for going transparent instead of disappearing
        #: (the latter avoids tab toggle)
        self.show_scroll = show_scroll



    def __setattr__(self, name, val):
        if name == "tab_spacing":
            self.tabs_container.spacing = val
        else:
            if name == "current_page":
                val = self.find_page(val)

            if self.__dict__.get(name, "hamster_graphics_no_value_really") == val:
                return
            Box.__setattr__(self, name, val)

            if name == "tab_position" and hasattr(self, "tabs_container"):
                self.tabs_container.x = 0
                self._position_contents()

            elif name == "scroll_position":
                # reorder sprites based on scroll position
                if val == "start":
                    sprites = [self.before_tabs, self.tabs_back, self.tabs_forward, self._tabs_viewport, self.after_tabs]
                elif val == "end":
                    sprites = [self.before_tabs, self._tabs_viewport, self.tabs_back, self.tabs_forward, self.after_tabs]
                else:
                    sprites = [self.before_tabs, self.tabs_back, self._tabs_viewport, self.tabs_forward, self.after_tabs]
                self.tabbox.sprites = sprites
            elif name == "current_page":
                self._select_current_page()


    def add_page(self, tab, contents = None, index = None):
        """inserts a new page with the given label
        will perform insert if index is specified. otherwise will append the
        new tab to the end.
        tab can be either a string or a widget. if it is a string, a
        ui.NootebookTab will be created.

        Returns: added page and tab
        """
        if isinstance(tab, basestring):
            tab = NotebookTab(tab)

        tab.attachment = "bottom" if self.tab_position.startswith("bottom") else "top"
        self.tabs_container.connect_child(tab, "on-mouse-down", self.on_tab_down)

        page = Container(contents, visible=False)
        page.tab = tab
        self.pages_container.connect_child(page, "on-render", self.on_page_render)

        if index is None:
            self.tabs.append(tab)
            self.pages.append(page)
            self.tabs_container.add_child(tab)
            self.pages_container.add_child(page)
        else:
            self.tabs.insert(index, tab)
            self.pages.insert(index, page)
            self.tabs_container.insert(index, tab)
            self.pages_container.insert(index, tab)


        self.current_page = self.current_page or page
        self._position_contents()

        if self.get_scene():
            self.tabs_container.queue_resize()
            self.tabbox.resize_children()

        return page, tab


    def remove_page(self, page):
        """remove given page. can also pass in the page index"""
        page = self.find_page(page)
        if not page:
            return

        idx = self.pages.index(page)

        self.pages_container.remove_child(page)
        del self.pages[idx]

        self.tabs_container.remove_child(self.tabs[idx])
        del self.tabs[idx]

        if page == self.current_page:
            self.current_page = idx

        self.tabs_container.resize_children()
        self._position_contents()


    def find_page(self, page):
        """find page by index, tab label or tab object"""
        if not self.pages:
            return None

        if page in self.pages:
            return page
        elif isinstance(page, int):
            page = min(len(self.pages)-1, max(page, 0))
            return self.pages[page]
        elif isinstance(page, basestring) or isinstance(page, NotebookTab):
            for i, tab in enumerate(self.tabs):
                if tab == page or tab.label == page:
                    found_page = self.pages[i]
                    return found_page
        return None

    def _select_current_page(self):
        self.emit("on-tab-change", self.current_page)

        if not self.current_page:
            return

        self.tabs[self.pages.index(self.current_page)].toggle()
        for page in self.pages:
            page.visible = page == self.current_page

        self.current_page.grab_focus()


    def scroll_to_tab(self, tab):
        """scroll the tab list so that the specified tab is visible
        you can pass in the tab object, index or label"""
        if isinstance(tab, int):
            tab = self.tabs[tab]

        if isinstance(tab, basestring):
            for target_tab in self.tabs:
                if target_tab.label == tab:
                    tab = target_tab
                    break

        if self.tabs_container.x + tab.x < 0:
            self.tabs_container.x = -tab.x
        elif self.tabs_container.x + tab.x + tab.width > self._tabs_viewport.width:
            self.tabs_container.x = -(tab.x + tab.width - self._tabs_viewport.width) - 1
        self._position_tabs()


    """resizing and positioning"""
    def resize_children(self):
        Box.resize_children(self)

        pos = self.tab_position
        horizontal = pos.startswith("right") or pos.startswith("left")
        if horizontal:
            self.tabbox.alloc_w, self.tabbox.alloc_h = self.tabbox.alloc_h, self.tabbox.alloc_w

        if pos.startswith("right"):
            self.tabbox.x += self.tabbox.height
        elif pos.startswith("left"):
            self.tabbox.y += self.tabbox.width


        # show/hide thes croll buttons
        # doing it here to avoid recursion as changing visibility calls parent resize
        self.tabs_back.visible = self.tabs_forward.visible = self.show_scroll in (True, "auto_invisible")
        self.tabbox.resize_children()
        self.tabs_container.resize_children()


        if self.show_scroll == "auto_invisible":
            self.tabs_back.visible = self.tabs_forward.visible = True
            if self.tabs_container.width < self._tabs_viewport.width:
                self.tabs_back.opacity = self.tabs_forward.opacity = 0
            else:
                self.tabs_back.opacity = self.tabs_forward.opacity = 1

        else:
            self.tabs_back.opacity = self.tabs_forward.opacity = 1
            self.tabs_back.visible = self.tabs_forward.visible = self.show_scroll is True or \
                                                                (self.show_scroll == "auto" and \
                                                                 self.tabs_container.width > self._tabs_viewport.width)

        self.tabbox.resize_children()
        self._position_tabs()



    def tabbox_get_min_size(self):
        w, h = HBox.get_min_size(self.tabbox)
        return h, h

    def tabbox_get_height_for_width_size(self):
        w, h = HBox.get_min_size(self.tabbox)

        if self.tab_position.startswith("right") or self.tab_position.startswith("left"):
            w, h = h, w

        return w, h

    def _tabs_viewport_get_min_size(self):
        # viewport has no demands on size, so we ask the tabs container
        # when positioned on top, tell that we need at least the height
        # when on the side tell that we need at least the width
        w, h = self.tabs_container.get_min_size()
        return 50, h


    def _tabs_viewport_resize_children(self):
        # allow x_align to take effect only if tabs fit.
        x = max(self.tabs_container.x, self._tabs_viewport.width - self.tabs_container.width - 1)

        Bin.resize_children(self._tabs_viewport)

        if self.tabs_container.width > self._tabs_viewport.width:
            self.tabs_container.x = x

        self._position_tabs()


    """utilities"""
    def _position_tabs(self):
        if self.scroll_selects_tab and self.current_page:
            tab = self.current_page.tab
            if self.tabs_container.x + tab.x + tab.width > self._tabs_viewport.width:
                self.tabs_container.x = -(tab.x + tab.width - self._tabs_viewport.width)
            elif self.tabs_container.x + tab.x < 0:
                self.tabs_container.x = -tab.x


        # find first good tab if we all don't fit
        if self.tabs_container.width > self._tabs_viewport.width:
            for tab in self.tabs:
                if tab.x + self.tabs_container.x >= 0:
                    self.tabs_container.x = -tab.x
                    break

        # update opacity so we are not showing partial tabs
        for tab in self.tabs:
            if self.tabs_container.x + tab.x < 0 or self.tabs_container.x + tab.x + tab.width > self._tabs_viewport.width:
                tab.opacity = 0
            else:
                tab.opacity = 1


        # set scroll buttons clickable
        if self.scroll_selects_tab:
            self.tabs_back.enabled = self.current_page and self.pages.index(self.current_page) > 0
            self.tabs_forward.enabled = self.current_page and self.pages.index(self.current_page) < len(self.pages) - 1
        else:
            self.tabs_back.enabled = self.tabs_container.x  < -self.tabs_container.padding_left
            self.tabs_forward.enabled = self.tabs_container.x + self.tabs_container.width > self._tabs_viewport.width


    def _position_contents(self):
        attachment, alignment = self.tab_position or "top", "left"
        if "-" in self.tab_position:
            attachment, alignment = self.tab_position.split("-")

        self.orient_horizontal = attachment in ("right", "left")

        if alignment == "center":
            self.tabs_container.x_align = 0.5
        elif alignment in ("right", "bottom"):
            self.tabs_container.x_align = 1
        else:
            self.tabs_container.x_align = 0

        # on left side the rotation is upside down
        if attachment == "left":
            self.tabs_container.x_align = 1 - self.tabs_container.x_align

        if attachment == "bottom":
            self.tabs_container.y_align = 0
        else:
            self.tabs_container.y_align = 1

        for tab in self.tabs:
            tab.attachment = attachment

        self.clear()
        if attachment == "right":
            self.add_child(self.pages_container, self.tabbox)
            self.tabbox.rotation = math.pi / 2
        elif attachment == "left":
            self.add_child(self.tabbox, self.pages_container)
            self.tabbox.rotation = -math.pi / 2
        elif attachment == "bottom":
            self.add_child(self.pages_container, self.tabbox)
            self.tabbox.rotation = 0
        else: # defaults to top
            self.add_child(self.tabbox, self.pages_container)
            self.tabbox.rotation = 0


        for tab in self.tabs:
            tab.pivot_x = tab.width / 2
            tab.pivot_y = tab.height / 2

            tab.container.pivot_x = tab.container.width / 2
            tab.container.pivot_y = tab.container.height / 2
            if attachment == "bottom":
                tab.rotation = math.pi
                tab.container.rotation = math.pi
            else:
                tab.rotation = 0
                tab.container.rotation = 0


            if tab.force_vertical_image and tab.image:
                tab.image.pivot_x = tab.image.width / 2
                tab.image.pivot_y = tab.image.height / 2

                if attachment == "right":
                    tab.image.rotation = -math.pi / 2
                elif attachment == "left":
                    tab.image.rotation = math.pi / 2
                else:
                    tab.image.rotation = 0

        self.queue_resize()


    """mouse events"""
    def on_back_press(self, button, event):
        if self.scroll_selects_tab:
            if self.pages.index(self.current_page) > 0:
                self.current_page = self.pages.index(self.current_page) - 1
        else:
            # find the first elem before 0:
            for tab in reversed(self.tabs):
                if self.tabs_container.x + tab.x < 0:
                    self.tabs_container.x = -tab.x
                    break
        self._position_tabs()


    def on_forward_press(self, button, event):
        if self.scroll_selects_tab:
            if self.pages.index(self.current_page) < len(self.pages):
                self.current_page = self.pages.index(self.current_page) + 1
        else:
            if self.tabs_container.x + self.tabs_container.width > self._tabs_viewport.width:
                # find the first which doesn't fit:
                found = None
                for tab in self.tabs:
                    if self.tabs_container.x + tab.x + tab.width > self._tabs_viewport.width:
                        found = True
                        break

                if found:
                    self.tabs_container.x = -(tab.x + tab.width - self._tabs_viewport.width) - 1
            else:
                self.tabs_container.x = -(self.tabs_container.width - self._tabs_viewport.width)
        self._position_tabs()

    def on_tab_down(self, tab, event):
        self.current_page = tab


    """rendering"""
    def on_page_render(self, page):
        page.graphics.rectangle(0, 0, page.width, page.height)
        page.graphics.clip()

    def do_render(self):
        self.graphics.set_line_style(width = 1)

        x, y, w, h = (self.pages_container.x + 0.5,
                      self.pages_container.y + 0.5,
                      self.pages_container.width-1,
                      self.pages_container.height-1)

        self.graphics.rectangle(x, y, w, h)
        self.graphics.fill_stroke("#fafafa", "#999")


class NotebookTab(ToggleButton):
    padding = 5
    def __init__(self, label="", attachment = "top", pressed_offset = 0, **kwargs):
        ToggleButton.__init__(self, label=label, pressed_offset = pressed_offset, **kwargs)
        self.attachment = attachment

        self.interactive = True

        self.force_vertical_image = True

    def do_render(self):
        x, y, x2, y2 = 0.5, 0.5, self.width, self.height

        self._rounded_line([(x, y2), (x, y), (x2, y), (x2, y2)], 4)

        if self.toggled:
            self.graphics.fill_stroke("#fafafa", "#999")
        elif self.state == "highlight":
            self.graphics.fill_stroke("#ddd", "#999")
        else:
            self.graphics.fill_stroke("#ccc", "#999")
