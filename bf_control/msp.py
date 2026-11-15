"""Minimal MSP v1 encoder/decoder for read-only flight controller inspection."""

from dataclasses import dataclass

MSP_API_VERSION = 1
MSP_FC_VARIANT = 2
MSP_FC_VERSION = 3
MSP_BOARD_INFO = 4


@dataclass(frozen=True)
class MspFrame:
    """Represents a decoded MSP v1 response frame."""

    cmd: int
    payload: bytes
    is_error: bool = False


def encode_msp_v1(cmd: int, payload: bytes = b"") -> bytes:
    """Encode an MSP v1 request frame ($M<)."""
    length = len(payload)
    if length > 255:
        raise ValueError("MSP v1 payload cannot exceed 255 bytes")
    checksum = length ^ cmd
    for byte in payload:
        checksum ^= byte
    return b"$M<" + bytes((length, cmd)) + payload + bytes((checksum,))


def parse_msp_v1_stream(data: bytes) -> MspFrame | None:
    """Extract the first complete MSP v1 response frame from a byte buffer."""
    idx = 0
    while idx + 6 <= len(data):
        if data[idx : idx + 2] == b"$M" and data[idx + 2 : idx + 3] in (b">", b"!"):
            is_error = data[idx + 2 : idx + 3] == b"!"
            length = data[idx + 3]
            cmd = data[idx + 4]
            end = idx + 5 + length
            if end + 1 > len(data):
                return None
            payload = data[idx + 5 : end]
            expected_crc = data[end]
            crc = length ^ cmd
            for byte in payload:
                crc ^= byte
            if crc == expected_crc:
                return MspFrame(cmd=cmd, payload=payload, is_error=is_error)
        idx += 1
    return None


def decode_fc_info(
    api_payload: bytes | None,
    variant_payload: bytes | None,
    version_payload: bytes | None,
    board_payload: bytes | None,
) -> dict[str, str]:
    """Decode standard Betaflight identification payloads into a readable dict."""
    info: dict[str, str] = {}
    if variant_payload and len(variant_payload) >= 4:
        info["fc_variant"] = variant_payload[:4].decode("ascii", errors="replace")
    if version_payload and len(version_payload) >= 3:
        info["fc_version"] = f"{version_payload[0]}.{version_payload[1]}.{version_payload[2]}"
    if api_payload and len(api_payload) >= 3:
        info["msp_api"] = f"{api_payload[1]}.{api_payload[2]}"
    if board_payload and len(board_payload) >= 4:
        info["board_id"] = board_payload[:4].decode("ascii", errors="replace").strip("\x00")
        if len(board_payload) >= 9:
            target_len = board_payload[8]
            if len(board_payload) >= 9 + target_len:
                info["target_name"] = board_payload[9 : 9 + target_len].decode(
                    "ascii", errors="replace"
                )
    return info
