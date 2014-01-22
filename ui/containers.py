# - coding: utf-8 -

# Copyright (c) 2011-2012 Media Modifications, Ltd.
# Dual licensed under the MIT or GPL Version 2 licenses.

from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import GObject as gobject

import math
from collections import defaultdict

from lib import graphics
from ui import Widget


def get_min_size(sprite):
    if hasattr(sprite, "get_min_size"):
        min_width, min_height = sprite.get_min_size()
    else:
        min_width, min_height = getattr(sprite, "width", 0), getattr(sprite, "height", 0)

    min_width = min_width * sprite.scale_x
    min_height = min_height * sprite.scale_y

    return min_width, min_height

def get_props(sprite):
    # gets all the relevant info for containers and puts it in a uniform dict.
    # this way we can access any object without having to check types and such
    keys = ("margin_top", "margin_right", "margin_bottom", "margin_left",
            "padding_top", "padding_right", "padding_bottom", "padding_left")
    res = dict((key, getattr(sprite, key, 0)) for key in keys)
    res["expand"] = getattr(sprite, "expand", True)

    return sprite, res


class Container(Widget):
    """The base container class that all other containers inherit from.
       You can insert any sprite in the container, just make sure that it either
       has width and height defined so that the container can do alignment, or
       for more sophisticated cases, make sure it has get_min_size function that
       returns how much space is needed.

       Normally while performing layout the container will update child sprites
       and set their alloc_h and alloc_w properties. The `alloc` part is short
       for allocated. So use that when making rendering decisions.
    """
    cache_attrs = Widget.cache_attrs | set(('_cached_w', '_cached_h'))
    _sizing_attributes = Widget._sizing_attributes | set(('padding_top', 'padding_right', 'padding_bottom', 'padding_left'))

    def __init__(self, contents = None, **kwargs):
        Widget.__init__(self, **kwargs)

        #: contents of the container - either a widget or a list of widgets
        self.contents = contents
        self._cached_w, self._cached_h = None, None


    def __setattr__(self, name, val):
        if self.__dict__.get(name, "hamster_graphics_no_value_really") == val:
            return

        Widget.__setattr__(self, name, val)
        if name == 'contents':
            if val:
                if isinstance(val, graphics.Sprite):
                    val = [val]
                self.add_child(*val)
            if self.sprites and self.sprites != val:
                self.remove_child(*list(set(self.sprites) ^ set(val or [])))

        if name in ("alloc_w", "alloc_h") and val:
            self.__dict__['_cached_w'], self.__dict__['_cached_h'] = None, None
            self._children_resize_queued = True


    @property
    def contents(self):
        return self.sprites


    def _Widget__on_render(self, sprite):
        if self._children_resize_queued:
            self.resize_children()
            self.__dict__['_children_resize_queued'] = False
        Widget._Widget__on_render(self, sprite)


    def _add(self, *sprites):
        Widget._add(self, *sprites)
        self.queue_resize()

    def remove_child(self, *sprites):
        Widget.remove_child(self, *sprites)
        self.queue_resize()

    def queue_resize(self):
        self.__dict__['_cached_w'], self.__dict__['_cached_h'] = None, None
        Widget.queue_resize(self)

    def get_min_size(self):
        # by default max between our requested size and the biggest child
        if self.visible == False:
            return 0, 0

        if self._cached_w is None:
            sprites = [sprite for sprite in self.sprites if sprite.visible]
            width = max([get_min_size(sprite)[0] for sprite in sprites] or [0])
            width += self.horizontal_padding  + self.margin_left + self.margin_right

            height = max([get_min_size(sprite)[1] for sprite in sprites] or [0])
            height += self.vertical_padding + self.margin_top + self.margin_bottom

            self._cached_w, self._cached_h = max(width, self.min_width or 0), max(height, self.min_height or 0)

        return self._cached_w, self._cached_h

    def get_height_for_width_size(self):
        return self.get_min_size()


    def resize_children(self):
        """default container alignment is to pile stuff just up, respecting only
        padding, margin and element's alignment properties"""
        width = self.width - self.horizontal_padding
        height = self.height - self.vertical_padding

        for sprite, props in (get_props(sprite) for sprite in self.sprites if sprite.visible):
            sprite.alloc_w = width
            sprite.alloc_h = height

            w, h = getattr(sprite, "width", 0), getattr(sprite, "height", 0)
            if hasattr(sprite, "get_height_for_width_size"):
                w2, h2 = sprite.get_height_for_width_size()
                w, h = max(w, w2), max(h, h2)

            w = w * sprite.scale_x + props["margin_left"] + props["margin_right"]
            h = h * sprite.scale_y + props["margin_top"] + props["margin_bottom"]

            sprite.x = self.padding_left + props["margin_left"] + (max(sprite.alloc_w * sprite.scale_x, w) - w) * getattr(sprite, "x_align", 0)
            sprite.y = self.padding_top + props["margin_top"] + (max(sprite.alloc_h * sprite.scale_y, h) - h) * getattr(sprite, "y_align", 0)


        self.__dict__['_children_resize_queued'] = False

