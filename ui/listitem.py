# - coding: utf-8 -

# Copyright (c) 2011-2012 Media Modifications, Ltd.
# Dual licensed under the MIT or GPL Version 2 licenses.

from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import GObject as gobject

from ui import Widget, Label, TreeModel, TreeModelRow, Entry, VBox, HBox, Button, ScrollArea, Fixed
from lib import graphics
from bisect import bisect
from gi.repository import Pango as pango

class Renderer(Widget):
    x_align = 0   #: horizontal alignment of the cell contents
    y_align = 0.5 #: vertical alignment of the cell contents

    def __init__(self, editable = False, **kwargs):
        Widget.__init__(self, **kwargs)
        self.editable = editable

        self._target = None
        self._cell = None

    def get_min_size(self, row):
        return max(self.min_width or 0, 10), max(self.min_height or 0, 10)

    def get_mouse_cursor(self):
        return False

    def show_editor(self, target, cell, event = None):
        pass

    def hide_editor(self):
        pass

    def set_data(self, data):
        pass

    def restore_data(self):
        pass

class ImageRenderer(Renderer):
    def __init__(self, **kwargs):
        Renderer.__init__(self, **kwargs)

    def render(self, context, w, h, data, state, enabled):
        if data:
            context.save()
            context.translate((w - data.width) * self.x_align, (h - data.height) * self.y_align)
            data._draw(context)
            context.restore()



class LabelRenderer(Renderer):
    padding = 5
    expand = True

    color = "#333" #: font color
    color_current = "#fff" #: font color when the row is selected

    color_disabled = "#aaa" #: color of the text when item is disabled
    color_disabled_current = "#fff" #: selected row font color when item is disabled

    def __init__(self, **kwargs):
        Renderer.__init__(self, **kwargs)
        self.label = Label(padding = self.padding, overflow = pango.EllipsizeMode.END)
        self.label.graphics = self.graphics
        self._prev_dict = {}

        self._editor = Entry()


    def __setattr__(self, name, val):
        Widget.__setattr__(self, name, val)
        if name.startswith("padding") and hasattr(self, "label"):
            setattr(self.label, name, val)

    def get_min_size(self, row):
        return max(self.min_width or 0, 10), max(self.min_height or 0, self.label.vertical_padding + 15)

    def get_mouse_cursor(self):
        if self.editable:
            return gdk.CursorType.XTERM
        return False

    def show_editor(self, target, cell, event = None):
        if not self.editable:
            return

        self._target, self._cell = target, cell
        target.add_child(self._editor)

        self._editor.x, self._editor.y = cell['x'], cell['y']
        self._editor.alloc_w, self._editor.alloc_h = cell['width'], cell['height']
        self._editor.text = cell['data']

        if event:
            event.x, event.y = self._editor.from_scene_coords(event.x, event.y)
            self._editor._Entry__on_mouse_down(self._editor, event)
        self._target = target
        self._editor.grab_focus()

    def hide_editor(self):
        if self._target:
            self._target.remove_child(self._editor)
            self._target.rows[self._cell['row']][self._cell['col']] = self._editor.text
            self._target = self._cell = None

    def set_data(self, data):
        # apply data to the renderer
        self._prev_dict = {}
        if isinstance(data, dict):
            for key, val in data.iteritems():
                self._prev_dict[key] = getattr(self.label, key, "") #store original state
                setattr(self.label, key, val)
        else:
            self.label.text = data

    def restore_data(self):
        # restore renderer's data representation to the original state
        for key, val in self._prev_dict.iteritems():
            setattr(self.label, key, val)


    def render(self, context, w, h, data, state, enabled=True):
        self.label.alloc_w = w
        if enabled:
            self.label.color = self.color_current if state == "current" else self.color
        else:
            self.label.color = self.color_disabled_current if state == "current" else self.color_disabled

        context.save()
        context.translate((w - self.label.width) * self.x_align, (h - self.label.height) * self.y_align)
        self.label._draw(context)
        context.restore()



