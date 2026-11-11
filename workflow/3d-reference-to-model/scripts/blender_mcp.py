#!/usr/bin/env python3
"""Client MCP stdio pour le serveur Blender déjà configuré, sans socket directe.

Employer le Python du venv MCP si le SDK n'est pas installé dans Python courant.
Les sorties sont limitées à projects/<slug>/ et .local-checks/ dans le dépôt.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tomllib


class CheckError(Exception):
    """Erreur explicite, sans données de configuration sensibles."""


def output_path(root: Path, value: str, suffix: str) -> Path:
    path = Path(value)
    path = (root / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        parts = path.relative_to(root).parts
    except ValueError as exc:
        raise CheckError("Sortie refusée : chemin hors du dépôt.") from exc
    allowed = (
        len(parts) >= 2 and parts[0] == ".local-checks"
        or len(parts) >= 3 and parts[0] == "projects"
        and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", parts[1]) is not None
        and len(parts[1]) <= 64
    )
    if not allowed or path.suffix.lower() != suffix:
        raise CheckError(f"Sortie refusée : utiliser projects/<slug>/ ou .local-checks/ et l'extension {suffix}.")
    if parts[0] == "projects" and parts[2:4] == ("references", "source"):
        raise CheckError("Sortie refusée : les références originales sont immuables.")
    if parts[0] == "projects" and path.exists() and suffix != ".log":
        raise CheckError("Sortie refusée : ne pas écraser un artefact de projet existant.")
    return path


def server_config(config: Path, name: str) -> dict:
    try:
        with config.open("rb") as stream:
            entry = tomllib.load(stream).get("mcp_servers", {}).get(name)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise CheckError("Configuration Codex inaccessible ou TOML invalide.") from exc
    if not isinstance(entry, dict) or entry.get("enabled") is False:
        raise CheckError(f"Serveur MCP {name!r} absent ou désactivé.")
    command = entry.get("command")
    if not isinstance(command, str) or not command:
        raise CheckError("Ce client exige un serveur stdio avec command ; URL HTTP non prise en charge.")
    if not (Path(command).is_file() or shutil.which(command)):
        raise CheckError("L'exécutable du serveur Blender configuré est introuvable.")
    arguments = entry.get("args", [])
    environment = entry.get("env", {})
    forwarded = entry.get("env_vars", [])
    if not isinstance(arguments, list) or not all(isinstance(v, str) for v in arguments):
        raise CheckError("args du serveur doit être une liste de chaînes.")
    if not isinstance(environment, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in environment.items()):
        raise CheckError("env du serveur doit contenir uniquement des chaînes.")
    if not isinstance(forwarded, list) or not all(isinstance(v, str) for v in forwarded):
        raise CheckError("env_vars du serveur doit être une liste de chaînes.")
    env = {key: os.environ[key] for key in forwarded if key in os.environ}
    env.update(environment)
    cwd = entry.get("cwd")
    if cwd is not None and (not isinstance(cwd, str) or not Path(cwd).is_dir()):
        raise CheckError("cwd du serveur est invalide ou absent.")
    return {"command": command, "args": arguments, "env": env, "cwd": cwd}


def tool_failed(result: dict) -> bool:
    if result.get("isError"):
        return True
    for block in result.get("content", []):
        if block.get("type") != "text":
            continue
        text = block.get("text", "").strip().lower()
        if text.startswith(("error", "rejected by safe mode", "couldn't ", "could not ")):
            return True
        if "could not connect to blender" in text or "traceback (most recent call last)" in text:
            return True
    return False


def known_failure(exc: BaseException) -> str | None:
    """Extraire nos erreurs sûres même sous les ExceptionGroup du SDK async."""
    if isinstance(exc, CheckError):
        return str(exc)
    if isinstance(exc, TimeoutError):
        return "Délai MCP dépassé ; scène non validée. Consulter le journal local du rapport."
    if isinstance(exc, BaseExceptionGroup):
        for nested in exc.exceptions:
            message = known_failure(nested)
            if message:
                return message
    return None


def save_content_images(result: dict, root: Path, report_path: Path, requested: str | None) -> list[str]:
    saved = []
    for block in result.get("content", []):
        if block.get("type") != "image":
            continue
        data = block.pop("data", "")
        mime = block.get("mimeType")
        if mime not in ("image/png", "image/jpeg"):
            raise CheckError("Format d'image MCP non pris en charge ; données retirées du rapport.")
        suffix = ".png" if mime == "image/png" else ".jpg"
        if requested:
            if suffix != ".png":
                raise CheckError("--image-output attend une PNG mais le serveur a renvoyé un autre format.")
            target = output_path(root, requested, suffix)
            if saved:
                target = output_path(root, str(target.with_name(f"{target.stem}-{len(saved) + 1}{suffix}")), suffix)
        else:
            target = output_path(root, str(report_path.with_name(f"{report_path.stem}-image-{len(saved) + 1:02d}{suffix}")), suffix)
        try:
            decoded = base64.b64decode(data, validate=True)
        except (ValueError, TypeError) as exc:
            raise CheckError("Contenu d'image MCP invalide.") from exc
        if suffix == ".png" and not decoded.startswith(b"\x89PNG\r\n\x1a\n"):
            raise CheckError("La réponse annoncée PNG n'a pas la signature d'une PNG.")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(decoded)
        block["saved_image"] = str(target.relative_to(root)).replace("\\", "/")
        saved.append(str(target))
    return saved


async def connect(args, root: Path, report_path: Path, settings: dict) -> dict:
    import anyio
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    report = {"schema_version": 1, "transport": "MCP stdio", "server": args.server,
              "status": "FAIL", "operations": [], "images": []}
    params = StdioServerParameters(**settings)
    log_path = output_path(root, str(report_path.with_suffix(".stderr.log")), ".log")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log:
        with anyio.fail_after(args.timeout):
            async with stdio_client(params, errlog=log) as (read, write):
                async with ClientSession(read, write) as session:
                    initialized = await session.initialize()
                    report["server_info"] = initialized.serverInfo.model_dump(mode="json")
                    report["protocol_version"] = initialized.protocolVersion
                    listing = await session.list_tools()
                    tool_names = {tool.name for tool in listing.tools}
                    report["tools"] = [tool.model_dump(mode="json", exclude_none=True) for tool in listing.tools]

                    async def call(name: str, arguments: dict):
                        if name not in tool_names:
                            raise CheckError(f"Outil {name!r} absent du tools/list réel.")
                        if name == "generate_3d":
                            raise CheckError("La génération 3D externe est exclue de ce workflow.")
                        result = (await session.call_tool(name, arguments)).model_dump(mode="json", exclude_none=True)
                        images = save_content_images(result, root, report_path, getattr(args, "image_output", None))
                        report["images"].extend(images)
                        report["operations"].append({"tool": name, "status": "FAIL" if tool_failed(result) else "PASS", "result": result})

                    if args.action == "probe":
                        await call("get_scene_info", {})
                        # Lecture seule via le vrai outil de code ; aucun ajout d'objet.
                        if not any(op["status"] == "FAIL" for op in report["operations"]):
                            await call("execute_blender_code", {"code": 'import bpy\nimport json\nprint(json.dumps({"blender_version": bpy.app.version_string, "scene": bpy.context.scene.name, "filepath": bpy.data.filepath}))'})
                    else:
                        await call(args.tool, args.arguments)
                    report["status"] = "PASS" if report["operations"] and all(op["status"] == "PASS" for op in report["operations"]) else "FAIL"
    return report


def main() -> int:
    # Les pipes PowerShell/SDK attendent de l'UTF-8, même sous une locale Windows ANSI.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[4]), help="Racine du dépôt (déduite du skill par défaut).")
    parser.add_argument("--config", default=str(Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "config.toml"), help="Configuration Codex à lire, jamais modifiée.")
    parser.add_argument("--server", default="blender", help="Nom de mcp_servers à utiliser.")
    parser.add_argument("--timeout", type=float, default=45, help="Limite totale en secondes, entre 5 et 120 (défaut 45).")
    actions = parser.add_subparsers(dest="action", required=True)
    probe = actions.add_parser("probe", help="initialize, tools/list, lecture de scène et version Blender.")
    probe.add_argument("--output", required=True, help="Rapport JSON sous projects/<slug>/ ou .local-checks/.")
    call = actions.add_parser("call", help="Appeler un outil réellement découvert, avec arguments JSON.")
    call.add_argument("--tool", required=True)
    call.add_argument("--arguments-file", required=True, help="Fichier JSON contenant un objet d'arguments.")
    call.add_argument("--output", required=True, help="Rapport JSON sous projects/<slug>/ ou .local-checks/.")
    call.add_argument("--image-output", help="PNG locale si le tool retourne ImageContent (sinon nom voisin du rapport).")
    args = parser.parse_args()
    report_path = None
    try:
        root = Path(args.repo_root).resolve(strict=True)
        if not root.is_dir() or not 5 <= args.timeout <= 120:
            raise CheckError("Racine invalide ou timeout hors de l'intervalle 5–120 secondes.")
        report_path = output_path(root, args.output, ".json")
        if args.action == "call":
            if args.image_output:
                output_path(root, args.image_output, ".png")
            try:
                args.arguments = json.loads(Path(args.arguments_file).read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError) as exc:
                raise CheckError("Fichier d'arguments inaccessible ou JSON invalide.") from exc
            if not isinstance(args.arguments, dict):
                raise CheckError("Le fichier d'arguments doit contenir un objet JSON.")
        settings = server_config(Path(args.config), args.server)
        try:
            import anyio
            import mcp  # noqa: F401 -- contrôle explicite de la dépendance optionnelle
        except ImportError as exc:
            raise CheckError("SDK MCP absent : lancer ce script avec .tools/mcp-for-blender/Scripts/python.exe ou le Python du serveur déjà installé.") from exc
        report = anyio.run(connect, args, root, report_path, settings)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": report["status"], "report": str(report_path), "images": report["images"]}, ensure_ascii=False))
        return 0 if report["status"] == "PASS" else 1
    except CheckError as exc:
        error = str(exc)
    except TimeoutError:
        error = "Délai MCP dépassé ; scène non validée. Consulter le journal local du rapport."
    except (OSError, ValueError):
        error = "Échec d'accès local ou de réponse MCP ; scène non validée. Consulter le journal local."
    except Exception as exc:
        # Les groupes d'exceptions du transport peuvent contenir env/arguments : ne pas les afficher.
        error = known_failure(exc) or f"Échec du transport MCP ({type(exc).__name__}) ; scène non validée. Consulter le journal local."
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps({"schema_version": 1, "status": "FAIL", "error": error}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "FAIL", "error": error}, ensure_ascii=False), file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
