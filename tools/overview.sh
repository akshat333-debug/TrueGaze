#!/bin/sh
# Joins the stills in outputs/renders/ into the overview images used by the README and deck. Needs ffmpeg.
set -e
R=outputs/renders
sheet() {  # sheet <columns>x<rows> <output> <stills...>
  layout=$1; out=$2; shift 2
  args=""; for f in "$@"; do args="$args -i $R/$f.png"; done
  ffmpeg -v error -y $args -filter_complex "concat=n=$#:v=1:a=0,scale=640:360,tile=$layout" -frames:v 1 -q:v 3 "$out"
}
# each set: front view above its close-up
sheet 4x4 docs/texture_sets.jpg 01_front 02_front 03_front 04_front 01_close 02_close 03_close 04_close \
                                05_front 06_front 07_front 08_front 05_close 06_close 07_close 08_close
sheet 4x2 docs/hero_sets.jpg 01_hero 02_hero 03_hero 04_hero 05_hero 06_hero 07_hero 08_hero
sheet 3x1 docs/breakdown.jpg 01_wire_hero 01_clay_hero 01_hero
