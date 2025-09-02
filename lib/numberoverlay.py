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
    NSFloatingWindowLevel, NSTextField, NSColor, NSFont, NSCenterTextAlignment, NSScreen
)
from Foundation import NSObject
import objc
from PyObjCTools import AppHelper
import Quartz

W = 900
H = 500

class NumberOverlay(NSObject):
    def init(self):
        self = objc.super(NumberOverlay, self).init()
        if self is None:
            return None

        rect = NSMakeRect(0, 0, W, H)
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
        self.setBorderRadius_((self.window, 50))

        self.gid = NSTextField.alloc().initWithFrame_(NSMakeRect(0, H * 0.75, W, H * 0.2))
        self.gid.setStringValue_("A")
        self.gid.setAlignment_(NSCenterTextAlignment)
        self.gid.setFont_(NSFont.boldSystemFontOfSize_(75))
        self.gid.setBezeled_(False)
        self.gid.setDrawsBackground_(False)
        self.gid.setEditable_(False)
        self.gid.setSelectable_(False)
        self.gid.setAlignment_(NSCenterTextAlignment)
        self.gid.setTextColor_(NSColor.whiteColor())
        self.window.contentView().addSubview_(self.gid)

        self.label = NSTextField.alloc().initWithFrame_(NSMakeRect(0, H * 0.1, W, H * 0.8))
        self.label.setStringValue_("-")
        self.label.setAlignment_(NSCenterTextAlignment)
        self.label.setFont_(NSFont.boldSystemFontOfSize_(350))
        self.label.setBezeled_(False)
        self.label.setDrawsBackground_(False)
        self.label.setEditable_(False)
        self.label.setSelectable_(False)
        self.label.setAlignment_(NSCenterTextAlignment)
        self.label.setTextColor_(NSColor.whiteColor())
        self.window.contentView().addSubview_(self.label)
        return self

    def setBorderRadius_(self, params):
        window, radius = params
        content_view = window.contentView()
        content_view.setWantsLayer_(True)

        layer = content_view.layer()
        layer.setCornerRadius_(radius)
        layer.setMasksToBounds_(True)
        color = Quartz.CGColorCreateGenericRGB(0.0, 0.0, 0.0, 0.5)
        layer.setBackgroundColor_(color)

    def show(self):
        def _show():
            self.window.orderFrontRegardless()
        AppHelper.callAfter(_show)

    def hide(self):
        def _hide():
            self.window.orderOut_(None)
        AppHelper.callAfter(_hide)

    def setValue_(self, flash):
        def _tick(flash):
            self.label.setStringValue_(str(flash[0]))
            self.gid.setStringValue_(str(flash[1]))
        self.show()
        AppHelper.callAfter(_tick, flash)

    def center_(self, rect):
        def _center(rect):
            sh = NSScreen.mainScreen().frame().size.height
            frame = NSMakeRect(rect[0] + (rect[2] / 2) - (W / 2), 
                               sh - H - (rect[1] + (rect[3] / 2) - (H / 2)), 
                               W, H)
            self.window.setFrame_display_(frame, True)
        AppHelper.callAfter(_center, rect)
