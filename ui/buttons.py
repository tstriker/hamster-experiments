# - coding: utf-8 -

# Copyright (c) 2011-2012 Media Modifications, Ltd.
# Dual licensed under the MIT or GPL Version 2 licenses.

from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import GObject as gobject

from lib import graphics
from ui.containers import Widget, Container, Bin, Table, Box, HBox, VBox, Fixed, Viewport, Group
from ui.widgets import Label
import math

class Button(Label):
    """A simple button"""
    __gsignals__ = {
        "on-state-change": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
    }
    fill = True
    padding = (6, 8)
    x_align = 0.5

    def __init__(self, label = "", bevel = True, repeat_down_delay = 0, pressed_offset = 1,**kwargs):
        Label.__init__(self, **kwargs)
        self.interactive, self.can_focus = True, True

        #: current state
        self.state = "normal"

        #: label
        self.label = label

        #: if set, will repeat the on-mouse-down signal every specified miliseconds while the button is pressed
        #: when setting: 100 is a good initial value
        self.repeat_down_delay = repeat_down_delay

        #: draw border
        self.bevel = bevel

        #: by how many pixels should the label move towards bottom right when pressed
        #: defaults to 1
        self.pressed_offset = pressed_offset


        #: a rather curious figure telling how many times the button has been
        #: pressed since gaining focus. resets on losing the focus
        self.times_clicked = 0

        self.colors = {
            # fill, fill, stroke, outer stroke
            "normal": ("#fcfcfc", "#efefef", "#dedcda", "#918e8c"),
            "highlight": ("#fff", "#F4F3F2", "#dedcda", "#918e8c"),
            "pressed": ("#CFD1D3", "#B9BBC0", "#E0DEDD", "#5B7AA1"),
            "focused": ("#fcfcfc", "#efefef", "#52749E", "#89ADDA")
        }

        self.connect("on-mouse-over", self.__on_mouse_over)
        self.connect("on-mouse-out", self.__on_mouse_out)
        self.connect("on-mouse-down", self.__on_mouse_down)
        self.connect("on-render", self.__on_render)

        self._pressed = False
        self._scene_mouse_up = None

        self._timeout = None


    def __setattr__(self, name, val):
        if name == "label":
            name = "text"
        Label.__setattr__(self, name, val)

        if name == "focused" and val == False:
            self.times_clicked = 0

    @property
    def label(self):
        return self.text



    def __on_render(self, sprite):
        """we want the button to be clickable"""
        self.graphics.rectangle(0, 0, self.width, self.height)
        self.graphics.new_path()


    def __on_mouse_over(self, button):
        if self._pressed:
            self._set_state("pressed")
            if self.repeat_down_delay > 0:
                self._repeat_mouse_down()
        else:
            cursor, mouse_x, mouse_y, mods = button.get_scene().get_window().get_pointer()
            if gdk.ModifierType.BUTTON1_MASK & mods:
                if self._scene_mouse_up: # having scene_mouse_up means the mouse-down came from us
                    self._set_state("pressed")
            else:
                self._set_state("highlight")

    def __on_mouse_out(self, sprite):
        self.__cancel_timeout()
        self._set_state("normal")

    def __cancel_timeout(self):
        if self._timeout:
            gobject.source_remove(self._timeout)
            self._timeout = None


    def __on_mouse_down(self, sprite, event):
        self._set_state("pressed")
        if not self._scene_mouse_up:
            self._scene_mouse_up = self.get_scene().connect("on-mouse-up", self._on_scene_mouse_up)

        if event and self.repeat_down_delay > 0 and self._timeout is None:
            self._repeat_mouse_down()

    def _repeat_mouse_down(self):
        # responsible for repeating mouse-down every repeat_down_delay miliseconds
        def repeat_mouse_down():
            self._do_mouse_down(None)
            return True

        if not self._timeout:
            self._timeout = gobject.timeout_add(self.repeat_down_delay, repeat_mouse_down)


    def _on_scene_mouse_up(self, sprite, event):
        self.__cancel_timeout()

        if self.check_hit(event.x, event.y):
            self._set_state("highlight")
        else:
            self._set_state("normal")

        self._pressed = False
        if self._scene_mouse_up:
            self.get_scene().disconnect(self._scene_mouse_up)
            self._scene_mouse_up = None

    def _set_state(self, state):
        if state != self.state:
            if state == "pressed" or self.state == "pressed":
                offset = self.pressed_offset if state == "pressed" else 0
                self.container.padding_left = self.container.padding_top = offset
                self.container.padding_right = self.container.padding_bottom = -offset

            if state == "pressed":
                self.times_clicked += 1


            self.state = state
            self.emit("on-state-change", self.state)

    def do_render(self, colors = None):
        self.graphics.set_line_style(width = 1)
        width, height = self.width, self.height

        x, y, x2, y2 = 0.5, 0.5, width - 1, height - 1
        corner_radius = 4

        state = self.state



        colors = colors or self.colors[self.state]

        if self.focused:
            colors = colors[:2] + self.colors["focused"][2:]


        # upper half of the highlight
        self.graphics.fill_area(x, y, x2, y2 / 2.0, colors[0])

        # lower_half
        self.graphics.fill_area(x, y2 / 2.0, x2, y2 / 2.0, colors[1])


        if self.bevel:
            # outline
            self.graphics.rectangle(0, 0, width, height, corner_radius)
            self.graphics.stroke(colors[2])

            # main line
            self.graphics.rectangle(0.5, 0.5, width - 1, height - 1, corner_radius)
            self.graphics.stroke(colors[3])



