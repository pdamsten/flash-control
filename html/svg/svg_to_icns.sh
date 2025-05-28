#!/bin/bash

# Exit on error
set -e

# Input SVG file (required)
SVG="$1"

# Output ICNS name (optional)
BASENAME=$(basename "$SVG" .svg)
ICONSET="${BASENAME}.iconset"
ICNS="${BASENAME}.icns"

if [[ -z "$SVG" || ! -f "$SVG" ]]; then
    echo "Usage: $0 icon.svg"
    exit 1
fi

# Clean up any existing iconset
rm -rf "$ICONSET"
mkdir "$ICONSET"

# Generate base 1024x1024 PNG
/Applications/Inkscape.app/Contents/MacOS/inkscape -w 1024 -h 1024 "$SVG" -o "${ICONSET}/icon_512x512@2x.png"

SIZES=(
  "16 icon_16x16.png"
  "32 icon_16x16@2x.png"
  "32 icon_32x32.png"
  "64 icon_32x32@2x.png"
  "128 icon_128x128.png"
  "256 icon_128x128@2x.png"
  "256 icon_256x256.png"
  "512 icon_256x256@2x.png"
  "512 icon_512x512.png"
)

# Generate all required sizes from the 1024x1024 PNG
for entry in "${SIZES[@]}"; do
  size=$(echo $entry | cut -d' ' -f1)
  name=$(echo $entry | cut -d' ' -f2)
  sips -Z "$size" "${ICONSET}/icon_512x512@2x.png" --out "${ICONSET}/${name}" >/dev/null
done

# Build .icns file
iconutil -c icns "$ICONSET" -o "$ICNS"

echo "✅ Created $ICNS"
