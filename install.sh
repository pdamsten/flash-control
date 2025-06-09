#!/bin/sh

echo "Installing dependencies..."

python -m pip install -r dependencies-macos.txt

echo "Updating workflow file in app bundle..."

PYTHON=$(which python3)
APP="$(pwd)/flash-control.py"
CMD="\"$PYTHON\" \"$APP\""
WFLOW="$(pwd)/Flash Control.app/Contents/document.wflow"

echo $CMD
ESCAPED_COMMAND=$(printf "%s" "$CMD" | sed 's/"/\\\"/g' | awk '{printf "%s", $0}')
#echo $ESCAPED_COMMAND
sed -i '' -E "/<key>COMMAND_STRING<\/key>/{n;s|<string>.*</string>|<string>$ESCAPED_COMMAND</string>|;}" "$WFLOW"