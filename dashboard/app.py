#!/usr/bin/env python3
"""Local Friends SMP control panel with every Bedrock server.properties option."""

from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from fields import FIELDS, GROUPS, KEYS

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"
INDEX_PATH = Path(__file__).resolve().parent / "index.html"
XRAY_PACK = ROOT / "dist" / "friends-smp-xray.mcpack"
HOST = os.environ.get("DASHBOARD_HOST", "0.0.0.0")
PORT = int(os.environ.get("DASHBOARD_PORT", "8088"))
COMPOSE = ["docker", "compose", "-f", str(ROOT / "docker-compose.yml")]
CONTAINER = "friends-smp"
apply_lock = threading.Lock()
apply_state = {"busy": False, "message": "", "ok": True}
RULE_KEYS = {
    "SHOW_COORDINATES": "true",
    "DAY_MODE": "cycle",
    "SHOW_DAYS_PLAYED": "true",
    "JOIN_ANNOUNCE": "true",
}
DAY_MODES = {"cycle", "always-day", "always-night"}
JOIN_RE = re.compile(r"Player connected:\s*([^,\n]+)", re.I)
events_lock = threading.Lock()
join_events: list[dict] = []
seen_joins: set[str] = set()
TAILSCALE = Path(r"C:\Program Files\Tailscale\tailscale.exe")
BACKUP_META = Path(r"D:\Backup raghav\projects\friends-smp\last-backup.json")


def last_backup() -> dict:
    try:
        data = json.loads(BACKUP_META.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def run(cmd: list[str], timeout: int = 90) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        encoding="utf-8",
        errors="replace",
    )


def read_env() -> dict[str, str]:
    values: dict[str, str] = {}
    if not ENV_PATH.exists():
        return values
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, val = stripped.split("=", 1)
        values[key] = val
    return values


def write_env(updates: dict[str, str]) -> None:
    existing = ENV_PATH.read_text(encoding="utf-8") if ENV_PATH.exists() else ""
    lines = existing.splitlines()
    seen: set[str] = set()
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0]
            if key in updates:
                out.append(f"{key}={updates[key]}")
                seen.add(key)
                continue
        out.append(line)
    for key in list(KEYS) + list(RULE_KEYS):
        if key not in seen and key in updates:
            out.append(f"{key}={updates[key]}")
    ENV_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")


def container_state() -> dict:
    inspect = run(
        [
            "docker",
            "inspect",
            CONTAINER,
            "--format",
            "{{.State.Status}}|{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}",
        ],
        timeout=20,
    )
    if inspect.returncode != 0:
        return {"running": False, "health": "stopped", "status": "stopped"}
    status, health = (inspect.stdout.strip().split("|", 1) + ["none"])[:2]
    return {"running": status == "running", "health": health, "status": status}


def current_settings() -> dict[str, str]:
    env = read_env()
    values: dict[str, str] = {}
    for field in FIELDS:
        values[field["key"]] = env.get(field["key"], field["default"])
    return values


def current_rules() -> dict[str, str]:
    env = read_env()
    return {key: env.get(key, default) for key, default in RULE_KEYS.items()}


def tailscale_ip() -> str:
    if not TAILSCALE.exists():
        return ""
    try:
        proc = run([str(TAILSCALE), "ip", "-4"], timeout=8)
        if proc.returncode != 0:
            return ""
        line = (proc.stdout or "").strip().splitlines()
        return line[0].strip() if line else ""
    except Exception:
        return ""


def send_command(cmd: str) -> None:
    proc = run(["docker", "exec", CONTAINER, "send-command", cmd], timeout=8)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "World command failed").strip())


world_day = {"value": None}
DAY_COUNT_RE = re.compile(r"Day is (\d+)", re.I)


def refresh_world_day() -> None:
    try:
        send_command("time query day")
        time.sleep(0.5)
        match = DAY_COUNT_RE.search(logs_tail(40))
        if match:
            world_day["value"] = int(match.group(1))
    except Exception:
        pass


