#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""Working on trying to abstract the boring cellrenderer technical
   implementation details under our fab graphics cover.

   Work in progress.
"""


import gtk, gobject
from lib import graphics, pytweener
from lib.graphics import Colors
import datetime as dt

class Cell(object):
    def __init__(self, renderer, cell_area):
        self.renderer = renderer
        self.cell_area = cell_area
        self.overrides = {}

    def __setattr__(self, name, value):
        # never complain about non-existing thing
        self.__dict__[name] = value

    def __getattr__(self, name):
        if name not in self.__dict__:
            return None
        else:
            return self.__dict__[name]

    def redraw(self):
        self.renderer.redraw(self.cell_area)

    def update_overrides(self, sprite, items):
        self.overrides.setdefault(sprite, {}).update(items)


class TweenProxy(object):
    """tween proxy never complains about missing keys"""
    def __init__(self, cell,  sprite):
        self.cell = cell
        self.sprite = sprite

    def __setattr__(self, name, value):
        # never complain about non-existing thing
        self.__dict__[name] = value

    def __getattr__(self, name):
        if name not in self.__dict__:
            return None
        else:
            return self.__dict__[name]

    def __str__(self):
        return str(self.__dict__)



class MagicCellRenderer(gtk.GenericCellRenderer):
    """ We need all kinds of wrapping and spanning and the treeview just does
        not cut it"""

    __gproperties__ = {
        "data": (gobject.TYPE_PYOBJECT, "Data", "Data", gobject.PARAM_READWRITE),
    }

    __gsignals__ = {
        "on-enter-frame": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
        "on-finish-frame": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
    }



    def __init__(self, framerate=60, interactive=True, background_color=None):
        gtk.GenericCellRenderer.__init__(self)

        #: list of sprites in scene. use :func:`add_child` to add sprites
        self.sprites = []

        #: framerate of animation. This will limit how often call for
        #: redraw will be performed (that is - not more often than the framerate). It will
        #: also influence the smoothness of tweeners.
        self.framerate = framerate

        #: Scene width. Will be `None` until first expose (that is until first
        #: on-enter-frame signal below).
        self.width = None

        self.cell_data = {}

        #: Scene height. Will be `None` until first expose (that is until first
        #: on-enter-frame signal below).
        self.height = None

        #: instance of :class:`pytweener.Tweener` that is used by
        #: :func:`animate` function, but can be also accessed directly for advanced control.
        self.tweener = None
        if pytweener:
            self.tweener = pytweener.Tweener(0.4, pytweener.Easing.Cubic.ease_in_out)

        #: instance of :class:`Colors` class for color parsing
        self.colors = Colors

        #: read only info about current framerate (frames per second)
        self.fps = 0 # inner frames per second counter

        #: Background color of the scene. Use either a string with hex color or an RGB triplet.
        self.background_color = background_color

        self._last_frame_time = None

        self.__drawing_queued = False
        self._redraw_in_progress = True

        self.current_cell = None
        self.window = None

        self.__pending_cells = set()

    def add_child(self, *sprites):
        """Add one or several :class:`Sprite` objects to the scene"""
        for sprite in sprites:
            if sprite.parent:
                sprite.parent.remove_child(sprite)
            self.sprites.append(sprite)
            sprite.parent = self
        self._sort()

    def _sort(self):
        """sort sprites by z_order"""
        self.sprites = sorted(self.sprites, key=lambda sprite:sprite.z_order)

    def do_set_property (self, pspec, value):
        setattr(self, pspec.name, value)

    def on_get_size(self, window, cell_area):
        return (0, 0, 0, 0)

    def animate(self, cell, sprite, duration = None, easing = None, on_complete = None, on_update = None, **kwargs):
        if not self.tweener: # here we complain
            raise Exception("pytweener was not found. Include it to enable animations")

        tween_proxy = TweenProxy(cell, sprite)

        # set initial values from the target sprite
        for key in kwargs.keys():
            setattr(tween_proxy, key, getattr(sprite, key))

        def on_finish(proxy):
            values = dict(proxy.__dict__)
            del values['cell']
            del values['sprite']
            proxy.cell.update_overrides(proxy.sprite, values)
            if on_complete:
                on_complete(proxy)

        tween = self.tweener.add_tween(tween_proxy,
                                       duration=duration,
                                       easing=easing,
                                       on_complete=on_finish,
                                       on_update=on_update,
                                       **kwargs)
        self.redraw(cell.cell_area)


    def on_render(self, window, tree, background_area, cell_area, expose_area, flags):
        context = window.cairo_create()
        # clip to the visible part
        context.rectangle(expose_area.x, expose_area.y,
                          expose_area.width, expose_area.height)
        if self.background_color:
            color = self.colors.parse(self.background_color)
            context.set_source_rgb(*color)
            context.fill_preserve()
        context.clip()

        x, y, self.width, self.height = cell_area
        context.translate(x, y)

        # update tweens
        now = dt.datetime.now()
        delta = (now - (self._last_frame_time or dt.datetime.now())).microseconds / 1000000.0
        self._last_frame_time = now
        if self.tweener:
            self.tweener.update(delta)

        self.fps = 1 / delta


        self.window = window
        self.current_cell = cell_area

        cell = self.cell_data.setdefault((cell_area.x, cell_area.y), Cell(self, background_area))
        cell.data = self.data # be sure to have the latest value

        # swap out overrides
        for override in cell.overrides:
            for key in cell.overrides[override]:
                v1,v2 = getattr(override, key), cell.overrides[override][key]
                cell.overrides[override][key] = v1
                setattr(override, key, v2)

        # swap out
        for proxy in self.tweener.current_tweens:
            if proxy.cell == cell:
                for tween in self.tweener.current_tweens[proxy]:
                    for key, tweenable in tween.tweenables:
                        v1,v2 = getattr(proxy, key), getattr(proxy.sprite, key)
                        setattr(proxy.sprite, key, v1)
                        setattr(proxy, key, v2)


        self.emit("on-enter-frame", cell, context)
        for sprite in self.sprites:
            sprite._draw(context)

        self.emit("on-finish-frame", cell, context)

        # swap back
        for override in cell.overrides:
            for key in cell.overrides[override]:
                v1,v2 = getattr(override, key), cell.overrides[override][key]
                cell.overrides[override][key] = v1
                setattr(override, key, v2)

        # swap back
        for proxy in self.tweener.current_tweens:
            if proxy.cell == cell:
                for tween in self.tweener.current_tweens[proxy]:
                    for key, tweenable in tween.tweenables:
                        v1,v2 = getattr(proxy, key), getattr(proxy.sprite, key)
                        setattr(proxy.sprite, key, v1)
                        setattr(proxy, key, v2)


        self.current_cell = None

    def redraw(self, cell_area):
        """Queue redraw. The redraw will be performed not more often than
           the `framerate` allows"""

        self.__pending_cells.add((cell_area.x, cell_area.y, cell_area.width, cell_area.height))


        if self.__drawing_queued == False: #if we are moving, then there is a timeout somewhere already
            self.__drawing_queued = True
            self._last_frame_time = dt.datetime.now()
            gobject.timeout_add(1000 / self.framerate, self.__redraw_loop)

    def __redraw_loop(self):
        """loop until there is nothing more to tween"""

        for x,y,w,h in self.__pending_cells:
            self.window.invalidate_rect((x,y,w,h), False) # this will trigger do_expose_event when the current events have been flushed


        self.__pending_cells = set([(proxy.cell.cell_area.x, proxy.cell.cell_area.y, proxy.cell.cell_area.width, proxy.cell.cell_area.height)
                                    for proxy in self.tweener.current_tweens.keys()] or [])

        self.__drawing_queued = self.tweener and self.tweener.has_tweens()
        return self.__drawing_queued


class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_default_size(600, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        self.liststore = gtk.ListStore(gobject.TYPE_PYOBJECT)
        self.liststore.append(['Open'])
        self.liststore.append(['New'])
        self.liststore.append(['Plint'])
        self.liststore.append(['Open'])
        self.liststore.append(['New'])
        self.liststore.append(['Plint'])

        self.treeview = gtk.TreeView(self.liststore)

        fact_cell = MagicCellRenderer()
        fact_cell.connect("on-enter-frame", self.on_enter_frame)
        fact_column = gtk.TreeViewColumn("", fact_cell, data=0)
        self.treeview.append_column(fact_column)

        self.rect = graphics.Rectangle(10, 10, stroke = "#000")
        fact_cell.add_child(self.rect)



        window.add(self.treeview)
        window.show_all()

    def on_enter_frame(self, renderer, cell, context):
        g = graphics.Graphics(context)

        cell.rect_x = cell.rect_x or 1
        cell.color = cell.color or "#f00"

        #g.rectangle(cell.rect_x, 0.5, 10, 10)
        #g.fill_stroke(cell.color, "#000")


        if cell.color =="#f00" and cell.data=="New":
            cell.color = "#0f0"
            renderer.animate(cell, self.rect, stroke="#0f0", x=100, duration=1)

if __name__ == '__main__':
    window = BasicWindow()
    gtk.main()
