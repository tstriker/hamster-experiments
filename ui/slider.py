# - coding: utf-8 -

# Copyright (c) 2011-2012 Media Modifications, Ltd.
# Dual licensed under the MIT or GPL Version 2 licenses.

from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import GObject as gobject

from lib import graphics
from ui import Widget, Button, Fixed

class SliderGrip(Button):
    width = 20
    def __init__(self, **kwargs):
        Button.__init__(self, **kwargs)
        self.padding = 0
        self.margin = 0
        self.draggable = True
        self.connect("on-drag-finish", self.__on_drag_finish)

    def do_render(self):
        w, h = self.width, self.height
        self.graphics.rectangle(0.5, 0.5, int(w), int(h), 3)
        self.graphics.fill_stroke("#999", "#333")

    def __on_drag_finish(self, sprite, event):
        # re-trigger the state change as we override it in the set_state
        self._on_scene_mouse_up(self, event)

    def _set_state(self, state):
        if state == self.state:
            return

        if state == "normal":
            scene = self.get_scene()
            if scene._drag_sprite == self:
                state = "pressed"


        self.state = state
        self.emit("on-state-change", self.state)




class SliderSnapPoint(Widget):
    def __init__(self, value, label = None, **kwargs):
        Widget.__init__(self, **kwargs)

        #: value
        self.value = value

        #: label
        self.label = label


    def do_render(self):
        self.graphics.move_to(0.5, 0)
        self.graphics.line_to(0.5, self.height)
        self.graphics.stroke("#555")



