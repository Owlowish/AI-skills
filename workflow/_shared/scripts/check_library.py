#!/usr/bin/env python3
"""Vérifier la structure des skills et leurs références locales, sans lancer Blender."""
import ast
from pathlib import Path
import re
import sys
import yaml

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / "workflow"


def check():
    errors = []
    skills = sorted(WORKFLOW.glob("*/SKILL.md"))
    if not skills:
        errors.append("Aucun skill.")
    for skill in skills:
        content = skill.read_text(encoding="utf-8-sig")
        match = re.match(r"^---\s*\n(.*?)\n---", content, re.S)
        if not match:
            errors.append(f"{skill}: frontmatter absent")
            continue
        try:
            meta = yaml.safe_load(match.group(1))
            name, desc = meta["name"], meta["description"]
            if name != skill.parent.name or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
                errors.append(f"{skill}: nom invalide")
            if not isinstance(desc, str) or not desc.strip() or len(desc) > 1024:
                errors.append(f"{skill}: description invalide")
        except (yaml.YAMLError, KeyError, TypeError) as exc:
            errors.append(f"{skill}: {exc}")
        ui = skill.parent / "agents/openai.yaml"
        if not ui.is_file():
            errors.append(f"{skill}: agents/openai.yaml absent")
        else:
            try:
                data = yaml.safe_load(ui.read_text(encoding="utf-8-sig"))
                interface = data["interface"]
                if not interface.get("display_name") or not 25 <= len(interface["short_description"]) <= 64:
                    errors.append(f"{ui}: métadonnées UI invalides")
            except (yaml.YAMLError, KeyError, TypeError) as exc:
                errors.append(f"{ui}: {exc}")
    for path in [ROOT / "README.md"] + list(WORKFLOW.rglob("*.md")):
        text = path.read_text(encoding="utf-8-sig")
        if re.search(r"\[TODO:", text):
            errors.append(f"{path}: scaffold TODO non terminé")
        for target in re.findall(r"\]\(([^)\n]+)\)", text):
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"):
                continue
            target = target.split("#", 1)[0].strip("<>")
            if target and not (path.parent / target).exists():
                errors.append(f"{path}: lien absent {target}")
    for path in WORKFLOW.rglob("*.py"):
        try:
            ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        except SyntaxError as exc:
            errors.append(str(exc))
    if errors:
        for error in errors:
            print("ERREUR : " + error)
        return 1
    print(f"PASS : {len(skills)} skills, métadonnées, références et syntaxe Python.")
    print("Ce contrôle ne valide aucun modèle, rig, pose ou tirage physique.")
    return 0


if __name__ == "__main__":
    sys.exit(check())
