****************
hamster.graphics
****************

The hamster graphics library is a sprite-styled abstraction layer on top of
pygtk and cairo.
Create a :class:`graphics.Scene` and add it to the window. Then you can start
adding and manipulating sprites.

**Hello world**::

    import gtk
    from lib import graphics

    class Scene(graphics.Scene):
        def __init__(self):
            graphics.Scene.__init__(self)
            label = graphics.Label("Hello World", 24, "#000", x = 5, y = 5)
            self.add_child(label) # remember to add sprites to the scene

    window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    window.add(Scene())
    window.show_all()
    gtk.main()



The Scene
========================

.. autoclass:: graphics.Scene
   :members:
   :inherited-members:

Scene attributes
------------------

**sprites** - list of sprites in scene

**framerate** - framerate of animation. This will limit how often call for
redraw will be performed (that is - not more often than the framerate). It will
also influence the smoothness of tweeners.

**width, height** - width and height of the scene. Will be `None` until first
expose (that is until first on-enter-frame signal below).

**tweener** - instance of :class:`pytweener.Tweener` that is used by
:func:`animate` function, but can be also accessed directly for advanced control.

**colors** - instance of :class:`Colors` class for color parsing

**mouse_x, self.mouse_y** - last known coordinates of mouse cursor


Scene signals
--------------
Subscribe to signals using the `connect(signal, callback)` function of scene.

**on-enter-frame** *(context)* - fired before drawing sprites and will pass
context to the listener

**on-finish-frame** *(context)* - fired after sprites have been drawn

**on-click** *(mouse_event, affected_sprites)* fired when user clicks in scene.
`mouse_event` is `gtk.gdk.Event for BUTTON_PRESS <http://www.pygtk.org/docs/pygtk/class-gdkevent.html#id2898704>`_.
`affected_sprites` is list of sprites that have been affected by the click.

**on-drag** *(mouse_event, affected_sprites)* - fired when user drags a
sprite. `mouse_event` is `gtk.gdk.Event for MOTION_NOTIFY <http://www.pygtk.org/docs/pygtk/class-gdkevent.html#id2920267>`_.
The signal is emitted also for sprites that have `draggable` disabled.
So you can for example disable automatic dragging but react to the drag motion.

**on-mouse-move** *(mouse_event)* - fired when user moves the mouse.
`mouse_event` is `gtk.gdk.Event for MOTION_NOTIFY <http://www.pygtk.org/docs/pygtk/class-gdkevent.html#id2920267>`_.


**on-mouse-over** *(affected_sprites)* - fired when user moves over any interactive sprite.

**on-mouse-out** *(affected_sprites)* - fired when user leaves an interactive sprite.

**on-mouse-up** *()* - fired when user releases mouse button


:class:`Sprite` objects
========================

.. autoclass:: graphics.Sprite
   :members:


Sprite attributes
--------------------------

**graphics** - instance of :ref:`graphics` for this sprite

**x, y** - coordinates

**pivot_x, pivot_y** - coordinates of the sprites anchor and rotation point

**rotation** - rotation of the sprite in radians

**visible** - boolean visibility flag

**interactive** - boolean denoting whether the sprite responds to mouse events

**draggable** - boolean marking if sprite can be automatically dragged

**opacity** - sprite opacity

**sprites** - list of children sprites

**parent** - pointer to parent :class:`Sprite` or :class:`Scene`




Sprite signals
----------------------

Subscribe to signals using the `connect(signal, callback)` function of sprite.

**on-mouse-over** *()* - fired when user moves over the sprite.

**on-mouse-out** *()* - fired when user leaves the sprite.

**on-click** *(mouse_event)* fired when user clicks on sprite.
`mouse_event` is `gtk.gdk.Event for BUTTON_PRESS <http://www.pygtk.org/docs/pygtk/class-gdkevent.html#id2898704>`_.

**on-drag** *(mouse_event)* - fired when user drags the sprite.
`mouse_event` is `gtk.gdk.Event for MOTION_NOTIFY <http://www.pygtk.org/docs/pygtk/class-gdkevent.html#id2920267>`_.
The signal is emitted also if attribute `draggable` is disabled.


.. _graphics:

:class:`Graphics` class
========================
:class:`Scene` and all :class:`Sprite` objects have a graphics attribute, that
is an instance of :class:`Graphics` class. All the drawing is performed by
calling functions of this attribute.
The :class:`Graphics` class can also be used on it's own, by passing in Cairo
`context` into constructor.

.. autoclass:: graphics.Graphics
   :members:


:class:`Shape` objects
========================
Shape is an abstract class for simple sprites (like :ref:`primitives` below) with stroke and fill.
Implement the draw_shape function (where you can use the .graphics property) to draw the shape.
Leave out stroke and fill instructions, as those will be performed automatically by the shape.

.. autoclass:: graphics.Shape
   :members:
   :inherited-members:


.. _primitives:

Primitives
==========
A few shapes to speed up your drawing.

.. autoclass:: graphics.Circle
   :members:

   Attributes: **fill, stroke, radius**

.. autoclass:: graphics.Rectangle
   :members:

   Attributes: **fill, stroke, width, height, corner_radius**

.. autoclass:: graphics.Polygon
   :members:

   Attributes:

   **fill, stroke** - fill and stroke colors of the poligon

   **points** - list of (x,y) tuples that the line should go through. Polygon
   will automatically close path.

.. autoclass:: graphics.Label
   :members:

   Attributes:

   **text** - label text

   **color** - color of label either as hex string or an (r,g,b) tuple

   **font_desc** - string with pango font description




The Tweener
========================
You can use the tweener on it's own but must convenient is to use the
:func:`animate` function of :class:`Scene`, or alternatively the `Scene.tweener`
that is an instance of this class.

.. autoclass:: pytweener.Tweener
   :members:

.. autoclass:: pytweener.Tween
   :members:

.. autoclass:: pytweener.Easing
   :members:

    Subclasses are: **Back, Bounce, Circ, Cubic, Elastic, Expo, Linear,
    Quad, Quart, Quint, Sine, Strong**

    Example of tweener usage::

      from pytweener import Easing

      scene.animate(my_object, x = 100, easing=Easing.Cubic.ease_out)