def apply_world_rules(rules: dict[str, str] | None = None) -> None:
    rules = rules or current_rules()
    show = rules.get("SHOW_COORDINATES", "true").lower() == "true"
    send_command(f"gamerule showcoordinates {'true' if show else 'false'}")
    days = rules.get("SHOW_DAYS_PLAYED", "true").lower() == "true"
    send_command(f"gamerule showdaysplayed {'true' if days else 'false'}")
    mode = rules.get("DAY_MODE", "cycle")
    if mode == "always-day":
        send_command("gamerule dodaylightcycle false")
        send_command("time set day")
    elif mode == "always-night":
        send_command("gamerule dodaylightcycle false")
        send_command("time set night")
    else:
        send_command("gamerule dodaylightcycle true")
    refresh_world_day()


def apply_world_rules_retry(rules: dict[str, str] | None = None) -> None:
    last: Exception | None = None
    for _ in range(8):
        try:
            apply_world_rules(rules)
            return
        except Exception as exc:
            last = exc
            time.sleep(2)
    if last:
        raise last


def validate_rules(body: dict) -> dict[str, str]:
    mode = str(body.get("DAY_MODE", RULE_KEYS["DAY_MODE"])).strip().lower()
    if mode not in DAY_MODES:
        raise ValueError("Days must be normal cycle, always day, or always night.")
    return {
        "SHOW_COORDINATES": as_bool(body.get("SHOW_COORDINATES", RULE_KEYS["SHOW_COORDINATES"])),
        "DAY_MODE": mode,
        "SHOW_DAYS_PLAYED": as_bool(body.get("SHOW_DAYS_PLAYED", RULE_KEYS["SHOW_DAYS_PLAYED"])),
        "JOIN_ANNOUNCE": as_bool(body.get("JOIN_ANNOUNCE", RULE_KEYS["JOIN_ANNOUNCE"])),
    }


def recent_joins() -> list[dict]:
    with events_lock:
        return list(join_events)


def lan_addresses() -> dict[str, list[str]]:
    ipv4: list[str] = []
    ipv6: list[str] = []
    try:
        ps = run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                (
                    "Get-NetIPAddress -AddressFamily IPv4 | "
                    "Where-Object { $_.IPAddress -notlike '127.*' -and $_.PrefixOrigin -ne 'WellKnown' } | "
                    "Select-Object -ExpandProperty IPAddress"
                ),
            ],
            timeout=15,
        )
        for ip in ps.stdout.splitlines():
            ip = ip.strip()
            if ip and not ip.startswith("172.") and ip not in ipv4:
                ipv4.append(ip)
    except Exception:
        pass
    try:
        ps6 = run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                (
                    "Get-NetIPAddress -AddressFamily IPv6 -InterfaceAlias 'Wi-Fi' | "
                    "Where-Object { $_.SuffixOrigin -eq 'Link' -and $_.PrefixOrigin -eq 'RouterAdvertisement' } | "
                    "Select-Object -ExpandProperty IPAddress"
                ),
            ],
            timeout=15,
        )
        for ip in ps6.stdout.splitlines():
            ip = ip.strip()
            if ip and ":" in ip:
                ipv6.append(ip)
    except Exception:
        pass
    if not ipv4:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(("8.8.8.8", 80))
            ipv4.append(sock.getsockname()[0])
            sock.close()
        except Exception:
            pass
    return {"ipv4": ipv4, "ipv6": ipv6}


def as_bool(raw) -> str:
    if isinstance(raw, str):
        return "true" if raw.lower() in {"1", "true", "yes", "on"} else "false"
    return "true" if raw else "false"