class Bin(Container):
    """A container with only one child. Adding new children will throw the
    previous ones out"""
    def __init__(self, contents = None, **kwargs):
        Container.__init__(self, contents, **kwargs)

    @property
    def child(self):
        """child sprite. shorthand for self.sprites[0]"""
        return self.sprites[0] if self.sprites else None

    def get_height_for_width_size(self):
        if self._children_resize_queued:
            self.resize_children()

        sprites = [sprite for sprite in self.sprites if sprite.visible]
        width, height = 0, 0
        for sprite in sprites:
            if hasattr(sprite, "get_height_for_width_size"):
                w, h = sprite.get_height_for_width_size()
            else:
                w, h = getattr(sprite, "width", 0), getattr(sprite, "height", 0)

            w, h = w * sprite.scale_x, h * sprite.scale_y

            width = max(width, w)
            height = max(height, h)

        #width = width + self.horizontal_padding + self.margin_left + self.margin_right
        #height = height + self.vertical_padding + self.margin_top + self.margin_bottom

        return width, height


    def add_child(self, *sprites):
        if not sprites:
            return

        sprite = sprites[-1] # there can be just one

        # performing add then remove to not screw up coordinates in
        # a strange reparenting case
        Container.add_child(self, sprite)
        if self.sprites and self.sprites[0] != sprite:
            self.remove_child(*list(set(self.sprites) ^ set([sprite])))



class Fixed(Container):
    """Basic container that does not care about child positions. Handy if
       you want to place stuff yourself or do animations.
    """
    def __init__(self, contents = None, **kwargs):
        Container.__init__(self, contents, **kwargs)

    def resize_children(self):
        # don't want
        pass



