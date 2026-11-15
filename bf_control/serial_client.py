"""USB serial client for Betaflight MSP queries and CLI automation."""

import time
from dataclasses import dataclass

import serial
from serial.tools import list_ports

from bf_control.msp import (
    MSP_API_VERSION,
    MSP_BOARD_INFO,
    MSP_FC_VARIANT,
    MSP_FC_VERSION,
    decode_fc_info,
    encode_msp_v1,
    parse_msp_v1_stream,
)


@dataclass(frozen=True)
class DetectedPort:
    """Metadata for a detected serial port."""

    device: str
    description: str
    manufacturer: str
    vid: int | None
    pid: int | None
    is_likely_betaflight: bool


def list_serial_ports() -> list[DetectedPort]:
    """List available serial ports, flagging likely Betaflight USB CDC devices."""
    results: list[DetectedPort] = []
    for port in list_ports.comports():
        desc = port.description or ""
        mfg = port.manufacturer or ""
        dev = port.device or ""
        # On macOS, /dev/cu.* should be used instead of /dev/tty.* for outgoing serial.
        if dev.startswith("/dev/tty."):
            continue
        is_bf = (
            "usbmodem" in dev.lower()
            or "betaflight" in desc.lower()
            or "betaflight" in mfg.lower()
            or "stm" in desc.lower()
            or "stmicroelectronics" in mfg.lower()
            or "at32" in desc.lower()
            or port.vid == 0x0483  # STMicroelectronics USB VCP
        )
        results.append(
            DetectedPort(
                device=dev,
                description=desc,
                manufacturer=mfg,
                vid=port.vid,
                pid=port.pid,
                is_likely_betaflight=is_bf,
            )
        )
    return sorted(results, key=lambda p: (not p.is_likely_betaflight, p.device))


def resolve_port(explicit_port: str | None) -> str:
    """Resolve an explicit serial port or auto-detect a single Betaflight port."""
    if explicit_port:
        return explicit_port
    candidates = [p for p in list_serial_ports() if p.is_likely_betaflight]
    if not candidates:
        raise RuntimeError(
            "Nessuna porta Betaflight rilevata. Collega il drone via USB e chiudi "
            "l'app Betaflight Configurator (può tenere occupata la porta)."
        )
    if len(candidates) > 1:
        names = ", ".join(p.device for p in candidates)
        raise RuntimeError(
            f"Trovate più porte possibili ({names}). Specifica la porta con --port."
        )
    return candidates[0].device


class BetaflightClient:
    """Context-managed USB serial client supporting MSP queries and CLI sessions."""

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 0.2) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._ser: serial.Serial | None = None
        self._in_cli = False

    def __enter__(self) -> "BetaflightClient":
        self._ser = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            timeout=self.timeout,
            write_timeout=2.0,
        )
        time.sleep(0.15)
        self._ser.reset_input_buffer()
        self._ser.reset_output_buffer()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._ser is not None:
            try:
                self._ser.close()
            except (serial.SerialException, OSError):
                # Betaflight reboots on `exit`/`save`, which drops the USB CDC link.
                pass
            self._ser = None

    @property
    def ser(self) -> serial.Serial:
        if self._ser is None:
            raise RuntimeError("Serial connection is not open")
        return self._ser

    def query_msp(self, cmd: int, timeout: float = 1.5) -> bytes | None:
        """Send an MSP v1 request without payload and return the response payload."""
        if self._in_cli:
            raise RuntimeError("Cannot send MSP commands while in CLI mode")
        self.ser.reset_input_buffer()
        self.ser.write(encode_msp_v1(cmd))
        self.ser.flush()

        deadline = time.monotonic() + timeout
        buf = bytearray()
        while time.monotonic() < deadline:
            chunk = self.ser.read(256)
            if chunk:
                buf.extend(chunk)
                frame = parse_msp_v1_stream(bytes(buf))
                if frame is not None and frame.cmd == cmd:
                    if frame.is_error:
                        return None
                    return frame.payload
        return None

    def get_fc_info(self) -> dict[str, str]:
        """Query basic flight controller metadata via MSP."""
        return decode_fc_info(
            api_payload=self.query_msp(MSP_API_VERSION),
            variant_payload=self.query_msp(MSP_FC_VARIANT),
            version_payload=self.query_msp(MSP_FC_VERSION),
            board_payload=self.query_msp(MSP_BOARD_INFO),
        )

    def enter_cli(self, timeout: float = 3.0) -> str:
        """Enter Betaflight CLI mode by sending `#` and waiting for the `# ` prompt."""
        if self._in_cli:
            return ""
        self.ser.reset_input_buffer()
        self.ser.write(b"#\r\n")
        self.ser.flush()
        output = self._read_until_prompt(timeout=timeout)
        if "#" not in output:
            raise RuntimeError(
                "Impossibile entrare in modalità CLI. Verifica che il cavo USB supporti "
                "i dati e che nessun'altra app stia usando la porta."
            )
        self._in_cli = True
        return output

    def run_cli_command(
        self,
        command: str,
        timeout: float = 3.0,
        idle_timeout: float = 0.4,
    ) -> str:
        """Run a single CLI command and return the flight controller's text output."""
        if not self._in_cli:
            self.enter_cli()
        cleaned = command.strip()
        if not cleaned:
            return ""
        self.ser.reset_input_buffer()
        self.ser.write((cleaned + "\r\n").encode("utf-8"))
        self.ser.flush()
        return self._read_until_prompt(timeout=timeout, idle_timeout=idle_timeout)

    def exit_cli(self, save: bool = False) -> None:
        """Exit CLI mode (`save` persists changes and reboots; `exit` discards/reboots)."""
        if not self._in_cli:
            return
        cmd = "save\r\n" if save else "exit\r\n"
        try:
            self.ser.write(cmd.encode("utf-8"))
            self.ser.flush()
            time.sleep(0.25)
        except (serial.SerialException, OSError):
            pass
        finally:
            self._in_cli = False

    def _read_until_prompt(self, timeout: float = 3.0, idle_timeout: float = 0.4) -> str:
        """Read CLI output until Betaflight's `# ` prompt appears or timeouts elapse."""
        deadline = time.monotonic() + timeout
        last_rx = time.monotonic()
        buf = bytearray()

        while time.monotonic() < deadline:
            waiting = self.ser.in_waiting
            chunk = self.ser.read(waiting or 1)
            if chunk:
                buf.extend(chunk)
                last_rx = time.monotonic()
                text = buf.decode("utf-8", errors="replace")
                if text.endswith("\n# ") or text.endswith("\r# ") or text == "# ":
                    return text
            else:
                if buf and (time.monotonic() - last_rx) >= idle_timeout:
                    break
        return buf.decode("utf-8", errors="replace")
