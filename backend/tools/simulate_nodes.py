#!/usr/bin/env python3
"""Generate distributed traffic logs against the FluxSentinel collect endpoint."""

from __future__ import annotations

import argparse
import json
import random
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone


NORMAL_ENDPOINTS = ["/", "/api/status", "/search", "/profile", "/products"]
ATTACK_ENDPOINTS = ["/login", "/auth", "/admin", "/checkout", "/api/search"]


def make_payload(node_id: int, attack_ratio: float) -> dict:
    is_attack = random.random() < attack_ratio
    base_ip = f"10.0.{node_id % 255}.{random.randint(1, 254)}"

    if is_attack:
        return {
            "ip": base_ip,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "endpoint": random.choice(ATTACK_ENDPOINTS),
            "request_rate": random.randint(180, 420),
            "status_code": random.choice([401, 403, 429, 500]),
            "payload_size": random.randint(900, 4500),
            "failed_logins": random.randint(8, 30),
            "total_logins": random.randint(10, 35),
            "unique_endpoints_count": random.randint(12, 80),
            "time_gap_between_requests": round(random.uniform(0.001, 0.05), 4),
            "baseline_payload_size": random.randint(256, 768),
        }

    return {
        "ip": base_ip,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "endpoint": random.choice(NORMAL_ENDPOINTS),
        "request_rate": random.randint(5, 90),
        "status_code": random.choices([200, 201, 204, 304], weights=[70, 15, 10, 5], k=1)[0],
        "payload_size": random.randint(100, 1800),
        "failed_logins": random.randint(0, 2),
        "total_logins": random.randint(0, 5),
        "unique_endpoints_count": random.randint(1, 8),
        "time_gap_between_requests": round(random.uniform(0.08, 2.5), 4),
        "baseline_payload_size": random.randint(300, 1000),
    }


def post_log(url: str, payload: dict, timeout: float) -> tuple[bool, dict | None, str | None]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url=url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            parsed = json.loads(body) if body else None
            return response.status < 400, parsed, None
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return False, None, f"HTTP {exc.code}: {body[:180]}"
    except Exception as exc:
        return False, None, str(exc)


class SimulatorNode(threading.Thread):
    def __init__(
        self,
        node_id: int,
        url: str,
        attack_ratio: float,
        interval_ms: int,
        timeout: float,
        stop_event: threading.Event,
        counters: dict,
        lock: threading.Lock,
    ) -> None:
        super().__init__(daemon=True)
        self.node_id = node_id
        self.url = url
        self.attack_ratio = attack_ratio
        self.interval_ms = interval_ms
        self.timeout = timeout
        self.stop_event = stop_event
        self.counters = counters
        self.lock = lock

    def run(self) -> None:
        while not self.stop_event.is_set():
            payload = make_payload(self.node_id, self.attack_ratio)
            ok, result, error = post_log(self.url, payload, self.timeout)

            with self.lock:
                self.counters["sent"] += 1
                if ok:
                    self.counters["success"] += 1
                    if result and int(result.get("prediction", 0)) == 1:
                        self.counters["detected_attacks"] += 1
                else:
                    self.counters["failed"] += 1
                    self.counters["last_error"] = error

            sleep_seconds = max(self.interval_ms + random.randint(-80, 80), 10) / 1000
            self.stop_event.wait(sleep_seconds)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Simulate distributed traffic nodes against /api/collect-log"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:5000/api/collect-log",
        help="Collect log endpoint URL",
    )
    parser.add_argument("--nodes", type=int, default=5, help="Number of simulator nodes")
    parser.add_argument(
        "--duration-seconds", type=int, default=60, help="Simulation duration in seconds"
    )
    parser.add_argument(
        "--interval-ms",
        type=int,
        default=250,
        help="Base delay between requests per node in milliseconds",
    )
    parser.add_argument(
        "--attack-ratio",
        type=float,
        default=0.30,
        help="Fraction of generated traffic that should look malicious (0.0 to 1.0)",
    )
    parser.add_argument("--timeout", type=float, default=5.0, help="HTTP request timeout")
    parser.add_argument(
        "--print-every",
        type=int,
        default=5,
        help="Progress print interval in seconds",
    )
    parser.add_argument("--seed", type=int, default=None, help="Optional random seed")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    if args.nodes < 1:
        raise SystemExit("--nodes must be >= 1")
    if args.duration_seconds < 1:
        raise SystemExit("--duration-seconds must be >= 1")
    if not 0 <= args.attack_ratio <= 1:
        raise SystemExit("--attack-ratio must be between 0 and 1")

    counters = {
        "sent": 0,
        "success": 0,
        "failed": 0,
        "detected_attacks": 0,
        "last_error": None,
    }
    lock = threading.Lock()
    stop_event = threading.Event()

    nodes = [
        SimulatorNode(
            node_id=index + 1,
            url=args.url,
            attack_ratio=args.attack_ratio,
            interval_ms=args.interval_ms,
            timeout=args.timeout,
            stop_event=stop_event,
            counters=counters,
            lock=lock,
        )
        for index in range(args.nodes)
    ]

    print(
        f"[sim] starting nodes={args.nodes} duration={args.duration_seconds}s "
        f"attack_ratio={args.attack_ratio} url={args.url}"
    )

    for node in nodes:
        node.start()

    started_at = time.time()
    next_print = started_at + args.print_every

    try:
        while time.time() - started_at < args.duration_seconds:
            if time.time() >= next_print:
                with lock:
                    print(
                        "[sim] sent={sent} success={success} failed={failed} detected_attacks={detected_attacks}".format(
                            **counters
                        )
                    )
                next_print += args.print_every
            time.sleep(0.2)
    finally:
        stop_event.set()
        for node in nodes:
            node.join(timeout=2)

    with lock:
        print("[sim] complete")
        print(
            "[sim] totals sent={sent} success={success} failed={failed} detected_attacks={detected_attacks}".format(
                **counters
            )
        )
        if counters["last_error"]:
            print(f"[sim] last_error={counters['last_error']}")

    return 0 if counters["success"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
