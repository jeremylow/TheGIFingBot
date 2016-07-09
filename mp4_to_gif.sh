#!/bin/sh

palette="/tmp/palette.png"

filters=""

ffmpeg -i "$1" -vf "palettegen" -y $palette
ffmpeg -i "$1" -i $palette -lavfi "paletteuse" -y -r 8 $2
