#!/bin/bash

SVG="$1"
BASENAME=$(basename "$SVG" .svg)
ICO="${BASENAME}.ico"

convert "$SVG" -background none -density 300 -define icon:auto-resize="256,128,64,32,16" "$ICO"
