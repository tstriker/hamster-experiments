# - coding: utf-8 -

# Copyright (c) 2011-2012 Media Modifications, Ltd.
# Dual licensed under the MIT or GPL Version 2 licenses.

from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import GObject as gobject

import re
from lib import graphics

from ui import Bin, Viewport, ScrollArea, Button, Table, Label, Widget
from gi.repository import Pango as pango


class Entry(Bin):
    """A text entry field"""
    __gsignals__ = {
        "on-change": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        "on-position-change": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
    }

    padding = 5

    mouse_cursor = gdk.CursorType.XTERM

    font_desc = "Sans Serif 10" #: pango.FontDescription to use for the label

    color = "#000" #: font color
    cursor_color = "#000" #: cursor color
    selection_color = "#A8C2E0" #: fill color of the selection region

    def __init__(self, text="", draw_border = True,  valid_chars = None,
                 validate_on_type = True, single_paragraph = True,
                 text_formatter = None, alignment = None,
                 font_desc = None, **kwargs):
        Bin.__init__(self, **kwargs)

        self.display_label = graphics.Label(color=self.color)

        self.viewport = Viewport(self.display_label)
        self.viewport.connect("on-render", self.__on_viewport_render)

        self.add_child(self.viewport)

        self.can_focus = True

        self.interactive = True

        self.editable = True

        #: current cursor position
        self.cursor_position = None

        #: start position of the selection
        self.selection_start = 0

        #: end position of the selection
        self.selection_end = 0

        if font_desc is not None:
            self.font_desc = font_desc
        self.display_label.font_desc = self.font_desc

        #: text alignment in the entry
        self.alignment = alignment

        #: if True, a border will be drawn around the input element
        self.draw_border = draw_border

        #self.connect("on-key-press", self.__on_key_press)
        self.connect("on-mouse-down", self.__on_mouse_down)
        self.connect("on-double-click", self.__on_double_click)
        self.connect("on-triple-click", self.__on_triple_click)
        self.connect("on-blur", self.__on_blur)
        self.connect("on-focus", self.__on_focus)

        self.connect_after("on-render", self.__on_render)

        self._scene_mouse_move = None
        self._scene_mouse_up = None
        self._selection_start_position = None
        self._letter_positions = []

        #: a string, function or regexp or valid chars for the input
        #: in case of function, it will receive the string to be tested
        #: as input and expects to receive back a boolean of whether the string
        #: is valid or not
        self.valid_chars = valid_chars

        #: should the content be validate right when typing and invalid version prohibited
        self.validate_on_type = validate_on_type

        #: function to style the entry text - change color and such
        #: the function receives one param - the text, and must return
        #: processed text back. will be using original text if the function
        #: does not return anything.
        #: Note: this function can change only the style, not the actual content
        #: as the latter will mess up text selection because of off-sync between
        #: the label value and what is displayed
        self.text_formatter = text_formatter if text_formatter else self.text_formatter


        #: should the text input support multiple lines
        self.single_paragraph = single_paragraph

        self.update_text(text)
        self._last_good_value = text # last known good value of the input


    def __setattr__(self, name, val):
        if name == "cursor_position" and not self.editable:
            val = None

        if self.__dict__.get(name, "hamster_graphics_no_value_really") == val:
            return

        if name == "text":
            val = val or ""
            if getattr(self, "text_formatter", None):
                markup = self.text_formatter(val.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

            if markup:
                self.display_label.markup = markup
            else:
                self.display_label.text = val

        Bin.__setattr__(self, name, val)

        if name == "text":
            self.emit("on-change", val)

        if name in("font_desc", "alignment", "single_paragraph", "color"):
            setattr(self.display_label, name, val)

        elif name == "alloc_w" and getattr(self, "overflow", False) != False and hasattr(self, "display_label"):
            self.display_label.width = val - self.horizontal_padding

        elif name == "overflow" and val != False and hasattr(self, "display_label"):
            if val in (pango.WrapMode.WORD, pango.WrapMode.WORD_CHAR, pango.WrapMode.CHAR):
                self.display_label.wrap = val
                self.display_label.ellipsize = None
            elif val in (pango.EllipsizeMode.START, pango.EllipsizeMode.END):
                self.display_label.wrap = None
                self.display_label.ellipsize = val

        if name == "cursor_position":
            self.emit("on-position-change", val)

    def get_min_size(self):
        return self.min_width or 0, max(self.min_height, self.display_label.height + self.vertical_padding)

    def text_formatter(self, text):
        return None

    def test_value(self, text):
        if not self.valid_chars:
            return True
        elif isinstance(self.valid_chars, basestring):
            return set(text) - set(self.valid_chars) == set([])
        elif hasattr(self.valid_chars, '__call__'):
            return self.valid_chars(text)
        else:
            return False

    def get_height_for_width_size(self):
        return self.get_min_size()


    def update_text(self, text):
        """updates the text field value and the last good known value,
        respecting the valid_chars and validate_on_type flags"""
        text = text or ""

        if self.test_value(text):
            self.text = text
            if self.validate_on_type:
                self._last_good_value = text
        elif not self.validate_on_type:
            self.text = text
        else:
            return False

        self.viewport.height = self.display_label.height
        if self.cursor_position is None:
            self.cursor_position = len(text)

        return True


    def _index_to_pos(self, index):
        """give coordinates for the position in text. maps to the
        display_label's pango function"""
        ext = self.display_label._test_layout.index_to_pos(index)
        extents = [e / pango.SCALE for e in (ext.x, ext.y, ext.width, ext.height)]
        return extents

    def _xy_to_index(self, x, y):
        """from coordinates caluculate position in text. maps to the
        display_label's pango function"""
        x = x - self.display_label.x - self.viewport.x
        index = self.display_label._test_layout.xy_to_index(int(x*pango.SCALE), int(y*pango.SCALE))
        return index[0] + index[1]


    def __on_focus(self, sprite):
        self._last_good_value = self.text

    def __on_blur(self, sprite):
        self._edit_done()

    def _edit_done(self):
        if self.test_value(self.text):
            self._last_good_value = self.text
        else:
            self.update_text(self._last_good_value)

    def __on_mouse_down(self, sprite, event):
        i = self._xy_to_index(event.x, event.y)

        self.selection_start = self.selection_end = self.cursor_position = i
        self._selection_start_position = self.selection_start

        scene = self.get_scene()
        if not self._scene_mouse_up:
            self._scene_mouse_up = scene.connect("on-mouse-up", self._on_scene_mouse_up)
            self._scene_mouse_move = scene.connect("on-mouse-move", self._on_scene_mouse_move)

    def __on_double_click(self, sprite, event):
        # find the word
        cursor = self.cursor_position
        self.selection_start = self.text.rfind(" ", 0, cursor) + 1

        end = self.text.find(" ", cursor)
        self.cursor_position = self.selection_end = end if end > 0 else len(self.text)


    def __on_triple_click(self, sprite, event):
        self.selection_start = 0
        self.cursor_position = self.selection_end = len(self.text)

    def _on_scene_mouse_up(self, scene, event):
        scene.disconnect(self._scene_mouse_up)
        scene.disconnect(self._scene_mouse_move)
        self._scene_mouse_up = self._scene_mouse_move = None

    def _on_scene_mouse_move(self, scene, event):
        if self.focused == False:
            return

        # now try to derive cursor position
        x, y = self.display_label.from_scene_coords(event.x, event.y)
        x = x + self.display_label.x + self.viewport.x
        i = self._xy_to_index(x, y)

        self.cursor_position = i
        if self.cursor_position < self._selection_start_position:
            self.selection_start = self.cursor_position
            self.selection_end = self._selection_start_position
        else:
            self.selection_start = self._selection_start_position
            self.selection_end = self.cursor_position

    def _get_iter(self, index = 0):
        """returns iterator that has been run till the specified index"""
        iter = self.display_label._test_layout.get_iter()
        for i in range(index):
            iter.next_char()
        return iter

    def _do_key_press(self, event):
        """responding to key events"""
        key = event.keyval
        shift = event.state & gdk.ModifierType.SHIFT_MASK
        control = event.state & gdk.ModifierType.CONTROL_MASK

        if not self.editable:
            return

        def emit_and_return():
            self.emit("on-key-press", event)
            return


        if self.single_paragraph and key == gdk.KEY_Return:
            self._edit_done()
            return emit_and_return()

        self._letter_positions = []

        if key == gdk.KEY_Left:
            if shift and self.cursor_position == 0:
                return emit_and_return()

            if control:
                self.cursor_position = self.text[:self.cursor_position].rstrip().rfind(" ") + 1
            else:
                self.cursor_position -= 1

            if shift:
                if self.cursor_position < self.selection_start:
                    self.selection_start = self.cursor_position
                else:
                    self.selection_end = self.cursor_position
            elif self.selection_start != self.selection_end:
                self.cursor_position = self.selection_start

        elif key == gdk.KEY_Right:
            if shift and self.cursor_position == len(self.text):
                return emit_and_return()

            if control:
                prev_pos = self.cursor_position
                self.cursor_position = self.text[self.cursor_position:].lstrip().find(" ")
                if self.cursor_position == -1:
                    self.cursor_position = len(self.text)
                else:
                    self.cursor_position += prev_pos + 1
            else:
                self.cursor_position += 1

            if shift:
                if self.cursor_position > self.selection_end:
                    self.selection_end = self.cursor_position
                else:
                    self.selection_start = self.cursor_position
            elif self.selection_start != self.selection_end:
                self.cursor_position = self.selection_end

        elif key == gdk.KEY_Up and self.single_paragraph == False:
            iter = self._get_iter(self.cursor_position)

            if str(iter.get_line_readonly()) != str(self.display_label._test_layout.get_line_readonly(0)):
                char_pos = iter.get_char_extents().x
                char_line = str(iter.get_line_readonly())

                # now we run again to run until previous line
                prev_iter, iter = self._get_iter(), self._get_iter()
                prev_line = None
                while str(iter.get_line_readonly()) != char_line:
                    if str(prev_line) != str(iter.get_line_readonly()):
                        prev_iter = iter.copy()
                        prev_line = iter.get_line_readonly()
                    iter.next_char()

                index = prev_iter.get_line_readonly().x_to_index(char_pos - prev_iter.get_char_extents().x)
                index = index[1] + index[2]

                self.cursor_position = index

                if shift:
                    if self.cursor_position < self.selection_start:
                        self.selection_start = self.cursor_position
                    else:
                        self.selection_end = self.cursor_position
                elif self.selection_start != self.selection_end:
                    self.cursor_position = self.selection_start


        elif key == gdk.KEY_Down and self.single_paragraph == False:
            iter = self._get_iter(self.cursor_position)
            char_pos = iter.get_char_extents().x

            if iter.next_line():
                index = iter.get_line_readonly().x_to_index(char_pos - iter.get_char_extents().x)
                index = index[1] + index[2]
                self.cursor_position = index

                if shift:
                    if self.cursor_position > self.selection_end:
                        self.selection_end = self.cursor_position
                    else:
                        self.selection_start = self.cursor_position
                elif self.selection_start != self.selection_end:
                    self.cursor_position = self.selection_end


        elif key == gdk.KEY_Home:
            if self.single_paragraph or control:
                self.cursor_position = 0
                if shift:
                    self.selection_end = self.selection_start
                    self.selection_start = self.cursor_position
            else:
                iter = self._get_iter(self.cursor_position)
                line = str(iter.get_line_readonly())

                # find the start of the line
                iter = self._get_iter()
                while str(iter.get_line_readonly()) != line:
                    iter.next_char()
                self.cursor_position = iter.get_index()

                if shift:
                    start_iter = self._get_iter(self.selection_start)
                    end_iter = self._get_iter(self.selection_end)
                    if str(start_iter.get_line_readonly()) == str(end_iter.get_line_readonly()):
                        self.selection_end = self.selection_start
                        self.selection_start = self.cursor_position
                    else:
                        if self.cursor_position < self.selection_start:
                            self.selection_start = self.cursor_position
                        else:
                            self.selection_end = self.cursor_position

        elif key == gdk.KEY_End:
            if self.single_paragraph or control:
                self.cursor_position = len(self.text)
                if shift:
                    self.selection_start = self.selection_end
                    self.selection_end = self.cursor_position
            else:
                iter = self._get_iter(self.cursor_position)

                #find the end of the line
                line = str(iter.get_line_readonly())
                prev_iter = None

                while str(iter.get_line_readonly()) == line:
                    prev_iter = iter.copy()
                    moved = iter.next_char()
                    if not moved:
                        prev_iter = iter
                        break

                self.cursor_position = prev_iter.get_index()

                if shift:
                    start_iter = self._get_iter(self.selection_start)
                    end_iter = self._get_iter(self.selection_end)
                    if str(start_iter.get_line_readonly()) == str(end_iter.get_line_readonly()):
                        self.selection_start = self.selection_end
                        self.selection_end = self.cursor_position
                    else:
                        if self.cursor_position > self.selection_end:
                            self.selection_end = self.cursor_position
                        else:
                            self.selection_start = self.cursor_position


        elif key == gdk.KEY_BackSpace:
            if self.selection_start != self.selection_end:
                if not self.update_text(self.text[:self.selection_start] + self.text[self.selection_end:]):
                    return emit_and_return()
            elif self.cursor_position > 0:
                if not self.update_text(self.text[:self.cursor_position-1] + self.text[self.cursor_position:]):
                    return emit_and_return()
                self.cursor_position -= 1

        elif key == gdk.KEY_Delete:
            if self.selection_start != self.selection_end:
                if not self.update_text(self.text[:self.selection_start] + self.text[self.selection_end:]):
                    return emit_and_return()
            elif self.cursor_position < len(self.text):
                if not self.update_text(self.text[:self.cursor_position] + self.text[self.cursor_position+1:]):
                    return emit_and_return()
        elif key == gdk.KEY_Escape:
            return emit_and_return()

        #prevent garbage from common save file mneumonic
        elif control and key in (gdk.KEY_s, gdk.KEY_S):
            return emit_and_return()

        # copying and pasting
        elif control and key in (gdk.KEY_c, gdk.KEY_C): # copy
            clipboard = gtk.Clipboard()
            clipboard.set_text(self.text[self.selection_start:self.selection_end])
            return emit_and_return()

        elif control and key in (gdk.KEY_x, gdk.KEY_X): # cut
            text = self.text[self.selection_start:self.selection_end]
            if self.update_text(self.text[:self.selection_start] + self.text[self.selection_end:]):
                clipboard = gtk.Clipboard()
                clipboard.set_text(text)

        elif control and key in (gdk.KEY_v, gdk.KEY_V): # paste
            clipboard = gtk.Clipboard()
            clipboard.request_text(self._on_clipboard_text)
            return emit_and_return()

        elif control and key in (gdk.KEY_a, gdk.KEY_A): # select all
            self.selection_start = 0
            self.cursor_position = self.selection_end = len(self.text)
            return emit_and_return()

        # normal letters
        elif event.string:
            if self.update_text(self.text[:self.selection_start] + event.string + self.text[self.selection_end:]):
                self.cursor_position = self.selection_start + 1
                self.selection_start = self.selection_end = self.cursor_position
            return emit_and_return()
        else: # in case of anything else just go home
            return emit_and_return()


        self.cursor_position = min(max(0, self.cursor_position), len(self.text))
        self.selection_start = min(max(0, self.selection_start), len(self.text))
        self.selection_end = min(max(0, self.selection_end), len(self.text))

        if shift == False:
            self.selection_start = self.selection_end = self.cursor_position

        return emit_and_return()

    def _on_clipboard_text(self, clipboard, text, data):
        if self.update_text(self.text[:self.selection_start] + text + self.text[self.selection_end:]):
            self.selection_start = self.selection_end = self.cursor_position = self.selection_start + len(text)

    def do_render(self):
        self.graphics.set_line_style(width=1)
        self.graphics.rectangle(0.5, -1.5, self.width, self.height + 2, 3)
        if self.draw_border:
            self.graphics.fill_preserve("#fff")
            self.graphics.stroke("#aaa")


    def __on_render(self, sprite):
        self.graphics.rectangle(0, 0, self.width, self.height)
        self.graphics.new_path()

        if self.cursor_position is not None:
            cur_x, cur_y, cur_w, cur_h = self._index_to_pos(self.cursor_position)
            if self.display_label.x + cur_x > self.viewport.width:
                self.display_label.x = min(0, self.viewport.width - cur_x) # cursor visible at the right side
            elif self.display_label.x + cur_x < 0:
                self.display_label.x -= (self.display_label.x + cur_x) # cursor visible at the left side
            elif self.display_label.x < 0 and self.display_label.x + self.display_label.width < self.viewport.width:
                self.display_label.x = min(self.viewport.width - self.display_label.width, 0)

        # align the label within the entry
        if self.display_label.width < self.viewport.width:
            if self.alignment == pango.Alignment.RIGHT:
                self.display_label.x = self.viewport.width - self.display_label.width
            elif self.alignment == pango.Alignment.CENTER:
                self.display_label.x = (self.viewport.width - self.display_label.width) / 2

        #if self.single_paragraph:
        #    self.display_label.y = (self.viewport.height - self.display_label.height) / 2.0
        self.viewport._sprite_dirty = True # so that we get the cursor drawn


    def __on_viewport_render(self, viewport):
        if self.focused == False:
            return

        if self.cursor_position is None:
            return

        cur_x, cur_y, cur_w, cur_h = self._index_to_pos(self.cursor_position)
        cur_x = cur_x + self.display_label.x
        cur_y += self.display_label.y

        viewport.graphics.move_to(cur_x + 0.5, cur_y)
        viewport.graphics.line_to(cur_x + 0.5, cur_y + cur_h)
        viewport.graphics.stroke(self.cursor_color)

        if self.selection_start == self.selection_end:
            return # all done!


        start_x, start_y, start_w, start_h = self._index_to_pos(self.selection_start)
        end_x, end_y, end_w, end_h = self._index_to_pos(self.selection_end)


        iter = self._get_iter(self.selection_start)

        char_exts = iter.get_char_extents()
        cur_x, cur_y = char_exts.x / pango.SCALE, char_exts.y / pango.SCALE + self.display_label.y

        cur_line = None
        for i in range(self.selection_end - self.selection_start):
            prev_iter = pango.LayoutIter.copy(iter)
            iter.next_char()

            line = iter.get_line_readonly()
            if str(cur_line) != str(line): # can't compare layout lines for some reason
                exts = prev_iter.get_char_extents()
                char_exts = [ext / pango.SCALE for ext in (exts.x, exts.y, exts.width, exts.height)]
                viewport.graphics.rectangle(cur_x + self.display_label.x, cur_y,
                                            char_exts[0] + char_exts[2] - cur_x, char_exts[3])

                char_exts = iter.get_char_extents()
                cur_x, cur_y = char_exts.x / pango.SCALE, char_exts.y / pango.SCALE + self.display_label.y

            cur_line = line

        exts = iter.get_char_extents()
        char_exts = [ext / pango.SCALE for ext in  (exts.x, exts.y, exts.width, exts.height)]

        viewport.graphics.rectangle(cur_x + self.display_label.x, cur_y,
                                    char_exts[0] - cur_x, self.display_label.y + char_exts[1] - cur_y + char_exts[3])
        viewport.graphics.fill(self.selection_color)



class TextArea(ScrollArea):
    """A text input field that displays scrollbar when text does not fit anymore"""
    padding = 5

    mouse_cursor = gdk.CursorType.XTERM

    font_desc = "Sans Serif 10" #: pango.FontDescription to use for the label

    color = "#000" #: font color
    cursor_color = "#000" #: cursor color
    selection_color = "#A8C2E0" #: fill color of the selection region

    def __init__(self, text="", valid_chars = None,
                 validate_on_type = True, text_formatter = None,
                 alignment = None, font_desc = None, **kwargs):
        ScrollArea.__init__(self, **kwargs)


        self._entry = Entry(text, single_paragraph=False,
                            draw_border=False, padding=0,
                            valid_chars=valid_chars,
                            validate_on_type=validate_on_type,
                            text_formatter=text_formatter,
                            alignment=alignment,
                            font_desc=font_desc)
        self._entry.get_min_size = self.entry_get_min_size

        self._entry.connect("on-change", self.on_entry_change)
        self._entry.connect("on-position-change", self.on_entry_position_change)
        self.viewport.add_child(self._entry)


    def __setattr__(self, name, val):
        if name in ("text", "valid_chars", "validate_on_type", "text_formatter",
                    "alignment", "font_desc"):
            self._entry.__setattr__(name, val)
        else:
            ScrollArea.__setattr__(self, name, val)


    def on_entry_change(self, entry, text):
        self._entry.viewport.width = self._entry.display_label.width
        #self.display_label.max_width = self.viewport.width
        self._entry.queue_resize()
        self._scroll_to_cursor()

    def on_entry_position_change(self, entry, new_position):
        self._scroll_to_cursor()

    def _scroll_to_cursor(self):
        if self._entry.cursor_position is None or self._entry.cursor_position < 0:
            return

        x, y, w, h = self._entry._index_to_pos(self._entry.cursor_position)

        if x + self._entry.x < 0:
            self.scroll_x(-x)
        if x + self._entry.x + w > self.viewport.width:
            self.scroll_x(self.viewport.width - x - w)

        if y + self._entry.y < 0:
            self.scroll_y(-y)
        if y + self._entry.y + h > self.viewport.height:
            self.scroll_y(self.viewport.height - y - h)


    def entry_get_min_size(self):
        return max(self.min_width, self._entry.display_label.width + self.horizontal_padding), \
               max(self.min_height, self._entry.display_label.height + self.vertical_padding)






class SpinButton(Table):
    """retrieve an integer or floating-point number from the user"""
    padding = 1
    def __init__(self, val = 0, min_val = 0, max_val = 99, **kwargs):
        Table.__init__(self, cols = 2, rows = 2, horizontal_spacing = 2, vertical_spacing = 2, **kwargs)

        self.input = Entry("", draw_border=False)
        self.input.test_value = self._input_test_value
        self.input.connect("on-change", self.on_input_change)
        self.input.fill = True

        self.input.width = 30

        self.up = SpinButtonButton(up=True)
        self.down = SpinButtonButton(up=False)

        #: current value
        self.val = val

        #: minimum allowed value
        self.min_val = min_val

        #: maximum valid value
        self.max_val = max_val

        self.attach(self.input, 0, 1, 0, 2)
        self.attach(self.up, 1, 2, 0, 1)
        self.attach(self.down, 1, 2, 1, 2)

        self.connect_child(self.up, "on-mouse-down", self.on_up_pressed)
        self.connect_child(self.down, "on-mouse-down", self.on_down_pressed)
        self._direction = 0

    def __setattr__(self, name, val):
        Table.__setattr__(self, name, val)
        if name == "val" and val is not None:
            self.input.text = str(val)

    def _input_test_value(self, val):
        try:
            val = int(val)
            return self.min_val <= val <= self.max_val
        except:
            return False

    def on_up_pressed(self, sprite = None, event = None):
        val = self.val + 1 if self.val is not None else 0
        if self._input_test_value(val):
            self.val = val

    def on_down_pressed(self, sprite = None, event = None):
        val = self.val - 1 if self.val is not None else 0

        if self._input_test_value(val):
            self.val = val

    def on_input_change(self, input, val):
        if val:
            self.val = int(val)
        else:
            self.val = None

    def do_render(self):
        self.resize_children()

        self.graphics.rectangle(0.5, 0.5, self.width, self.height, 4)

        self.graphics.move_to(self.up.x - 0.5, 0)
        self.graphics.line_to(self.up.x - 0.5, self.height)

        self.graphics.move_to(self.up.x - 0.5, self.down.y - 0.5)
        self.graphics.line_to(self.width, self.down.y - 0.5)

        self.graphics.stroke("#999")


class SpinButtonButton(Button):
    def __init__(self, up=True, expand=False, width = 15, padding=0, repeat_down_delay = 100, **kwargs):

        Button.__init__(self, expand=expand, width=width, padding=padding,
                        repeat_down_delay=repeat_down_delay, **kwargs)
        self.up = up

    def do_render(self):
        self.graphics.rectangle(0, 0, self.width+1, self.height+1, 3)
        self.graphics.fill("#eee");

        self.graphics.translate((self.width - 5) / 2, (self.height - 2) / 2)

        if self.up:
            self.graphics.move_to(0, 3)
            self.graphics.line_to(3, 0)
            self.graphics.line_to(6, 3)
        else:
            self.graphics.move_to(0, 0)
            self.graphics.line_to(3, 3)
            self.graphics.line_to(6, 0)

        self.graphics.stroke("#000" if self.state in ("highlight", "pressed") else "#444")