class ToggleButton(Button):
    """A button that retains its state. If you pack toggle buttons in
       :class:`~ui.containers.Group` then toggle one button will untoggle all the others in
       that group.
    """
    __gsignals__ = {
        "on-toggle": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }
    def __init__(self, label = "", toggled = False, group = None, **kwargs):
        Button.__init__(self, label = label, **kwargs)

        #: whether the button currently is toggled or not
        self.toggled = toggled

        self.group = group

        self.connect("on-click", self.on_click)
        self.connect("on-key-press", self.on_key_press)


    def __setattr__(self, name, val):
        if val == self.__dict__.get(name, "hamster_graphics_no_value_really"):
            return

        if name == 'group':
            # add ourselves to group
            prev_group = getattr(self, 'group', None)
            if prev_group:
                prev_group._remove_item(self)
            if val:
                val._add_item(self)

        Button.__setattr__(self, name, val)


    def on_click(self, sprite, event):
        self.toggle()

    def on_key_press(self, sprite, event):
        if event.keyval == gdk.KEY_Return or event.keyval == gdk.KEY_space:
            self.toggle()

    def toggle(self):
        """toggle button state"""
        self.toggled = not self.toggled
        self.emit("on-toggle")


    def do_render(self):
        state = self.state
        if self.toggled:
            state = "pressed"

        colors = self.colors[state]

        if self.focused:
            colors = self.colors[state][:2] + self.colors["focused"][2:]


        if isinstance(self.parent, Group) == False or len(self.parent.sprites) == 1:
            # normal button
            Button.do_render(self, colors)
        else:
            # otherwise check how many are there, am i the first etc.
            width, height = self.width, self.height

            x, y, x2, y2 = 0.5, 0.5, 0.5 + width, 0.5 + height
            corner_radius = 4


            # bit of sphagetti code - will clean up later with gradients and such
            # TODO - add gradients to graphics
            if self.parent.sprites.index(self) == 0:
                # upper half of the highlight
                self._rounded_line([(x2, y), (x, y), (x, y2 / 2.0)], corner_radius)
                self.graphics.line_to([(x2, y2 / 2.0), (x2, y)])
                self.graphics.fill(colors[0])

                # lower half
                self._rounded_line([(x, y2 / 2.0), (x, y2), (x2, y2)], corner_radius)
                self.graphics.line_to([(x2, y2 / 2.0), (x, y2 / 2.0)])
                self.graphics.fill(colors[1])

                # outline
                self._rounded_line([(x2+0.5, 0), (0, 0), (0, y2+0.5), (x2+0.5, y2+0.5)], corner_radius)
                self.graphics.line_to(x2+0.5, 0)
                self.graphics.stroke(colors[2])


                # main line
                self._rounded_line([(x2, y), (x, y), (x, y2), (x2, y2)], corner_radius)
                self.graphics.line_to(x2, y)
                self.graphics.stroke(colors[3])

            elif self.parent.sprites.index(self) == len(self.parent.sprites) - 1:
                # upper half of the highlight
                self._rounded_line([(x, y), (x2, y), (x2, y2 / 2.0)], corner_radius)
                self.graphics.line_to([(x, y2 / 2.0), (x, y)])
                self.graphics.fill(colors[0])

                # lower half
                self._rounded_line([(x2, y2 / 2.0), (x2, y2), (x, y2)], corner_radius)
                self.graphics.line_to([(x, y2 / 2.0), (x2, y2 / 2.0)])
                self.graphics.fill(colors[1])

                # outline
                self._rounded_line([(0, 0), (x2 + 0.5, 0), (x2 + 0.5, y2+0.5), (0, y2+0.5)], corner_radius)
                self.graphics.line_to(0, 0)
                self.graphics.stroke(colors[2])


                # main line
                self._rounded_line([(x, y), (x2, y), (x2, y2), (x, y2)], corner_radius)
                self.graphics.line_to(x, y)
                self.graphics.stroke(colors[3])

            else:
                # upper half of the highlight
                self.graphics.fill_area(x, y, x2, y2 / 2.0, colors[0])

                # lower half of the highlight
                self.graphics.fill_area(x, y2 / 2.0, x2, y2 / 2.0, colors[1])

                # outline
                self.graphics.rectangle(0, 0, x2 + 0.5, y2 + 0.5)
                self.graphics.stroke(colors[2])

                # outline
                self._rounded_line([(x2+0.5, 0), (0, 0), (0, y2+0.5), (x2+0.5, y2+0.5)], corner_radius)
                self.graphics.line_to(x2+0.5, 0)
                self.graphics.stroke(colors[2])

                # main line
                self.graphics.rectangle(x, y, x2 - 0.5, y2 - 0.5)
                self.graphics.stroke(colors[3])



