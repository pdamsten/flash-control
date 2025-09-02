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

from lib.logger import INFO, ERROR, EXCEPTION, DEBUG, VERBOSE
from copy import deepcopy

fractions = [2 ** n for n in range(11)]
rfractions = deepcopy(fractions)
rfractions.reverse()

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

def fraction2Full(power):
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
    f = float(pwr)
    nbr = int(f)
    s = '1/' + str(rfractions[nbr]) + (('+' + str(round(f - nbr, 1))) if f - nbr != 0 else '')
    return s
    
