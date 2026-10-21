#!/usr/bin/python3
"""A stand-in for polkit-agent-helper-1 with its line protocol: reads the
cookie, asks for the password, and succeeds only with "secret"."""
import sys

user = sys.argv[1] if len(sys.argv) > 1 else ""
cookie = sys.stdin.readline().strip()
sys.stdout.write("PAM_PROMPT_ECHO_OFF Password: \n")
sys.stdout.flush()
password = sys.stdin.readline().rstrip("\n")
if cookie == "cookie-1" and user == "velt" and password == "secret":
    sys.stdout.write("SUCCESS\n")
    sys.stdout.flush()
    sys.exit(0)
sys.stdout.write("PAM_ERROR_MSG Authentication failure\\nTry again\n")
sys.stdout.write("FAILURE\n")
sys.stdout.flush()
sys.exit(2)
