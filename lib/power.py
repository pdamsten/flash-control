#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
#**************************************************************************
#
#   Copyright (c) 2025 by Petri Damstén <petri.damsten@gmail.com> 
#                         https://petridamsten.com
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the
#   Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
#**************************************************************************

import math
from lib.logger import INFO, ERROR, EXCEPTION, DEBUG, VERBOSE
from copy import deepcopy

fractions = [2 ** n for n in range(11)]
rfractions = deepcopy(fractions)
rfractions.reverse()

TTLMAX = 3.0
TTLMIN = -3.0
MMAX = 10.0
MMIN = 2.0

def power2godox(s):
    s = 0 if not s else s
    if isinstance(s, str) and s.find('/') != -1:
        l = s.replace('1/', '').split('+')
        if len(l) > 1:
            try:
                b = float(l[1])
            except:
                b = 0.0
            b = b if b < 1.0 else b / 10.0
            b = int(max(min(0.9, b), 0.0) * 10)
        else:
            b = 0
        try:
            an = int(l[0])
        except:
            an = 1
        a = min(range(len(fractions)), \
                key = lambda n : abs(fractions[n] - an))
        res = max(a * 10 - b, 0)
    else:
        res = int(round((10.0 - float(s)) * 10))
    return res
        
def ttl2godox(s):
    n = float(s)
    if n >= 0.0:
        res = int(round(n * 10))
    else:
        res = 0x80 + int(round(abs(n) * 10))
    return res

def fraction2full(power):
    if not isinstance(power, str):
        return power
    l = power.replace('1/', '').split('+')
    if len(l) > 1:
        try:
            b = float(l[1])
        except:
            b = 0.0
    else:
        b = 0
    try:
        an = int(l[0])
    except:
        an = 1
    a = min(enumerate(rfractions), key = lambda x: abs(x[1] - an))[0]
    res = max(a + b, 0)
    return res

def full2fraction(pwr):
    f = fraction(pwr)
    s = '1/' + str(rfractions[integer(pwr)]) + (('+' + str(f)) if f != 0 else '')
    return s

def full2percentage(n, m):    
    if m == 'M':
        nmax = MMAX
        nmin = MMIN
    else:
        nmax = TTLMAX
        nmin = TTLMIN
    return (n - nmin) / nmax

def percentage2full(percentage, m, separate_frac = 0.0):    
    if m == 'M':
        v = (MMAX * v + separate_frac) + MMIN
    else:
        v = (TTLMAX * v + separate_frac) + TTLMIN
    return round(v, 1)

def integer(n):    
    _, i = math.modf(float(n))
    return int(i)

def fraction(n):    
    frac, _ = math.modf(float(n))
    return abs(round(frac, 1))
