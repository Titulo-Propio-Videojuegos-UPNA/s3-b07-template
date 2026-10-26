#!/usr/bin/env python3
"""
McpSecurityGate — Compuerta determinista de seguridad para herramientas MCP
===========================================================================

Material de referencia para el Bloque B07 (S3: IA Espacial y Táctica en C++ y Agentes
con Herramientas Verificadas MCP — subbloque B07.3: Ingeniería de agentes verificados y protocolo MCP).

Implementa las cuatro defensas obligatorias del laboratorio:
  1. Lista blanca estricta de herramientas permitidas (allow-list).
  2. Validación de tipos, rangos y rutas sobre los argumentos (anti-traversal).
  3. Modo de simulación (dry-run) antes de mutar la escena o el disco.
  4. Registro de auditoría inmutable en formato JSON Lines (.jsonl).

Uso directo (auto-test de los 3 vectores del laboratorio):
    python evolucion/s3-ia/mcp_gate.py
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class ToolSpec:
    """Especificación declarativa de una herramienta MCP expuesta al agente."""

    name: str
    required_args: dict[str, type]
    numeric_bounds: dict[str, tuple[float, float]] = field(default_factory=dict)
    path_arg: str | None = None
    allowed_root: Path | None = None
    mutates_state: bool = False


@dataclass
class GateDecision:
    """Resultado determinista de evaluar una invocación de herramienta."""

    allowed: bool
    tool: str
    reason: str
    dry_run: bool
    sanitized_args: dict[str, Any] = field(default_factory=dict)
    result: Any = None


class McpSecurityGate:
    """Compuerta de seguridad que intercepta toda llamada del agente antes del motor."""

    def __init__(
        self,
        allowed_tools: dict[str, ToolSpec],
        audit_log_path: Path,
        dry_run: bool = False,
    ) -> None:
        self._specs = dict(allowed_tools)
        self._audit_log_path = audit_log_path
        self._dry_run = dry_run

    def execute(
        self,
        tool_name: str,
        args: dict[str, Any],
        handler: Callable[[dict[str, Any]], Any] | None = None,
    ) -> GateDecision:
        # 1. Allow-list estricta de herramientas
        spec = self._specs.get(tool_name)
        if spec is None:
            decision = GateDecision(
                allowed=False,
                tool=tool_name,
                reason=f"Tool '{tool_name}' is not in the MCP allow-list",
                dry_run=self._dry_run,
            )
            self._write_audit(decision, raw_args=args)
            return decision

        # 2. Comprobación de argumentos obligatorios y tipos
        extra_keys = set(args.keys()) - set(spec.required_args.keys())
        if extra_keys:
            decision = GateDecision(
                allowed=False,
                tool=tool_name,
                reason=f"Unexpected arguments: {sorted(extra_keys)}",
                dry_run=self._dry_run,
            )
            self._write_audit(decision, raw_args=args)
            return decision

        for arg_name, expected_type in spec.required_args.items():
            if arg_name not in args:
                decision = GateDecision(
                    allowed=False,
                    tool=tool_name,
                    reason=f"Missing required argument '{arg_name}'",
                    dry_run=self._dry_run,
                )
                self._write_audit(decision, raw_args=args)
                return decision

            val = args[arg_name]
            # En Python bool es subclase de int; lo rechazamos si se espera int/float
            if expected_type in (int, float) and isinstance(val, bool):
                decision = GateDecision(
                    allowed=False,
                    tool=tool_name,
                    reason=f"Argument '{arg_name}' must be numeric, got bool",
                    dry_run=self._dry_run,
                )
                self._write_audit(decision, raw_args=args)
                return decision

            if expected_type is float and isinstance(val, (int, float)):
                continue
            if not isinstance(val, expected_type):
                decision = GateDecision(
                    allowed=False,
                    tool=tool_name,
                    reason=(
                        f"Argument '{arg_name}' expected {expected_type.__name__}, "
                        f"got {type(val).__name__}"
                    ),
                    dry_run=self._dry_run,
                )
                self._write_audit(decision, raw_args=args)
                return decision

        # 3. Límites numéricos (evita denegación de servicio por miles de spawns)
        for arg_name, (min_val, max_val) in spec.numeric_bounds.items():
            num = float(args[arg_name])
            if not (min_val <= num <= max_val):
                decision = GateDecision(
                    allowed=False,
                    tool=tool_name,
                    reason=(
                        f"Argument '{arg_name}'={num} out of bounds "
                        f"[{min_val}, {max_val}]"
                    ),
                    dry_run=self._dry_run,
                )
                self._write_audit(decision, raw_args=args)
                return decision

        # 4. Confinamiento de rutas (anti-path-traversal fuera del sandbox)
        sanitized = dict(args)
        if spec.path_arg and spec.allowed_root is not None:
            raw_path = str(args[spec.path_arg])
            root = spec.allowed_root.resolve()
            candidate = (root / raw_path).resolve()
            try:
                candidate.relative_to(root)
            except ValueError:
                decision = GateDecision(
                    allowed=False,
                    tool=tool_name,
                    reason=f"Path traversal blocked: '{raw_path}' escapes '{root}'",
                    dry_run=self._dry_run,
                )
                self._write_audit(decision, raw_args=args)
                return decision
            sanitized[spec.path_arg] = candidate.as_posix()

        # 5. Ejecución o modo dry-run
        output = None
        if not (self._dry_run and spec.mutates_state) and handler is not None:
            output = handler(sanitized)

        decision = GateDecision(
            allowed=True,
            tool=tool_name,
            reason="Dry-run simulated OK" if (self._dry_run and spec.mutates_state) else "Allowed",
            dry_run=self._dry_run,
            sanitized_args=sanitized,
            result=output,
        )
        self._write_audit(decision, raw_args=args)
        return decision

    def _write_audit(self, decision: GateDecision, raw_args: dict[str, Any]) -> None:
        self._audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "tool": decision.tool,
            "allowed": decision.allowed,
            "dry_run": decision.dry_run,
            "reason": decision.reason,
            "raw_args": raw_args,
        }
        with self._audit_log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def build_default_scene_gate(sandbox_root: Path, audit_log: Path, dry_run: bool = True) -> McpSecurityGate:
    """Construye la compuerta de referencia para el servidor MCP de escena."""
    specs = {
        "list_scene_nodes": ToolSpec(
            name="list_scene_nodes",
            required_args={"filter_prefix": str},
            mutates_state=False,
        ),
        "spawn_prop": ToolSpec(
            name="spawn_prop",
            required_args={"asset_id": str, "count": int, "x": float, "y": float},
            numeric_bounds={"count": (1, 25), "x": (-1000.0, 1000.0), "y": (-1000.0, 1000.0)},
            mutates_state=True,
        ),
        "export_scene_report": ToolSpec(
            name="export_scene_report",
            required_args={"relative_path": str},
            path_arg="relative_path",
            allowed_root=sandbox_root,
            mutates_state=True,
        ),
    }
    return McpSecurityGate(allowed_tools=specs, audit_log_path=audit_log, dry_run=dry_run)


def _run_self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        sandbox = tmp_path / "sandbox_exports"
        sandbox.mkdir(parents=True, exist_ok=True)
        audit_file = tmp_path / "mcp_audit.jsonl"

        gate = build_default_scene_gate(sandbox_root=sandbox, audit_log=audit_file, dry_run=True)

        # Caso 1: invocación legítima dentro de rango
        ok_decision = gate.execute(
            "spawn_prop",
            {"asset_id": "crate_wood_01", "count": 4, "x": 12.0, "y": -8.5},
        )
        assert ok_decision.allowed, f"Expected allowed, got: {ok_decision}"

        # Vector 1 (inyección en descripción de asset -> herramienta destructiva no listada)
        v1_decision = gate.execute("delete_all_actors", {"confirm": True})
        assert not v1_decision.allowed, "Vector 1 (unlisted destructive tool) must be blocked"

        # Vector 2 (path traversal intentando escapar de sandbox_exports/)
        v2_decision = gate.execute(
            "export_scene_report",
            {"relative_path": "../../secrets/credentials.json"},
        )
        assert not v2_decision.allowed, "Vector 2 (path traversal) must be blocked"

        # Vector 3 (agotamiento de recursos / spawn masivo fuera de cota)
        v3_decision = gate.execute(
            "spawn_prop",
            {"asset_id": "barrel_explosive", "count": 50000, "x": 0.0, "y": 0.0},
        )
        assert not v3_decision.allowed, "Vector 3 (out-of-bounds spawn count) must be blocked"

        lines = audit_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 4, f"Expected 4 audit log entries, got {len(lines)}"

    print("[OK] McpSecurityGate superó los 4 casos de verificación (1 legítimo + 3 vectores de ataque).")
    return 0


if __name__ == "__main__":
    sys.exit(_run_self_test())
