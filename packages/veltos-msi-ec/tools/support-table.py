#!/usr/bin/env python3
"""Which EC firmware versions the pinned msi-ec knows, and whether it lights
their keyboard, read from its source at package build time:

    support-table.py upstream/msi-ec.c support.json

msi-ec.c has one `struct msi_ec_conf CONF_*` per family of laptops, with
the firmware versions it accepts (`.allowed_fw = ALLOWED_FW_*`, a list of
strings, most with the laptops' names as a comment) and the keyboard
light's EC address (`.kbd_bl.bl_state_address`; MSI_EC_ADDR_UNSUPP when it
has none). The result maps each firmware version to
{"keyboard": bool, "models": "..."}. The build stops when the source no
longer looks like that (upstream changed).
"""

import json
import re
import sys
from pathlib import Path


def table(source):
    lists = dict(re.findall(r"static const char \*(?: const)? ?(ALLOWED_FW_\w+)\[\] __initconst = \{(.*?)\};",
                            source, re.S))
    confs = re.findall(r"static struct msi_ec_conf (CONF_\w+) __initdata = \{(.*?)\n\};", source, re.S)
    if not lists or not confs:
        raise SystemExit("msi-ec.c: no firmware lists or configurations found (upstream changed?)")
    out = {}
    for name, body in confs:
        allowed = re.search(r"\.allowed_fw\s*=\s*(\w+)", body)
        light = re.search(r"\.kbd_bl\s*=\s*\{(.*?)\n\t\}", body, re.S)
        if not allowed or allowed.group(1) not in lists or not light:
            raise SystemExit(f"msi-ec.c: {name} has no firmware list or keyboard light entry (upstream changed?)")
        address = re.search(r"\.bl_state_address\s*=\s*([^,]+),", light.group(1))
        if not address:
            raise SystemExit(f"msi-ec.c: {name} has no bl_state_address (upstream changed?)")
        keyboard = address.group(1).strip() not in ("MSI_EC_ADDR_UNSUPP", "MSI_EC_ADDR_UNKNOWN")
        for fw, comment in re.findall(r'"([^"]+)",[ \t]*(?://[ \t]*([^\n]*))?', lists[allowed.group(1)]):
            out[fw] = {"keyboard": keyboard, "models": comment.strip()}
    return out


def main():
    source, dest = Path(sys.argv[1]), Path(sys.argv[2])
    result = table(source.read_text(encoding="utf-8"))
    if len(result) < 50:
        raise SystemExit(f"msi-ec.c: only {len(result)} firmware versions found (upstream changed?)")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"{dest}: {len(result)} firmware versions, {sum(v['keyboard'] for v in result.values())} with a keyboard light")


if __name__ == "__main__":
    main()