class Box(Container):
    """Align children either horizontally or vertically.
        Normally you would use :class:`HBox` or :class:`VBox` to be
        specific but this one is suited so you can change the packing direction
        dynamically.
    """
    #: spacing in pixels between children
    spacing = 5

    #: whether the box is packing children horizontally (from left to right) or vertically (from top to bottom)
    orient_horizontal = True

    def __init__(self, contents = None, horizontal = None, spacing = None, **kwargs):
        Container.__init__(self, contents, **kwargs)

        if horizontal is not None:
            self.orient_horizontal = horizontal

        if spacing is not None:
            self.spacing = spacing

    def get_total_spacing(self):
        # now lay them out
        padding_sprites = 0
        for sprite in self.sprites:
            if sprite.visible:
                if getattr(sprite, "expand", True):
                    padding_sprites += 1
                else:
                    if hasattr(sprite, "get_min_size"):
                        size = sprite.get_min_size()[0] if self.orient_horizontal else sprite.get_min_size()[1]
                    else:
                        size = getattr(sprite, "width", 0) * sprite.scale_x if self.orient_horizontal else getattr(sprite, "height", 0) * sprite.scale_y

                    if size > 0:
                        padding_sprites +=1
        return self.spacing * max(padding_sprites - 1, 0)


    def resize_children(self):
        if not self.parent:
            return

        width = self.width - self.padding_left - self.padding_right
        height = self.height - self.padding_top - self.padding_bottom

        sprites = [get_props(sprite) for sprite in self.sprites if sprite.visible]

        # calculate if we have any spare space
        sprite_sizes = []
        for sprite, props in sprites:
            if self.orient_horizontal:
                sprite.alloc_h = height / sprite.scale_y
                size = get_min_size(sprite)[0]
                size = size + props["margin_left"] + props["margin_right"]
            else:
                sprite.alloc_w = width / sprite.scale_x
                size = get_min_size(sprite)[1]
                if hasattr(sprite, "get_height_for_width_size"):
                    size = max(size, sprite.get_height_for_width_size()[1] * sprite.scale_y)
                size = size + props["margin_top"] + props["margin_bottom"]
            sprite_sizes.append(size)


        remaining_space = width if self.orient_horizontal else height
        if sprite_sizes:
            remaining_space = remaining_space - sum(sprite_sizes) - self.get_total_spacing()


        interested_sprites = [sprite for sprite, props in sprites if getattr(sprite, "expand", True)]


        # in order to stay pixel sharp we will recalculate remaining bonus
        # each time we give up some of the remaining space
        remaining_interested = len(interested_sprites)
        bonus = 0
        if remaining_space > 0 and interested_sprites:
            bonus = int(remaining_space / remaining_interested)

        actual_h = 0
        x_pos, y_pos = 0, 0

        for (sprite, props), min_size in zip(sprites, sprite_sizes):
            sprite_bonus = 0
            if sprite in interested_sprites:
                sprite_bonus = bonus
                remaining_interested -= 1
                remaining_space -= bonus
                if remaining_interested:
                    bonus = int(float(remaining_space) / remaining_interested)


            if self.orient_horizontal:
                sprite.alloc_w = (min_size + sprite_bonus) / sprite.scale_x
            else:
                sprite.alloc_h = (min_size + sprite_bonus) / sprite.scale_y

            w, h = getattr(sprite, "width", 0), getattr(sprite, "height", 0)
            if hasattr(sprite, "get_height_for_width_size"):
                w2, h2 = sprite.get_height_for_width_size()
                w, h = max(w, w2), max(h, h2)

            w = w * sprite.scale_x + props["margin_left"] + props["margin_right"]
            h = h * sprite.scale_y + props["margin_top"] + props["margin_bottom"]


            sprite.x = self.padding_left + x_pos + props["margin_left"] + (max(sprite.alloc_w * sprite.scale_x, w) - w) * getattr(sprite, "x_align", 0.5)
            sprite.y = self.padding_top + y_pos + props["margin_top"] + (max(sprite.alloc_h * sprite.scale_y, h) - h) * getattr(sprite, "y_align", 0.5)


            actual_h = max(actual_h, h * sprite.scale_y)

            if (min_size + sprite_bonus) > 0:
                if self.orient_horizontal:
                    x_pos += int(max(w, sprite.alloc_w * sprite.scale_x)) + self.spacing
                else:
                    y_pos += max(h, sprite.alloc_h * sprite.scale_y) + self.spacing


        if self.orient_horizontal:
            for sprite, props in sprites:
                sprite.__dict__['alloc_h'] = actual_h

        self.__dict__['_children_resize_queued'] = False

    def get_height_for_width_size(self):
        if self._children_resize_queued:
            self.resize_children()

        sprites = [sprite for sprite in self.sprites if sprite.visible]
        width, height = 0, 0
        for sprite in sprites:
            if hasattr(sprite, "get_height_for_width_size"):
                w, h = sprite.get_height_for_width_size()
            else:
                w, h = getattr(sprite, "width", 0), getattr(sprite, "height", 0)

            w, h = w * sprite.scale_x, h * sprite.scale_y


            if self.orient_horizontal:
                width += w
                height = max(height, h)
            else:
                width = max(width, w)
                height = height + h

        if self.orient_horizontal:
            width = width + self.get_total_spacing()
        else:
            height = height + self.get_total_spacing()

        width = width + self.horizontal_padding + self.margin_left + self.margin_right
        height = height + self.vertical_padding + self.margin_top + self.margin_bottom

        return width, height



    def get_min_size(self):
        if self.visible == False:
            return 0, 0

        if self._cached_w is None:
            sprites = [sprite for sprite in self.sprites if sprite.visible]

            width, height = 0, 0
            for sprite in sprites:
                if hasattr(sprite, "get_min_size"):
                    w, h = sprite.get_min_size()
                else:
                    w, h = getattr(sprite, "width", 0), getattr(sprite, "height", 0)

                w, h = w * sprite.scale_x, h * sprite.scale_y

                if self.orient_horizontal:
                    width += w
                    height = max(height, h)
                else:
                    width = max(width, w)
                    height = height + h

            if self.orient_horizontal:
                width = width + self.get_total_spacing()
            else:
                height = height + self.get_total_spacing()

            width = width + self.horizontal_padding + self.margin_left + self.margin_right
            height = height + self.vertical_padding + self.margin_top + self.margin_bottom

            w, h = max(width, self.min_width or 0), max(height, self.min_height or 0)
            self._cached_w, self._cached_h = w, h

        return self._cached_w, self._cached_h


