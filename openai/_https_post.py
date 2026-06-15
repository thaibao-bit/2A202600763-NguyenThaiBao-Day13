from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request


def main():
    request = json.loads(sys.stdin.read())
    data = json.dumps(request["payload"]).encode("utf-8")
    req = urllib.request.Request(
        request["endpoint"],
        data=data,
        headers=request["headers"],
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=request.get("timeout") or 120) as resp:
            sys.stdout.buffer.write(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP {exc.code}: {body}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
