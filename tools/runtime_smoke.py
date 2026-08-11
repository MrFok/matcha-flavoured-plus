#!/usr/bin/env python3
"""Exercise a dedicated Minecraft server through its local RCON endpoint."""

from __future__ import annotations

import argparse
from pathlib import Path
import socket
import struct
import time


AUTH = 3
AUTH_RESPONSE = 2
COMMAND = 2
RESPONSE_VALUE = 0


class RconError(RuntimeError):
    pass


class Rcon:
    def __init__(self, host: str, port: int, password: str):
        self.socket = socket.create_connection((host, port), timeout=5)
        self.socket.settimeout(10)
        self.request_id = 0
        self._authenticate(password)

    def close(self) -> None:
        self.socket.close()

    def _next_request_id(self) -> int:
        self.request_id += 1
        return self.request_id

    def _read_exact(self, length: int) -> bytes:
        chunks = bytearray()
        while len(chunks) < length:
            chunk = self.socket.recv(length - len(chunks))
            if not chunk:
                raise RconError("RCON connection closed before a complete packet arrived")
            chunks.extend(chunk)
        return bytes(chunks)

    def _read_packet(self) -> tuple[int, int, str]:
        (length,) = struct.unpack("<i", self._read_exact(4))
        if length < 10:
            raise RconError(f"RCON response has invalid length: {length}")
        packet = self._read_exact(length)
        request_id, packet_type = struct.unpack("<ii", packet[:8])
        if packet[-2:] != b"\x00\x00":
            raise RconError("RCON response is missing its terminator")
        return request_id, packet_type, packet[8:-2].decode("utf-8")

    def _send_packet(self, request_id: int, packet_type: int, body: str) -> None:
        encoded = body.encode("utf-8")
        packet = struct.pack("<iii", len(encoded) + 10, request_id, packet_type)
        self.socket.sendall(packet + encoded + b"\x00\x00")

    def _authenticate(self, password: str) -> None:
        request_id = self._next_request_id()
        self._send_packet(request_id, AUTH, password)
        while True:
            response_id, packet_type, _ = self._read_packet()
            if response_id == -1:
                raise RconError("RCON authentication failed")
            if response_id == request_id and packet_type == AUTH_RESPONSE:
                return

    def command(self, command: str) -> str:
        request_id = self._next_request_id()
        self._send_packet(request_id, COMMAND, command)
        response = []
        while True:
            response_id, packet_type, body = self._read_packet()
            if response_id == -1:
                raise RconError(f"RCON command failed: {command}")
            if response_id == request_id and packet_type == RESPONSE_VALUE:
                response.append(body)
                return "".join(response)


def wait_for_server(log_path: Path, host: str, port: int, password: str, timeout: int) -> Rcon:
    deadline = time.monotonic() + timeout
    last_error: OSError | RconError | None = None
    while time.monotonic() < deadline:
        if log_path.exists() and "Done (" in log_path.read_text(
            encoding="utf-8", errors="replace"
        ):
            try:
                return Rcon(host, port, password)
            except (OSError, RconError) as error:
                last_error = error
        time.sleep(1)
    detail = f" ({last_error})" if last_error else ""
    raise RconError(f"Minecraft server did not accept RCON within {timeout} seconds{detail}")


def wait_for_log(log_path: Path, expected: str, timeout: int) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if log_path.exists() and expected in log_path.read_text(
            encoding="utf-8", errors="replace"
        ):
            return
        time.sleep(1)
    raise RconError(f"Minecraft server did not log {expected!r} within {timeout} seconds")


def assert_clean_matcha_log(log_path: Path) -> None:
    log = log_path.read_text(encoding="utf-8", errors="replace")
    prohibited = (
        "InvalidMixinException",
        "MixinApplyError",
        "InjectionError",
        "Mixin transformation of",
        "Invalid path in pack:",
        "Couldn't parse data file",
        "Failed to parse data file",
        "Failed to load function",
        "Unknown or incomplete command",
        "Unknown scoreboard objective",
        "Missing block model: minecraft:block/bedrock_buster",
        "Missing block model: minecraft:block/warding_stone",
        "Found loot table element validation problem in {minecraft:entities/skeleton",
        "Found loot table element validation problem in {minecraft:chests/adventure_old/ruin_generic_storage",
    )
    failures = [line for line in log.splitlines() if any(token in line for token in prohibited)]
    if failures:
        raise RconError("Matcha runtime load errors:\n" + "\n".join(failures))


def assert_expected_gpu(log_path: Path, expected_gpu: str) -> None:
    log = log_path.read_text(encoding="utf-8", errors="replace")
    device_lines = [
        line for line in log.splitlines() if "Using graphics device:" in line
    ]
    if not device_lines:
        raise RconError("Client log does not report a graphics device")
    if expected_gpu.casefold() not in device_lines[-1].casefold():
        raise RconError(
            f"Expected graphics device {expected_gpu!r}, got: {device_lines[-1]}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument(
        "--log-only",
        action="store_true",
        help="Validate an existing client or server log without connecting over RCON.",
    )
    parser.add_argument(
        "--require-gpu",
        help="Require the client log's selected graphics device to contain this text.",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=25575)
    parser.add_argument("--password")
    parser.add_argument("--timeout", type=int, default=90)
    args = parser.parse_args()

    if args.log_only:
        assert_clean_matcha_log(args.log)
        if args.require_gpu:
            assert_expected_gpu(args.log, args.require_gpu)
        return

    if args.require_gpu:
        parser.error("--require-gpu is only valid with --log-only")

    if not args.password:
        parser.error("--password is required unless --log-only is used")

    rcon = wait_for_server(args.log, args.host, args.port, args.password, args.timeout)
    try:
        enabled_packs = rcon.command("datapack list enabled")
        if "matcha_flavoured_plus" not in enabled_packs:
            raise RconError(f"Matcha data pack is not enabled: {enabled_packs}")

        initial_objectives = rcon.command("scoreboard objectives list")
        if "sleepTimerScore" not in initial_objectives:
            raise RconError(
                "Matcha load function did not create sleepTimerScore: "
                f"{initial_objectives}"
            )
        keep_inventory = rcon.command("gamerule keep_inventory")
        if "true" not in keep_inventory.lower():
            raise RconError(f"Matcha gamerule setup did not enable keepInventory: {keep_inventory}")

        rcon.command("reload")
        reloaded_objectives = rcon.command("scoreboard objectives list")
        if "sleepTimerScore" not in reloaded_objectives:
            raise RconError(
                "sleepTimerScore disappeared after /reload: "
                f"{reloaded_objectives}"
            )
        rcon.command("scoreboard objectives remove sleepTimerScore")
        rcon.command("function matcha_flavoured_plus:main/setup/scoreboard")
        sleep_timer = rcon.command("scoreboard players get 1 sleepTimerScore")
        if "has 1 [sleepTimerScore]" not in sleep_timer:
            raise RconError(f"Sleep timer did not initialize: {sleep_timer}")
    finally:
        try:
            rcon.command("stop")
        except (OSError, RconError):
            pass
        rcon.close()

    wait_for_log(args.log, "Stopping server", 30)
    assert_clean_matcha_log(args.log)


if __name__ == "__main__":
    main()
