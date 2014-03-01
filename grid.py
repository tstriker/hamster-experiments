#!/usr/bin/env python
# - coding: utf-8 -

# Copyright 2013 Bryce W. Harrington <bryce@bryceharrington.org>
# Dual licensed under the MIT or GPL Version 2 licenses.
# See http://github.com/tbaugis/hamster_experiments/blob/master/README.textile

from lib import graphics

class GridElement(object):
    def __init__(self, i,j, height,width, **args):
        self.__graphic = None
        self.i = i
        self.j = j
        self.height = height
        self.width = width
        self.stroke_width = args.get('stroke_width', 2)
        self.color_foreground = args.get('color_foreground', "#fff")
        self.color_stroke = args.get('color_stroke', "#000")
        self.on_click = args.get('on_click', None)
        self.args = args

    def set_origin(self, x, y):
        '''Move this element to the given x,y location'''
        self.graphic.x = x
        self.graphic.y = y

    def create_sprite(self):
        '''Returns a new GridElementSprite for this element's location'''
        t = GridElementSprite(self.i, self.j, self.width, self.height, **self.args)
        t.interactive = True
        t.on_click = self.on_click
        t.connect('on-render', self.on_render)
        t.connect('on-mouse-over', self.on_over)
        t.connect('on-mouse-out', self.on_out)
        if t.on_click:
            t.connect('on-click', t.on_click)
        return t

    def on_over(self, sprite):
        '''Highlight the cell element when hovering over the element'''
        if not sprite: return # ignore blank clicks
        tmp = self.color_foreground
        self.color_foreground = self.color_stroke
        self.color_stroke = tmp

    def on_out(self, sprite):
        '''Unhighlight element when mouse no longer over the element'''
        if not sprite: return # ignore blank clicks
        tmp = self.color_foreground
        self.color_foreground = self.color_stroke
        self.color_stroke = tmp

    def on_render(self, sprite):
        '''Draw the shape for this element'''
        assert False, "Override this with your own drawing code"

    @property
    def graphic(self):
        if self.__graphic is None:
            self.__graphic = self.create_sprite()
        assert(self.__graphic is not None)
        return self.__graphic


class GridElementSprite(graphics.Sprite):
    def __init__(self, i, j, width=100, height=100, color_foreground="#333", color_stroke="#000", stroke_width=2):
        graphics.Sprite.__init__(self)
        self.i = i
        self.j = j
        self.width = width
        self.height = height
        self.stroke_width = stroke_width
        self.color_foreground = color_foreground
        self.color_stroke = color_stroke
        self.on_click = None


class Grid(graphics.Sprite):
    '''Infinite 2D array of grid elements'''
    def __init__(self, x=0, y=0, x_spacing=50, y_spacing=50):
        '''
        The x,y coordinates is the canvas location for the top left
        origin of the grid.  The x_spacing and y_spacing are the offsets
        of each subsequent grid element's location.  The spacings should
        be equal to the grid element dimensions to make a regular packed grid.
        '''
        graphics.Sprite.__init__(self, x=x, y=y)
        self.x_spacing = x_spacing
        self.y_spacing = y_spacing
        self.__elements = {}
        self.connect("on-render", self.on_render)

    def add(self, e):
        '''Adds an element to the grid at the element's i,j coordinate'''
        if e.i not in self.__elements.keys():
            self.__elements[e.i] = {}
        self.__elements[e.i][e.j] = e

    def get(self, i, j):
        '''Returns the element at the given i,j coordinate'''
        if (i not in self.__elements.keys() or
            j not in self.__elements[i].keys()):
            return None
        return self.__elements[i][j]

    def set(self, i, j, e):
        '''Insert element e at location i, j'''
        self.__elements[i][j] = e

    def remove(self, i, j):
        '''Delete the element at the given i, j location'''
        del self.__elements[i][j]

    def on_render(self, widget):
        '''Handler to render all elements in the grid'''
        x = 0
        y = 0
        self.graphics.clear()
        self.sprites = []
        for column in self.__elements.values():
            for e in column.values():
                e.set_origin(x, y)
                e.on_render(e.graphic)
                self.add_child(e.graphic)
                y += self.y_spacing
            y = 0
            x += self.x_spacing

    def elements(self):
        '''Sequentially yields all grid elements'''
        for row in self.__elements.values():
            for col in row.values():
                yield col


