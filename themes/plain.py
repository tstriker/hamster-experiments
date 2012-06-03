import cairo

from lib import graphics
import ui
from utils import override, vertical_gradient


""" here starts the theme """
@override(ui.Button)
def do_render(self, *args):
    """ Properties that affect rendering:
        state:   normal / highlight / pressed
        focused: True / False
        enabled: True / False
    """

    self.graphics.set_line_style(width=1)
    self.graphics.rectangle(0.5, 0.5, self.width, self.height, 4)

    if self.state == "highlight":
        vertical_gradient(self, "#fff", "#edeceb", 0, self.height)
        self.graphics.fill_preserve()
    elif self.state == "pressed":
        vertical_gradient(self, "#B9BBC0", "#ccc", 0, self.height)
        self.graphics.fill_preserve()
    else:
        # normal
        vertical_gradient(self, "#fcfcfc", "#e8e7e6", 0, self.height)
        self.graphics.fill_preserve()


    if self.focused:
        self.graphics.stroke("#89ADDA")
    elif self.state == "pressed":
        self.graphics.stroke("#aaa")
    else:
        self.graphics.stroke("#cdcdcd")



@override(ui.ToggleButton)
def do_render(self):
    self.graphics.set_line_style(width=1)

    x, y, x2, y2 = 0.5, 0.5, 0.5 + self.width, 0.5 + self.height
    if isinstance(self.parent, ui.Group) == False or len(self.parent.sprites) == 1:
        # normal button
        self.graphics.rectangle(0.5, 0.5, self.width, self.height, 4)
    elif self.parent.sprites.index(self) == 0:
        self._rounded_line([(x2, y), (x, y), (x, y2), (x2, y2)], 4)
        self.graphics.line_to(x2, y)
    elif self.parent.sprites.index(self) == len(self.parent.sprites) - 1:
        self._rounded_line([(x, y), (x2, y), (x2, y2), (x, y2)], 4)
        self.graphics.line_to(x, y)
    else:
        self.graphics.rectangle(x, y, x2 - 0.5, y2 - 0.5)

    state = self.state
    if self.toggled:
        state = "pressed"

    # move the label when pressed a bit
    self.label_container.padding_left = 1 if state == "pressed" else 0
    self.label_container.padding_right = -1 if state == "pressed" else 0
    self.label_container.padding_top = 1 if state == "pressed" else 0
    self.label_container.padding_bottom = -1 if state == "pressed" else 0

    if state == "highlight":
        vertical_gradient(self, "#fff", "#edeceb", 0, self.height)
        self.graphics.fill_preserve()
    elif state == "pressed":
        vertical_gradient(self, "#B9BBC0", "#ccc", 0, self.height)
        self.graphics.fill_preserve()
    else:
        # normal
        vertical_gradient(self, "#fcfcfc", "#e8e7e6", 0, self.height)
        self.graphics.fill_preserve()


    if self.focused:
        self.graphics.stroke("#89ADDA")
    elif state == "pressed":
        self.graphics.stroke("#aaa")
    else:
        self.graphics.stroke("#cdcdcd")




@override(ui.CheckButton)
def do_render(self):
    tick_box_size = 12

    x, y = tick_box_size + self.padding_left + 1, (self.height - tick_box_size) / 2.0
    x, y = int(x) + 0.5, int(y) + 0.5

    stroke = "#999"
    if self.state in ("highlight", "pressed"):
        stroke = "#333"

    self.graphics.rectangle(x, y, tick_box_size, tick_box_size)
    vertical_gradient(self, "#fff", "#edeceb", y, y + tick_box_size)
    self.graphics.fill_preserve()

    self.graphics.stroke(stroke)


    if self.toggled:
        self.graphics.set_line_style(1)
        self.graphics.move_to(x + 2, y + tick_box_size * 0.5)
        self.graphics.line_to(x + tick_box_size * 0.4, y + tick_box_size - 3)
        self.graphics.line_to(x + tick_box_size - 2, y + 2)
        self.graphics.stroke("#333")

    self.graphics.rectangle(0, 0, self.width, self.height)
    self.graphics.new_path()



@override(ui.RadioButton)
def do_render(self):
    radio_radius = 5.5

    x, y = self._radio_radius + self.padding_left + 1, self.height / 2.0
    x, y = int(x) + 0.5, int(y) + 0.5

    stroke = "#999"
    if self.state in ("highlight", "pressed"):
        stroke = "#333"

    self.graphics.circle(x, y, self._radio_radius)
    self.graphics.fill_stroke("#fff", stroke)


    if self.toggled:
        self.graphics.circle(x, y, self._radio_radius - 2)
        self.graphics.fill("#999")

    self.graphics.rectangle(0, 0, self.width, self.height)
    self.graphics.new_path()
