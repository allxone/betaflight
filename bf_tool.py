#!/usr/bin/env python3
"""Command-line tool to inspect, backup, and configure Betaflight over USB."""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from bf_control.serial_client import BetaflightClient, list_serial_ports, resolve_port

ROOT_DIR = Path(__file__).resolve().parent
BACKUPS_DIR = ROOT_DIR / "drone" / "backups"


def _strip_cli_echo_and_prompt(raw: str, sent_cmd: str) -> str:
    """Clean echoed command and trailing `# ` prompt from CLI output."""
    lines = raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if lines and lines[0].strip() == sent_cmd.strip():
        lines = lines[1:]
    if lines and lines[-1].strip() == "#":
        lines = lines[:-1]
    return "\n".join(lines).strip() + "\n"


def cmd_ports(_args: argparse.Namespace) -> int:
    ports = list_serial_ports()
    if not ports:
        print("Nessuna porta seriale trovata.")
        return 1
    for p in ports:
        tag = "[Betaflight?]" if p.is_likely_betaflight else "             "
        extra = " - ".join(x for x in (p.description, p.manufacturer) if x)
        print(f"{tag} {p.device}  ({extra})")
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    port = resolve_port(args.port)
    with BetaflightClient(port) as client:
        info = client.get_fc_info()
        if info:
            print(f"Porta: {port}")
            for key, val in info.items():
                print(f"  {key}: {val}")
        else:
            print(f"Porta: {port} (MSP non ha risposto, provo CLI `version`)")
            client.enter_cli()
            print(_strip_cli_echo_and_prompt(client.run_cli_command("version"), "version"))
            client.exit_cli(save=False)
    return 0


def cmd_backup(args: argparse.Namespace) -> int:
    port = resolve_port(args.port)
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    prefix = args.name or "air65"

    with BetaflightClient(port) as client:
        client.enter_cli()
        version_out = _strip_cli_echo_and_prompt(
            client.run_cli_command("version", timeout=3.0), "version"
        )
        diff_out = _strip_cli_echo_and_prompt(
            client.run_cli_command("diff all", timeout=8.0, idle_timeout=0.7), "diff all"
        )
        diff_path = BACKUPS_DIR / f"{prefix}_{stamp}_diff_all.txt"
        diff_path.write_text(f"# version\n{version_out}\n# diff all\n{diff_out}", encoding="utf-8")
        print(f"Salvato diff all: {diff_path}")

        if args.with_dump:
            dump_out = _strip_cli_echo_and_prompt(
                client.run_cli_command("dump", timeout=15.0, idle_timeout=1.0), "dump"
            )
            dump_path = BACKUPS_DIR / f"{prefix}_{stamp}_dump.txt"
            dump_path.write_text(dump_out, encoding="utf-8")
            print(f"Salvato dump completo: {dump_path}")

        client.exit_cli(save=False)
    return 0


def cmd_cli(args: argparse.Namespace) -> int:
    port = resolve_port(args.port)
    command_str = " ".join(args.command).strip()
    if not command_str:
        print("Specifica un comando CLI, es: python bf_tool.py cmd status", file=sys.stderr)
        return 2
    if command_str.lower() == "save":
        print("Usa `apply --save` per salvare modifiche, non `cmd save`.", file=sys.stderr)
        return 2

    with BetaflightClient(port) as client:
        client.enter_cli()
        out = _strip_cli_echo_and_prompt(
            client.run_cli_command(command_str, timeout=6.0, idle_timeout=0.6), command_str
        )
        print(out, end="")
        client.exit_cli(save=False)
    return 0


def cmd_apply(args: argparse.Namespace) -> int:
    cfg_path = Path(args.file)
    if not cfg_path.is_file():
        print(f"File non trovato: {cfg_path}", file=sys.stderr)
        return 2

    raw_lines = cfg_path.read_text(encoding="utf-8").splitlines()
    commands: list[str] = []
    for line in raw_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.lower() in ("save", "exit"):
            # `save`/`exit` are controlled explicitly via --save.
            continue
        commands.append(stripped)

    if not commands:
        print("Nessun comando valido nel file.")
        return 0

    if args.dry_run:
        print(f"[DRY-RUN] Comandi che verrebbero inviati ({len(commands)}):")
        for c in commands:
            print(f"  {c}")
        print(f"[DRY-RUN] save={args.save}")
        return 0

    port = resolve_port(args.port)
    with BetaflightClient(port) as client:
        client.enter_cli()
        for c in commands:
            out = _strip_cli_echo_and_prompt(
                client.run_cli_command(c, timeout=4.0, idle_timeout=0.3), c
            )
            print(f"> {c}")
            if out.strip():
                print(out.strip())
        client.exit_cli(save=args.save)
        if args.save:
            print("Configurazione salvata (`save`) e FC riavviato.")
        else:
            print("Modalità test (`--save` non passato): modifiche NON salvate in EEPROM.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Controllo programmatico Betaflight (CLI & MSP) per BetaFPV Air65 Racing"
    )
    parser.add_argument("--port", help="Porta seriale esplicita (es. /dev/cu.usbmodem...)")
    sub = parser.add_subparsers(dest="subcommand", required=True)

    p_ports = sub.add_parser("ports", help="Elenca le porte seriali disponibili")
    p_ports.set_defaults(func=cmd_ports)

    p_info = sub.add_parser("info", help="Legge versione firmware e target via MSP")
    p_info.set_defaults(func=cmd_info)

    p_backup = sub.add_parser("backup", help="Salva backup `diff all` (e opzionale `dump`)")
    p_backup.add_argument("--name", default="air65", help="Prefisso del file di backup")
    p_backup.add_argument("--with-dump", action="store_true", help="Salva anche `dump` completo")
    p_backup.set_defaults(func=cmd_backup)

    p_cmd = sub.add_parser("cmd", help="Esegue un comando CLI senza salvare")
    p_cmd.add_argument("command", nargs="+", help="Comando CLI da eseguire (es. status)")
    p_cmd.set_defaults(func=cmd_cli)

    p_apply = sub.add_parser("apply", help="Applica un file di comandi CLI")
    p_apply.add_argument("file", help="Percorso del file .txt/.cfg con comandi Betaflight CLI")
    p_apply.add_argument("--save", action="store_true", help="Invia `save` al termine")
    p_apply.add_argument("--dry-run", action="store_true", help="Mostra i comandi senza inviarli")
    p_apply.set_defaults(func=cmd_apply)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
