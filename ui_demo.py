#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2011 Toms Bauģis <toms.baugis at gmail.com>

sample_text = "And now for something totally different! A label that not only supports newlines but also wraps and perhaps even triggers scroll. All we essentially want here, is a lot of text to play with. A few lines. Five or seven or seventeen. Well i think you should have caught the drift by now!"
accordion_text = "My contents - merely a label, nothing impressive. But i'll still try to pack lots of text in it. My contents - merely a label, nothing impressive. But i'll still try to pack lots of text in it. My contents - merely a label, nothing impressive. But i'll still try to pack lots of text in it. My contents - merely a label, nothing impressive. But i'll still try to pack lots of text in it. My contents - merely a label, nothing impressive. But i'll still try to pack lots of text in it. My contents - merely a label, nothing impressive. But i'll still try to pack lots of text in it. My contents - merely a label, nothing impressive. But i'll still try to pack lots of text in it. My contents - merely a label, nothing impressive. But i'll still try to pack lots of text in it."

from themes import utils
utils.install_font("danube_regular.ttf")

from gi.repository import Gtk as gtk
from gi.repository import Pango as pango

from lib import graphics
import ui
from themes import bitmaps
import datetime as dt


class Rectangle(ui.Container):
    """rectangle is good for forgetting it's dimensions"""
    def __init__(self, width = 10, height = 10, fill_color = "#ccc", **kwargs):
        ui.Container.__init__(self, width = width, height = height, **kwargs)

        self.interactive = True
        self.fill_color = fill_color

        self.connect("on-render", self.on_render)

    def on_render(self, sprite):
        self.graphics.set_line_style(width = 1)
        self.graphics.rectangle(0.5, 0.5, self.width, self.height)
        self.graphics.fill_stroke(self.fill_color, "#666")




