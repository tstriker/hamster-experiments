#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

import gtk

from hamster import pytweener
from hamster import graphics
from hamster.pytweener import Easing

class TailParticle(object):
    def __init__(self, x, y, follow = None):
        self.x = x
        self.y = y
        self.follow = follow
    
    def draw(self, area):
        area.draw_rect(self.x - 5, self.y - 5, 10, 10, 3)
        area.set_color("#121266")
        area.context.fill()
        if self.follow:
            area.context.move_to(self.x, self.y)
            area.context.line_to(self.follow.x, self.follow.y)
            area.context.stroke()

class Canvas(graphics.Area):
    def __init__(self):
        graphics.Area.__init__(self)

        self.tail = []
        for i in range(50):
            previous = self.tail[-1] if self.tail else None

            
            self.tail.append(TailParticle(10, 10, previous))

        self.connect("motion_notify_event", self.on_mouse_move)        
        self.mouse_moving = False


    def on_mouse_move(self, widget, event):
        # oh i know this should not be performed using tweeners, but hey - a demo!
        if event.is_hint:
            x, y, state = event.window.get_pointer()
        else:
            x = event.x
            y = event.y
            state = event.state
        
        for particle in reversed(self.tail):
            new_x, new_y = x, y
            if particle.follow:
                new_x, new_y = particle.follow.x, particle.follow.y
            
            self.tweener.killTweensOf(particle)
            
            
            self.tweener.addTween(particle, **dict(x=new_x, y=new_y, tweenType = Easing.Expo.easeOut, tweenTime=0.5))
        
        self.mouse_moving = True


    def on_expose(self):
        # on expose is called when we are ready to draw
        for tail in self.tail:
            tail.draw(self)

        if self.mouse_moving == False:
            # retract tail when the movement has stopped
            for particle in reversed(self.tail):
                if particle.follow:
                    new_x, new_y = particle.follow.x, particle.follow.y
                    
                    [self.tweener.removeTween(tween) for tween in self.tweener.getTweensAffectingObject(particle)]
                    
                    self.tweener.addTween(particle, **dict(x=new_x, y=new_y, tweenType = Easing.Expo.easeOut, tweenTime=0.5))

        self.mouse_moving = False    
        self.redraw_canvas() # constant redraw (maintaining the requested frame rate)


class BasicWindow:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_title("Graphics Module")
        window.set_size_request(300, 300)
        window.connect("delete_event", lambda *args: gtk.main_quit())
    
        canvas = Canvas()
        
        box = gtk.VBox()
        box.pack_start(canvas)
        
    
        window.add(box)
        window.show_all()
        
        
if __name__ == "__main__":
    example = BasicWindow()
    gtk.main()

    """
    some profiling rubbish
    tweener = pytweener.Tweener()
    
    particles = []
    
    # create
    for i in range(2000):
        tp = TailParticle(10, 10)
        particles.append(tp)
        tweener.addTween(tp, x=10, y=15)
    
    # stop and update
    for particle in particles:
        tweens = tweener.killTweensOf(particle)
        tweener.addTween(particle, x=20, y=30)

    """