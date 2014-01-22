# - coding: utf-8 -

# Copyright (c) 2011-2012 Media Modifications, Ltd.
# Dual licensed under the MIT or GPL Version 2 licenses.

from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import GObject as gobject
from gi.repository import Pango as pango

from lib import graphics

from ui import ScrollArea, ListView, ToggleButton

class ComboBox(ToggleButton):
    """a button with a drop down menu.

    **Signals**:

    **on-change** *(sprite, new_val)*
    - fired after selecting a new value.
    """
    __gsignals__ = {
        "on-change": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
    }

    #: how much space will the dropmark occupy
    drop_mark_width = 20

    #: maximum height of the dropdown
    dropdown_height = 200

    x_align = 0

    #: class to use for the dropdown
    DropdownClass = ListView

    def __init__(self, rows = [], dropdown_height=None, open_below = True,
                 overflow = pango.EllipsizeMode.END, **kwargs):
        ToggleButton.__init__(self, overflow = overflow, **kwargs)

        if dropdown_height:
            self.dropdown_height = dropdown_height

        self.padding_right = self.drop_mark_width
        self._scene_mouse_down = None # scene mouse down listener to hide our window if clicked anywhere else
        self._echo = False

        self.listitem = self.DropdownClass(select_on_drag = True)
        self.connect_child(self.listitem, "on-mouse-move", self._on_listitem_mouse_move)
        self.connect_child(self.listitem, "on-mouse-up", self._on_listitem_mouse_up)
        self.connect_child(self.listitem, "on-select", self._on_listitem_select)

        #: the list of text strings available for selection
        self.rows = rows

        #: Whether the dropdown should appear below or over the input element
        self.open_below = open_below

        if rows:
            self._set_label(self.label or rows[0])

        self.scrollbox = ScrollArea(fill=False)
        self.scrollbox.add_child(self.listitem)

        self.connect("on-mouse-move", self.__on_mouse_move)
        self.connect("on-mouse-down", self.__on_mouse_down)
        self.connect("on-click", self.__on_click)
        self.connect("on-toggle", self._on_toggle)
        self.connect("on-key-press", self._on_key_press)

        self._echo_up = False

    def __setattr__(self, name, val):
        if name == "label":
            self._set_label(val)
            return

        if name == "rows":
            self.listitem.rows = val
            if val and hasattr(self, "label"):
                if self.label in val:
                    self.listitem.select(self.listitem.rows[self.listitem.find(self.label)])
                else:
                    self._set_label(val[0])

            # make sure we get pointer to the listitems treemodel
            ToggleButton.__setattr__(self, name, self.listitem.rows)
            return

        ToggleButton.__setattr__(self, name, val)
        if name == "drop_mark_width":
            self.padding_right = val

    def _set_label(self, item):
        if isinstance(item, (dict)):
            label = item.get("text", pango.parse_markup(item.get("markup", ""), -1, "0")[2])
        else:
            label = item

        if label == self.label:
            return #have it already!

        idx = self.listitem.find(label)

        if idx != -1:
            ToggleButton.__setattr__(self, 'label', label)

            # mark current row
            if not self.listitem.current_row or self.listitem.current_row[0] != self.label:
                self.listitem.select(self.listitem.rows[idx])

            self.emit("on-change", item)



    def _on_toggle(self, sprite):
        # our state strictly depends on whether the dropdown is visible or not
        self.toggled = self.scrollbox in self.get_scene().sprites

    def _on_key_press(self, sprite, event):
        if event.keyval == gdk.KEY_Return:
            self.toggle_display()

    def __on_mouse_down(self, sprite, event):
        self._echo = True
        if self.open_below is False:
            self._echo_up = True
        self.toggle_display()


    def resize_children(self):
        ToggleButton.resize_children(self)
        self.display_label.max_width = self.width - self.horizontal_padding


    def toggle_display(self):
        if self.scrollbox not in self.get_scene().sprites:
            self.listitem.select(self.label)
            self.show_dropdown()
            self.listitem.grab_focus()
        else:
            self.hide_dropdown()


    def __on_click(self, sprite, event):
        if self.toggled:
            self.listitem.grab_focus()


    def __on_scene_mouse_down(self, scene, event):
        if self._echo == False and (self.scrollbox.check_hit(event.x, event.y) == False and \
                                    self.check_hit(event.x, event.y) == False):
            self.hide_dropdown()
        self._echo = False


    def __on_scene_mouse_up(self, sprite, event):
        self._echo = False
        self._echo_up = False

    def __on_mouse_move(self, sprite, event):
        self._echo_up = False
        self._echo = False

    def _on_listitem_mouse_up(self, sprite, event):
        if self._echo_up:
            self._echo_up = False
            return

        if self.listitem.current_row:
            self._set_label(self.listitem.current_row[0])
        self.toggle_display()

    def _on_listitem_mouse_move(self, sprite, event):
        self._echo_up = False

    def _on_listitem_select(self, sprite, event=None):
        if self.listitem.current_row:
            self._set_label(self.listitem.current_row[0])
        self.hide_dropdown()


    def show_dropdown(self):
        """show the dropdown"""
        if not self.rows:
            return
        scene = self.get_scene()
        self.__scene_mouse_down = scene.connect_after("on-mouse-down", self.__on_scene_mouse_down)
        self.__scene_mouse_up = scene.connect("on-mouse-up", self.__on_scene_mouse_up)

        scene.add_child(self.scrollbox)
        self.scrollbox.x, self.scrollbox.y = self.to_scene_coords()

        self.scrollbox.width, self.scrollbox.height = self.width, min(self.listitem.height, self.dropdown_height)

        if self.open_below:
            self.scrollbox.y += self.height + 1
        else:
            if self.listitem.current_row:
                self.scrollbox.y -= self.listitem.get_row_position(self.listitem.current_row)


        if self.open_below:
            self.scrollbox.y = min(max(self.scrollbox.y, 0), scene.height - self.height - self.scrollbox.height - 1)
            self._echo_up = False
        else:
            self.scrollbox.y = min(max(self.scrollbox.y, 0), scene.height - self.scrollbox.height - 1)

        self.toggled = True


    def hide_dropdown(self):
        """hide the dropdown"""
        scene = self.get_scene()
        if self.__scene_mouse_down:
            scene.disconnect(self.__scene_mouse_down)
            scene.disconnect(self.__scene_mouse_up)
            self.__scene_mouse_down, self.__scene_mouse_up = None, None
        scene.remove_child(self.scrollbox)
        self.toggled = False
        self._echo_up = False
        self._echo = False

    def do_render(self):
        ToggleButton.do_render(self)
        w, h = self.drop_mark_width, self.height

        self.graphics.save_context()
        self.graphics.translate(self.width - self.drop_mark_width + 0.5, 0)

        self.graphics.move_to(0, 5)
        self.graphics.line_to(0, h - 5)
        self.graphics.stroke("#888")

        self.graphics.translate((w - 8) / 2.0, (h - 10) / 2.0 - 5)

        self.graphics.move_to(0, 8)
        self.graphics.line_to(3, 5)
        self.graphics.line_to(6, 8)

        self.graphics.move_to(0, 12)
        self.graphics.line_to(3, 15)
        self.graphics.line_to(6, 12)
        self.graphics.stroke("#666")

        self.graphics.restore_context()