def validate(body: dict) -> dict[str, str]:
    cleaned: dict[str, str] = {}
    for field in FIELDS:
        key = field["key"]
        raw = body.get(key, field["default"])
        kind = field["kind"]
        if kind == "bool":
            cleaned[key] = as_bool(raw)
            continue
        if kind == "select":
            value = str(raw).strip()
            options = {str(opt) for opt in field["options"]}
            folded = {opt.lower(): opt for opt in field["options"]}
            if value in options:
                cleaned[key] = value
            elif value.lower() in folded:
                cleaned[key] = folded[value.lower()]
            else:
                raise ValueError(f"{field['label']}: pick one of {', '.join(field['options'])}.")
            continue
        if kind == "number":
            try:
                number = int(float(raw))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{field['label']} must be a whole number.") from exc
            low, high = field.get("min"), field.get("max")
            if low is not None and number < low:
                raise ValueError(f"{field['label']} must be at least {low}.")
            if high is not None and number > high:
                raise ValueError(f"{field['label']} must be at most {high}.")
            cleaned[key] = str(number)
            continue
        if kind == "float":
            try:
                number = float(raw)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{field['label']} must be a number.") from exc
            low, high = field.get("min"), field.get("max")
            if low is not None and number < low:
                raise ValueError(f"{field['label']} must be at least {low}.")
            if high is not None and number > high:
                raise ValueError(f"{field['label']} must be at most {high}.")
            cleaned[key] = str(number)
            continue
        cleaned[key] = str(raw).strip()
        if key == "SERVER_NAME":
            if not cleaned[key] or ";" in cleaned[key] or len(cleaned[key]) > 40:
                raise ValueError("Server name must be 1–40 characters and cannot contain ;")
    cleaned["WHITE_LIST"] = cleaned.get("ALLOW_LIST", "false")
    cleaned["SERVER_PORT_V6"] = cleaned.get("SERVER_PORT", "19132")
    return cleaned


def apply_settings(cleaned: dict[str, str]) -> None:
    write_env(cleaned)
    up = run(COMPOSE + ["up", "-d", "bedrock"], timeout=180)
    if up.returncode != 0:
        raise RuntimeError((up.stderr or up.stdout or "Docker Compose failed").strip())
    for _ in range(45):
        state = container_state()
        if state["health"] == "healthy":
            apply_world_rules_retry()
            return
        time.sleep(2)
    raise RuntimeError("Settings saved, but the server is still starting. Check it in a minute.")


def power(action: str) -> None:
    global _rules_applied
    if action == "start":
        proc = run(COMPOSE + ["up", "-d", "bedrock"], timeout=120)
    elif action == "stop":
        proc = run(["docker", "stop", CONTAINER], timeout=90)
    elif action == "restart":
        proc = run(["docker", "restart", CONTAINER], timeout=90)
    else:
        raise ValueError("Unknown power action.")
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "Docker command failed").strip())
    if action in {"start", "restart"}:
        _rules_applied = False
    elif action == "stop":
        _rules_applied = False


def logs_tail(lines: int = 40) -> str:
    proc = run(["docker", "logs", "--tail", str(lines), CONTAINER], timeout=20)
    return ((proc.stdout or "") + (proc.stderr or ""))[-8000:]


LEAVE_RE = re.compile(r"Player disconnected:\s*([^,\n]+)", re.I)
_log_mark = ""
_rules_applied = False


def _record_join(name: str) -> None:
    stamp = time.strftime("%H:%M:%S")
    with events_lock:
        seen_joins.add(name)
        join_events.append({"name": name, "at": stamp, "ts": int(time.time())})
        del join_events[:-30]
    if current_rules().get("JOIN_ANNOUNCE", "true").lower() == "true":
        safe = re.sub(r"[^A-Za-z0-9_ \-]", "", name)[:32] or "Someone"
        try:
            send_command(f"say {safe} joined the game")
        except Exception:
            pass


