#!/usr/bin/env python3
"""Audit STL ASCII/binaire en supposant des coordonnées millimétriques."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import struct


def read_triangles(path: Path):
    data = path.read_bytes()
    if len(data) >= 84:
        count = struct.unpack_from("<I", data, 80)[0]
        if len(data) == 84 + count * 50:
            triangles = []
            for i in range(count):
                values = struct.unpack_from("<12fH", data, 84 + i * 50)
                triangles.append(tuple(tuple(values[j:j+3]) for j in (3, 6, 9)))
            return triangles
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("STL binaire tronqué ou texte invalide.") from exc
    if not text.lstrip().lower().startswith("solid"):
        raise ValueError("En-tête STL invalide.")
    vertices = []
    facets = 0
    ends = 0
    for line in text.splitlines():
        fields = line.strip().split()
        if not fields:
            continue
        word = fields[0].lower()
        if word == "facet":
            facets += 1
        elif word == "endfacet":
            ends += 1
        elif word == "vertex":
            if len(fields) != 4:
                raise ValueError("Sommet ASCII invalide.")
            vertices.append(tuple(float(x) for x in fields[1:]))
    if len(vertices) % 3 or facets != len(vertices) // 3 or ends != facets:
        raise ValueError("Facettes ASCII incomplètes.")
    return [tuple(vertices[i:i+3]) for i in range(0, len(vertices), 3)]


def audit_stl(path: Path, expected_mm=None, allow_multiple_shells=False):
    triangles = read_triangles(Path(path))
    if not triangles:
        raise ValueError("STL vide.")
    if any(not math.isfinite(x) for tri in triangles for v in tri for x in v):
        raise ValueError("Coordonnée NaN ou infinie.")
    low = [min(v[i] for tri in triangles for v in tri) for i in range(3)]
    high = [max(v[i] for tri in triangles for v in tri) for i in range(3)]
    dimensions = [high[i] - low[i] for i in range(3)]
    origin = [(high[i] + low[i]) / 2 for i in range(3)]
    edges = defaultdict(list)
    signatures = Counter()
    parents = list(range(len(triangles)))
    volumes = []
    degenerates = 0

    def root(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i

    for index, triangle in enumerate(triangles):
        keys = [tuple(round(x, 6) for x in v) for v in triangle]
        signatures[tuple(sorted(keys))] += 1
        a, b, c = triangle
        ab = [b[i] - a[i] for i in range(3)]
        ac = [c[i] - a[i] for i in range(3)]
        cross = (ab[1]*ac[2]-ab[2]*ac[1], ab[2]*ac[0]-ab[0]*ac[2], ab[0]*ac[1]-ab[1]*ac[0])
        if len(set(keys)) != 3 or sum(x*x for x in cross) <= 1e-24:
            degenerates += 1
        ar, br, cr = [[v[i] - origin[i] for i in range(3)] for v in triangle]
        volumes.append((ar[0]*(br[1]*cr[2]-br[2]*cr[1])
                        - ar[1]*(br[0]*cr[2]-br[2]*cr[0])
                        + ar[2]*(br[0]*cr[1]-br[1]*cr[0])) / 6)
        for j in range(3):
            u, v = keys[j], keys[(j+1) % 3]
            key = tuple(sorted((u, v)))
            edges[key].append((index, 1 if u <= v else -1))
    for uses in edges.values():
        for index, _ in uses[1:]:
            parents[root(index)] = root(uses[0][0])
    components = defaultdict(float)
    for i, volume in enumerate(volumes):
        components[root(i)] += volume
    boundary = sum(len(uses) == 1 for uses in edges.values())
    nonmanifold = sum(len(uses) != 2 for uses in edges.values())
    orientation = sum(len(uses) == 2 and sum(direction for _, direction in uses) != 0 for uses in edges.values())
    duplicate = sum(n - 1 for n in signatures.values() if n > 1)
    volume = sum(volumes)
    issues = []
    for condition, message in [
        (degenerates, "Triangles dégénérés"),
        (boundary, "Bords ouverts"),
        (nonmanifold, "Arêtes nonmanifold"),
        (orientation, "Orientation incohérente des faces adjacentes"),
        (duplicate, "Triangles dupliqués"),
        (volume <= 1e-12, "Volume signé nul ou négatif"),
        (len(components) != 1 and not allow_multiple_shells, "Plusieurs composantes de surface : examen explicite requis"),
    ]:
        if condition:
            issues.append(message)
    if expected_mm is not None:
        if len(expected_mm) != 3 or any(not math.isfinite(x) or x <= 0 for x in expected_mm):
            raise ValueError("Dimensions attendues : trois nombres positifs en mm.")
        if any(abs(a-b) > max(.001, abs(b)*1e-5) for a, b in zip(dimensions, expected_mm)):
            issues.append("Dimensions différentes de celles attendues en mm")
    return {
        "status": "FAIL" if issues else "PASS",
        "units_assumption": "mm",
        "triangles": len(triangles),
        "bounds": [low, high],
        "dimensions_mm": dimensions,
        "signed_volume_mm3": volume,
        "surface_components": len(components),
        "component_volumes_mm3": list(components.values()),
        "degenerate_triangles": degenerates,
        "boundary_edges": boundary,
        "nonmanifold_edges": nonmanifold,
        "orientation_errors": orientation,
        "duplicate_triangles": duplicate,
        "issues": issues,
        "limits": "Pas de preuve exhaustive d'absence d'auto-intersections, ni contrôle des supports ou du tranchage."
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stl", type=Path)
    parser.add_argument("--expected-mm", type=float, nargs=3)
    parser.add_argument("--allow-multiple-shells", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = audit_stl(args.stl, args.expected_mm, args.allow_multiple_shells)
        output = json.dumps(result, ensure_ascii=False, indent=2)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(output + "\n")
        print(output)
        return 0 if result["status"] == "PASS" else 1
    except (OSError, ValueError) as exc:
        print("ERREUR : " + str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
