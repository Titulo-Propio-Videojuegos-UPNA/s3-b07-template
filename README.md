# Agentes e Interfaces de Herramientas Verificadas (`MCP`) (`Plan Definitivo · 2026-10-25` — Subbloque `B07.3`)

> **Fecha de verificación y consolidación:** `2026-10-25`

| Fichero | Qué es | Subbloque vigente (`2026-10-25`) | Estado verificado |
|---|---|---|---|
| [`mcp_gate.py`](mcp_gate.py) | Compuerta determinista `McpSecurityGate`: *allow-list* de herramientas MCP, validación de esquemas JSON y cotas numéricas, confinamiento de rutas (*anti-traversal*), modo *dry-run* y auditoría `.jsonl` | `B07.3` (*Integración de agentes con herramientas verificadas MCP y pasarela de seguridad*, `4 h`) | **Implementado y verificado** (`python evolucion/s3-ia/mcp_gate.py`, 4 casos en verde) |
| [`laboratorio-seguridad-agentes.md`](laboratorio-seguridad-agentes.md) | Guion del laboratorio práctico de `B07.3`: tres trampas inofensivas (inyección en documentación, paquete inexistente y secreto en contexto) y su mitigación con `McpSecurityGate` | `B07.3` | **Listo para aula** |

---

## Cápsulas de Sesión y Etiquetas de Paracaídas (`s3-b07-template`)

- **Proyecto / Toybox:** Proyecto 7: «Escuadrón Táctico Autónomo en C++ (BT + EQS) y Agente MCP» (arena táctica con coberturas donde agentes C++ patrullan, flanquean con EQS y exponen herramientas seguras vía MCP Python).
- **Capas 70 / 20 / 10:** • 70 % Base (en aula): Agente C++ con AAIController, UAIPerceptionComponent, UBTTaskNode/UBTService en C++, consulta EQS de cobertura y herramienta MCP local validada. · • 20 % Reto autónomo: Coordinación táctica de 2 agentes (flanqueo/supresión) depurada en Visual Logger + guardarraíl de timeout en MCP. · • 10 % Extra Portfolio: Vídeo comparativo del comportamiento táctico con superposición del Visual Logger y EQS.
- **Plataforma docente (vídeo indexado y entregas):** [https://ikasyn.com/titulo-videojuegos](https://ikasyn.com/titulo-videojuegos)

| Sesión | Subbloque | Horas | Título | Tag Inicio (`sync_checkpoint`) | Tag Fin |
|:---:|:---:|:---:|---|---|---|
| `S3-01` | `B07.1` | 2 h | IA Táctica en C++ · Arquitectura de AAIController, APawn y UBlackboardComponent | `scripts\sync_checkpoint.bat s3-01-start` | `s3-01-end` |
| `S3-02` | `B07.1` | 2 h | IA Táctica en C++ · Percepción sensorial en C++ (UAIPerceptionComponent: Vista y Oído) | `scripts\sync_checkpoint.bat s3-02-start` | `s3-02-end` |
| `S3-03` | `B07.1` | 2 h | IA Táctica en C++ · Behavior Trees: selectores, secuencias, decoradores Observer Aborts y comparativa con State Trees | `scripts\sync_checkpoint.bat s3-03-start` | `s3-03-end` |
| `S3-04` | `B07.2` | 2 h | IA Táctica en C++ · Programación de nodos nativos en C++: UBTTaskNode y UBTService | `scripts\sync_checkpoint.bat s3-04-start` | `s3-04-end` |
| `S3-05` | `B07.2` | 2 h | IA Táctica en C++ · Consultas espaciales tácticas con Environment Query System (EQS) | `scripts\sync_checkpoint.bat s3-05-start` | `s3-05-end` |
| `S3-06` | `B07.2` | 2 h | IA Táctica en C++ · Depuración rebobinable frame a frame con Visual Logger (UE_VLOG) | `scripts\sync_checkpoint.bat s3-06-start` | `s3-06-end` |
| `S3-07` | `B07.3` | 2 h | Agentes Verificados (MCP) · Pasarela Model Context Protocol (Python ↔ UE5) con validación de esquemas | `scripts\sync_checkpoint.bat s3-07-start` | `s3-07-end` |
| `S3-08` | `B07.3` | 2 h | Cierre B07 · Guardarraíles de ingeniería (listas blancas, timeouts y fallback determinista) y defensa en aula | `scripts\sync_checkpoint.bat s3-08-end` | `s3-08-end` |
