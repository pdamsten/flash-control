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
    NSFloatingWindowLevel, NSImageView, NSColor, NSScreen, NSImage, NSBitmapImageRep,
    NSImageScaleProportionallyUpOrDown
)
from Foundation import NSObject
import objc
from PyObjCTools import AppHelper
import time

class Splash(NSObject):
    def init_(self, img):
        self = objc.super(Splash, self).init()
        if self is None:
            return None

        image = NSImage.alloc().initWithContentsOfFile_(img)
        if image is None:
            print("Failed to load image.")
            return None

        self.width, self.height = self.getPixelSize_(image)

        print(self.width, self.height)
        rect = NSMakeRect(0, 0, self.width, self.height)
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

        self.image_view = NSImageView.alloc().initWithFrame_(rect)
        self.image_view.setImage_(image)
        self.image_view.setImageScaling_(NSImageScaleProportionallyUpOrDown)
        self.window.contentView().addSubview_(self.image_view)
        self.window.orderFrontRegardless()
        self.window.center()
        return self

    def getPixelSize_(self, nsimage):
        representations = nsimage.representations()
        for rep in representations:
            if isinstance(rep, NSBitmapImageRep):
                width = rep.pixelsWide()
                height = rep.pixelsHigh()
                return width, height
        return None, None 

    def setBorderRadius_(self, params):
        window, radius = params
        content_view = window.contentView()
        content_view.setWantsLayer_(True)

        layer = content_view.layer()
        layer.setCornerRadius_(radius)
        layer.setMasksToBounds_(True)

    def show(self):
        def _show():
            self.window.orderFrontRegardless()
        AppHelper.callAfter(_show)

    def hide(self):
        def _hide():
            self.window.orderOut_(None)
        AppHelper.callAfter(_hide)


if __name__ == "__main__":
    def quit_app():
        NSApplication.sharedApplication().terminate_(None)

    from AppKit import (
        NSApplication
    )

    app = NSApplication.sharedApplication()
    splash = Splash.alloc().init_('../splash.png')
    splash.show()
    AppHelper.callLater(4, quit_app)
    app.run()
