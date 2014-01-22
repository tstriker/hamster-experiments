# - coding: utf-8 -

# Copyright (c) 2011-2012 Media Modifications, Ltd.
# Dual licensed under the MIT or GPL Version 2 licenses.

import math
from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import GObject as gobject

from lib import graphics
import datetime as dt

class Widget(graphics.Sprite):
    """Base class for all widgets. You can use the width and height attributes
    to request a specific width.
    """
    __gsignals__ = {
        "on-mnemonic-activated": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
    }

    _sizing_attributes = set(("visible", "min_width", "min_height",
                              "expand", "expand_vert", "fill", "spacing",
                              "horizontal_spacing", "vertical_spacing", "x_align",
                              "y_align"))

    min_width = None  #: minimum width of the widget
    min_height = None #: minimum height of the widget

    #: Whether the child should receive extra space when the parent grows.
    expand = True

    #: whether the child should receive extra space when the parent grows
    #: vertically. Applicable to only when the widget is in a table.
    expand_vert = True

    #: Whether extra space given to the child should be allocated to the
    #: child or used as padding. Edit :attr:`x_align` and
    #: :attr:`y_align` properties to adjust alignment when fill is set to False.
    fill = True

    #: horizontal alignment within the parent. Works when :attr:`fill` is False
    x_align = 0.5

    #: vertical alignment within the parent. Works when :attr:`fill` is False
    y_align = 0.5

    #: child padding - shorthand to manipulate padding in pixels ala CSS. tuple
    #: of one to four elements. Setting this value overwrites values of
    #: :attr:`padding_top`, :attr:`padding_right`, :attr:`padding_bottom`
    #: and :attr:`padding_left`
    padding = None
    padding_top = None    #: child padding - top
    padding_right = None  #: child padding - right
    padding_bottom = None #: child padding - bottom
    padding_left = None   #: child padding - left

    #: widget margins - shorthand to manipulate margin in pixels ala CSS. tuple
    #: of one to four elements. Setting this value overwrites values of
    #: :attr:`margin_top`, :attr:`margin_right`, :attr:`margin_bottom` and
    #: :attr:`margin_left`
    margin = 0
    margin_top = 0     #: top margin
    margin_right = 0   #: right margin
    margin_bottom = 0  #: bottom margin
    margin_left = 0    #: left margin

    enabled = True #: whether the widget is enabled

    mouse_cursor = False #: Mouse cursor. see :attr:`graphics.Sprite.mouse_cursor` for values

    #: tooltip position - currently supports only "auto" and "mouse"
    #: "auto" positions the tooltip below the widget and "mouse" positions at
    #: the mouse cursor position
    tooltip_position = "auto"

    #: (x, y) offset from the calculated position of the tooltip to appear
    tooltip_offset = None


    def __init__(self, width = None, height = None, expand = None, fill = None,
                 expand_vert = None, x_align = None, y_align = None,
                 padding_top = None, padding_right = None,
                 padding_bottom = None, padding_left = None, padding = None,
                 margin_top = None, margin_right = None,
                 margin_bottom = None, margin_left = None, margin = None,
                 enabled = None, tooltip = None, **kwargs):
        graphics.Sprite.__init__(self, **kwargs)

        def set_if_not_none(name, val):
            # set values - avoid pitfalls of None vs 0/False
            if val is not None:
                setattr(self, name, val)

        set_if_not_none("min_width", width)
        set_if_not_none("min_height", height)

        self._enabled = enabled if enabled is not None else self.__class__.enabled

        set_if_not_none("fill", fill)
        set_if_not_none("expand", expand)
        set_if_not_none("expand_vert", expand_vert)
        set_if_not_none("x_align", x_align)
        set_if_not_none("y_align", y_align)

        # set padding
        # (class, subclass, instance, and constructor)
        if padding is not None or self.padding is not None:
            self.padding = padding if padding is not None else self.padding
        self.padding_top = padding_top or self.__class__.padding_top or self.padding_top or 0
        self.padding_right = padding_right or self.__class__.padding_right or self.padding_right or 0
        self.padding_bottom = padding_bottom or self.__class__.padding_bottom or self.padding_bottom or 0
        self.padding_left = padding_left or self.__class__.padding_left or self.padding_left or 0

        if margin is not None or self.margin is not None:
            self.margin = margin if margin is not None else self.margin
        self.margin_top = margin_top or self.__class__.margin_top or self.margin_top or 0
        self.margin_right = margin_right or self.__class__.margin_right or self.margin_right or 0
        self.margin_bottom = margin_bottom or self.__class__.margin_bottom or self.margin_bottom or 0
        self.margin_left = margin_left or self.__class__.margin_left or self.margin_left or 0


        #: width in pixels that have been allocated to the widget by parent
        self.alloc_w = width if width is not None else self.min_width

        #: height in pixels that have been allocated to the widget by parent
        self.alloc_h = height if height is not None else self.min_height

        #: tooltip data (normally string). See :class:`Tooltip` for details
        self.tooltip = tooltip

        self.connect_after("on-render", self.__on_render)
        self.connect("on-mouse-over", self.__on_mouse_over)
        self.connect("on-mouse-out", self.__on_mouse_out)
        self.connect("on-mouse-down", self.__on_mouse_down)
        self.connect("on-key-press", self.__on_key_press)

        self._children_resize_queued = True
        self._scene_resize_handler = None


    def __setattr__(self, name, val):
        # forward width and height to min_width and min_height as i've ruined the setters a bit i think
        if name == "width":
            name = "min_width"
        elif name == "height":
            name = "min_height"
        elif name == 'enabled':
            name = '_enabled'
        elif name == "padding":
            val = val or 0
            if isinstance(val, int):
                val = (val, )

            if len(val) == 1:
                self.padding_top = self.padding_right = self.padding_bottom = self.padding_left = val[0]
            elif len(val) == 2:
                self.padding_top = self.padding_bottom = val[0]
                self.padding_right = self.padding_left = val[1]

            elif len(val) == 3:
                self.padding_top = val[0]
                self.padding_right = self.padding_left = val[1]
                self.padding_bottom = val[2]
            elif len(val) == 4:
                self.padding_top, self.padding_right, self.padding_bottom, self.padding_left = val
            return

        elif name == "margin":
            val = val or 0
            if isinstance(val, int):
                val = (val, )

            if len(val) == 1:
                self.margin_top = self.margin_right = self.margin_bottom = self.margin_left = val[0]
            elif len(val) == 2:
                self.margin_top = self.margin_bottom = val[0]
                self.margin_right = self.margin_left = val[1]
            elif len(val) == 3:
                self.margin_top = val[0]
                self.margin_right = self.margin_left = val[1]
                self.margin_bottom = val[2]
            elif len(val) == 4:
                self.margin_top, self.margin_right, self.margin_bottom, self.margin_left = val
            return


        if self.__dict__.get(name, "hamster_graphics_no_value_really") == val:
            return

        graphics.Sprite.__setattr__(self, name, val)

        # in widget case visibility affects placement and everything so request repositioning from parent
        if name == 'visible'and getattr(self, "parent", None):
            self.parent.resize_children()

        elif name == '_enabled' and getattr(self, "sprites", None):
            self._propagate_enabledness()

        if name in self._sizing_attributes:
            self.queue_resize()

    def _propagate_enabledness(self):
        # runs down the tree and marks all child sprites as dirty as
        # enabledness is inherited
        self._sprite_dirty = True
        for sprite in self.sprites:
            next_call = getattr(sprite, "_propagate_enabledness", None)
            if next_call:
                next_call()

    def _with_rotation(self, w, h):
        """calculate the actual dimensions after rotation"""
        res_w = abs(w * math.cos(self.rotation) + h * math.sin(self.rotation))
        res_h = abs(h * math.cos(self.rotation) + w * math.sin(self.rotation))
        return res_w, res_h

    @property
    def horizontal_padding(self):
        """total calculated horizontal padding. A read-only property."""
        return self.padding_left + self.padding_right

    @property
    def vertical_padding(self):
        """total calculated vertical padding.  A read-only property."""
        return self.padding_top + self.padding_bottom

    def __on_mouse_over(self, sprite):
        cursor, mouse_x, mouse_y, mods = sprite.get_scene().get_window().get_pointer()
        if self.tooltip and not gdk.ModifierType.BUTTON1_MASK & mods:
            self._set_tooltip(self.tooltip)


    def __on_mouse_out(self, sprite):
        if self.tooltip:
            self._set_tooltip(None)

    def __on_mouse_down(self, sprite, event):
        if self.can_focus:
            self.grab_focus()
        if self.tooltip:
            self._set_tooltip(None)


    def _set_tooltip(self, tooltip):
        scene = self.get_scene()
        if not scene:
            return

        if hasattr(scene, "_tooltip") == False:
            scene._tooltip = TooltipWindow()

        scene._tooltip.show(self, tooltip)


    def __on_key_press(self, sprite, event):
        if event.keyval in (gdk.KEY_Tab, gdk.KEY_ISO_Left_Tab):
            idx = self.parent.sprites.index(self)

            if event.state & gdk.ModifierType.SHIFT_MASK: # going backwards
                if idx > 0:
                    idx -= 1
                    self.parent.sprites[idx].grab_focus()
            else:
                if idx < len(self.parent.sprites) - 1:
                    idx += 1
                    self.parent.sprites[idx].grab_focus()


    def queue_resize(self):
        """request the element to re-check it's child sprite sizes"""
        self._children_resize_queued = True
        parent = getattr(self, "parent", None)
        if parent and isinstance(parent, graphics.Sprite) and hasattr(parent, "queue_resize"):
            parent.queue_resize()


    def get_min_size(self):
        """returns size required by the widget"""
        if self.visible == False:
            return 0, 0
        else:
            return ((self.min_width or 0) + self.horizontal_padding + self.margin_left + self.margin_right,
                    (self.min_height or 0) + self.vertical_padding + self.margin_top + self.margin_bottom)



    def insert(self, index = 0, *widgets):
        """insert widget in the sprites list at the given index.
        by default will prepend."""
        for widget in widgets:
            self._add(widget, index)
            index +=1 # as we are moving forwards
        self._sort()


    def insert_before(self, target):
        """insert this widget into the targets parent before the target"""
        if not target.parent:
            return
        target.parent.insert(target.parent.sprites.index(target), self)

    def insert_after(self, target):
        """insert this widget into the targets parent container after the target"""
        if not target.parent:
            return
        target.parent.insert(target.parent.sprites.index(target) + 1, self)


    @property
    def width(self):
        """width in pixels"""
        alloc_w = self.alloc_w

        if self.parent and self.parent == self.get_scene():
            alloc_w = self.parent.width

            def res(scene, event):
                if self.parent:
                    self.queue_resize()
                else:
                    scene.disconnect(self._scene_resize_handler)
                    self._scene_resize_handler = None


            if not self._scene_resize_handler:
                # TODO - disconnect on reparenting
                self._scene_resize_handler = self.parent.connect("on-resize", res)

            if hasattr(self.parent, '_global_shortcuts') is False:
                self.parent._global_shortcuts = GlobalShortcuts(self.parent)

        min_width = (self.min_width or 0) + self.margin_left + self.margin_right
        w = alloc_w if alloc_w is not None and self.fill else min_width
        w = max(w or 0, self.get_min_size()[0])
        return w - self.margin_left - self.margin_right

    @property
    def height(self):
        """height in pixels"""
        alloc_h = self.alloc_h

        if self.parent and self.parent == self.get_scene():
            alloc_h = self.parent.height

        min_height = (self.min_height or 0) + self.margin_top + self.margin_bottom
        h = alloc_h if alloc_h is not None and self.fill else min_height
        h = max(h or 0, self.get_min_size()[1])
        return h - self.margin_top - self.margin_bottom

    @property
    def enabled(self):
        """whether the user is allowed to interact with the
        widget. Item is enabled only if all it's parent elements are"""
        enabled = self._enabled
        if not enabled:
            return False

        if self.parent and isinstance(self.parent, Widget):
            if self.parent.enabled == False:
                return False

        return True


    def __on_render(self, sprite):
        self.do_render()
        if self.debug:
            self.graphics.save_context()

            w, h = self.width, self.height
            if hasattr(self, "get_height_for_width_size"):
                w2, h2 = self.get_height_for_width_size()
                w2 = w2 - self.margin_left - self.margin_right
                h2 = h2 - self.margin_top - self.margin_bottom
                w, h = max(w, w2), max(h, h2)

            self.graphics.rectangle(0.5, 0.5, w, h)
            self.graphics.set_line_style(5)
            self.graphics.stroke("#666", 0.5)
            self.graphics.restore_context()

            if self.pivot_x or self.pivot_y:
                self.graphics.fill_area(self.pivot_x - 3, self.pivot_y - 3, 6, 6, "#666")

    def __emit(self, event_name, *args):
        if (self.enabled and self.opacity > 0):
            self.emit(event_name, *args)

    # emit events only if enabled
    def _do_click(self, event):
        self.__emit("on-click", event)
    def _do_double_click(self, event):
        self.__emit("on-double-click", event)
    def _do_triple_click(self, event):
        self.__emit("on-triple-click", event)
    def _do_mouse_down(self, event):
        self.__emit("on-mouse-down", event)
    def _do_mouse_up(self, event):
        self.__emit("on-mouse-up", event)
    def _do_mouse_over(self):
        self.__emit("on-mouse-over")
    def _do_mouse_move(self, event):
        self.__emit("on-mouse-move", event)
    def _do_mouse_out(self):
        self.__emit("on-mouse-out")
    def _do_key_press(self, event):
        self.__emit("on-key-press", event)
    def _do_mnemonic_activated(self, event):
        self.__emit("on-mnemonic-activated", event)

    def do_render(self):
        """this function is called in the on-render event. override it to do
           any drawing. subscribing to the "on-render" event will work too, but
           overriding this method is preferred for easier subclassing.
        """
        pass


    def _rounded_line(self, coords, corner_radius = 4):
        # draws a line that is rounded in the corners
        half_corner = corner_radius / 2

        current_x, current_y = coords[0]
        self.graphics.move_to(current_x, current_y)

        for (x1, y1), (x2, y2) in zip(coords[1:], coords[2:]):
            if current_x == x1:
                #vertically starting curve going somewhere
                dy = (y1 < current_y) * 2 - 1
                dx = (x1 < x2) * 2 - 1

                self.graphics.line_to(x1, y1 + corner_radius * dy)
                self.graphics.curve_to(x1, y1 + half_corner * dy, x1 + half_corner * dx, y1, x1 + corner_radius * dx, y1)


            elif current_y == y1:
                #horizontally starting curve going somewhere
                dx = (x1 < current_x) * 2 - 1
                dy = (y1 < y2) * 2 - 1

                self.graphics.line_to(x1 + corner_radius * dx, y1)
                self.graphics.curve_to(x1 + half_corner * dx, y1, x1, y1 + half_corner * dy, x1, y1 + corner_radius * dy)


            current_x, current_y = x1, y1
        self.graphics.line_to(*coords[-1])



