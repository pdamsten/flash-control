#!/bin/sh

# Depedencies installation

#python -m pip install -r dependencies-macos.txt

# Update the workflow file to use the new command string

PYTHON=$(which python3)
APP="$(pwd)/flash-control.py"
CMD="\"$PYTHON\" \"$APP\""
WFLOW="$(pwd)/Flash Control.app/Contents/document.wflow"

ESCAPED_COMMAND=$(printf "%s" "$CMD" | sed 's/"/\\\"/g' | awk '{printf "%s\\n", $0}')
echo $ESCAPED_COMMAND
sed -i '' -E "/<key>COMMAND_STRING<\/key>/{n;s|<string>.*</string>|<string>$ESCAPED_COMMAND</string>|;}" "$WFLOW"