class HBox(Box):
    """A horizontally aligned box. identical to ui.Box(horizontal=True)"""
    def __init__(self, contents = None, **kwargs):
        Box.__init__(self, contents, **kwargs)
        self.orient_horizontal = True


class VBox(Box):
    """A vertically aligned box. identical to ui.Box(horizontal=False)"""
    def __init__(self, contents = None, **kwargs):
        Box.__init__(self, contents, **kwargs)
        self.orient_horizontal = False


class Flow(Container):
    """container that flows the child sprites either horizontally or vertically.
       Currently it does not support any smart width/height sizing and so labels
       and other height-for-width-for-height type of containers should be told
       a fixed size in order to work properly
    """
    horizontal = True #: flow direction
    horizontal_spacing = 0 #: horizontal spacing
    vertical_spacing = 0 #: vertical spacing

    wrap = True #: should the items wrap when not fitting in the direction

    def __init__(self, horizontal = None, horizontal_spacing = None,
                 vertical_spacing = None, wrap = True, **kwargs):
        Container.__init__(self, **kwargs)

        if wrap is not None:
            self.wrap = wrap

        if horizontal is not None:
            self.horizontal = horizontal

        if horizontal_spacing is not None:
            self.horizontal_spacing = horizontal_spacing

        if vertical_spacing is not None:
            self.vertical_spacing = vertical_spacing


    def get_height_for_width_size(self):
        if self._children_resize_queued:
            self.resize_children()

        sprites = [sprite for sprite in self.sprites if sprite.visible]
        width, height = 0, 0
        for sprite in sprites:
            if hasattr(sprite, "get_height_for_width_size"):
                w, h = sprite.get_height_for_width_size()
            else:
                w, h = getattr(sprite, "width", 0), getattr(sprite, "height", 0)

            w = sprite.x + (w + sprite.horizontal_padding) * sprite.scale_x
            h = sprite.y + (h + sprite.horizontal_padding) * sprite.scale_y

            width = max(width, w)
            height = max(height, h)

        width = width + self.padding_right
        height = height + self.padding_bottom

        return width, height


    def get_rows(self):
        """returns extents of each row (x, y, x2, y2) and the sprites it
        contains"""
        sprites = [sprite for sprite in self.sprites if sprite.visible]

        width = self.width - self.padding_left - self.padding_right
        height = self.height - self.padding_top - self.padding_bottom

        x, y = self.padding_left, self.padding_top
        row_size = 0

        rows = []
        row_x, row_y, row_sprites = x, y, []
        for sprite in sprites:
            if self.horizontal:
                if self.wrap == False or x == self.padding_left or x + sprite.width < width:
                    row_size = max(row_size, sprite.height)
                    row_sprites.append(sprite)
                else:
                    #wrap
                    rows.append(((row_x, row_y, width, row_y + row_size), row_sprites))

                    y = y + row_size + self.vertical_spacing
                    x = self.padding_left
                    row_size = sprite.height

                    row_x, row_y, row_sprites = x, y, [sprite]

                x = x + sprite.width + self.horizontal_spacing
            else:
                if self.wrap == False or y == self.padding_top or y + sprite.height < height:
                    row_size = max(row_size, sprite.width)
                    row_sprites.append(sprite)
                else:
                    #wrap
                    rows.append(((row_x, row_y, row_x + row_size, height), row_sprites))

                    x = x + row_size + self.spacing
                    y = self.padding_top
                    row_size = sprite.width

                    row_x, row_y, row_sprites = x, y, [sprite]

                y = y + sprite.height + self.vertical_spacing

        if row_sprites:
            if self.horizontal:
                rows.append(((row_x, row_y, width, row_y + row_size), row_sprites))
            else:
                rows.append(((row_x, row_y, row_x + row_size, height), row_sprites))


        return rows


    def resize_children(self):
        for (x, y, x2, y2), sprites in self.get_rows():
            for sprite in sprites:
                sprite.x, sprite.y = x, y
                if self.horizontal:
                    x += sprite.width + self.horizontal_spacing
                else:
                    y += sprite.height + self.vertical_spacing
        self.__dict__['_children_resize_queued'] = False