class TriangularGridElement(GridElement):
    x_spacing_factor = 0.5
    y_spacing_factor = 1
    def __init__(self, i,j, height,width, **args):
        GridElement.__init__(self, i,j, height,width, **args)

    def set_origin(self, x,y):
        if self.i % 2 == 0:
            GridElement.set_origin(self, x, y)
        else:
            GridElement.set_origin(self, x, y+self.height)

    def on_render(self, sprite):
        sprite.graphics.clear()
        if self.i % 2 == 1:
            sprite.graphics.triangle(0,0, self.width,-1 * self.height)
        else:
            sprite.graphics.triangle(0,0, self.width,self.height)
        sprite.graphics.set_line_style(self.stroke_width)
        sprite.graphics.fill_preserve(self.color_foreground)
        sprite.graphics.stroke(self.color_stroke)

    def create_sprite(self):
        t = GridElement.create_sprite(self)
        if self.i % 2 == 1:
            t.height = -1 * t.height
        return t


class RectangularGridElement(GridElement):
    x_spacing_factor = 1
    y_spacing_factor = 1
    def __init__(self, i,j, height,width, **args):
        GridElement.__init__(self, i,j, height,width, **args)

    def set_origin(self, x,y):
        GridElement.set_origin(self, x, y)

    def on_render(self, sprite):
        sprite.graphics.clear()
        sprite.graphics.rectangle(0, 0, self.width, self.height)
        sprite.graphics.set_line_style(self.stroke_width)
        sprite.graphics.fill_preserve(self.color_foreground)
        sprite.graphics.stroke(self.color_stroke)


class HexagonalGridElement(GridElement):
    x_spacing_factor = 0.75
    y_spacing_factor = 0.866
    def __init__(self, i,j, height,width, **args):
        GridElement.__init__(self, i,j, height,width, **args)

    def set_origin(self, x,y):
        if self.i % 2 == 1:
            GridElement.set_origin(self, x, y + self.height/2 * 0.866)
        else:
            GridElement.set_origin(self, x, y)

    def on_render(self, sprite):
        sprite.graphics.clear()
        sprite.graphics.hexagon(0,0, self.height)
        sprite.graphics.set_line_style(self.stroke_width)
        sprite.graphics.fill_preserve(self.color_foreground)
        sprite.graphics.stroke(self.color_stroke)