class Slider(Fixed):
    """ a slider widget that allows the user to select a value by dragging
    a slider along a rail

    **Signals**:

    **on-change** *(sprite, val)*
    - fired when the current value of the widget is changed. brings the new
    current value with the event.
    """


    #: class for the slidergrip
    slidergrip_class = SliderGrip

    #: class for the slidersnappoint
    slidersnappoint_class = SliderSnapPoint

    __gsignals__ = {
        "on-change": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
    }
    def __init__(self, values = [], selection = None,
                 snap_to_ticks = True, range = False, grips_can_cross = True,
                 snap_points = None, snap_distance = 20, inverse = False,
                 snap_on_release = False, **kwargs):
        Fixed.__init__(self, **kwargs)

        self.scale_width = 10.5

        #: list of available items. It can be list of either strings or numbers
        #: for number ranges use the python `range <http://docs.python.org/library/functions.html#range>`_ generator.
        self.values = values

        #: Possible values: [True, "start", "end"]. When set to true will add
        #: second handler to select range.
        #: if "start" the selection range will be from start till current position
        #: if "end", the selection range will be from current position till end
        #: Defaults is False which means that a single value is selected instead
        self.range = range

        #: if set to true, the selection will be painted on the outer range
        self.inverse = inverse

        #: should the slider snap to the exact tick position
        self.snap_to_ticks = snap_to_ticks

        self._snap_sprites = []
        #: list of specially highlighted points
        self.snap_points = snap_points

        #: distance in pixels at which the snap points should start attracting
        self.snap_distance = snap_distance

        #: Normally the grip snaps to the snap points when dragged.
        #: This changes behaviour so that dragging is free, but upon release,
        #: if a snap point is in the distance, snaps to that.
        self.snap_on_release = snap_on_release

        #: works for ranges. if set to False, then it won't be possible to move
        #: start grip after end grip and vice versa
        self.grips_can_cross = grips_can_cross

        self._prev_value = None

        self.start_grip = self.slidergrip_class( )
        self.end_grip = self.slidergrip_class(visible = range == True)

        for grip in (self.start_grip, self.end_grip):
            self.connect_child(grip, "on-drag", self.on_grip_drag)
            self.connect_child(grip, "on-drag-finish", self.on_grip_drag_finish)

        self.add_child(self.start_grip, self.end_grip)

        self._selection = selection

        self._mark_selection = True

        self.connect("on-render", self.__on_render)


    def __setattr__(self, name, val):
        if name == 'selection':
            name = "_selection"
            self._mark_selection = True

        if self.__dict__.get(name, "hamster_graphics_no_value_really") == val:
            return


        Fixed.__setattr__(self, name, val)
        if name == 'range' and hasattr(self, "end_grip"):
            self.end_grip.visible = val == True
        elif name in ("alloc_w", "min_width") and hasattr(self, "range"):
            self._adjust_grips()
        elif name == "snap_points":
            self._rebuild_snaps()
        elif name == "_selection":
            self._adjust_grips()


    def resize_children(self):
        self.start_grip.alloc_h = self.end_grip.alloc_h = self.scale_width
        self.start_grip.y = self.end_grip.y = self.padding_top

        for snap in self._snap_sprites:
            snap.x = (self.width - self.end_grip.width) * float(self.values.index(snap.value)) / (len(self.values) - 1) + self.start_grip.width / 2
            snap.y = self.start_grip.y + self.start_grip.height + 3
            snap.alloc_h = self.height - self.padding_bottom - snap.y

        # XXX - resize children should not be called when dragging
        if self.get_scene() and self.get_scene()._drag_sprite not in (self.start_grip, self.end_grip):
            self._adjust_grips()


    def get_min_size(self):
        w, h = self.start_grip.width * 3, self.scale_width
        if self.snap_points:
            h = h * 2
        return int(w), int(h)


    @property
    def selection(self):
        """current selection"""
        # make sure that in case of range start is always lower than end
        res = self._selection
        if self.range is True:
            start, end = res
            if start > end:
                start, end = end, start
            return (start, end)
        else:
            return res


    def _rebuild_snaps(self):
        self.remove_child(*(self._snap_sprites))
        self._snap_sprites = []
        if self.snap_points is not None:
            for point in self.snap_points:
                snap_sprite = self.slidersnappoint_class(point)
                self.add_child(snap_sprite)
                self._snap_sprites.append(snap_sprite)


    def _adjust_grips(self):
        """position grips according to their value"""
        start_x, end_x = self.start_grip.x, self.end_grip.x
        if self.range is True:
            start_val, end_val = self.selection or (None, None)
        else:
            start_val, end_val = self.selection, None

        if start_val is not None:
            self.start_grip.x = (self.width - self.start_grip.width) * float(self.values.index(start_val)) / (len(self.values) - 1)

        if end_val is not None:
            self.end_grip.x = (self.width - self.end_grip.width) * float(self.values.index(end_val)) / (len(self.values) - 1)

        if start_x != self.start_grip.x or end_x != self.end_grip.x:
            self._sprite_dirty = True


    def _snap_grips(self, grip):
        """move grips to the snap points if any snap point is in the proximity"""
        prev_pos = grip.x

        candidates = []
        grip_x = grip.x + grip.width / 2
        for snap in self._snap_sprites:
            if abs(grip_x - snap.x) < self.snap_distance:
                candidates.append((snap, abs(grip_x - snap.x)))

        if candidates:
            closest, proximity = list(sorted(candidates, key=lambda cand:cand[1]))[0]
            grip.x = closest.x - grip.width / 2

        if prev_pos != grip.x:
            self._update_selection(grip)
            self._sprite_dirty = True

    def _update_selection(self, grip = None):
        pixels = float(self.width - self.start_grip.width - self.horizontal_padding)

        start_val, end_val = None, None

        if self.range is True:
            if grip in (None, self.start_grip):
                normalized = (self.start_grip.x - self.padding_left) / pixels # get into 0..1
                pos = int(normalized * (len(self.values) - 1))
                start_val = self.values[pos]
            else:
                start_val = self.selection[0] if self.start_grip.x < self.end_grip.x else self.selection[1]


            if grip in (None, self.end_grip):
                normalized = (self.end_grip.x - self.padding_left) / pixels # get into 0..1
                pos = int(normalized * (len(self.values) - 1))
                end_val = self.values[pos]
            else:
                end_val = self.selection[1] if self.start_grip.x < self.end_grip.x else self.selection[0]
        else:
            normalized = (self.start_grip.x - self.padding_left) / pixels # get into 0..1
            pos = int(normalized * (len(self.values) - 1))
            start_val = self.values[pos]


        if self.range is True:
            selection = (start_val, end_val)
        else:
            selection = start_val

        self.__dict__['_selection'] = selection # avoid echoing

        if self._prev_value != selection:
            self._prev_value = selection
            self.emit("on-change", self.selection)




    def on_grip_drag(self, grip, event):
        if self.enabled is False or self.interactive is False:
            grip.x, grip.y = grip.drag_x, grip.drag_y
            return

        grip.y = self.padding_top

        if grip == self.start_grip:
            min_x, max_x = self.padding_left, self.width - grip.width - self.padding_right
        else:
            min_x, max_x = self.padding_left, self.width - grip.width - self.padding_right

        grip.x = min(max(grip.x, min_x), max_x)


        if not self.snap_on_release:
            self._snap_grips(grip)

        if self.range is True and self.grips_can_cross == False:
            if grip == self.start_grip:
                grip.x = min(grip.x, self.end_grip.x - 1)
            else:
                grip.x = max(grip.x, self.start_grip.x + 1)


        if self.snap_to_ticks:
            pixels = float(self.width - self.start_grip.width - self.horizontal_padding)
            normalized = (grip.x - self.padding_left) / float(pixels) # get into 0..1
            pos = int(normalized * (len(self.values) - 1))
            # restrict just to tick position
            grip.x = min_x + (max_x - min_x) * (float(pos) / (len(self.values) - 1))

        self._update_selection(grip)
        self._sprite_dirty = True # dragging grips changes fill and we paint the fill

    def on_grip_drag_finish(self, grip, event):
        if self.snap_on_release:
            self._snap_grips(grip)


    def __on_render(self, sprite):
        if self._mark_selection:
            self._adjust_grips()
            self._mark_selection = False

    def do_render(self):
        scale_h = int(self.scale_width * 0.5)
        x = self.padding_left + 0.5 + self.start_grip.width / 2
        y = self.padding_top + (self.scale_width - scale_h) / 2 + 0.5
        w = self.width - self.horizontal_padding - x - self.start_grip.width / 2
        h = scale_h

        # the whole slide
        self.graphics.rectangle(x, y, w, h, 3)
        self.graphics.fill_stroke("#eee", "#888")

        start_x, end_x = self.start_grip.x, self.end_grip.x
        if self.range is True and start_x > end_x:
            start_x, end_x = end_x, start_x


        if self.range == "start":
            self.graphics.rectangle(x, y, start_x, h, 3)
        elif self.range == "end":
            self.graphics.rectangle(start_x, y, w - start_x + self.start_grip.width / 2, h, 3)
        elif self.range is True:
            if not self.inverse:
                # middle
                self.graphics.rectangle(start_x, y, end_x - start_x, h, 3)
            else:
                self.graphics.rectangle(x, y, start_x, h, 3)
                self.graphics.rectangle(end_x, y, w - end_x + self.end_grip.width / 2, h, 3)


        self.graphics.fill_stroke("#A1AFD0", "#888")