class RadioMark(Widget):
    def __init__(self, state="normal", toggled=False, **kwargs):
        Widget.__init__(self, **kwargs)
        self.state = state
        self.toggled = toggled

    def do_render(self):
        """tickmark rendering function. override to render your own visuals"""
        size = self.min_height

        fill, stroke = "#fff", "#444"
        if self.state == "highlight":
            fill, stroke = "#ECF2F4", "#6A7D96"
        elif self.state == "pressed":
            fill, stroke = "#BDCDE2", "#6A7D96"

        self.graphics.set_line_style(width=1)
        self.graphics.ellipse(0, 0, size, size)
        self.graphics.fill_stroke(fill, stroke)

        if self.toggled:
            self.graphics.ellipse(2, 2, size - 4, size - 4)
            self.graphics.fill("#444")

class RadioButton(ToggleButton):
    """A choice of one of multiple check buttons. Pack radiobuttons in
       :class:`ui.containers.Group`.
    """
    #: class that renders the checkmark
    Mark = RadioMark

    padding = 0

    def __init__(self, label = "", pressed_offset = 0, spacing = 10, **kwargs):
        ToggleButton.__init__(self, label = label, pressed_offset = pressed_offset,
                              spacing=spacing, **kwargs)

        #: visual tick mark. it replaces the label's image
        self.tick_mark = self.Mark(state=self.state, toggled=self.toggled, width=11, height=11, fill=False)

        self.image = self.tick_mark
        self.container.x_align = 0

    def __setattr__(self, name, val):
        ToggleButton.__setattr__(self, name, val)
        if name in ("state", "toggled") and hasattr(self, "tick_mark"):
            setattr(self.tick_mark, name, val)

    def do_render(self):
        self.graphics.rectangle(0, 0, self.width, self.height)
        self.graphics.new_path()



class CheckMark(RadioMark):
    def do_render(self):
        size = self.min_height

        fill, stroke = "#fff", "#999"
        if self.state in ("highlight", "pressed"):
            fill, stroke = "#BDCDE2", "#6A7D96"

        self.graphics.set_line_style(1)
        self.graphics.rectangle(0.5, 0.5, size, size)
        self.graphics.fill_stroke(fill, stroke)

        if self.toggled:
            self.graphics.set_line_style(2)
            self.graphics.move_to(2, size * 0.5)
            self.graphics.line_to(size * 0.4, size - 3)
            self.graphics.line_to(size - 2, 2)
            self.graphics.stroke("#000")

class CheckButton(RadioButton):
    """a toggle button widget styled as a checkbox and label"""
    Mark = CheckMark




class ScrollButton(Button):
    """a button well suited for scrollbars and other scrollies"""
    def __init__(self, direction = "up", repeat_down_delay=50, **kwargs):
        Button.__init__(self, repeat_down_delay = repeat_down_delay, **kwargs)

        #: which way is the arrow looking. one of "up", "down", "left", "right"
        self.direction = direction


    def do_render(self):
        w, h = self.width, self.height
        size = min(self.width, self.height) - 1
        self.graphics.rectangle(int((w - size) / 2) + 0.5, int((h - size) / 2) + 0.5, size, size, 2)

        if self.enabled == False:
            colors = "#fff", "#ccc"
        else:
            colors = "#fff", "#a8aca8"

        self.graphics.fill_stroke(*colors)


        self.graphics.save_context()
        arrow_size = 6
        self.graphics.translate(w / 2.0, h / 2.0 + 0.5)
        #self.graphics.fill_area(-1, -1, 2, 2, "#000")

        if self.direction == "left":
            self.graphics.rotate(math.pi)
        elif self.direction == "up":
            self.graphics.rotate(-math.pi / 2)
        elif self.direction == "down":
            self.graphics.rotate(math.pi / 2)

        self.graphics.move_to(-1, -3)
        self.graphics.line_to(2, 0)
        self.graphics.line_to(-1, 3)


        if self.enabled == False:
            color = "#ccc"
        else:
            color = "#444"
        self.graphics.stroke(color)

        self.graphics.restore_context()