class Table(Container):
    """Table allows aligning children in a grid. Elements can span several
    rows or columns"""
    def __init__(self, cols=1, rows=1, horizontal_spacing = 0, vertical_spacing = 0, **kwargs):
        Container.__init__(self, **kwargs)

        #: number of rows
        self.rows = rows

        #: number of columns
        self.cols = cols

        #: vertical spacing in pixels between the elements
        self.vertical_spacing = vertical_spacing

        #: horizontal spacing in pixels between the elements
        self.horizontal_spacing = horizontal_spacing

        self._horiz_attachments, self._vert_attachments = {}, {}


    def attach(self, sprite, left, right, top, bottom):
        """Attach a widget to the table. Use the left, right, top and bottom
        attributes to specify the attachment. Use this function instead of
        :py:func:`graphics.Sprite.add_child` to add sprites to the table"""
        self._horiz_attachments[sprite] = (left, right)
        self._vert_attachments[sprite] = (top, bottom)
        if sprite not in self.sprites:
            self.add_child(sprite)


    def get_min_size(self):
        if self._cached_w is None:
            if self.visible == False:
                return 0, 0

            w, h = sum(self.get_col_sizes()), sum(self.get_row_sizes())
            w = w + self.horizontal_spacing * (self.cols - 1) + self.horizontal_padding + self.margin_left + self.margin_right
            h = h + self.vertical_spacing * (self.rows - 1) + self.vertical_padding + self.margin_top + self.margin_bottom

            w, h = max(self.min_width, w), max(self.min_height, h)
            self._cached_w, self._cached_h = w, h

        return self._cached_w, self._cached_h

    def get_col_sizes(self):
        return self._get_section_sizes()

    def get_row_sizes(self):
        return self._get_section_sizes(horizontal = False)

    def _get_section_sizes(self, horizontal = True):
        if horizontal:
            sections, attachments, attr = self.cols, self._horiz_attachments, "x"
        else:
            sections, attachments, attr = self.rows, self._vert_attachments, "y"

        remaining, section_sizes = {}, []

        for i in range(sections):
            min_size = 0

            for sprite in attachments:
                if sprite.visible == False or attachments[sprite][0] > i or attachments[sprite][1] <= i:
                    continue

                start, end = attachments[sprite]

                if sprite not in remaining:
                    remaining_sections = end - start
                    sprite_size = get_min_size(sprite)[0] if attr =="x" else get_min_size(sprite)[1]

                    remaining[sprite] = remaining_sections, sprite_size
                else:
                    remaining_sections, sprite_size = remaining[sprite]

                min_size = max(min_size, sprite_size / remaining_sections)
                remaining[sprite] = remaining_sections - 1, sprite_size - min_size

            section_sizes.append(min_size)

        return section_sizes


    def resize_children(self):
        if not self.get_scene() or not self.get_scene().get_window():
            return

        width = self.width - self.padding_left - self.padding_right
        height = self.height - self.padding_top - self.padding_bottom

        def align(space, sections, attachments, attr):
            spacing = self.horizontal_spacing if attr == "x" else self.vertical_spacing
            expand_sections = defaultdict(list)
            section_sizes = self._get_section_sizes(attr == "x")

            """"
            # this code can tell you the actual partitions and which ones should be collapse
            # of potential used if we decide to implement the table more properly
            real_sections = set()
            for part in attachments.values():
                real_sections = real_sections | set(part)
            real_sections = list(real_sections)
            partitions = zip(real_sections, real_sections[1:])

            self.log(partitions, section_sizes)

            collapsed_sections = [i for start, end in partitions for i in range(start+1, end)]
            self.log("collapsed sections", collapsed_sections)
            """



            for i, min_size in enumerate(section_sizes):
                for sprite in attachments:
                    if attachments[sprite][0] > i or attachments[sprite][1] <= i:
                        continue

                    expand_sections[i].append((attr =="x" and  getattr(sprite, "expand", True)) or (attr == "y" and getattr(sprite, "expand_vert", True)))

                if min_size == 0:
                    expand_sections[i].append(True)

            # distribute the remaining space
            available_space = space - sum(section_sizes) - (sections - 1) * spacing

            # expand only those sections everybody agrees on
            expand_sections = [expand[0] for expand in expand_sections.items() if all(expand[1])]

            expand_sections = expand_sections or [sections-1] # if nobody wants to expand we tell the last partition to do that

            if available_space > 0 and expand_sections:
                bonus = available_space / len(expand_sections)
                for section in expand_sections:
                    section_sizes[section] += bonus

            positions = []
            pos = 0
            for s in section_sizes:
                positions.append(pos)
                pos += s + spacing

            positions.append(pos)

            for i, (sprite, (start, end)) in enumerate(attachments.iteritems()):
                if attr == "x":
                    sprite.alloc_w = positions[end] - positions[start] - spacing
                    sprite.x = positions[start] + (sprite.alloc_w - sprite.width) * getattr(sprite, "x_align", 0.5) + self.padding_left
                else:
                    sprite.alloc_h = positions[end] - positions[start] - spacing
                    sprite.y = positions[start] + (sprite.alloc_h - sprite.height) * getattr(sprite, "y_align", 0.5) + self.padding_top


            if self.debug:
                for i, p in enumerate(positions):
                    if i == sections:
                        p = p - spacing

                    if attr == "x":
                        self.graphics.move_to(p + self.padding_left, 0 + self.padding_top)
                        self.graphics.line_to(p + self.padding_left, height + self.padding_top)
                        self.graphics.stroke("#0f0")
                    else:
                        self.graphics.move_to(0 + self.padding_left, p + self.padding_top)
                        self.graphics.line_to(width + self.padding_left, p + self.padding_top)
                        self.graphics.stroke("#f00")


        align(width, self.cols, self._horiz_attachments, "x")
        align(height, self.rows, self._vert_attachments, "y")
        self.__dict__['_children_resize_queued'] = False

