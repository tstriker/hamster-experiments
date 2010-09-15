.. _graphics:
.. currentmodule:: graphics


****************
hamster.graphics
****************

The hamster graphics library is a sprite-styled abstraction layer on top of
pygtk and cairo.
Create a :class:`Scene` and add it to the window. Then you can start
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

.. autoclass:: Scene
   :members:
   :inherited-members:


Scene signals
--------------
Subscribe to signals using the `connect(signal, callback)` function of scene.

**on-enter-frame** *(context)*
- fired before drawing sprites and will pass context to the listener

**on-finish-frame** *(context)*
- fired after sprites have been drawn

**on-click** (`button_press_event <http://www.pygtk.org/docs/pygtk/class-gdkevent.html#id2898704>`_, target_sprite)

**on-drag-start** (`motion_notify_event <http://www.pygtk.org/docs/pygtk/class-gdkevent.html#id2920267>`_,
drag_sprite)

**on-drag** (`motion_notify_event <http://www.pygtk.org/docs/pygtk/class-gdkevent.html#id2920267>`_,
drag_sprite) - fired on each drag motion

**on-drag-finish** (`motion_notify_event <http://www.pygtk.org/docs/pygtk/class-gdkevent.html#id2920267>`_,
drag_sprite)

**on-mouse-move** (`motion_notify_event <http://www.pygtk.org/docs/pygtk/class-gdkevent.html#id2920267>`_)

**on-mouse-down** (`button_press_event <http://www.pygtk.org/docs/pygtk/class-gdkevent.html#id2898704>`_)
- fired when a mouse button is pressed down.

**on-mouse-up** (`button_press_event <http://www.pygtk.org/docs/pygtk/class-gdkevent.html#id2898704>`_)
- fired when a mouse button is released

**on-mouse-over** (target_sprite)
- fired when mouse cursor moves over an interactive sprite.

**on-mouse-out** (target_sprite)
- fired when mouse cursor leaves an interactive sprite.

**on-scroll** (`scroll_event <http://www.pygtk.org/docs/pygtk/class-gdkevent.html#id2981883>`_)
- fired on scroll wheel motion


:class:`Sprite` objects
========================

.. autoclass:: Sprite
   :members:


Sprite signals
---------------

Subscribe to signals using the `connect(signal, callback)` function of sprite.

**on-mouse-over()**
- fired when cursor moves over the sprite.

**on-mouse-out()**
- fired when cursor leaves the sprite.

**on-click** (`button_press_event <http://www.pygtk.org/docs/pygtk/class-gdkevent.html#id2898704>`_)

**on-drag-start** (`motion_notify_event <http://www.pygtk.org/docs/pygtk/class-gdkevent.html#id2920267>`_)

**on-drag** (`motion_notify_event <http://www.pygtk.org/docs/pygtk/class-gdkevent.html#id2920267>`_)
- fired on every drag motion

**on-drag-finish** (`motion_notify_event <http://www.pygtk.org/docs/pygtk/class-gdkevent.html#id2920267>`_)

**on-render** *()* fired before rendering the sprite in case if any of the class attributes have changed (except for transformations as those are handled by matrixes, not sprite graphics).
Example::

    class Ball(graphics.Sprite):
        def __init__(self, color):
            graphics.Sprite.__init__(self)
            self.color = color
            self.connect("on-render", self.on_render)

        def on_render(self, sprite):
            self.graphics.clear() # clear any previous state
            self.graphics.circle(0, 0, 10)
            self.graphics.fill(self.color) # fill with the whatever color we have at the moment

Normally if you would change the color attribute of the Ball class nothing
would happen as the sprite draws whatever there currently is in the instructions.
But as the on_render will be called whenever a class attribute changes, this will
trigger a redraw, and so the ball sprite will correctly render with the new color.

.. _graphics.Graphics:

:class:`Graphics` class
========================
:class:`Scene` and :class:`Sprite` objects have a graphics attribute that
is an instance of :class:`Graphics` class. All the drawing is performed by
calling functions of this class.
By passing in `Cairo context <http://cairographics.org/documentation/pycairo/2/reference/context.html>`_
into constructor the :class:`Graphics` class can also be used on it's own.

.. autoclass:: Graphics
   :members:
   :undoc-members:


.. _primitives:

Sprites: Icons and images
==========================
Load icons and images as :class:`Sprite` objects.

:class:`Image` and :class:`Icon` both are subclasses of :class:`BitmapSprite`
which performs data caching in a surface similar to target. That basically makes
sure that redraws are low on CPU and conversion between source and destination
is performed just once. They are fully fledges sprites, so all the interaction
and transformation bits are there.

.. autoclass:: Image
   :members:

.. autoclass:: Icon
   :members:

.. autoclass:: BitmapSprite
   :members:

Sprites: Primitives
====================
A few shapes to speed up your drawing. They are full fledged Sprites.

.. autoclass:: Circle
   :members:

.. autoclass:: Rectangle
   :members:


.. autoclass:: Polygon
   :members:

.. autoclass:: Label
   :members:



The Tweener
============
You can use the tweener on it's own but must convenient is to use the
:func:`animate` function of :class:`Scene`, or alternatively the :data:`Scene.tweener`
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