class Scene(graphics.Scene):
    def __init__(self):
        now = dt.datetime.now()

        graphics.Scene.__init__(self)

        self.notebook = ui.Notebook(tab_position = "top-left", scroll_position="end", show_scroll = "auto_invisible", scroll_selects_tab = False)

        # boxes packed and nested horizontally and vertically, with a draggable corner
        self.box = ui.HBox(spacing = 3, x=10, y=10)
        self.button = ui.Button("My image changes position", image = graphics.Image("assets/hamster.png"), fill = False)
        self.button.connect("on-click", self.on_button_click)

        self.box.add_child(*[ui.VBox([self.button,
                                      ui.ToggleButton("I'm a toggle button! Have a tooltip too!", image = graphics.Image("assets/day.png"), fill = True, tooltip="Oh hey there, i'm a tooltip!"),
                                      ui.Label("I'm a label \nand we all can wrap", image = graphics.Image("assets/week.png"), spacing = 5, padding = 5, x_align = 0),
                                      ui.Entry("Feel free to edit me! I'm a rather long text that will scroll nicely perhaps. No guarantees though!", expand = False),
                                      ui.Entry("And me too perhaps", expand = False)],
                                     spacing = 5, padding = 10),
                             Rectangle(20, expand = False),
                             graphics.Label("rrrr", color="#666"),
                             Rectangle(20, expand = False),
                             ui.VBox([Rectangle(fill = False), Rectangle(), Rectangle()], spacing = 3)
                             ])


        box_w, box_h = self.box.get_min_size()
        self.corner = graphics.Rectangle(10, 10, fill="#666",
                                         x = self.box.x + box_w,
                                         y = self.box.y + box_h,
                                         draggable=True,
                                         interactive=True,
                                         z_order = 100)
        self.corner.connect("on-drag", self.on_corner_drag)


        # a table
        self.table = ui.Table(3, 3, snap_to_pixel = False, padding=10)
        self.table.attach(Rectangle(fill_color = "#f00", expand_vert = False), 0, 3, 0, 1) # top
        self.table.attach(Rectangle(fill_color = "#0f0", expand = False), 2, 3, 1, 2)      # right
        self.table.attach(Rectangle(fill_color = "#f0f", expand_vert = False), 0, 3, 2, 3) # bottom
        self.table.attach(Rectangle(fill_color = "#0ff", expand = False), 0, 1, 1, 2)      # left
        center = Rectangle()
        center.connect("on-mouse-over", self.on_table_mouse_over)
        center.connect("on-mouse-out", self.on_table_mouse_out)
        self.table.attach(center, 1, 2, 1, 2)


        # a scroll area with something to scroll in it
        self.scroll = ui.ScrollArea(border = 0)
        self.scroll.add_child(ui.Container(ui.Button("Scroll me if you can!", width = 1000, height = 300, fill=False), fill = False, padding=15))


        # bunch of different input elements
        inputs = ui.Panes(padding=10)
        listitem = ui.ListItem(["Sugar", "Spice", "Everything Nice", "--", "Feel",
                                "Free", "To", "Click", "On", "Me", {'markup': "<span color='red'>And</span>"},
                                "Use", "The", "Arrows!", "Ah", "And", "It", "Seems",
                                "That", "There", "Are", "So", "Many", "Elements"])

        def print_selection(listitem, item):
            print "selection", item

        def print_change(listitem, item):
            print "change", item

        listitem.connect("on-change", print_change)
        listitem.connect("on-select", print_selection)
        inputs.add_child(listitem)

        one = ui.ToggleButton("One", margin=[15, 10, 20, 30], id="one")

        group1 = ui.Group([one,
                           ui.ToggleButton("Two", scale_x = 0.5, scale_y = 0.5, expand=False, id="two"),
                           ui.ToggleButton("Three", id="three"),
                           ui.ToggleButton("Four", id="four")],
                          expand = False, allow_no_selection=True)
        label1 = ui.Label("Current value: none selected", x_align=0, expand = False)
        def on_toggle1(group, current_item):
            if current_item:
                label1.text = "Current value: %s" % current_item.label
            else:
                label1.text = "No item selected"
        group1.connect("on-change", on_toggle1)

        group2 = ui.Group([ui.RadioButton("One"),
                           ui.RadioButton("Two"),
                           ui.RadioButton("Three"),
                           ui.RadioButton("Four")],
                          horizontal = False)
        label2 = ui.Label("Current value: none selected", x_align = 0, expand=False)
        def on_toggle2(group, current_item):
            label2.text = "Current value: %s" % current_item.label
        group2.connect("on-change", on_toggle2)

        slider = ui.Slider(range(100),
                           expand = False,
                           snap_to_ticks = False,
                           range=True,
                           selection=(23, 80),
                           grips_can_cross = False,
                           snap_points = [5, 20, 50, 75],
                           snap_on_release = True)
        slider_value = ui.Label(" ")
        def on_slider_change(slider, value):
            slider_value.text = str(value)
        slider.connect("on_change", on_slider_change)

        spinner = ui.Spinner(active = False, expand=False, width = 40)
        spinner_button = ui.Button("Toggle spin", expand=False)
        spinner_button.spinner = spinner

        def on_spinner_button_click(button, event):
            button.spinner.active = not button.spinner.active
        spinner_button.connect("on-click", on_spinner_button_click)

        combo = ui.ComboBox(["Sugar", "Spice", "Everything Nice", "And", "Other", "Nice", "Things"],
                             open_below=True,
                             expand = False)
        inputs.add_child(ui.VBox([combo,
                                  group1, label1,
                                  ui.HBox([group2,
                                           ui.VBox([ui.CheckButton("And a few of those", expand = False),
                                                    ui.CheckButton("Check boxes", expand = False),
                                                    ui.CheckButton("Which don't work for groups", expand = False)])
                                          ]),
                                  label2,
                                  slider,
                                  slider_value,
                                  ui.HBox([spinner, spinner_button], expand=False, spacing = 10),
                                  ui.HBox([ui.ScrollArea(ui.Label(sample_text * 3, overflow = pango.WrapMode.WORD, fill=True, padding=[2, 5]), height=45, scroll_horizontal=False),
                                           ui.SpinButton(expand = False, fill=False)], expand = False),
                                  ],
                                 expand = False, spacing = 10))

        combo.rows = ["some", "things", "are", "made", "of", "bananas", "and", "icecream"]


        menu = ui.Menu([ui.MenuItem(label="One", menu=ui.Menu([ui.MenuItem(label="One one", menu=ui.Menu([ui.MenuItem(label="One one one"),
                                                                                                          ui.MenuItem(label="One one two"),
                                                                                                          ui.MenuSeparator(),
                                                                                                          ui.MenuItem(label="One one three")])),
                                                               ui.MenuSeparator(),
                                                               ui.MenuItem(label="One two", mnemonic="Ctrl+1"),
                                                               ui.MenuItem(label="One three", mnemonic="Alt+1")])),

                        ui.MenuItem(label="Two", menu=ui.Menu([ui.MenuItem(label="Two one", mnemonic="Ctrl+Alt+2"),
                                                               ui.MenuItem(label="Two two", mnemonic="Ctrl+2"),
                                                               ui.MenuSeparator(),
                                                               ui.MenuItem(label="Two three", mnemonic="Alt+2")])),

                        ui.MenuItem(label="Three", menu=ui.Menu([ui.MenuItem(label="Three one", mnemonic="Ctrl+Alt+3"),
                                                                 ui.MenuItem(label="Three two", mnemonic="Ctrl+3"),
                                                                 ui.MenuSeparator(),
                                                                 ui.MenuItem(label="Three three", mnemonic="Alt+3")])),
                        ui.MenuItem(label="Four", menu=ui.Menu([ui.MenuItem(label="Four one", mnemonic="Ctrl+Alt+4"),
                                                                ui.MenuItem(label="Four two", mnemonic="Ctrl+4"),
                                                                ui.MenuSeparator(),
                                                                ui.MenuItem(label="Four three", mnemonic="Alt+4")])),
                       ], horizontal=True)

        self.menu_selection_label = ui.Label("Pick a menu item!", expand = False, x_align = 1)
        def on_menuitem_selected(menu, item, event):
            self.menu_selection_label.text = item.label
        menu.connect("selected", on_menuitem_selected)

        # adding notebook and attaching pages
        self.notebook.add_page(ui.NotebookTab(image=graphics.Image("assets/day.png"), label="boxes", padding=[1,5]),
                               ui.Fixed([self.box, self.corner], x = 10, y = 10))
        self.notebook.add_page(ui.NotebookTab("Table", tooltip="Oh hey, i'm a table!"), self.table)
        self.notebook.add_page("Scroll Area", self.scroll)
        self.notebook.add_page("Input Elements", inputs)

        self.notebook.add_page("Menu", ui.VBox([menu, self.menu_selection_label,
                                                ui.HBox(ui.Menu([ui.MenuItem(label="", image = graphics.Image("assets/day.png"), submenu_offset_x = 0, submenu_offset_y = 0,
                                                                       menu=ui.Menu([ui.MenuItem(label="", image = graphics.Image("assets/month.png")),
                                                                                     ui.MenuItem(label="", image = graphics.Image("assets/hamster.png")),
                                                                                     ui.MenuSeparator(),
                                                                                     ui.MenuItem(label="", image = graphics.Image("assets/hamster.png")),
                                                                                     ui.MenuItem(label="", image = graphics.Image("assets/month.png"))], horizontal=True)),
                                                                 ui.MenuItem(label="", image = graphics.Image("assets/hamster.png"),submenu_offset_x = 0, submenu_offset_y = 0,
                                                                       menu=ui.Menu([ui.MenuItem(label="", image = graphics.Image("assets/month.png")),
                                                                                     ui.MenuItem(label="", image = graphics.Image("assets/month.png")),
                                                                                     ui.MenuItem(label="", image = graphics.Image("assets/week.png")),
                                                                                     ui.MenuSeparator(),
                                                                                     ui.MenuItem(label="", image = graphics.Image("assets/month.png"))], horizontal=True)),
                                                                 ui.MenuItem(label="", image = graphics.Image("assets/month.png"), submenu_offset_x = 0, submenu_offset_y = 0,
                                                                       menu=ui.Menu([ui.MenuItem(label="", image = graphics.Image("assets/week.png")),
                                                                                     ui.MenuItem(label="", image = graphics.Image("assets/week.png")),
                                                                                     ui.MenuSeparator(),
                                                                                     ui.MenuItem(label="", image = graphics.Image("assets/week.png")),
                                                                                     ui.MenuItem(label="", image = graphics.Image("assets/month.png"))], horizontal=True)),
                                                                ], horizontal=False, spacing=50, hide_on_leave = True, open_on_hover = 0.01), expand=False),
                                                ui.Box()], padding=10))



        self.slice_image = ui.Image('assets/slice9.png', fill=True, slice_left = 35, slice_right = 230, slice_top = 35, slice_bottom = 220)

        data = []
        image = graphics.Image("assets/day.png")
        for i in range(10):
            data.append(["aasdf asdfasdf asdfasdf", "basdfasdf asdfasdf asdfasdf", image, "rrr"])
            data.append(["1", "2", None, "rrr"])
            data.append(["4", "5", None, "rrr"])

        tree = ui.ListItem(data,
                           [ui.LabelRenderer(editable=True),
                            ui.LabelRenderer(editable=True),
                            ui.ImageRenderer(expand=False, width=90)],
                           headers=["Text", "More text", "An icon!"],
                           fixed_headers = False,
                           scroll_border = 0
                           )
        self.notebook.add_page("Tree View", tree)

        #tree.data[0][1] = "I was actually modified afterwards!"


        self.notebook.add_page("Accordion", ui.Accordion([
            ui.AccordionPage("I'm am the first in the row", [ui.Label(accordion_text, overflow = pango.WrapMode.WORD, padding=5)]),
            ui.AccordionPage("I'm am the first in the row", [ui.Label(accordion_text, overflow = pango.WrapMode.WORD, padding=5)]),
            ui.AccordionPage("I'm am the first in the row", [ui.Label(accordion_text, overflow = pango.WrapMode.WORD, padding=5)]),
            ui.AccordionPage("I'm am the first in the row", [ui.Label(accordion_text, overflow = pango.WrapMode.WORD, padding=5)]),
            ui.AccordionPage("I'm am the first in the row", [ui.Label(accordion_text, overflow = pango.WrapMode.WORD, padding=5)]),
            ui.AccordionPage("I'm am the first in the row", [ui.Label(accordion_text, overflow = pango.WrapMode.WORD, padding=5)]),
            ui.AccordionPage("I'm am the first in the row", [ui.Label(accordion_text, overflow = pango.WrapMode.WORD, padding=5)]),
            ui.AccordionPage("I'm am the first in the row", [ui.Label(accordion_text, overflow = pango.WrapMode.WORD, padding=5)]),
            ui.AccordionPage("I'm am the first in the row", [ui.Label(accordion_text, overflow = pango.WrapMode.WORD, padding=5)]),
            ui.AccordionPage("I'm am the first in the row", [ui.Label(accordion_text, overflow = pango.WrapMode.WORD, padding=5)]),
            ui.AccordionPage("I'm am the first in the row", [ui.Label(accordion_text, overflow = pango.WrapMode.WORD, padding=5)]),
            ui.AccordionPage("I'm different!", [
                ui.VBox([
                    ui.Button("I'm a button", fill=False, expand=False),
                    ui.Button("I'm another one", fill=False, expand=False),
                    ui.Group([
                        ui.ToggleButton("We"),
                        ui.ToggleButton("Are"),
                        ui.ToggleButton("Brothers"),
                        ui.ToggleButton("Radio Brothers"),
                    ], expand=False)
                ], expand=False)
            ]),
        ], padding_top = 1, padding_left = 1))

        from pie_menu import Menu
        pie_menu = Menu(0, 0)
        pie_menu.y_align = 0.45

        self.magic_box = ui.VBox([ui.HBox([ui.Button("Hello", expand=False),
                                           ui.Button("Thar", expand=False),
                                           ui.Label("Drag the white area around", x_align=1)], expand=False, padding=5),
                                  pie_menu], x=50, y=50, spacing=50, draggable=True)
        self.magic_box.width = 500
        self.magic_box.height = 400
        def just_fill():
            box = self.magic_box
            box.graphics.fill_area(0, 0, box.width, box.height, "#fefefe")
        self.magic_box.do_render = just_fill
        self.notebook.add_page("Ordinary Sprite", ui.Fixed(self.magic_box))

        for i in range(5):
            self.notebook.add_page("Tab %d" % i)


        self.notebook.current_page = 3


        # a little button to change tab orientation
        self.tab_orient_switch = ui.Button("Change tab attachment", expand=False, tooltip="change")
        self.tab_orient_switch.connect("on-click", self.on_tab_orient_click)

        self.page_disablist = ui.Button("Enable/Disable current tab", expand=False, tooltip="disable")
        self.page_disablist.connect("on-click", self.on_page_disablist_click)

        self.dialog_button = ui.Button("Show a dialog", expand=False, tooltip="show")
        self.dialog_button.connect("on-click", self.on_dialog_button_click)


        top_menu = ui.Menu([ui.MenuItem(label="One", menu=ui.Menu([ui.MenuItem(label="One one oh one oh one etc etc",
                                                                               menu=ui.Menu([ui.MenuItem(label="One one one"),
                                                                                    ui.MenuItem(label="One one two"),
                                                                                    ui.MenuItem(label="One one three")])),
                                                                   ui.MenuItem(label="One two"),
                                                                   ui.MenuItem(label="One three")])),
                            ui.MenuItem(label="Two", menu=ui.Menu([ui.MenuItem(label="Two one"),
                                                        ui.MenuItem(label="Two two"),
                                                        ui.MenuItem(label="Two three")])),
                            ui.MenuItem(label="Three", menu=ui.Menu([ui.MenuItem(label="Three one"),
                                                          ui.MenuItem(label="Three two"),
                                                          ui.MenuItem(label="Three three")])),
                            ui.MenuItem(label="Four", menu=ui.Menu([ui.MenuItem(label="Four one"),
                                                         ui.MenuItem(label="Four two"),
                                                         ui.MenuItem(label="Four three")])),
                            ui.MenuItem(label="Five")
                            ], horizontal=True, disable_toggling=True)


        # not sure how elegant but let's override the flow for now for demo purposes!
        dummy_flow = ui.Flow()
        def flow_resize():
            dummy_flow.alloc_w, dummy_flow.alloc_h = top_menu.alloc_w, top_menu.alloc_h
            dummy_flow.sprites = top_menu.sprites
            dummy_flow.resize_children()
            top_menu.height = top_menu.sprites[-1].y + top_menu.sprites[-1].height

        def flow_height_for_width_size():
            dummy_flow.alloc_w, dummy_flow.alloc_h = top_menu.alloc_w, top_menu.alloc_h
            dummy_flow.sprites = top_menu.sprites
            w, h = dummy_flow.get_height_for_width_size()
            return w, h

        def flow_min_size():
            dummy_flow.sprites = top_menu.sprites
            w, h = dummy_flow.get_min_size()
            return w+ top_menu.horizontal_padding, h  + top_menu.vertical_padding

        # flow if b0rken ATM
        for i in range(20):
            top_menu.add_child(ui.MenuItem(label="flow %d" % i))
        top_menu.resize_children = flow_resize
        #top_menu.get_height_for_width_size = flow_height_for_width_size
        top_menu.get_min_size = flow_min_size





        self.add_child(ui.VBox([top_menu, ui.VBox([self.notebook,
                                                   ui.HBox([self.tab_orient_switch,
                                                            self.page_disablist,
                                                            self.dialog_button], expand = False, fill=False, x_align=1),
                               ], padding=20, spacing=10)], spacing = 10))






        self.connect("on-click", self.on_click)

        self.notebook.after_tabs.add_child(ui.Button("Yohoho"))
        print dt.datetime.now() - now

    def on_tab_orient_click(self, button, event):
        orient = ["left-top", "left-center", "left-bottom",
                  "bottom-left", "bottom-center", "bottom-right",
                  "right-bottom", "right-center", "right-top",
                  "top-right", "top-center", "top-left"]
        self.notebook.tab_position = orient[orient.index(self.notebook.tab_position) -1]
        self.notebook._position_contents()

    def on_page_disablist_click(self, button, event):
        self.notebook.current_page.enabled = not self.notebook.current_page.enabled

    def on_dialog_button_click(self, button, event):
        dialog = ui.ConfirmationDialog("It's friday",
                                       "If you agree, Rebecca will be taking the back seat this time ah noes i'll never fit here. I should wrap for sure, but will that happen? Oh who knows! If you agree, Rebecca will be taking the back seat this time ah noes i'll never fit here. I should wrap for sure, but will that happen? Oh who knows! I should wrap for sure, but will that happen? Oh who knows! If you agree, Rebecca will be taking the back seat this time ah noes i'll never fit here. I should wrap for sure, but will that happen? Oh who knows!",
                                       "Cancel", "I'm fine with that!")
        dialog.show(self)


    def on_button_click(self, button, event):
        orient = ["left", "bottom", "right", "top"]
        button.image_position = orient[orient.index(button.image_position) -1]


    def on_table_mouse_over(self, sprite):
        self.table.animate(vertical_spacing = 10, horizontal_spacing = 10)

    def on_table_mouse_out(self, sprite):
        self.table.animate(vertical_spacing = 0, horizontal_spacing = 0)


    def on_click(self, scene, event, elem):
        if elem and isinstance(elem, Rectangle):
            elem.expand = not elem.expand
            self.redraw()


    def on_corner_drag(self, corner, event):
        min_x, min_y = self.box.get_min_size()

        self.box.alloc_w = max(corner.x - self.box.x + 5, min_x)
        self.box.alloc_h = max(corner.y - self.box.y + 5, min_y)

        self.corner.x = self.box.x + self.box.alloc_w - 5
        self.corner.y = self.box.y + self.box.alloc_h - 5
        self.redraw()



class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_default_size(800, 600)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        scene = Scene()
        w, h = scene.notebook.get_min_size()
        window.set_size_request(int(w), int(h))
        window.add(scene)
        window.show_all()


if __name__ == '__main__':
    window = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
