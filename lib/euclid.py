#!/usr/bin/env python
#
# euclid graphics maths module
#
# Copyright (c) 2006 Alex Holkner
# Alex.Holkner@mail.google.com
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 2.1 of the License, or (at your
# option) any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA

'''euclid graphics maths module

Documentation and tests are included in the file "euclid.txt", or online
at http://code.google.com/p/pyeuclid
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'
__revision__ = '$Revision$'

import math
import operator
import types



class Vector2(object):
    __slots__ = ['x', 'y']

    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def __copy__(self):
        return self.__class__(self.x, self.y)

    copy = __copy__

    def __repr__(self):
        return 'Vector2(%.2f, %.2f)' % (self.x, self.y)

    def __eq__(self, other):
        if not other: return False

        if isinstance(other, Vector2):
            return self.x == other.x and \
                   self.y == other.y
        else:
            if hasattr(other, '__len__') and len(other) == 2:
                return self.x == other[0] and \
                       self.y == other[1]
            else:
                return False

    def __neq__(self, other):
        return not self.__eq__(other)

    def __nonzero__(self):
        return self.x != 0 or self.y != 0

    def __len__(self):
        return 2

    def __getitem__(self, key):
        return (self.x, self.y)[key]

    def __setitem__(self, key, value):
        l = [self.x, self.y]
        l[key] = value
        self.x, self.y = l

    def __iter__(self):
        return iter((self.x, self.y))

    def __getattr__(self, name):
        try:
            return tuple([(self.x, self.y)['xy'.index(c)] \
                          for c in name])
        except ValueError:
            raise AttributeError, name

    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)

    __radd__ = __add__

    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y
        return self

    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)

    def __rsub__(self, other):
        return Vector2(other.x - self.x, other.y - self.y)

    def __mul__(self, other):
        return Vector2(self.x * other, self.y * other)

    __rmul__ = __mul__

    def __imul__(self, other):
        self.x *= other
        self.y *= other
        return self

    def __div__(self, other):
        return Vector2(operator.div(self.x, other),
                       operator.div(self.y, other))


    def __rdiv__(self, other):
        return Vector2(operator.div(other, self.x),
                       operator.div(other, self.y))

    def __floordiv__(self, other):
        return Vector2(operator.floordiv(self.x, other),
                       operator.floordiv(self.y, other))


    def __rfloordiv__(self, other):
        return Vector2(operator.floordiv(other, self.x),
                       operator.floordiv(other, self.y))

    def __truediv__(self, other):
        return Vector2(operator.truediv(self.x, other),
                       operator.truediv(self.y, other))

    def __rtruediv__(self, other):
        return Vector2(operator.truediv(other, self.x),
                       operator.truediv(other, self.y))

    def __neg__(self):
        return Vector2(-self.x, -self.y)

    __pos__ = __copy__

    def __abs__(self):
        return math.sqrt(self.x * self.x + self.y * self.y)

    magnitude = __abs__

    def magnitude_squared(self):
        return self.x * self.x + self.y * self.y

    def normalize(self):
        d = self.magnitude()
        if d:
            self.x /= d
            self.y /= d
        return self

    def normalized(self):
        d = self.magnitude()
        if d:
            return Vector2(self.x / d, self.y / d)
        return self.copy()

    def dot(self, other):
        assert isinstance(other, Vector2)
        return self.x * other.x + \
               self.y * other.y

    def cross(self):
        return Vector2(self.y, -self.x)

    def product(self, v2):
        # product of our vector and the other vector's perpendicular
        return self.x * v2.y - self.y * v2.x

    def reflect(self, normal):
        # assume normal is normalized
        assert isinstance(normal, Vector2)
        d = 2 * (self.x * normal.x + self.y * normal.y)
        return Vector2(self.x - d * normal.x,
                       self.y - d * normal.y)

    def limit(self, max_magnitude):
        if self.magnitude() > max_magnitude:
            self.normalize()
            self *= max_magnitude

    def heading(self):
        return math.atan2(self.y, self.x)

    def angle(self, other):
        """angle between this and the other vector in radians"""
        if self == -other:  # same vector facing the opposite way will kill acos on float precision
            return math.pi

        return math.acos(self.normalized().dot(other.normalized()))


# Geometry
# Much maths thanks to Paul Bourke, http://astronomy.swin.edu.au/~pbourke
# ---------------------------------------------------------------------------

class Geometry(object):
    def _connect_unimplemented(self, other):
        raise AttributeError, 'Cannot connect %s to %s' % \
            (self.__class__, other.__class__)

    def _intersect_unimplemented(self, other):
        raise AttributeError, 'Cannot intersect %s and %s' % \
            (self.__class__, other.__class__)

    _intersect_point2 = _intersect_unimplemented
    _intersect_line2 = _intersect_unimplemented
    _intersect_circle = _intersect_unimplemented
    _connect_point2 = _connect_unimplemented
    _connect_line2 = _connect_unimplemented
    _connect_circle = _connect_unimplemented


    def intersect(self, other):
        raise NotImplementedError

    def connect(self, other):
        raise NotImplementedError

    def distance(self, other):
        c = self.connect(other)
        if c:
            return c.length
        return 0.0

def _intersect_point2_circle(P, C):
    return (P - C.c).magnitude_squared() <= C.r * C.r

def _intersect_line2_line2(A, B):
    d = B.v.y * A.v.x - B.v.x * A.v.y
    if d == 0:
        return None

    dy = A.p.y - B.p.y
    dx = A.p.x - B.p.x
    ua = (B.v.x * dy - B.v.y * dx) / d
    if not A._u_in(ua):
        return None
    ub = (A.v.x * dy - A.v.y * dx) / d
    if not B._u_in(ub):
        return None

    return Point2(A.p.x + ua * A.v.x,
                  A.p.y + ua * A.v.y)

def _intersect_line2_circle(L, C):
    a = L.v.magnitude_squared()
    b = 2 * (L.v.x * (L.p.x - C.c.x) + \
             L.v.y * (L.p.y - C.c.y))
    c = C.c.magnitude_squared() + \
        L.p.magnitude_squared() - \
        2 * C.c.dot(L.p) - \
        C.r * C.r
    det = b * b - 4 * a * c
    if det < 0:
        return None
    sq = math.sqrt(det)
    u1 = (-b + sq) / (2 * a)
    u2 = (-b - sq) / (2 * a)
    if not L._u_in(u1):
        u1 = max(min(u1, 1.0), 0.0)
    if not L._u_in(u2):
        u2 = max(min(u2, 1.0), 0.0)

    # Tangent
    if u1 == u2:
        return Point2(L.p.x + u1 * L.v.x,
                      L.p.y + u1 * L.v.y)

    return LineSegment2(Point2(L.p.x + u1 * L.v.x,
                               L.p.y + u1 * L.v.y),
                        Point2(L.p.x + u2 * L.v.x,
                               L.p.y + u2 * L.v.y))

def _connect_point2_line2(P, L):
    d = L.v.magnitude_squared()
    assert d != 0
    u = ((P.x - L.p.x) * L.v.x + \
         (P.y - L.p.y) * L.v.y) / d
    if not L._u_in(u):
        u = max(min(u, 1.0), 0.0)
    return LineSegment2(P,
                        Point2(L.p.x + u * L.v.x,
                               L.p.y + u * L.v.y))

def _connect_point2_circle(P, C):
    v = P - C.c
    v.normalize()
    v *= C.r
    return LineSegment2(P, Point2(C.c.x + v.x, C.c.y + v.y))

def _connect_line2_line2(A, B):
    d = B.v.y * A.v.x - B.v.x * A.v.y
    if d == 0:
        # Parallel, connect an endpoint with a line
        if isinstance(B, Ray2) or isinstance(B, LineSegment2):
            p1, p2 = _connect_point2_line2(B.p, A)
            return p2, p1
        # No endpoint (or endpoint is on A), possibly choose arbitrary point
        # on line.
        return _connect_point2_line2(A.p, B)

    dy = A.p.y - B.p.y
    dx = A.p.x - B.p.x
    ua = (B.v.x * dy - B.v.y * dx) / d
    if not A._u_in(ua):
        ua = max(min(ua, 1.0), 0.0)
    ub = (A.v.x * dy - A.v.y * dx) / d
    if not B._u_in(ub):
        ub = max(min(ub, 1.0), 0.0)

    return LineSegment2(Point2(A.p.x + ua * A.v.x, A.p.y + ua * A.v.y),
                        Point2(B.p.x + ub * B.v.x, B.p.y + ub * B.v.y))

def _connect_circle_line2(C, L):
    d = L.v.magnitude_squared()
    assert d != 0
    u = ((C.c.x - L.p.x) * L.v.x + (C.c.y - L.p.y) * L.v.y) / d
    if not L._u_in(u):
        u = max(min(u, 1.0), 0.0)
    point = Point2(L.p.x + u * L.v.x, L.p.y + u * L.v.y)
    v = (point - C.c)
    v.normalize()
    v *= C.r
    return LineSegment2(Point2(C.c.x + v.x, C.c.y + v.y), point)

def _connect_circle_circle(A, B):
    v = B.c - A.c
    v.normalize()
    return LineSegment2(Point2(A.c.x + v.x * A.r, A.c.y + v.y * A.r),
                        Point2(B.c.x - v.x * B.r, B.c.y - v.y * B.r))


class Point2(Vector2, Geometry):
    def __repr__(self):
        return 'Point2(%.2f, %.2f)' % (self.x, self.y)

    def intersect(self, other):
        return other._intersect_point2(self)

    def _intersect_circle(self, other):
        return _intersect_point2_circle(self, other)

    def connect(self, other):
        return other._connect_point2(self)

    def _connect_point2(self, other):
        return LineSegment2(other, self)

    def _connect_line2(self, other):
        c = _connect_point2_line2(self, other)
        if c:
            return c._swap()

    def _connect_circle(self, other):
        c = _connect_point2_circle(self, other)
        if c:
            return c._swap()

class Line2(Geometry):
    __slots__ = ['p', 'v']

    def __init__(self, *args):
        if len(args) == 3:
            assert isinstance(args[0], Point2) and \
                   isinstance(args[1], Vector2) and \
                   type(args[2]) == float
            self.p = args[0].copy()
            self.v = args[1] * args[2] / abs(args[1])
        elif len(args) == 2:
            if isinstance(args[0], Point2) and isinstance(args[1], Point2):
                self.p = args[0].copy()
                self.v = args[1] - args[0]
            elif isinstance(args[0], Point2) and isinstance(args[1], Vector2):
                self.p = args[0].copy()
                self.v = args[1].copy()
            else:
                raise AttributeError, '%r' % (args,)
        elif len(args) == 1:
            if isinstance(args[0], Line2):
                self.p = args[0].p.copy()
                self.v = args[0].v.copy()
            else:
                raise AttributeError, '%r' % (args,)
        else:
            raise AttributeError, '%r' % (args,)

        if not self.v:
            raise AttributeError, 'Line has zero-length vector'

    def __copy__(self):
        return self.__class__(self.p, self.v)

    copy = __copy__

    def __repr__(self):
        return 'Line2(<%.2f, %.2f> + u<%.2f, %.2f>)' % \
            (self.p.x, self.p.y, self.v.x, self.v.y)

    p1 = property(lambda self: self.p)
    p2 = property(lambda self: Point2(self.p.x + self.v.x,
                                      self.p.y + self.v.y))

    def _apply_transform(self, t):
        self.p = t * self.p
        self.v = t * self.v

    def _u_in(self, u):
        return True

    def intersect(self, other):
        return other._intersect_line2(self)

    def _intersect_line2(self, other):
        return _intersect_line2_line2(self, other)

    def _intersect_circle(self, other):
        return _intersect_line2_circle(self, other)

    def connect(self, other):
        return other._connect_line2(self)

    def _connect_point2(self, other):
        return _connect_point2_line2(other, self)

    def _connect_line2(self, other):
        return _connect_line2_line2(other, self)

    def _connect_circle(self, other):
        return _connect_circle_line2(other, self)

class Ray2(Line2):
    def __repr__(self):
        return 'Ray2(<%.2f, %.2f> + u<%.2f, %.2f>)' % \
            (self.p.x, self.p.y, self.v.x, self.v.y)

    def _u_in(self, u):
        return u >= 0.0

class LineSegment2(Line2):
    def __repr__(self):
        return 'LineSegment2(<%.2f, %.2f> to <%.2f, %.2f>)' % \
            (self.p.x, self.p.y, self.p.x + self.v.x, self.p.y + self.v.y)

    def _u_in(self, u):
        return u >= 0.0 and u <= 1.0

    def __abs__(self):
        return abs(self.v)

    def magnitude_squared(self):
        return self.v.magnitude_squared()

    def _swap(self):
        # used by connect methods to switch order of points
        self.p = self.p2
        self.v *= -1
        return self

    length = property(lambda self: abs(self.v))

class Circle(Geometry):
    __slots__ = ['c', 'r']

    def __init__(self, center, radius):
        assert isinstance(center, Vector2) and type(radius) == float
        self.c = center.copy()
        self.r = radius

    def __copy__(self):
        return self.__class__(self.c, self.r)

    copy = __copy__

    def __repr__(self):
        return 'Circle(<%.2f, %.2f>, radius=%.2f)' % \
            (self.c.x, self.c.y, self.r)

    def _apply_transform(self, t):
        self.c = t * self.c

    def intersect(self, other):
        return other._intersect_circle(self)

    def _intersect_point2(self, other):
        return _intersect_point2_circle(other, self)

    def _intersect_line2(self, other):
        return _intersect_line2_circle(other, self)

    def connect(self, other):
        return other._connect_circle(self)

    def _connect_point2(self, other):
        return _connect_point2_circle(other, self)

    def _connect_line2(self, other):
        c = _connect_circle_line2(self, other)
        if c:
            return c._swap()

    def _connect_circle(self, other):
        return _connect_circle_circle(other, self)