class Tooltip(object):
    """There is a single tooltip object per whole application and it is
    automatically created on the first call. The class attributes (color,
    padding, size, etc.) allow basic modifications of the looks.
    If you would like to have full control over the tooltip, you can set your
    own class in :class:`TooltipWindow`.

    Example::

        # make tooltip background red for the whole application and add more padding
        import ui
        ui.Tooltip.background_color = "#f00"
        ui.Tooltip.padding = 20
    """
    #: font description
    font_desc = "Sans serif 10"

    #: default font size
    size = None

    #: padding around the label in pixels
    padding = 5

    #: background color
    background_color = "#333"

    #: font color
    color = "#eee"


    def __init__(self):
        from ui.widgets import Label # unfortunately otherwise we run into a circular dependency
        self.label = Label(size=self.size,
                           font_desc=self.font_desc,
                           padding=self.padding,
                           background_color=self.background_color,
                           color=self.color)

    def __getattr__(self, name):
        # forward all getters to label (this way we walk around the label circular loop)
        # no need to repeat this when overriding, because at that point you already
        # have access to label and can inherit from that
        if name == 'label':
            return self.__dict__['label']
        else:
            return getattr(self.label, name)

    def set_tooltip(self, tooltip):
        """set_tooltip is internally called by the framework. Implement this
        function if you are creating a custom tooltip class.
        The `tooltip` parameter normally contains text, but you can set the
        :class:`Widget.tooltip` to anything (even sprites)"""
        self.label.text = tooltip