def _process_log_chunk(text: str) -> None:
    for line in text.splitlines():
        leave = LEAVE_RE.search(line)
        if leave:
            seen_joins.discard(leave.group(1).strip())
            continue
        joined = JOIN_RE.search(line)
        if joined:
            name = joined.group(1).strip()
            if name and name not in seen_joins:
                _record_join(name)


def join_watcher() -> None:
    global _log_mark, _rules_applied
    ticks = 0
    while True:
        time.sleep(3)
        ticks += 1
        try:
            state = container_state()
            if state.get("health") == "healthy" and not _rules_applied:
                try:
                    apply_world_rules()
                    _rules_applied = True
                except Exception:
                    pass
            if not state.get("running"):
                _rules_applied = False
                continue
            text = logs_tail(80)
            match = DAY_COUNT_RE.search(text)
            if match:
                world_day["value"] = int(match.group(1))
            if _log_mark and _log_mark in text:
                idx = text.rfind(_log_mark)
                _process_log_chunk(text[idx + len(_log_mark) :])
            _log_mark = text[-240:] if text else _log_mark
            if ticks % 10 == 0:
                refresh_world_day()
        except Exception:
            pass


def schema() -> dict:
    return {"groups": GROUPS, "fields": FIELDS}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _json(self, code: int, payload: dict) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        if path in {"/", "/index.html"}:
            body = INDEX_PATH.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path == "/xray.mcpack":
            # Served so a phone on the LAN can tap the link and let Minecraft import it.
            if not XRAY_PACK.exists():
                self._json(404, {"error": "X-ray pack not built. Run addons/build-xray.ps1."})
                return
            body = XRAY_PACK.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Disposition", 'attachment; filename="friends-smp-xray.mcpack"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path == "/api/schema":
            self._json(200, schema())
            return
        if path == "/api/status":
            addrs = lan_addresses()
            settings = current_settings()
            lan = [ip for ip in addrs["ipv4"] if not ip.startswith("100.")]
            self._json(
                200,
                {
                    **container_state(),
                    "apply": apply_state,
                    "settings": settings,
                    "rules": current_rules(),
                    "schema": schema(),
                    "joins": recent_joins(),
                    "world_day": world_day.get("value"),
                    "backup": last_backup(),
                    "join": {
                        "port": int(settings.get("SERVER_PORT") or 19132),
                        "lan": lan or addrs["ipv4"],
                        "tailscale": tailscale_ip(),
                        "public": addrs["ipv6"],
                    },
                    "logs": logs_tail(),
                },
            )
            return
        self._json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._json(400, {"error": "Invalid JSON"})
            return

        path = urlparse(self.path).path
        if path == "/api/settings":
            if not apply_lock.acquire(blocking=False):
                self._json(409, {"error": "Already applying settings. Wait a few seconds."})
                return
            try:
                apply_state.update(busy=True, message="Saving and restarting the world…", ok=True)
                cleaned = validate(body)
                apply_settings(cleaned)
                apply_state.update(busy=False, message="Settings are live.", ok=True)
                self._json(200, {"ok": True, "settings": cleaned, **container_state()})
            except Exception as exc:
                apply_state.update(busy=False, message=str(exc), ok=False)
                self._json(400, {"error": str(exc)})
            finally:
                apply_lock.release()
            return
        if path == "/api/power":
            try:
                power(str(body.get("action", "")))
                time.sleep(1)
                self._json(200, {"ok": True, **container_state()})
            except Exception as exc:
                self._json(400, {"error": str(exc)})
            return
        if path == "/api/rules":
            try:
                rules = validate_rules(body)
                write_env(rules)
                apply_world_rules_retry(rules)
                self._json(200, {"ok": True, "rules": rules})
            except Exception as exc:
                self._json(400, {"error": str(exc)})
            return
        self._json(404, {"error": "Not found"})


def main() -> None:
    threading.Thread(target=join_watcher, name="join-watcher", daemon=True).start()
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Friends SMP dashboard: http://127.0.0.1:{PORT}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
