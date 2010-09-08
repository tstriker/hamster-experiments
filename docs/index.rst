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

**on-render** *()* fired before rendering the sprite, in case if any of the class attributes have changed (except for transformations as those are handled by matrixes, not sprite graphics).
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

Now, normally if you would change the color attribute of the Ball class nothing
would happen as the sprite draws whatever there currently is in the instructions.
But as the on_render will be called whenever a class attribute changes, this will
trigger redrawal, and so the ball will correctly show the new color.

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


.. _primitives:

Sprites: Icons and images
=================
Load icons and images as :class:`Sprite` objects. :class:`Image` and
:class:`Icon` both are subclasses of :class:`Bitmap` which performs data
caching in a surface similar to target. That basically makes sure that redraws
are low on CPU and conversion between source and destination is performed just
once. They are fully fledges sprites, so all the interaction and transformation
bits are there.

.. autoclass:: graphics.Image
   :members:

.. autoclass:: graphics.Icon
   :members:

.. autoclass:: graphics.Bitmap
   :members:

Sprites: Primitives
==========
A few shapes to speed up your drawing. They are full fledged Sprites.

.. autoclass:: graphics.Circle
   :members:

.. autoclass:: graphics.Rectangle
   :members:


.. autoclass:: graphics.Polygon
   :members:

.. autoclass:: graphics.Label
   :members:



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
