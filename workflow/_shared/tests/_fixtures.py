"""Fixtures SYNTHETIC : aucune modélisation ou validation visuelle réelle."""
from pathlib import Path
import json
import struct
import zlib

VERTS = [(0,0,0),(1,0,0),(0,1,0),(1,1,0),(0,0,1),(1,0,1),(0,1,1),(1,1,1)]
QUADS = [(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)]


def cube(scale=(1,2,3), offset=(0,0,0), reverse=False):
    vertices = [tuple(v[i]*scale[i]+offset[i] for i in range(3)) for v in VERTS]
    result = []
    for a,b,c,d in QUADS:
        for face in [(a,b,c),(a,c,d)]:
            points = tuple(vertices[i] for i in face)
            result.append(tuple(reversed(points)) if reverse else points)
    return result


def stl(path, triangles=None, ascii=False):
    path = Path(path);path.parent.mkdir(parents=True, exist_ok=True)
    triangles = cube() if triangles is None else triangles
    if ascii:
        lines = ["solid SYNTHETIC"]
        for tri in triangles:
            lines += ["facet normal 0 0 0", "outer loop"]
            lines += ["vertex " + " ".join(str(x) for x in point) for point in tri]
            lines += ["endloop", "endfacet"]
        path.write_text("\n".join(lines + ["endsolid SYNTHETIC"]), encoding="utf-8")
    else:
        data = b"SYNTHETIC TEST ONLY".ljust(80, b" ") + struct.pack("<I", len(triangles))
        for tri in triangles:
            data += struct.pack("<12fH", 0,0,0, *(x for v in tri for x in v), 0)
        path.write_bytes(data)
    return path


def png(path):
    def chunk(kind, data):
        return struct.pack(">I",len(data)) + kind + data + struct.pack(">I",zlib.crc32(kind+data) & 0xffffffff)
    path = Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    raw = b"".join(b"\x00" + b"\x80\x80\x80"*128 for _ in range(128))
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR",struct.pack(">IIBBBBB",128,128,8,2,0,0,0)) + chunk(b"IDAT",zlib.compress(raw)) + chunk(b"IEND",b""))


def write_json(path, data):
    path = Path(path);path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
