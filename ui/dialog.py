# - coding: utf-8 -

# Copyright (c) 2011-2012 Media Modifications, Ltd.
# Dual licensed under the MIT or GPL Version 2 licenses.

from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import GObject as gobject

from ui import VBox, HBox, Fixed, Label, Button, ScrollArea
from gi.repository import Pango as pango


class DialogTitle(Label):
    """dialog title - an ordinary label classed out for themeing.
    set the dialog's title_class to use your class"""
    x_align = 0
    y_align = 0
    padding = 10
    margin = [0, 2]
    fill = True
    expand = False

    def __init__(self, markup="", size=16, background_color = "#999", **kwargs):
        Label.__init__(self, markup=markup, size=size,
                       background_color=background_color,
                       **kwargs)

class DialogBox(VBox):
    """the container with dialog title, contents and buttons, classed out for
    themeing. set the dialog's dialog_box_class to use your class"""
    def __init__(self, contents=None, spacing = 0, **kwargs):
        VBox.__init__(self, contents=contents, spacing=spacing, **kwargs)

    def do_render(self):
        self.graphics.rectangle(-0.5, -0.5, self.width, self.height, 5)
        self.graphics.fill_stroke("#eee", "#999", line_width = 5)


class Dialog(Fixed):
    """An in-window message box

    **Signals**

        **on-close** *(sprite, pressed_button)*
        - fired when the window is closed. returns back the label of the button that triggered closing
    """
    __gsignals__ = {
        "on-close": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
    }

    title_class = DialogTitle
    dialog_box_class = DialogBox

    def __init__(self, contents = None,
                 title = None, draggable = True,
                 width = 500,
                 modal = False,
                 **kwargs):
        Fixed.__init__(self, **kwargs)
        self.interactive, self.mouse_cursor = True, False

        #: whether the dialog is modal or not. in case of modality won't be able
        #: to click on other interface elements while dialog is being displayed
        self.modal = modal

        #: dialog content - message and such like
        self.contents = contents

        #: container for description and buttons
        # setting it interactive and filling extents so that they can't be clicked through
        self.box = VBox(contents, interactive=True, mouse_cursor = False)
        def fill_blank():
            self.box.graphics.rectangle(0, 0, self.box.width, self.box.height)
            self.box.graphics.new_path()
        self.box.do_render = fill_blank

        #: the main container box that contains title and contents
        components = []
        self.title_label = None
        if title:
            self.title_label = self.title_class(title)
            components.append(self.title_label)
        components.append(self.box)

        self.main_box = self.dialog_box_class(components, interactive=draggable, draggable=draggable, width=width, padding=0)

        self.connect_child(self.main_box, "on-drag", self.on_drag)
        self._dragged = False

        self.add_child(self.main_box)

        #: fill color for the background when the dialog is modal
        self.background_fill = "#fff"

        #: opacity of the background fill when the dialog is modal
        self.background_opacity = .5

        #: initial centered position as a tuple in lieu of scale_x, scale_y
        self.pre_dragged_absolute_position = None


    def on_drag(self, sprite, event):
        self.main_box.x = max(min(self.main_box.x, self.width - 10), -self.main_box.width + 10 )
        self.main_box.y = max(min(self.main_box.y, self.height - 10), -self.main_box.height + 10 )
        self._dragged = True


    def __setattr__(self, name, val):
        if name in ("width",) and hasattr(self, "main_box"):
            self.main_box.__setattr__(name, val)
        else:
            Fixed.__setattr__(self, name, val)

        if name == "contents" and hasattr(self, "box"):
            self.box.add_child(val)

    def show(self, scene):
        """show the dialog"""
        scene.add_child(self)

    def resize_children(self):
        if not self._dragged:
            if not self.pre_dragged_absolute_position:
                self.main_box.x = (self.width - self.main_box.width) * self.x_align
                self.main_box.y = (self.height - self.main_box.height) * self.y_align
            else:
                #put it right where we want it
                self.main_box.x = self.pre_dragged_absolute_position[0] - (self.main_box.width * 0.5)
                self.main_box.y = self.pre_dragged_absolute_position[1] - (self.main_box.height * 0.5)
                #but ensure it is in bounds, cause if it ain't you could be in a world of modal pain
                self.on_drag( None, None )
        else:
            self.on_drag(self.main_box, None)

    def close(self, label = ""):
        self.emit("on-close", label)
        scene = self.get_scene()
        if scene:
            scene.remove_child(self)


    def do_render(self):
        if self.modal:
            self.graphics.rectangle(0, 0, self.width + 1, self.height + 1)
            self.graphics.fill(self.background_fill, self.background_opacity)
        else:
            self.graphics.clear()



class ConfirmationDialog(Dialog):
    def __init__(self, title, message, affirmative_label,
                 decline_label = "Cancel", width=500, modal = False):
        Dialog.__init__(self, title = title, width = width, modal=modal)

        scrollbox = ScrollArea(Label(markup=message, padding=5, overflow=pango.WrapMode.WORD),
                                    scroll_horizontal = False,
                                    border = 0,
                                    margin=2, margin_right=3,
                                    height = 150)

        affirmative = Button(affirmative_label, id="affirmative_button")
        affirmative.connect("on-click", self._on_button_click)
        decline = Button(decline_label, id="decline_button")
        decline.connect("on-click", self._on_button_click)

        self.box.contents = VBox([scrollbox, HBox([HBox(), decline, affirmative], expand=False, padding=10)])

    def _on_button_click(self, button, event):
        approved = button.id == "affirmative_button"
        self.close(approved)
