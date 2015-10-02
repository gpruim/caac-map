# Adapted from code by William Yager:
# https://github.com/openleap/PyLeapMouse/blob/97d8839f094eed05a778ea657683ea70cfd475f3/Geometry.py

# Used under this license:

# Copyright (c) 2012, William Yager
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
#    Redistribution of this software in binary form or as source code as part
#    of a software package that is non-free or closed-source is forbidden
#    without express written consent of the author.
#
#    Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# https://github.com/openleap/PyLeapMouse/blob/97d8839f094eed05a778ea657683ea70cfd475f3/LICENSE.txt

import math


class Vector(object):
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
    def __add__(self, other):
        return Vector(self.x + other.x, self.y+other.y, self.z+other.z)
    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y, self.z - other.z)
    def __mul__(self, other):
        return Vector(self.x * other, self.y * other, self.z * other)
    def __matmul__(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z
    def __pow__(self, other):       # The ** operator allows us to multiply a vector by a scalar
        return self * other
    def cross(self, other):
        x = self.y * other.z - other.y * self.z
        y = -(self.x * other.z - other.x * self.z)
        z = self.x * other.y - other.x * self.y
        return Vector(x,y,z)
    def __mod__(self, other):       # The % operator is cross product
        return self.cross(other)
    def norm(self):                 # Length of self
        return math.sqrt(self @ self)
    def distance(self, other):
        return (self-other).norm()  # Find difference and then the length of it
    def unit_vector(self):
        magnitude = self.norm()
        return Vector(1.0*self.x/magnitude, 1.0*self.y/magnitude, 1.0*self.z/magnitude)
    def pitch(self):
        return math.atan(1.0*self.z/self.y)
    def roll(self):
        return math.atan(1.0*self.x/self.y)
    def yaw(self):
        return math.atan(1.0*self.x/self.z)


class Segment(object):

    def __init__(self, point1, point2):
        self.point1 = point1
        self.point2 = point2

    def min_distance_infinite(self, other):
        """Return shortest distance between two lines.

        Based off of http://geomalgorithms.com/a07-_distance.html.

        """
        u = self.point2 - self.point1
        v = other.point2 - other.point1
        w = self.point1 - other.point1
        a = u @ u
        b = u @ v
        c = v @ v
        d = u @ w
        e = v @ w
        D = a @ c - b @ b
        sc = 0.0
        tc = 0.0
        basically_zero = .000000001
        if D < basically_zero:
            sc = 0.0
            if b > c:
                tc = d/b
            else:
                tc = e/c
        else:
            sc = (b @ e - c @ d) / D
            tc = (a @ e - b @ d) / D
        dP = w + u**sc - v**tc
        return dP.norm()

    def min_distance_finite(self, other):
        """Return shortest distance between two segments.
        """
        u = self.point2 - self.point1
        v = other.point2 - other.point1
        w = self.point1 - other.point1
        a = u @ u  #* here is cross product
        b = u @ v
        c = v @ v
        d = u @ w
        e = v @ w
        D = a @ c - b @ b
        sc = 0.0
        sN = 0.0
        sD = D
        tc = 0.0
        tN = 0.0
        tD = D
        basically_zero = .000000001
        if D < basically_zero:
            sN = 0.0
            sD = 1.0
            tN = e
            tD = c
        else:
            sN = (b@e - c@d)
            tN = (a@e - b@d)
            if sN < 0.0:
                sN = 0.0
                tN = e
                tD = c
            elif sN > sD:
                sN = sD
                tN = e + b
                tD = c
        if(tN < 0.0):
            tN = 0.0
            if(-d < 0.0):
                sN = 0.0
            elif (-d > a):
                sN = sD
            else:
                sN = -d
                sD = a
        elif tN > tD:
            tN = tD
            if (-d + b) < 0.0:
                sN = 0
            elif (-d + b) > a:
                sN = sD
            else:
                sN = (-d + b)
                sD = a
        if abs(sN) < basically_zero:
            sc = 0
        else:
            sc = sN / sD
        if abs(tN) < basically_zero:
            tc = 0.0
        else:
            tc = tN / tD
        dP = w + u**sc - v**tc  # I'm pretty sure dP is the actual vector linking the lines
        return dP.norm()


class Line(Segment):
    def __init__(self, point1, direction_vector):
        self.point1 = point1
        self.direction = direction_vector.unit_vector()
        self.point2 = point1 + self.direction


def angle_between_vectors(vector1, vector2):
    #cos(theta)=dot product / (|a|*|b|)
    top = vector1 @ vector2
    bottom = vector1.norm() @ vector2.norm()
    angle = math.acos(top/bottom)
    return angle  # In radians
