from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import Pango as pango

import cairo
from lib import graphics
import ui
from utils import override, get_image


"""
@override(ui.VBox)
def do_render(self, *args):
    self.graphics.rectangle(0, 0, self.width, self.height)
    image_data = cairo.ImageSurface.create_from_png("themes/assets/background.png")


    pattern = cairo.SurfacePattern(image_data)
    pattern.set_extend(cairo.EXTEND_REPEAT)

    self.graphics.set_source(pattern)
    self.graphics.fill()
"""


""" The theme starts here """

#ui.Entry.font_desc = pango.FontDescription('Danube 8')
#ui.Label.font_desc = pango.FontDescription('Danube 8')

@override(ui.Label)
def do_render(self):
    """the label is looking for an background_image attribute and if it is found
    it paints it"""
    if getattr(self, "background_image", None):
        self.background_image.render(self.graphics, self.width, self.height)

ui.Button.images = {
    "normal": get_image("themes/assets/button_normal.png", 3, 3, 3, 3),
    "highlight": get_image("themes/assets/button_highlight.png", 3, 3, 3, 3),
    "pressed": get_image("themes/assets/button_pressed.png", 3, 3, 3, 3),
    "disabled": get_image("themes/assets/button_disabled.png", 3, 3, 3, 3),
}

ui.Button.font_desc = pango.FontDescription('Serif 10')
@override(ui.Button)
def do_render(self, state=None):
    """ Properties that affect rendering:
        state:   normal / highlight / pressed
        focused: True / False
        enabled: True / False
    """
    state = state or self.state

    if self.enabled:
        self.display_label.color = "#000"
        self.display_label.background_image = None
        image = self.images.get(state)
    else:
        self.display_label.color = "#999"
        image = self.images["disabled"]

    image.render(self.graphics, self.width, self.height)


@override(ui.ToggleButton)
def do_render(self, *args):
    """this example of togglebutton does not sort out the button-group, where
    you would have different graphics for first and last item"""
    state = self.state
    if self.toggled:
        state = "pressed"
    ui.Button.do_render(self, state = state)


ui.Entry.images = {
    "normal": get_image("themes/assets/input_normal.png", 5, 5, 5, 5),
    "disabled":  get_image("themes/assets/input_disabled.png", 5, 5, 5, 5)
}
@override(ui.Entry)
def do_render(self):
    """ Properties that affect rendering:
        state:   normal / highlight / pressed
        focused: True / False
        enabled: True / False
    """
    if self.draw_border:
        image = self.images["normal"] if self.enabled else self.images["disabled"]
        image.render(self.graphics, self.width, self.height)


ui.CheckMark.images = {
    # toggled, enabled - all combinations
    (False, True): get_image("themes/assets/checkbox_normal.png"),
    (True, True):  get_image("themes/assets/checkbox_toggled.png"),
    (False, False): get_image("themes/assets/checkbox_disabled.png"),
    (True, False):  get_image("themes/assets/checkbox_disabled_toggled.png")
}
@override(ui.CheckMark)
def do_render(self, *args):
    """ Properties that affect rendering:
        state:   normal / highlight / pressed
        focused: True / False
        enabled: True / False
    """

    image = self.images[(self.toggled, self.enabled)]
    image.render(self.graphics)




@override(ui.SliderSnapPoint)
def do_render(self):
    """the label is looking for an background_image attribute and if it is found
    it paints it"""
    pass



ui.SliderGrip.grip_image = get_image("themes/assets/slider_knob.png")
ui.SliderGrip.width = ui.SliderGrip.grip_image.width

@override(ui.SliderGrip)
def do_render(self):
    w, h = self.width, self.height
    self.grip_image.render(self.graphics)


ui.Slider.images = {
    "background": get_image("themes/assets/slider_bg.png", 4, 4, 4, 4),
    "fill": get_image("themes/assets/slider_fill.png", 4, 4, 4, 4),
}

@override(ui.Slider)
def do_render(self):
    x = 0
    y = self.start_grip.grip_image.height

    w = self.width
    h = self.images["background"].height

    self.images["background"].render(self.graphics, w, h, x, 3)

    start_x, end_x = self.start_grip.x, self.end_grip.x
    if self.range is True and start_x > end_x:
        start_x, end_x = end_x, start_x


    if self.range == "start":
        self.images['fill'].render(self.graphics, int(start_x) + 9, 9, 0, 3)
    elif self.range == "end":
        self.images['fill'].render(self.graphics, self.width - int(start_x) , 9, int(start_x), 3)
    elif self.range is True:
        if not self.inverse:
            # middle
            self.images['fill'].render(self.graphics, end_x - start_x + 6, 9, int(start_x), 3)
        else:
            self.images['fill'].render(self.graphics, int(start_x) + 9, 9, 0, 3)
            self.images['fill'].render(self.graphics, self.width - int(end_x) , 9, int(end_x), 3)





ui.ScrollBar.images = {
    "normal": get_image("themes/assets/scrollbar/gutter_s9.png", 1,1,1,1),
    "disabled": get_image("themes/assets/scrollbar/gutter_s9_disabled.png", 1,1,1,1),
}
ui.ScrollBar.thickness = 10

@override(ui.ScrollBar)
def do_render(self):
    image = self.images["normal"] if self.enabled else self.images["disabled"]
    image.render(self.graphics, self.width, self.height)


ui.ScrollBarSlider.images = {
    "normal": get_image("themes/assets/scrollbar/knob.png", 2, 2, 2, 2),
    "highlight": get_image("themes/assets/scrollbar/knob_hot.png", 2, 2, 2, 2),
    "pressed": get_image("themes/assets/scrollbar/knob_down.png", 2, 2, 2, 2),
    "disabled": get_image("themes/assets/scrollbar/knob_disabled.png", 2, 2, 2, 2),
}
@override(ui.ScrollBarSlider)
def do_render(self):
    state = self.state
    if not self.enabled:
        state = "disabled"
    elif self.get_scene() and self.get_scene()._drag_sprite == self:
        state = "pressed"

    self.images[state].render(self.graphics, self.width, self.height)


ui.ScrollBarButton.images = {
    "up_normal": get_image("themes/assets/scrollbar/up.png"),
    "up_pressed": get_image("themes/assets/scrollbar/up_down.png"),
    "up_disabled": get_image("themes/assets/scrollbar/up_disabled.png"),
    "down_normal": get_image("themes/assets/scrollbar/dn.png"),
    "down_pressed": get_image("themes/assets/scrollbar/dn_down.png"),
    "down_disabled": get_image("themes/assets/scrollbar/dn_disabled.png"),
}
@override(ui.ScrollBarButton)
def do_render(self):
    state = self.state
    if not self.enabled:
        state = "disabled"

    direction = self.direction
    if direction in ("left", "right"): #haven't rotated the left/right ones yet
        direction = "up" if direction == "left" else "down"

    image = self.images.get("%s_%s" % (direction, state)) or self.images["%s_normal" % direction]

    image.render(self.graphics, self.width, self.height)