class TooltipWindow(object):
    """Object that contains the actual tooltip :class:`gtk.Window`.
    By setting class attributes here you can control the tooltip class and
    the timespan before showing the tooltip"""

    #: class that renders tooltip contents. override this attribute if you
    #: want to use your own tooltip class
    TooltipClass = Tooltip

    #: delay before showing the tooltip
    first_appearance_milis = 300


    def __init__(self):
        self.label = None
        self.popup = gtk.Window(type = gtk.WindowType.POPUP)
        self.popup_scene = graphics.Scene(interactive=False)
        self.popup.add(self.popup_scene)

        self.tooltip = self.TooltipClass()
        self.popup_scene.add_child(self.tooltip)

        self._display_timeout = None
        self._last_display_time = None
        self._current_widget = None
        self._prev_tooltip = None


    def show(self, widget, tooltip):
        """Show tooltip. This function is called automatically by the library."""
        if not tooltip:
            self._prev_tooltip = tooltip
            self.popup.hide()

            if self._display_timeout:
                gobject.source_remove(self._display_timeout)
            return


        if widget == self._current_widget and tooltip == self._prev_tooltip:
            return


        if not self._last_display_time or (dt.datetime.now() - self._last_display_time) > dt.timedelta(milliseconds = self.first_appearance_milis):
            self._display_timeout = gobject.timeout_add(self.first_appearance_milis,
                                                        self._display, widget, tooltip)
        else:
            self._display(widget, tooltip)


    def _display(self, widget, tooltip):
        self._current_widget, self._prev_tooltip = widget, tooltip

        self._last_display_time = dt.datetime.now()

        scene = widget.get_scene()

        parent_window = scene.get_parent_window()
        dummy, window_x, window_y = parent_window.get_origin()

        exts = widget.get_extents()
        widget_x, widget_y, widget_w, widget_h = exts.x, exts.y, exts.width, exts.height


        screen = parent_window.get_screen()
        screen_w, screen_h = screen.get_width(), screen.get_height()

        #set label to determine dimensions
        self.tooltip.set_tooltip(tooltip)
        popup_w, popup_h = self.tooltip.width, self.tooltip.height
        if hasattr(self.tooltip, "get_height_for_width_size"):
            popup_w, popup_h = self.tooltip.get_height_for_width_size()
            popup_w += self.tooltip.horizontal_padding
            popup_h += self.tooltip.vertical_padding


        self.popup.resize(popup_w, popup_h)

        if widget.tooltip_position == "mouse":
            cursor_size = parent_window.get_display().get_default_cursor_size()
            tooltip_x = scene.mouse_x + (cursor_size - popup_w) / 2
            tooltip_y = scene.mouse_y + cursor_size
        else:
            tooltip_x = widget_x + (widget_w - popup_w) / 2
            tooltip_y = widget_y + widget_h

        if widget.tooltip_offset:
            tooltip_x += widget.tooltip_offset[0]
            tooltip_y += widget.tooltip_offset[1]

        popup_x = window_x + tooltip_x
        popup_x = max(0, min(popup_x, screen_w - popup_w))

        # show below the widget if possible. otherwise - on top
        popup_y = window_y + tooltip_y
        if popup_y + popup_h > screen_h:
            popup_y = window_y + widget_y - popup_h


        self.popup.move(int(popup_x), int(popup_y))
        self.popup.show_all()


