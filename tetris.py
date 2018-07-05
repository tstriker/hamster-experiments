#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2018 Tom Striker <tom.striker.b@gmail.com>

"""Not tetris"""
import gi
import math
import random

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import GObject as gobject
from lib import graphics



class TShape(graphics.Sprite):
    """little bit of refresher as to what shapes we do have in tetris (7):
            xxxx     xxx  xxx  xxx   xx    xx     xx
                     x     x     x    xx   xx    xx

        i was doing rotation math etc at first, but then got lazy and just spelled out all shapes
        and rotations in a 4x4 matrix. and then compressed to hex
        eg hex(int("1000111000000000", 2))
    """
    shapes = [
        ["4444", "0f00"],  # straight
        ["4460", "e80", "c440", "2e00"],  # right-sided L
        ["4c40", "4e00", "4640", "e40"],  # T
        ["44c0", "8e00", "6440", "e200"],  # left-sided L
        ["2640", "c600"],  # Z
        ["cc00"],  # o
        ["4620", "6c00"],  # S
    ]

    def __init__(self, shape=None, size=10, **kwargs):
        graphics.Sprite.__init__(self, **kwargs)
        if shape is None:
            shape = random.randint(0, 6)
        self.shape, self.size = shape, size
        self.angle = -1
        self.turn()
        self.connect("on-render", self.on_render)

    def turn(self):
        self.angle = (self.angle + 1) % len(self.shapes[self.shape])
        if len(self.shapes[self.shape]) >= self.angle:
            self.shapeform = format(int(self.shapes[self.shape][self.angle], 16), "0>16b")

    def to_2d(self):
        xy = {}
        for i, byte in enumerate(self.shapeform):
            x, y = i % 4, i // 4
            xy[(x, y)] = int(byte)
        return xy

    def on_render(self, sprite):
        size = self.size
        self.graphics.set_line_style(width=1)

        for (x, y), byte in self.to_2d().items():
            if byte:
                self.graphics.rectangle(x * size + 1, y * size + 1, size - 2, size - 2)

        self.graphics.fill_preserve("#666")
        self.graphics.stroke("#333")


class Block(graphics.Sprite):

    def __init__(self, size, **kwargs):
        graphics.Sprite.__init__(self, **kwargs)
        self.connect("on-render", self.on_render)
        self.color = None
        self.size = size


    def on_render(self, sprite):
        self.opacity = 0.3 if not self.color else 1

        self.graphics.set_line_style(width=1)
        self.graphics.rectangle(1, 1, self.size - 2, self.size - 2)

        self.graphics.fill_preserve("#999")
        self.graphics.stroke("#333")



class Tray(graphics.Sprite):
    """where we put the cubes in, you. a very plain x * y grid"""
    width = 10
    height = 20
    __gsignals__ = {
        "game-over": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        "lines-cleared": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
    }

    def __init__(self, size=10, **kwargs):
        graphics.Sprite.__init__(self, **kwargs)
        self.size = size

        self.blocks = []
        for row in range(self.height):
            self.blocks.append([])
            for col in range(self.width):
                block = Block(size=self.size, x=col * self.size, y=row*self.size)
                self.add_child(block)
                self.blocks[-1].append(block)

                #if row == self.height - 1 and col < self.width-1:
                #    block.color = 1

        self.current_col = self.width // 2
        self.current_row = 0
        self.current = TShape(size=self.size, x=self.current_col * size, y=self.current_row)
        self.add_child(self.current)

        self.connect("on-render", self.on_render)

    def move(self, direction=-1):
        self.current_col += direction
        if not(self.movement_possible()):
            self.current_col -= direction

        self.current.x = self.current_col * self.size

    def turn(self):
        self.current.turn()

    def movement_possible(self):
        # checks if downwards movement is possible at this position
        # effectively, pretends that we are current line + 1
        coords = self.current.to_2d()

        for y in range(4):
            for x in range(4):
                if not (coords[(x, y)]):
                    # nothing to see - nothing to check
                    continue

                cur_y = self.current_row + y
                cur_x = self.current_col + x

                if cur_x < 0 or cur_x >= self.width or cur_y >= self.height:
                    # out of bounds
                    return False

                if self.blocks[cur_y][cur_x].color:
                    # overlap
                    return False
        return True

    def transfer_blocks(self):
        # moves all the blocks of the current one, wherever it is right now, to the tray
        # after which, shakes up the tray (resolves lines)
        coords = self.current.to_2d()
        for y in range(4):
            for x in range(4):
                if not (coords[(x, y)]):
                    # nothing to see - nothing to check
                    continue

                cur_y = self.current_row + y
                cur_x = self.current_col + x
                self.blocks[cur_y][cur_x].color = 1

        # scan lines
        blocks, popped = list(self.blocks), []
        for y in range(self.height - 1, 0, -1):
            set_blocks = [block for block in blocks[y] if block.color]
            if len(set_blocks) == self.width:
                #we have to destroy this line and push all other lines down
                popped.append(self.blocks.pop(y))

        if popped:
            for row in range(len(popped)):
                self.blocks.insert(0, [])
                for col in range(self.width):
                    block = Block(size=self.size, x=col * self.size, y=row * self.size)
                    self.add_child(block)
                    self.blocks[0].append(block)

            for row in popped:
                for block in row:
                    block.pivot_x, block.pivot_y = self.size / 2, self.size / 2
                    block.animate(scale_x=0, scale_y=0, duration=0.5, on_complete=self._kill_block)

            self.animate(duration=1, delay=2, on_complete=self._move_blocks)
            self.emit("lines-cleared", len(popped))

    def _move_blocks(self, sprite):
        for r, row in enumerate(self.blocks):
            for col, block in enumerate(row):
                block.animate(y=r*self.size)


    def _kill_block(self, sprite):
        self.remove_child(sprite)

    def tick(self):
        self.current_row += 1
        if not self.movement_possible():
            if self.current_row <= 1:
                self.emit("game-over")

            self.current_row -= 1
            self.transfer_blocks()
            self.remove_child(self.current)
            self.current_col = self.width // 2
            self.current_row = 0
            self.current = TShape(size=self.size, x=self.current_col * self.size, y=self.current_row)
            self.add_child(self.current)

        self.current.y = self.current_row * self.size

    def on_render(self, sprite):
        self.graphics.set_line_style(width=2)
        self.graphics.move_to(-5, -5)
        self.graphics.line_to(-5, self.height * self.size + 5)
        self.graphics.line_to(self.width * self.size + 5, self.height * self.size + 5)
        self.graphics.line_to(self.width * self.size + 5, -5)
        self.graphics.stroke("#666")