class Scene(graphics.Scene):
    '''
    '''
    ELEMENT_CLASSES = [
        RectangularGridElement,
        HexagonalGridElement,
        TriangularGridElement,
        ]

    def __init__(self, width, height):
        assert(width)
        assert(height)

        graphics.Scene.__init__(self)
        self.background_color = "#000"
        self.element_number = 0
        self.size = 60
        self.margin = 30
        self.cols = 0
        self.rows = 0
        self.old_width = width
        self.old_height = height

        self.connect('on-mouse-over', self.on_mouse_over)
        self.connect('on-mouse-out', self.on_mouse_out)
        self.connect('on-resize', self.on_resize)
        self.create_grid(self.margin, self.margin, width-self.margin, height-self.margin)

    def cols_visible(self):
        '''Calculate the number of cols that should fit in the current window dimensions'''
        w = self.width
        if w is None:
            w = self.old_width
        return int( (w - 2*self.margin) / self.grid.x_spacing )

    def rows_visible(self):
        '''Calculate the number of cols that should fit in the current window dimensions'''
        h = self.height
        if h is None:
            h = self.old_height
        return int( (h - 2*self.margin) / self.grid.y_spacing )

    def create_element(self, cls, i, j):
        '''Create a sprite element of type cls at the given location'''
        if j % 2 == i % 2:
            color = "#060"
        else:
            color = "#666"
        e = cls(i, j, height=self.size, width=self.size,
                color_foreground=color,
                color_stroke="#000",
                stroke_width=2)
        self.grid.add(e)

    def set_action(self, i, j, on_click):
        '''Hook a handler to the on-click event of the object at the given coordinates'''
        e = self.grid.get(i, j)
        if not e:
            return
        e.on_click = on_click
        if e.on_click:
            e.color_foreground = "#0a0"
        elif j % 2 == i % 2:
            e.color_foreground = "#060"
        else:
            e.color_foreground = "#666"

    def create_grid(self, x, y, width, height):
        '''Builds a new width x height sized grid at the given screen position'''
        self.grid = Grid(x=x, y=y)
        cls = self.ELEMENT_CLASSES[0]
        self.grid.x_spacing = self.size * cls.x_spacing_factor
        self.grid.y_spacing = self.size * cls.y_spacing_factor
        self.add_child(self.grid)

        self.cols = self.cols_visible()
        self.rows = self.rows_visible()

        for i in range(0, self.cols):
            for j in range(0, self.rows):
                self.create_element(cls, i, j)

        # Add next and forward links
        self.set_action(0, 0, self.prev_grid_type)
        self.set_action(self.cols-1, 0, self.next_grid_type)

    def _set_grid_type(self, element_number):
        '''Switch to different type of grid, and redraw'''
        self.element_number = element_number
        cls = self.ELEMENT_CLASSES[self.element_number]
        for e in self.grid.elements():
            new_e = cls(e.i, e.j, self.size, self.size, **e.args)
            new_e.on_click = e.on_click
            self.grid.set(e.i, e.j, new_e)
        self.grid.x_spacing = self.size * new_e.x_spacing_factor
        self.grid.y_spacing = self.size * new_e.y_spacing_factor
        self._resize_grid()
        self.grid.on_render(new_e)

    def prev_grid_type(self, widget, event):
        self._set_grid_type( (self.element_number - 1) % len(self.ELEMENT_CLASSES))

    def next_grid_type(self, widget, event):
        self._set_grid_type( (self.element_number + 1) % len(self.ELEMENT_CLASSES))

    def _resize_grid(self):
        '''Add or remove cols and rows to fill window'''
        cls = self.ELEMENT_CLASSES[self.element_number]

        # Remove all the links
        self.set_action(0, 0, None)
        self.set_action(self.cols-1, 0, None)

        # Resize X
        old_cols = self.cols
        new_cols = self.cols_visible()
        if new_cols > old_cols:
            # Add more columns to the grid
            for i in range(old_cols, new_cols):
                for j in range(0, self.rows):
                    self.create_element(cls, i,j)
        elif new_cols < old_cols:
            # Remove unneeded columns
            for i in range(new_cols, old_cols):
                for j in range(0, self.rows):
                    self.grid.remove(i, j)
        self.cols = new_cols

        # Resize Y
        old_rows = self.rows
        new_rows = self.rows_visible()
        if new_rows > old_rows:
            # Add more rows to the grid
            for j in range(old_rows, new_rows):
                for i in range(0, self.cols):
                    self.create_element(cls, i, j)
        elif new_rows < old_rows:
            # Remove unneeded rows
            for j in range(new_rows, old_rows):
                for i in range(0, self.cols):
                    self.grid.remove(i, j)
        self.rows = new_rows

        # Re-add links in their new locations
        self.set_action(0, 0, self.prev_grid_type)
        self.set_action(self.cols-1, 0, self.next_grid_type)

    def on_resize(self, scene, event):
        self._resize_grid()
        self.grid.on_render(scene)

    def on_mouse_over(self, scene, sprite):
        if not sprite: return # ignore blank clicks
        if self.tweener.get_tweens(sprite): return
        tmp = sprite.color_foreground
        sprite.color_foreground = sprite.color_stroke
        sprite.color_stroke = tmp

    def on_mouse_out(self, scene, sprite):
        if not sprite: return
        tmp = sprite.color_foreground
        sprite.color_foreground = sprite.color_stroke
        sprite.color_stroke = tmp


if __name__ == '__main__':
    import gtk

    class BasicWindow:
        def __init__(self):
            window = gtk.Window(gtk.WINDOW_TOPLEVEL)
            window.set_default_size(800, 800)
            window.connect("delete_event", lambda *args: gtk.main_quit())
            window.add(Scene(800, 800))
            window.show_all()

    window = BasicWindow()
    gtk.main()