class ListView(Widget):
    """a widget for displaying selection lists"""
    __gsignals__ = {
        "on-select": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        "on-change": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
    }

    #: renderer classes that get initiated upon listitem construction
    renderers = [LabelRenderer]

    padding = 5

    background_current = "#7AA1D2" #: color of the selected row
    background_current_disabled = "#ddd"   #: background of disabled row
    background_hover =  "#efefef"  #: color of the mouse hovered row
    background_odd =  ""           #: background of the odd rows. Set to None to avoid painting
    background_even = "#f9f9f9"    #: background of the even rows. Set to None to avoid painting

    tooltip_position = "mouse"

    def __init__(self, rows = [], renderers = None,
                 select_on_drag = False, spacing=0,
                 row_height = None, **kwargs):
        Widget.__init__(self, **kwargs)
        self.interactive, self.can_focus = True, True
        self.mouse_cursor = False

        #: should an item be select upon drag motion. By default select happens
        #: only when clicking
        self.select_on_drag = select_on_drag

        #: the list of text strings available for selection
        self.rows = rows

        #: row height in pixels. if specified, will be using that instead of
        #: asking cell renderers. defaults to None.
        self.row_height = row_height

        self._search_string = ""
        self._search_timeout = None

        self._row_pos = None # cache of row positions

        self._hover_row = None

        #: currently selected item
        self.current_row = None


        if renderers is not None:
            self.renderers = renderers
        else:
            self.renderers = [renderer() for renderer in self.renderers]

        self.connect("on-mouse-move", self.__on_mouse_move)
        self.connect("on-mouse-down", self.__on_mouse_down)
        self.connect("on-mouse-out", self.__on_mouse_out)


        self.connect("on-mouse-scroll", self.on_mouse_scroll)
        self.connect("on-double-click", self.on_doubleclick)
        self.connect("on-key-press", self.__on_key_press)

        self.connect("on-render", self.__on_render)


    def __setattr__(self, name, val):
        new_rows = False
        if name == "rows":
            if isinstance(val, TreeModel) == False:
                val = TreeModel(val)

            if getattr(self, "rows", None):
                for listener in getattr(self, "_data_change_listeners", []):
                    self.rows.disconnect(listener)
            if getattr(self, "rows", None):
                new_rows = True
            self.queue_resize()

        row_changed = name == "current_row" and val != self.__dict__.get(name, 'hamster_no_value_really')
        Widget.__setattr__(self, name, val)

        if new_rows:
            self._on_row_deleted(self.rows)

        if row_changed:
            self.emit("on-change", val if val else None)

        if name == "rows":
            changed = self.rows.connect("row-changed", self._on_row_changed)
            deleted = self.rows.connect("row-deleted", self._on_row_deleted)
            inserted = self.rows.connect("row-inserted", self._on_row_inserted)
            self._data_change_listeners = [changed, deleted, inserted]
        elif name == "padding":
            for renderer in self.renderers:
                renderer.padding = val
        elif name == "current_row" and val:
            self.scroll_to_row(val)

    @property
    def current_index(self):
        """returns index of the current row, or -1 if no row is selected"""
        if not self.rows or not self.current_row:
            return -1
        return self.rows.index(self.current_row)

    def get_min_size(self):
        if not self.rows:
            return 0, 0

        # ask for 10 * <wherever the last row is> + height
        w = 0
        for renderer in self.renderers:
            renderer_w, renderer_h = renderer.get_min_size(None)
            w += renderer_w

        return w, self._get_row_pos()[-1] + self.get_row_height()

    def get_col_at_x(self, x):
        col_x, mouse_cursor = 0, False
        for renderer, width in zip(self.renderers, self._get_col_widths()):
            if col_x <= x <= col_x + width:
                return renderer
            col_x += width


    def select(self, row):
        """select row. accepts either the row object or the label of it's first column"""
        if isinstance(row, TreeModelRow):
            self.current_row = row
            return

        # otherwise go for search
        for row in self.rows:
            if row[0] == row:
                self.current_row = row
                return

    def __on_mouse_move(self, sprite, event):
        if not self.rows:
            return

        self._hover_row = self.rows[self.get_row_at_y(event.y)]
        if self.select_on_drag and gdk.ModifierType.BUTTON1_MASK & event.state:
            self.current_row = self._hover_row

        # determine mouse cursor
        col = self.get_col_at_x(event.x)
        if col:
            self.mouse_cursor = col.get_mouse_cursor()


    def __on_mouse_down(self, sprite, event):
        if not self.rows:
            return

        self.current_row = self.rows[self.get_row_at_y(event.y)]
        for renderer in self.renderers:
            renderer.hide_editor()

        cell = self.get_cell(event.x, event.y)

        event.x, event.y = self.to_scene_coords(event.x, event.y)
        cell['renderer'].show_editor(self, cell, event)

    def __on_mouse_out(self, sprite):
        self._hover_row = None

    def select_cell(self, row_num, col_num):
        if not self.enabled:
            return

        self.grab_focus()
        self.current_row = self.rows[row_num]
        if 0 < col_num < len(self.renderers):
            if self.renderers[col_num].editable:
                col_x = 0
                for i, w in enumerate(self._get_col_widths()):
                    if i == col_num:
                        break
                    col_x += w

                # somewhat a mad way to get the cell data for editor
                cell = self.get_cell(col_x + 1,
                                     row_num * self.get_row_height() + 1)

                self.renderers[col_num].show_editor(self, cell)

    def get_cell(self, x, y):
        """get row number, col number, renderer, and extents"""

        target_renderer = self.get_col_at_x(x)

        col_x = 0
        for col, width in zip(self.renderers, self._get_col_widths()):
            if col == target_renderer:
                break
            col_x += width

        row = self.get_row_at_y(y)
        col = self.renderers.index(target_renderer)

        row_height = self.get_row_height()

        return {
            'data': self.rows[row][col],
            'renderer': target_renderer,
            'row': row,
            'col': col,
            'x': col_x,
            'y': self.get_row_position(self.rows[row]),
            'width': width,
            'height': row_height
        }



    def on_mouse_scroll(self, sprite, event):
        direction  = 1 if event.direction == gdk.ScrollDirection.DOWN else -1
        parent = self.parent
        while parent and hasattr(parent, "vscroll") == False:
            parent = parent.parent

        y = self.y if hasattr(self.parent.parent, "vscroll") else self.parent.y

        if parent:
            parent.scroll_y(y - parent.step_size * direction)


    def _get_col_widths(self):
        """determine column widths and minimum row height"""
        widths = []

        remaining_space = self.width
        interested_cols = []
        for renderer in self.renderers:
            remaining_space = remaining_space - renderer.get_min_size(None)[0]

            if renderer.expand:
                interested_cols.append(renderer)

        # in order to stay pixel sharp we will recalculate remaining bonus
        # each time we give up some of the remaining space
        bonus = 0
        if remaining_space > 0 and interested_cols:
            bonus = int(remaining_space / len(interested_cols))

        for renderer in self.renderers:
            w = renderer.get_min_size(None)[0]
            if renderer in interested_cols:
                w += bonus

                interested_cols.remove(renderer)
                remaining_space -= bonus
                if interested_cols:
                    bonus = int(float(remaining_space) / len(interested_cols))

            widths.append(w)

        return widths

    def get_row_height(self):
        row_height = self.row_height or 0
        if not row_height:
            for renderer in self.renderers:
                row_height = max(row_height, renderer.get_min_size(None)[1])
        return row_height

    def get_visible_range(self):
        """returns index of the first and last row visible"""
        # suboptimal workaround for case when the list is packed in a vbox and then in a scrollbox
        # TODO - generalize and sniff out the actual crop area
        if self.parent and self.parent.parent and self.parent.parent and isinstance(self.parent.parent.parent, ScrollArea):
            scrollbox = self.parent.parent
            list_y = self.y + self.parent.y
        else:
            list_y = self.y
            scrollbox = self.parent

        row_height = self.get_row_height()
        first_row = int(-list_y / row_height)
        last_row = int((-list_y + scrollbox.height) / row_height)

        return max(first_row, 0), min(last_row + 1, len(self.rows))


    def _draw(self, context, opacity=1, *args, **kwargs):

        self.get_visible_range()

        col_widths = self._get_col_widths()
        width = self.width

        row_height = self.get_row_height()

        g = graphics.Graphics(context)

        x, y = 0, 0
        Widget._draw(self, context, opacity, *args, **kwargs)
        editor = None

        # suboptimal workaround for case when the list is packed in a vbox and then in a scrollbox
        # TODO - generalize and sniff out the actual crop area
        if self.parent and self.parent.parent and self.parent.parent and isinstance(self.parent.parent.parent, ScrollArea):
            scrollbox = self.parent.parent
            list_y = self.y + self.parent.y
        else:
            list_y = self.y
            scrollbox = self.parent

        g.rectangle(0, 0, scrollbox.width, scrollbox.height)
        g.clip()

        for row_idx in range(*self.get_visible_range()):
            y = row_idx * row_height
            row = self.rows[row_idx]


            state = "normal"
            if row == self.current_row:
                state = "current"
            elif row == self._hover_row:
                state = "highlight"

            context.save()
            context.translate(x, y + self.y)
            context.rectangle(0, 0, width, row_height)

            self.paint_row_background(g, row_idx, state, self.enabled)
            context.clip()

            col_x = 0
            for i, (data, renderer, col_width) in enumerate(zip(row, self.renderers, col_widths)):
                renderer.set_data(data)
                renderer.render(context, col_width, row_height, row[i], state, self.enabled)
                renderer.restore_data()
                context.translate(col_width, 0)

                # TODO - put some place else
                if renderer._cell and hasattr(renderer, "_editor") and renderer._cell['col'] == i:
                    renderer._editor.x, renderer._editor.alloc_w = col_x, col_width - 1
                    editor = renderer._editor

                col_x += col_width

            context.restore()


        if editor:
            # repaint editor as it is stepped all over
            context.save()
            context.translate(0, self.y)
            editor._draw(context, parent_matrix = self.get_matrix())
            context.restore()


    def paint_row_background(self, graphics, row_idx, state, enabled=True):
        """this function fills row background. the rectangle has been already
        drawn, so all that is left is fill. The graphics property is instance
        of graphics.Graphics for the current context, and state is one of
        normal, highlight and current"""
        if self.background_hover and state == "highlight" and self.enabled:
            graphics.fill_preserve(self.background_hover)
        elif self.background_current and state == "current" and self.enabled:
            graphics.fill_preserve(self.background_current)
        elif self.background_current_disabled and state == "current" and not self.enabled:
            graphics.fill_preserve(self.background_current_disabled)
        elif row_idx % 2 == 1 and self.background_even:
            graphics.fill_preserve(self.background_even)
        elif row_idx % 2 == 0 and self.background_odd:
            graphics.fill_preserve(self.background_odd)


    def _get_row_pos(self):
        if self._row_pos:
            return self._row_pos
        row_height = self.get_row_height()

        w, h, pos = 0, 0, []
        for row in self.rows:
            pos.append(h)
            h = h + row_height

        self._row_pos = pos

        return pos

    def get_row_at_y(self, y):
        return bisect(self._get_row_pos(), y) - 1

    def get_row_position(self, row):
        if row in self.rows:
            return self._get_row_pos()[self.rows.index(row)]
        return 0

    def on_doubleclick(self, sprite, event):
        if self.current_row:
            self.emit("on-select", self.current_row)

    def _on_row_changed(self, model, row_idx):
        self._row_pos = None
        if self.parent:
            self.parent.queue_resize()

    def _on_row_deleted(self, model):
        if self.current_row and self.current_row not in self.rows:
            self.current_row = None
        if self._hover_row and self._hover_row not in self.rows:
            self._hover_row = None

        self._row_pos = None
        self.parent.queue_resize()

    def _on_row_inserted(self, row_idx):
        self._row_pos = None
        self.parent.queue_resize()

    def __on_key_press(self, sprite, event):
        if self.current_row:
            idx = self.rows.index(self.current_row)
        else:
            idx = -1

        if event.keyval == gdk.KEY_Down:
            idx = min(idx + 1, len(self.rows) - 1)
        elif event.keyval == gdk.KEY_Up:
            idx = max(idx - 1, 0)
        elif event.keyval == gdk.KEY_Home:
            idx = 0
        elif event.keyval == gdk.KEY_End:
            idx = len(self.rows) - 1
        elif event.keyval == gdk.KEY_Return:
            self.emit("on-select", self.current_row)

        elif event.string:
            if self._search_timeout: # cancel the previous one!
                gobject.source_remove(self._search_timeout)
            self._search_string += event.string

            def clear_search():
                self._search_string = ""

            self._search_timeout = gobject.timeout_add(500, clear_search)
            idx = self.find(self._search_string, fragment=True)


        if 0 <= idx < len(self.rows):
            self.current_row = self.rows[idx]



    def find(self, label, fragment = False):
        """looks for a label in the list item. starts from current position including.
           if does not find anything, will wrap around.
           if an item matches, will select it.
        """
        start = self.rows.index(self.current_row) if self.current_row else None
        i = start + 1 if start is not None and start + 1 < len(self.rows) else 0

        def label_matches(row, label):
            row_label = self.rows[i][0]
            if isinstance(row_label, dict):
                row_label = row_label.get("text", pango.parse_markup(row_label.get("markup", ""), -1, "0")[2])
            if fragment:
                return row_label.lower().startswith(label.lower())
            else:
                return row_label.lower() == label.lower()

        while i != start:
            if label_matches(self.rows[i], label):
                return i

            i += 1
            if i >= len(self.rows):
                i = 0
                if start == None:
                    break

        # checking if we have wrapped around (so this is the only match
        if label_matches(self.rows[i], label):
            return i

        return -1


    def scroll_to_row(self, label):
        # find the scroll area if any and scroll where the row is
        parent = self.parent
        while parent and hasattr(parent, "vscroll") == False:
            parent = parent.parent

        if not parent:
            return

        area, viewport = parent, parent.viewport
        label_y = self.get_row_position(label)

        label_h = 0

        # if parent has not been allocated height yet, there is something funky going on
        # TODO - demistify
        if self.parent.height > 0:
            for renderer in self.renderers:
                label_h = max(label_h, renderer.get_min_size(label)[1])

        y = 0 if hasattr(self.parent.parent, "vscroll") else self.y
        if label_y + self.y + self.parent.y < 0:
            area.scroll_y(-label_y - y)

        if label_y + label_h + self.y + self.parent.y > parent.height:
            area.scroll_y(-label_y - label_h - y + parent.height)


    def __on_render(self, widget):
        # mark that the whole thing can be interacted with
        self.graphics.rectangle(0, 0, self.width, self.height)
        self.graphics.new_path()


