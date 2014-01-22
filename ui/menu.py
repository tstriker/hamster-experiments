# - coding: utf-8 -

# Copyright (c) 2011-2012 Media Modifications, Ltd.
# Dual licensed under the MIT or GPL Version 2 licenses.

from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import GObject as gobject

from ui import Widget, Box, Bin, Label, Button

class Menu(Box):
    """menu contains menuitems. menuitems can contain anything they want

    **Signals**:

    **selected** *(sprite, selected_item)*
    - fired when a menu item is selected.
    """
    __gsignals__ = {
        "selected": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
    }

    def __init__(self, contents = None, padding = 1, horizontal = False, owner = None,
                 open_on_hover = None, spacing = 0, hide_on_leave = False, hide_on_interstitial = False,
                 disable_toggling = False, **kwargs):
        Box.__init__(self, contents = contents, padding = padding, horizontal = horizontal, spacing = spacing, **kwargs)
        self.expand, self.expand_vert = False, False
        self.x_align = 0

        #: in case of a sub menu - a menu item that this menu belongs to
        self.owner = owner

        #: if specified, will open submenus menu after cursor has been over the item for the specified seconds
        self.open_on_hover = open_on_hover

        #: if set, will hide the menu when mouse moves out. defaults to False
        self._hide_on_leave = hide_on_leave

        #: if set, will hide the menu when mouse moves between menuitems.  defaults to False
        self._hide_on_interstitial = hide_on_interstitial

        #: if set, clicking on menu items with submenus will only show them instead of toggling
        #: this way the menu becomes more persistent
        self.disable_toggling = disable_toggling

        self._toggled = False
        self._scene_mouse_down = None
        self._scene_mouse_move = None
        self._scene_key_press = None
        self._echo = False

        self._timeout = None
        self.connect("on-render", self.__on_render)
        self.connect("on-mouse-down", self.__on_mouse_down)
        self.interactive = True


    def __setattr__(self, name, val):
        if name == "hide_on_leave":
            name = "_hide_on_leave"
        Box.__setattr__(self, name, val)

    @property
    def hide_on_leave(self):
        res = self._hide_on_leave
        owner = self.owner
        while owner and self.owner.parent:
            res = res or self.owner.parent._hide_on_leave
            owner = owner.parent.owner
        return res


    def add_child(self, *sprites):
        for sprite in sprites:
            Box.add_child(self, sprite)
            self.connect_child(sprite, "on-click", self.on_item_click)
            self.connect_child(sprite, "on-mouse-down", self.on_item_mouse_down)
            self.connect_child(sprite, "on-mouse-over", self.on_item_mouse_over)
            self.connect_child(sprite, "on-mouse-out", self.on_item_mouse_out)
        self.resize_children()

    def get_min_size(self):
        w, h = Box.get_min_size(self)
        if self.orient_horizontal:
            return w, h
        else:
            # for vertical ones give place to the submenu indicator
            return w + 8, h

    def __on_mouse_down(self, item, event):
        if self._toggled:
            self.collapse_submenus()
            self._toggled = False

    def on_item_mouse_down(self, item, event):
        self._on_item_mouse_down( item, event )

    def _on_item_mouse_down(self, item, event ):
        self._echo = True

        if not item.menu or self.disable_toggling == False:
            self._toggled = not self._toggled
        else:
            self._toggled = True

        if item.menu:
            if self._toggled:
                item.show_menu()
            else:
                item.hide_menu()
        self._on_item_mouse_over(item)


        # only top menu will be watching so we don't get anarchy and such
        if self.owner is None and not self._scene_mouse_down:
            self._scene_mouse_down = self.get_scene().connect_after("on-mouse-down", self.on_scene_mouse_down)
            self._scene_mouse_move = self.get_scene().connect_after("on-mouse-move", self.on_scene_mouse_move)

    def on_scene_mouse_down(self, scene, event):
        if self._scene_mouse_down and self._echo == False:
            ours = False
            for menu in list(self.get_submenus()) + [self]:
                ours = ours or (menu.parent and menu.check_hit(event.x, event.y))
                if ours:
                    break

            if not ours:
                self.collapse_submenus()
                self._toggled = False
        self._echo = False

    def on_scene_mouse_move(self, scene, event):

        ours = False
        for menu in [menu for menu in self.get_submenus() if menu.parent] + [self]:
            in_menu = menu.check_hit(event.x, event.y)
            if in_menu:
                if menu._hide_on_interstitial:
                    for item in menu.sprites:
                        ours = ours or (item.visible and item.check_hit(event.x, event.y))
                        if ours:
                            break
                else:
                    ours = True
            else:
                if menu.hide_on_leave:
                    #check if you are in your owner menu... don't be hasty
                    if not menu.owner or ( menu.owner and not menu.owner.check_hit(event.x, event.y) ):
                        ours = False
                        break
                else:
                    ours = True

            if ours:
                break

        if not ours:
            self.collapse_submenus()
            self._toggled = False

    @property
    def mnemonic_items(self):
        # returns list of all items that have mnemonics
        for menu in ([self] + list(self.get_submenus())):
            for item in menu.traverse("mnemonic"):
                if item.mnemonic:
                    yield item

    def get_submenus(self):
        """return a flattened list of submenus of this menu"""
        for item in self.sprites:
            if item.menu:
                yield item.menu
                for submenu in item.menu.get_submenus():
                    yield submenu

    def collapse_submenus(self):
        """collapses all sub menus, if there are any"""
        scene = self.get_scene()
        for menu in self.get_submenus():
            if menu.parent == scene:
                scene.remove_child(menu)

        for item in self.sprites:
            item.selected = False

        if self._scene_mouse_down:
            scene.disconnect(self._scene_mouse_down)
            scene.disconnect(self._scene_mouse_move)
            self._scene_mouse_down = None
            self._scene_mouse_move = None


    def on_item_click(self, item, event):
        if self._timeout:
            gobject.source_remove(self._timeout)

        if item.menu:
            return

        top_menu = item.parent
        while top_menu.owner:
            top_menu = top_menu.owner.parent

        for menuitem in top_menu.sprites:
            menuitem.selected = False
            menuitem.hide_menu()
        top_menu._toggled = False

        top_menu.emit("selected", item, event)

        #if you open on hover and you are still there.. open back up
        if not self.owner and self.open_on_hover:
            self._on_item_mouse_over( item )

    def on_item_mouse_over(self, item):
        self._on_item_mouse_over(item)

    def _on_item_mouse_over(self, item):
        for menuitem in self.sprites:
            menuitem.selected = False

        cursor, mouse_x, mouse_y, mods = item.get_scene().get_window().get_pointer()

        if self.open_on_hover and not self._toggled and not gdk.ModifierType.BUTTON1_MASK & mods:
            # show menu after specified seconds. we are emulating a click
            def show_menu():
                self._on_item_mouse_down(item, None)
                self._echo = False

            if self._timeout:
                gobject.source_remove(self._timeout)
            self._timeout = gobject.timeout_add(int(self.open_on_hover * 1000), show_menu)



        if self._toggled:
            item.selected = True
            # hide everybody else
            scene = self.get_scene()
            for sprite in self.sprites:
                if sprite.menu and sprite.menu.parent == scene:
                    sprite.menu._toggled = False
                    sprite.hide_menu()

            # show mine
            if item.menu:
                item.show_menu()
                item.menu._toggled = True

                # deal with going up the tree - hiding submenus and selected items
                for subitem in item.menu.sprites:
                    subitem.selected = False
                    if subitem.menu:
                        subitem.hide_menu()

    def on_item_mouse_out(self, sprite):
        if self._timeout:
            gobject.source_remove(self._timeout)
        self._timeout = None


    def __on_render(self, sprite):
        """if we are place with an offset, make sure the mouse still thinks
        it belongs to us (draw an invisible rectangle from parent till us"""
        if self.owner:
            x_offset, y_offset = self.owner.submenu_offset_x, self.owner.submenu_offset_y
        else:
            x_offset, y_offset = 0, 0

        self.graphics.rectangle(-x_offset, -y_offset,
                                self.width + x_offset, self.height + y_offset)
        self.graphics.new_path()


    def do_render(self):
        if self.owner:
            w, h = self.width, self.height
        else:
            w, h = self.width, self.height

        self.graphics.set_line_style(width = 1)
        self.graphics.rectangle(0.5, 0.5, w-1, h-1)
        self.graphics.fill_stroke("#eee", "#ddd")


