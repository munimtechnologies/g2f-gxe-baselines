# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
# Waits (up to 40 minutes) until the pre-registration is public on GitHub, so the job can only read
# yield data after the predictions are committed. Exits 1 if it never appears.
import sys
import time
import urllib.error
import urllib.request

URL = ("https://raw.githubusercontent.com/munimtechnologies/g2f-gxe-baselines/main/"
       "docs/g2f-envkernel-0.1.0-prereg.md")

for attempt in range(41):
    try:
        with urllib.request.urlopen(URL, timeout=30) as resp:
            text = resp.read().decode("utf-8", "replace")
        if "g2f-envkernel 0.1.0: pre-registration" in text:
            print("pre-registration is public:", URL, len(text), "chars, attempt", attempt, flush=True)
            sys.exit(0)
    except (urllib.error.URLError, OSError) as exc:
        print("attempt", attempt, "not yet:", exc, flush=True)
    time.sleep(60)
print("pre-registration never appeared at", URL, flush=True)
sys.exit(1)