class ListHeader(Fixed):
    padding = 0
    def __init__(self, expand=False, **kwargs):
        Fixed.__init__(self, expand=expand, **kwargs)
        self.connect("on-render", self.__on_render)

    def get_min_size(self):
        w, h = self.min_width or 0, self.min_height or 0
        for widget in self.sprites:
            min_w, min_h = widget.get_min_size()
            w = w + min_w
            h = max(h, min_h)
        return w, h

    def size_cols(self, col_widths):
        if not self.visible:
            return

        x = 0
        for i, w, in enumerate(col_widths):

            if i >= len(self.sprites):
                break

            self.sprites[i].x = x
            self.sprites[i].alloc_w = min(w, self.width - x)
            self.sprites[i].alloc_h = self.height
            x += w

    def __on_render(self, widget):
        if not self.parent:
            return

        # TODO - wrong control distribution, but the headers are lagging one
        # step behind in width otherwise

        if hasattr(self.parent, "list_view"):
            list_view = self.parent.list_view
        else:
            list_view = self.parent.parent.parent.parent.list_view

        self.size_cols(list_view._get_col_widths())

class ListHeaderCol(Button):
    x_align = 0

    def __init__(self, text):
        Button.__init__(self, text)
        self.color = "#444"
        self.get_min_size = lambda: (0, Label.get_min_size(self)[1])

    def do_render(self):
        if self.state == "normal":
            self.graphics.fill_area(0, 0, self.width, self.height, "#EDECEB")
        else:
            Button.do_render(self)


