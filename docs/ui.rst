:mod:`ui` -- User interface toolkit
====================================
.. module:: ui
   :synopsis: User interaction widgets (sophisticated sprites).

.. py:currentmodule:: ui

The user interface toolkit lets you extend your graphical applications by adding
fully customizable interface elements to them. Widgets include
:class:`~buttons.Button` for buttons, :class:`~entry.Entry` and
:class:`~entry.TextArea` for single and multi-line text input,
:class:`~listitem.ListItem` for list items, and many more.
Containers for packing widgets are available too. see :ref:`containers` for the
full list.

**Hello ui world**::

    from gi.repository import Gtk as gtk
    from lib import graphics
    import ui

    class Scene(graphics.Scene):
        def __init__(self):
            graphics.Scene.__init__(self)

            # here we pack the button in VBox and then in HBox.
            # And by disabling fill effectively center it.
            self.add_child(ui.VBox(ui.HBox(ui.Button("Click me!"), fill=False)))

    window = gtk.Window()
    window.add(Scene())
    window.show_all()
    gtk.main()

The toolkit is copying widget and attribute names from gtk where it is
possible and makes sense, but sometimes it goes beyond that to make it
more pythonic and more easy to work with. On the other hand, it also does less -
the functionality gets added to when necessary. So your milage may vary, but
don't be afraid to go into the source and read the code.

The standard gtk toolkit is recommended in most cases. But sometimes when you
need to go beyond the limits of static layouts and don't want to struggle with
gtk.Fixed to arbitrary position input elements, as well if you want to override
the looks of some of the widgets - this is where hamster ui toolkit comes in.

All of the widgets and containers descend from :class:`graphics.Sprite` so
you can do everything that you can do with a sprite.


********************
Base class - Widget
********************
.. currentmodule:: ui.widget


.. autoclass:: ui.widget.Widget
   :members:



.. currentmodule:: ui


.. _containers:

**********
Containers
**********

Use containers to align and pack widgets. All containers accept contents as
the first parameter so you can add children right at the moment of
construction. It should be either a sprite or list of sprites and you can
use it to add children directly in the moment of construction.

Example::

    # create a vertical box with three labels in it
    vbox = ui.VBox([ui.Label("one"), ui.Label("two"), ui.Label("three")])


.. automodule:: ui.containers
   :members:

******
Label
******
.. autoclass:: ui.widgets.Label
   :members:


*******
Buttons
*******
.. automodule:: ui.buttons
   :members:


***********
Text input
***********
.. automodule:: ui.entry
   :members: Entry, TextArea


***************************
List items and combo boxes
***************************
.. automodule:: ui.listitem
   :members:

.. automodule:: ui.combobox
   :members:

********
Sliders
********
.. automodule:: ui.slider
   :members:


******
Menus
******
.. automodule:: ui.menu
   :members:


**********************
Notebooks / tab pages
**********************
.. autoclass:: ui.notebook.Notebook
   :members:


**********
Scrolling
**********

.. automodule:: ui.scroll
   :members:

**************
Basic dialogs
**************

.. automodule:: ui.dialog
   :members:


*********************
Customizing tooltips
*********************
.. currentmodule:: ui.widget

It is possible to fully customize the look and behavior of tooltips. For basic
customization, override the :class:`Tooltip` class-level properties. For more
involved customization, refer to :class:`TooltipWindow`


.. autoclass:: ui.widget.Tooltip
   :members:

.. autoclass:: ui.widget.TooltipWindow
   :members:
