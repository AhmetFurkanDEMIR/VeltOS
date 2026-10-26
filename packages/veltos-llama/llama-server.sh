#!/bin/sh
# VeltOS AI's local model engine: llama.cpp's llama-server (veltos-llama).
# The CPU backends next to the program are found through its directory.
exec /usr/lib/veltos-llama/llama-server "$@"