class Viewport(Bin):
    """View a fragment of the child. Most commonly seen in
    :class:`~ui.scroll.ScrollArea`"""
    def __init__(self, contents=None, **kwargs):
        Bin.__init__(self, contents, **kwargs)
        self.connect("on-render", self.__on_render)

    def get_container_size(self):
        """returns the size of inner contents"""
        if not self.child:
            return 0,0

        if hasattr(self.child, "get_height_for_width_size"):
            self.resize_children()
            return self.child.get_height_for_width_size()
        else:
            return self.child.width, self.child.height

    def get_min_size(self):
        w, h = (self.min_width or 0, self.min_height or 0) if self.visible else (0, 0)
        return w, h

    def get_height_for_width_size(self):
        return self.get_min_size()

    def resize_children(self):
        """ help sprites a bit and tell them how much space we have in
            case they care (which they mostly should not as in fixed you can do
            anything """
        if not self.child: return

        w, h = self.width, self.height
        # invalidate child extents as the viewport is clipping to it's extents
        self._prev_parent_matrix = None

        self.child.alloc_w = w - max(self.child.x, 0)
        self.child.alloc_h = h - max(self.child.y, 0)
        self.__dict__['_children_resize_queued'] = False


    def __on_render(self, sprite):
        self.graphics.rectangle(0, 0, self.width+1, self.height)
        self.graphics.clip()



