# veltos-llama — the engine of VeltOS AI's local model

llama.cpp's `llama-server`, built from the pinned, SHA-256-checked release
in `upstream.json` (Debian 13 has no llama.cpp; Debian forky/sid has). It
is installed in `/usr/lib/veltos-llama/` with its private libraries and
started through `/usr/libexec/veltos/llama-server` by VeltOS AI
(`veltos_ai/local.py`) on 127.0.0.1 when the local model is used.

- Portable: the CPU backend is built in every x86-64 variant
  (`GGML_CPU_ALL_VARIANTS`) and the best one is loaded at start.
- No network during the build (no prebuilt web UI, no HTTPS client), no
  web UI at run time (`--no-webui`).
- No model is shipped: VeltOS AI downloads Gemma 3 270M (185 MB) or a
  model the user picks on Hugging Face.

Tests (`tests/test_server.py`): the built server starts, prints its version,
knows the options VeltOS AI passes and has its CPU backends.