class ListItem(VBox):
    """a list view with headers and an optional scroll when rows don't fit"""
    __gsignals__ = {
        "on-select": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        "on-change": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        "on-header-click": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT,)),
    }

    fixed_headers = True

    class_headers_container = ListHeader #: list headers container class
    class_header_col = ListHeaderCol #: list headers column class
    class_list_view = ListView #: list view class
    class_scroll_area = ScrollArea #: scroll area class


    def __init__(self, rows = [], renderers = None, headers = None,
                 select_on_drag = False, spacing = 0, scroll_border = 1,
                 row_height = None, fixed_headers = None, **kwargs):
        VBox.__init__(self, **kwargs)

        self.list_view = self.class_list_view(rows=rows)
        self.list_view.connect("on-render", self._on_list_render)

        for event in ("on-select", "on-change", "on-mouse-down",
                      "on-mouse-up", "on-click"):
            self.list_view.connect(event, self._forward_event, event)


        if renderers is not None:
            self.renderers = renderers
        self.select_on_drag = select_on_drag
        self.spacing = spacing
        self.row_height = row_height

        self.header_container = self.class_headers_container()
        self.headers = headers

        if fixed_headers is not None:
            self.fixed_headers = fixed_headers

        self.scrollbox = self.class_scroll_area(border = scroll_border)

        if self.fixed_headers:
            self.scrollbox.add_child(self.list_view)
            self.add_child(self.header_container, self.scrollbox)
        else:
            self.scrollbox.add_child(VBox([self.header_container, self.list_view], spacing=0))
            self.add_child(self.scrollbox)

    def __setattr__(self, name, val):
        # forward useful attributes to the list view
        if name in ("rows", "renderers", "select_on_drag", "spacing",
                    "row_height", "current_row", "_hover_row"):
            setattr(self.list_view, name, val)
            return


        if self.__dict__.get(name, 'hamster_no_value_really') == val:
            return
        VBox.__setattr__(self, name, val)


        if name == "scroll_border":
            self.scrollbox.border = val
        elif name == "headers":
            self._update_headers()

    def __getattr__(self, name):
        if name in ("rows", "renderers", "select_on_drag", "spacing",
                    "row_height", "current_row", "_hover_row",
                    "current_index", "_hover_row", "grab_focus",
                    "select_cell", "rows"):
            return getattr(self.list_view, name)

        if name in self.__dict__:
            return self.__dict__.get(name)
        else:
            raise AttributeError, "ListItem has no attribute '%s'" % name


    def resize_children(self):
        self.scrollbox.alloc_w = self.width
        self.scrollbox.resize_children()
        self.scrollbox.viewport.resize_children()
        VBox.resize_children(self)


    def get_list_size(self):
        return self.list_view.width, self.list_view.height

    def _update_headers(self):
        self.header_container.clear()
        for header in self.headers or []:
            if isinstance(header, basestring):
                header = self.class_header_col(header)
            self.header_container.add_child(header)
            self.header_container.connect_child(header, "on-click", self._on_header_clicked)
        self.header_container.size_cols(self.list_view._get_col_widths())

    def _on_list_render(self, list):
        self.header_container.size_cols(self.list_view._get_col_widths())

    def _on_header_clicked(self, header_col, event):
        self.emit("on-header-click", header_col, event)

    def _forward_event(self, list, info, event_name):
        self.emit(event_name, info)