class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self)
        self.connect("on-key-press", self.on_key_press)
        self.connect("on-key-release", self.on_key_release)

        self._init_tray()

        self._throttling = False

        gobject.timeout_add(1000 // (1 * 40), self._throttle_tick)
        self._ticking = False
        self.start_ticking()

    def _init_tray(self):
        self.clear()
        self.tray = Tray(size=30, x=50, y=50)
        self.tray.connect("game-over", self.on_game_over)
        self.tray.connect("lines-cleared", self.on_lines_cleared)
        self.add_child(self.tray)

        self.score_label = graphics.Label("Score: 0", size=20, x=400, y=100, color="#333")
        self.level_label = graphics.Label("Level: 1", size=18, x=400, y=130, color="#555")
        self.add_child(self.score_label, self.level_label)

        self.lines_cleared = 0
        self.score = 0
        self.level = 1

    def _tick(self):
        if not self._throttling:
            self.tray.tick()
        return self._ticking is not None

    def _throttle_tick(self):
        if self._throttling:
            self.tray.tick()
        return self._ticking is not None

    def on_game_over(self, event):
        self._init_tray()

    def on_lines_cleared(self, sprite, lines):
        self.lines_cleared += lines
        level = (self.lines_cleared // 20) + 1
        if self.level != level:
            self.level = level
            self.level_label.text = "Level: %d" % self.level
            gobject.source_remove(self._ticking)
            self.start_ticking()


        def _update_score_label(sprite):
            self.score_label.text = "Score: %d" % int(sprite.score)
        self.score_label.score = self.score
        self.score += lines * 100 +  math.pow(max(0, lines-1), 2) * 5
        self.score_label.animate(score=self.score, on_update=_update_score_label)


    def start_ticking(self):
        self._ticking = gobject.timeout_add(1000 // (1 * self.level * 0.8), self._tick)

    def throttle(self, throttling=True):
        if self._throttling == throttling:
            return

        self._throttling = throttling;
        if throttling:
            self._tick()
            self._throttle_tick()

    def on_key_press(self, scene, event):
        if not self._ticking:
            return

        key = event.keyval
        if key == gdk.KEY_Left:
            self.tray.move(-1)
        elif key == gdk.KEY_Right:
            self.tray.move(1)
        elif key == gdk.KEY_Up:
            self.tray.turn()
        elif key == gdk.KEY_Down:
            self.throttle()

    def on_key_release(self, scene, event):
        key = event.keyval
        if key == gdk.KEY_Down:
            self.throttle(False)



class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_default_size(600, 700)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        window.add(Scene())
        window.show_all()


if __name__ == '__main__':
    window = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
