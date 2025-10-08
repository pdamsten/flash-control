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
from copy import deepcopy

try:
    from lib.logger import INFO, ERROR, EXCEPTION, DEBUG, VERBOSE
except:
    pass

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
    s = '1/' + str(rfractions[fullstop(pwr)]) + (('+' + str(f)) if f != 0 else '')
    return s

def full2percentage(n, m):    
    if m == 'M':
        nmax = MMAX
        nmin = MMIN - 1
    else:
        nmax = TTLMAX
        nmin = TTLMIN - 1
    return (n - nmin) / (nmax - nmin)

def percentage2full(percentage, m, separate_frac = None):    
    if m == 'M':
        v = ((MMAX - (MMIN - 1)) * percentage)
    else:
        v = ((TTLMAX - (TTLMIN - 1)) * percentage)
    if separate_frac != None:
        v = fullstop(v)
    else:
        separate_frac = 0.0
    if m == 'M':
        v = (v + separate_frac) + (MMIN - 1)
    else:
        v = (v + separate_frac) + (TTLMIN - 1)
    return cap(v, m)

def fullstop(n):    
    return int(math.floor(float(n)))

def fraction(n):    
    frac, _ = math.modf(float(n))
    return abs(round(frac, 1))

def getminmax(mode):    
    if mode == 'M':
        nmax = MMAX
        nmin = MMIN
    else:
        nmax = TTLMAX
        nmin = TTLMIN
    return nmin, nmax

def cap(n, mode):    
    nmin, nmax = getminmax(mode)
    return round(max(nmin, min(nmax, n)), 1)

def limitPrecision(pwr, step, mode):
    nmin, nmax = getminmax(mode)
    rounded = round((pwr - nmin) / step) * step + nmin
    rounded = min(max(rounded, nmin), nmax)
    return round(rounded, 1)

def main():
    def test(power, mode, sep = None):
        per = full2percentage(power, mode)
        v = percentage2full(per, mode, sep)
        print(f'{mode} : {power} ({sep}) => {per:.2f} => {v}')

    def testPercentage(per, mode, sep = None):
        v = percentage2full(per, mode, sep)
        print(f'{mode} : {per:.2f} ({sep}) => {v}')

    test(12, 'M')
    test(10, 'M')
    test(8.9, 'M')
    test(6.5, 'M')
    test(4.1, 'M')
    test(2, 'M')
    test(0, 'M')

    testPercentage(0, 'M', 0.1)
    testPercentage(0.1, 'M', 0.1)
    testPercentage(0.2, 'M', 0.1)
    testPercentage(0.4, 'M', 0.1)
    testPercentage(0.7, 'M', 0.1)
    testPercentage(1.0, 'M', 0.1)

    test(4, 'TTL')
    test(3.0, 'TTL')
    test(2.9, 'TTL')
    test(0.5, 'TTL')
    test(-1.1, 'TTL')
    test(-3.0, 'TTL')
    test(-66, 'TTL')

    test(1, 'TTL', 0.2)
    test(0, 'TTL', 0.2)
    test(-1, 'TTL', 0.2)
    test(-1, 'TTL', 0.9)
    test(-1, 'TTL', 0.1)
    test(-2, 'TTL', 0.1)
    test(-3, 'TTL', 0.1)
    test(-4, 'TTL', 0.1)

    testPercentage(0, 'TTL', 0.1)
    testPercentage(0.1, 'TTL', 0.1)
    testPercentage(0.2, 'TTL', 0.1)
    testPercentage(0.4, 'TTL', 0.1)
    testPercentage(0.7, 'TTL', 0.1)
    testPercentage(1.0, 'TTL', 0.1)

if __name__ == "__main__":
    main()