class GlobalShortcuts(object):
    def __init__(self, target):
        self.target = target
        target.connect("on-key-press", self.on_key_press)
        target.connect("on-key-release", self.on_key_release)
        self._pressed_key = None


    def on_key_press(self, target, event):
        if self._pressed_key:
            return

        for widget in target.traverse():
            items = [widget] if hasattr(widget, 'mnemonic') else getattr(widget, 'mnemonic_items', [])
            for item in items:
                if item.mnemonic and self._check_mnemonic(item.mnemonic, event):
                    item._do_mnemonic_activated(event)
                    self._pressed_key = chr(event.keyval).lower() if chr < 256 else event.keyval
                    return #grab the first and go home. TODO - we are doing depth-first. consider doing width-first


    def on_key_release(self, target, event):
        if not event.string:
            return
        event_key = chr(event.keyval).lower() if chr < 256 else event.keyval
        if event_key == self._pressed_key:
            self._pressed_key = None


    def _check_mnemonic(self, mnemonic_string, event):
        pressed_key = event.string
        if not pressed_key:
            return

        mask_states = {
            'Shift': event.state & gdk.ModifierType.SHIFT_MASK,
            'Ctrl': event.state & gdk.ModifierType.CONTROL_MASK,
            'Alt': event.state & gdk.ModifierType.MOD1_MASK,
            'Super': event.state & gdk.ModifierType.SUPER_MASK,
        }
        keys = mnemonic_string.split("+")

        # check for modifiers
        for mask in mask_states.keys():
            if mask in keys:
                keys.remove(mask)
                if not mask_states[mask]:
                    return False
            else:
                if mask_states[mask]: # we have a modifier that was not asked for
                    return False

        # examine pressed key
        # have it case insensitive as we request the modifiers explicitly
        # and so have to avoid impossible cases like Ctrl+Shift+c  (lowercase c)
        return chr(event.keyval).lower() == keys[0].lower()