class Group(Box):
    """A container for radio and toggle buttons.

    **Signals**:

    **on-change** *(sprite, toggled_item)*
    - fired after the toggle.
    """
    __gsignals__ = {
        "on-change": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
    }
    spacing = 0

    def __init__(self, contents = None, allow_no_selection = False, **kwargs):
        Box.__init__(self, contents = contents, **kwargs)
        self.current_item = None

        #: If set to true, repeat toggle of the selected item will un-toggle it
        #: and thus there will be no current item
        self.allow_no_selection = allow_no_selection

        #: all group elements, not necessarily packed in the group
        self.elements = []

        self._add_item(*(contents or []))

    def add_child(self, *sprites):
        Box.add_child(self, *sprites)
        if hasattr(self, "elements"):
            self._add_item(*sprites)

    def remove_child(self, *sprites):
        Box.remove_child(self, *sprites)
        self._remove_item(*sprites)


    def _add_item(self, *elements):
        """adds item to group. this is called from the toggle button classes"""
        for item in elements:
            if item in self.elements:
                continue
            self.connect_child(item, "on-toggle", self.on_toggle)
            self.connect_child(item, "on-mouse-down", self.on_mouse_down)
            self.elements.append(item)
            item.group = self

    def _remove_item(self, *elements):
        """removes item from group. this is called from the toggle button classes"""
        for item in elements:
            self.disconnect_child(item)
            if item in self.elements:
                self.elements.remove(item)

    def on_mouse_down(self, button, event):
        if button.enabled == False:
            return
        if self.allow_no_selection:
            # avoid echoing out in the no-select cases
            return

        button.toggle()


    def on_toggle(self, sprite):
        changed = sprite != self.current_item or self.allow_no_selection
        sprite = sprite or self.current_item
        if sprite.toggled:
            self.current_item = sprite
        elif self.allow_no_selection:
            self.current_item = None

        for item in self.elements:
            item.toggled = item == self.current_item

        if changed:
            self.emit("on-change", self.current_item)

    def get_selected( self ):
        selected = None
        for item in self.elements:
            if item.toggled:
                selected = item
                break
        return selected


class Panes(Box):
    """a container that has a grip area between elements that allows to change
    the space allocated to each one"""
    spacing = 10
    def __init__(self, position = 150, **kwargs):
        Box.__init__(self, **kwargs)

        #: current position of the grip
        self.split_position = position

        self.grips = []

    def add_child(self, *sprites):
        for sprite in sprites:
            if sprite not in self.grips and len(self.sprites) > 0:
                grip = PanesGrip(x = self.split_position)
                self.connect_child(grip, "on-drag", self.__on_drag)
                self.grips.append(grip)
                self.add_child(grip)

            Box.add_child(self, sprite)

    def __on_drag(self, sprite, event):
        sprite.y = 0
        self.split_position = sprite.x
        self.resize_children()


    def resize_children(self):
        if not self.get_scene() or not self.get_scene().get_window():
            return

        if not self.sprites:
            return

        self.sprites[0].x = self.padding_left

        for sprite in self.sprites:
            sprite.y = self.padding_top
            sprite.alloc_h = self.height - self.vertical_padding

        prev_grip_x = self.padding_left
        for grip in self.grips:
            self.sprites[self.sprites.index(grip)-1].alloc_w = grip.x - prev_grip_x - self.spacing
            self.sprites[self.sprites.index(grip)+1].x = grip.x + grip.width + self.spacing

            prev_grip_x = grip.x

        self.sprites[-1].alloc_w = self.width - self.sprites[-1].x - self.padding_left
        self.__dict__['_children_resize_queued'] = False


class PanesGrip(Widget):
    """a grip element between panes"""
    mouse_cursor = gdk.CursorType.SB_H_DOUBLE_ARROW

    def __init__(self, width=1, **kwargs):
        Widget.__init__(self, **kwargs)
        self.width = width
        self.draggable = True

    def do_render(self):
        self.graphics.rectangle(0, 0, self.width, self.height)
        self.graphics.fill("#aaa")
