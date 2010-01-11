#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2010 Toms Bauģis <toms.baugis at gmail.com>

"""
 Proximity calculations
"""

from bisect import bisect

class ProximityStore(object):
    def __init__(self):
        self.positions = {}
        self.reverse_positions = {}

    def update_position(position):
        """Update position of the element"""
        pass

    def find_neighbours(location, radius):
        pass


# A AbstractProximityDatabase-style wrapper for the LQ bin lattice system
class LQProximityStore(ProximityStore):
    __slots__ = ['point1', 'point2', 'stride', 'grid_x', 'grid_y']
    def __init__(self, point1, point2, stride):
        ProximityStore.__init__(self)
        self.point1, self.point2, self.stride = point1, point2, stride

        # create the bin grid where we will be throwing in our friends
        self.grid_x = range(point1.x, point2.x, stride)
        self.grid_y = range(point1.y, point2.y, stride)

        self.velocity_weight = 10


    def update_position(self, boid):
        bin = (bisect(self.grid_x, boid.location.x), bisect(self.grid_y, boid.location.y))
        old_bin = self.reverse_positions.setdefault(boid, [])

        #if bin has changed, move
        if old_bin != bin:
            if old_bin:
                self.positions[old_bin].remove(boid)

            self.positions.setdefault(bin, [])
            self.positions[bin].append(boid)
            self.reverse_positions[boid] = bin


    def find_bins(self, boid, radius):
        # TODO, would be neat to operate with vectors here
        # create a bounding box and return all bins within it
        velocity_weight = self.velocity_weight
        min_x = bisect(self.grid_x, min(boid.location.x - radius,
                                        boid.location.x + boid.velocity.x * velocity_weight - radius))
        min_y = bisect(self.grid_y, min(boid.location.y - radius,
                                        boid.location.y + boid.velocity.y * velocity_weight - radius))
        max_x = bisect(self.grid_x, max(boid.location.x + radius,
                                        boid.location.x + boid.velocity.x * velocity_weight + radius))
        max_y = bisect(self.grid_y, max(boid.location.y + radius,
                                        boid.location.y + boid.velocity.y * velocity_weight + radius))

        bins = []
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                bins.append(self.positions.setdefault((x,y), []))
        return bins


    def find_neighbours(self, boid, radius):
        bins = self.find_bins(boid, radius)

        neighbours = []

        for bin in bins:
            for boid2 in bin:
                if boid is boid2:
                    continue

                dx = boid.location.x - boid2.location.x
                dy = boid.location.y - boid2.location.y
                d = dx * dx + dy * dy
                if d < radius * radius:
                    neighbours.append((boid2, d))

        return neighbours