class MenuItem(Button):
    """a menu item that can also own a menu"""

    secondary_label_class = Label
    def __init__(self, menu = None, padding = 5, submenu_offset_x = 2, submenu_offset_y = 2,
                 x_align = 0, y_align = 0.5, pressed_offset = 0,
                 secondary_label = "", mnemonic = "", **kwargs):
        Button.__init__(self, padding=padding, pressed_offset = pressed_offset, x_align = x_align, y_align = y_align, **kwargs)

        self.expand = False

        #: submenu of the item
        self.menu = menu

        self.selected = False

        #: if specified will push the submeny by the given pixels
        self.submenu_offset_x = submenu_offset_x

        #: if specified will push the submeny by the given pixels
        self.submenu_offset_y = submenu_offset_y

        #: the secondary label element
        self.secondary_display_label = self.secondary_label_class("",
                                                                  color = "#666",
                                                                  fill=True,
                                                                  x_align=1,
                                                                  padding_right = 5,
                                                                  visible = True)
        self.container.add_child(self.secondary_display_label)

        #: text of the secondary label that is placed to the right of the primary
        self.secondary_label = secondary_label

        #: keypress that can also triger activation of this menu item
        #: This is string in for "Key+Key+Key". For example: "Shift+c"
        self.mnemonic = mnemonic

        self.connect("on-mnemonic-activated", self.on_mnemonic_activated)


    def _position_contents(self):
        Button._position_contents(self)
        if hasattr(self, "secondary_display_label"):
            self.container.add_child(self.secondary_display_label)


    def __setattr__(self, name, val):
        if name == "menu":
            # make sure we re-parent also the submenu
            if getattr(self, "menu", None):
                self.menu.owner = None
            if val:
                val.owner = self
        elif name == "secondary_label":
            self.secondary_display_label.text = val
            if val:
                self.container.fill = self.secondary_display_label.visible = True
            else:
                self.container.fill = self.secondary_display_label.visible = False
            return
        elif name == "mnemonic":
            # trample over the secondary label. one can set it back if wants
            self.secondary_label = val

        Button.__setattr__(self, name, val)

    def on_mnemonic_activated(self, sprite, event):
        self._do_click(None)

    def show_menu(self):
        """display submenu"""
        if not self.menu: return

        self.menu.fill = False # submenus never fill to avoid stretching the whole screen

        scene = self.get_scene()
        scene.add_child(self.menu)
        self.menu.x, self.menu.y = self.to_scene_coords()
        self.menu.x += self.submenu_offset_x
        self.menu.y += self.submenu_offset_y
        #todo: this assumes the menuitems in this menu will pop down left || top aligned.. need to make a flag
        if self.parent.orient_horizontal:
            self.menu.y += self.height
        else:
            self.menu.x += self.width


    def hide_menu(self):
        """hide submenu"""
        if not self.menu: return

        for item in self.menu.sprites:
            if item.menu:
                item.hide_menu()

        scene = self.get_scene()
        if scene and self.menu in scene.sprites:
            scene.remove_child(self.menu)


    def do_render(self):
        selected = self.selected or self.state == "pressed"
        if selected:
            self.graphics.rectangle(0, 0, self.width, self.height)
            self.graphics.fill("#4A90D9")


        self.color = "#fff" if selected else "#333"

        # add submenu indicators
        if self.menu and self.parent and self.parent.orient_horizontal == False:
            self.graphics.move_to(self.width - 7, self.height / 2.0 - 3)
            self.graphics.line_to(self.width - 4, self.height / 2.0)
            self.graphics.line_to(self.width - 7, self.height / 2.0 + 3)

            self.graphics.stroke("#fff" if self.selected else "#999")


class MenuSeparator(Widget):
    """A simple menu item that is not selectable and is rendered as a separator"""
    spacing = 1
    def __init__(self, spacing=None, **kwargs):
        Widget.__init__(self)
        if spacing:
            self.spacing = spacing
        self.menu = None

    def get_min_size(self):
        if self.parent and self.parent.orient_horizontal:
            return self.spacing * 2 + 1, 1
        else:
            return 1, self.spacing * 2 + 1

    def do_render(self):
        self.graphics.rectangle(0, 0, self.width, self.height)
        self.graphics.new_path()

        if self.parent and self.parent.orient_horizontal:
            x = round(self.width / 2.0) - 0.5
            self.graphics.move_to(x, 0)
            self.graphics.line_to(x, self.height)
            self.graphics.stroke("#ccc")

            self.graphics.move_to(x+1, 0)
            self.graphics.line_to(x+1, self.height)
            self.graphics.stroke("#fff")
        else:
            y = round(self.height / 2.0) - 0.5
            self.graphics.move_to(0, y)
            self.graphics.line_to(self.width, y)
            self.graphics.stroke("#ccc")

            self.graphics.move_to(0, y+1)
            self.graphics.line_to(self.width, y+1)
            self.graphics.stroke("#fff")
