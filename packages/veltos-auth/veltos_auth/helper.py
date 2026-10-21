"""The conversation with polkit's setuid helper, polkit-agent-helper-1,
which checks a password through PAM and tells polkit the result.

    helper <user name>      first line of stdin: the cookie
    stdout lines:           PAM_PROMPT_ECHO_OFF <text>   answer with a line
                            PAM_PROMPT_ECHO_ON <text>    answer with a line
                            PAM_ERROR_MSG <text>, PAM_TEXT_INFO <text>
                            SUCCESS | FAILURE            the end

Messages are C-escaped by the helper (g_strescape); answers are plain
lines. Exit code 0 means the password was right and polkit has been told.
"""

import os

HELPER_PATHS = ("/usr/lib/polkit-1/polkit-agent-helper-1", "/usr/libexec/polkit-agent-helper-1",
                "/usr/lib/policykit-1/polkit-agent-helper-1")


def helper_path(environ=None):
    environ = os.environ if environ is None else environ
    override = environ.get("VELTOS_AUTH_HELPER")
    if override:
        return override
    for path in HELPER_PATHS:
        if os.path.isfile(path):
            return path
    return HELPER_PATHS[0]


def unescape(text):
    """g_strescape's escapes back to text."""
    return (text.replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "\r")
            .replace('\\"', '"').replace("\\\\", "\\"))


def parse_line(line):
    """("prompt", text, hidden) | ("error", text) | ("info", text) |
    ("success", "") | ("failure", "") | None for other output."""
    line = line.rstrip("\r\n")
    if line == "SUCCESS":
        return ("success", "", False)
    if line == "FAILURE":
        return ("failure", "", False)
    kind, _space, text = line.partition(" ")
    text = unescape(text)
    if kind == "PAM_PROMPT_ECHO_OFF":
        return ("prompt", text, True)
    if kind == "PAM_PROMPT_ECHO_ON":
        return ("prompt", text, False)
    if kind == "PAM_ERROR_MSG":
        return ("error", text, False)
    if kind == "PAM_TEXT_INFO":
        return ("info", text, False)
    return None
