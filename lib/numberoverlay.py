#!/usr/bin/env python
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

from Cocoa import (
    NSWindow, NSBackingStoreBuffered,
    NSMakeRect, NSBorderlessWindowMask,
    NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSFloatingWindowLevel, NSTextField, NSColor, NSFont
)
from Foundation import NSObject
import objc
from PyObjCTools import AppHelper

class NumberOverlay(NSObject):
    def init(self):
        self = objc.super(NumberOverlay, self).init()
        if self is None:
            return None

        rect = NSMakeRect(200, 500, 400, 400)
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect,
            NSBorderlessWindowMask,
            NSBackingStoreBuffered,
            False
        )
        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(NSColor.clearColor())
        self.window.setLevel_(NSFloatingWindowLevel)
        self.window.setCollectionBehavior_(NSWindowCollectionBehaviorCanJoinAllSpaces)
        self.window.setIgnoresMouseEvents_(True)
        self.window.setAlphaValue_(1.0)

        self.label = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 400, 400))
        self.label.setStringValue_("0")
        self.label.setFont_(NSFont.boldSystemFontOfSize_(200))
        self.label.setBezeled_(False)
        self.label.setDrawsBackground_(False)
        self.label.setEditable_(False)
        self.label.setSelectable_(False)
        self.label.setAlignment_(2)  # Center
        self.label.setTextColor_(NSColor.whiteColor())
        self.window.contentView().addSubview_(self.label)
        return self

    def show(self):
        def _show():
            self.window.orderFrontRegardless()
        AppHelper.callAfter(_show)

    def hide(self):
        def _hide():
            self.window.orderOut_(None)
        AppHelper.callAfter(_hide)

    def setValue_(self, txt):
        def _tick(txt):
            self.label.setStringValue_(str(txt))
        self.show()
        AppHelper.callAfter(_tick, txt)
