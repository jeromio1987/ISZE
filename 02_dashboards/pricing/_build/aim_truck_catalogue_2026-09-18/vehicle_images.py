#!/usr/bin/env python3
"""The vehicle picture and its zone hotspots for the AIM truck catalogue page.

CHANGING THE PICTURE
--------------------
Edit the one path in PICTURES for that vehicle. Nothing else needs to change: the
hotspots are stored as fractions of the bounding box the vehicle occupies inside
the picture, so a picture of a different size, crop or aspect ratio still works,
as long as it shows the same vehicle from roughly the same angle. If the framing
is very different, correct BBOX and the band numbers below, which is data, not
code.

HOW THE HOTSPOTS ARE FITTED
---------------------------
Rather than tracing each zone's outline by hand, which is error-prone and invisible
when it is wrong, each vehicle carries a bounding box for the vehicle in the
picture and the six zones are bands of that box. A zone is then a rectangle over
the part of the vehicle it names:

    front    the nose, ahead of the front axle
    cab      the driver's box, doors and glass
    engine   under the cab, where the engine sits
    rear     the body behind the cab, or the back of a pickup
    chassis  the underslung band along the whole vehicle
    elec     two small boxes inside the others, as it is a layer not a place

Because the boxes are defined as fractions of the vehicle's own bounding box, a
hotspot cannot fall into the background: if the bounding box is right, the zones
are on the vehicle by construction.

WHAT THE PICTURES ARE
---------------------
All four are genuine photographs of the real vehicle, from Wikimedia Commons under
CC BY-SA 4.0, so the page shows a real Isuzu rather than a model of one. They are
the working stand-in while a decision on purchased photoreal 3D models is pending.
Swapping in a render of such a model is a one-line change per vehicle below.
"""
from __future__ import annotations

import base64
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_FINAL = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_truck_ref\final"

# ===========================================================================
# THE SWAP POINT: one line per vehicle.
# ===========================================================================
PICTURES = {
    "dmax": os.path.join(_FINAL, "dmax.jpg"),
    "nlr":  os.path.join(_FINAL, "nlr.jpg"),
    "nmr":  os.path.join(_FINAL, "nmr.jpg"),
    "frr":  os.path.join(_FINAL, "frr.jpg"),
}

CREDIT = {
    "dmax": "Photograph: Isuzu D-Max, third generation. Wikimedia Commons, CC BY-SA 4.0.",
    "nlr":  "Photograph: Isuzu Elf (N-Series light cab-over). Wikimedia Commons, CC BY-SA 4.0.",
    "nmr":  "Photograph: Isuzu NQR (wide-cab N-Series). Wikimedia Commons, CC BY-SA 4.0.",
    "frr":  "Photograph: Isuzu Forward FRR (F-Series cab-chassis). Wikimedia Commons, CC BY-SA 4.0.",
}

# What each picture actually shows, stated so the page never implies more than the
# photograph supports.
DEPICTS = {
    "dmax": "Isuzu D-Max, third generation, double cab",
    "nlr":  "Isuzu Elf, the N-Series light cab-over (NLR-class)",
    "nmr":  "Isuzu NQR, the wide-cab N-Series (NPR/NMR-class)",
    "frr":  "Isuzu Forward FRR, the F-Series cab-chassis",
}

# ===========================================================================
# Where the vehicle sits in each picture, as fractions of the image, and which way
# it faces. This is the one thing to correct if a picture is replaced.
#   bbox  [x, y, x1, y1] round the vehicle itself
#   face  'left' when the nose points left, 'right' when it points right
#   kind  'pickup' or 'cabover' or 'side' - changes which bands are used
# ===========================================================================
FIT = {
    # Rear three-quarter, viewed along the driver's side; the cab and the bonnet
    # run off to the right, so the nose is the right-hand band.
    "dmax": {"bbox": [0.010, 0.075, 0.980, 0.965], "face": "right", "kind": "pickup"},
    # Front three-quarter facing left: nose, cab, then a dropside body.
    "nlr":  {"bbox": [0.015, 0.140, 0.985, 0.920], "face": "left",  "kind": "cabover"},
    # Front three-quarter facing left: nose, cab, then a box body.
    "nmr":  {"bbox": [0.010, 0.090, 0.985, 0.900], "face": "left",  "kind": "cabover"},
    # Side view facing left: nose, cab, then bare frame and rear axle.
    "frr":  {"bbox": [0.015, 0.030, 0.990, 0.930], "face": "left",  "kind": "side"},
}

# The zone boxes, as fractions of the vehicle's bounding box measured from its
# nose (x) and its top (y). A truck is not a rectangle, so each zone carries its
# own vertical range as well as its position along the vehicle: the dropside body
# of a cab-over is lower than the cab roof, and the nose of a cab-over is lower
# again than the box behind it. Defining all four edges is what stops a hotspot
# covering the sky above the load bed.
#
# For a vehicle facing right the x values are mirrored automatically.
ZONES_BOX = {
    # Front three-quarter cab-over facing left: a tall cab, a lower nose, and a
    # body box sitting on the frame behind the cab.
    "cabover": {
        "front":   [0.000, 0.105, 0.300, 0.960],
        "cab":     [0.105, 0.335, 0.000, 0.960],
        "rear":    [0.335, 1.000, 0.215, 0.775],
        "chassis": [0.000, 1.000, 0.735, 1.000],
        "engine":  [0.115, 0.330, 0.545, 0.930],
        "elec":    [0.160, 0.260, 0.030, 0.240],
    },
    # Side view cab-over on a bare chassis: the cab is tall, and behind it the
    # frame and rear axle sit low. Because this photograph is a bare cab-chassis,
    # the rear zone is fitted to the frame and axle that are actually there rather
    # than to a body the picture does not show, so no hotspot sits over the sky.
    "side": {
        "front":   [0.000, 0.110, 0.235, 0.880],
        "cab":     [0.110, 0.345, 0.000, 0.930],
        "rear":    [0.370, 1.000, 0.660, 0.980],
        "chassis": [0.000, 1.000, 0.640, 1.000],
        "engine":  [0.115, 0.340, 0.560, 0.920],
        "elec":    [0.160, 0.270, 0.040, 0.230],
    },
    # Rear three-quarter pickup facing right: cab and bonnet ahead, load bed
    # behind, both lower than the cab roof.
    "pickup": {
        "front":   [0.775, 1.000, 0.400, 0.930],
        "cab":     [0.330, 0.775, 0.000, 0.930],
        "rear":    [0.000, 0.330, 0.300, 0.930],
        "chassis": [0.000, 1.000, 0.700, 1.000],
        "engine":  [0.560, 0.800, 0.520, 0.900],
        "elec":    [0.420, 0.530, 0.120, 0.350],
    },
}
# The electrical layer is a tag rather than a place, so it has a second box, in
# the rear half, showing that a loom runs the length of the vehicle.
ELEC_SECOND = {
    "cabover": [0.470, 0.590, 0.130, 0.390],
    "side":    [0.460, 0.600, 0.280, 0.540],
    "pickup":  [0.100, 0.220, 0.400, 0.620],
}

# Label anchors, as fractions of the vehicle's bounding box: a point each zone
# actually covers, so the leader line points at the right part of the truck.
ANCHORS_BOX = {
    "cabover": {"front": [0.055, 0.62], "cab": [0.220, 0.40], "engine": [0.215, 0.74],
                "rear": [0.640, 0.36], "chassis": [0.620, 0.76], "elec": [0.195, 0.22]},
    "side":    {"front": [0.055, 0.58], "cab": [0.225, 0.36], "engine": [0.225, 0.72],
                "rear": [0.660, 0.82], "chassis": [0.640, 0.84], "elec": [0.200, 0.17]},
    "pickup":  {"front": [0.900, 0.56], "cab": [0.520, 0.28], "engine": [0.780, 0.62],
                "rear": [0.170, 0.55], "chassis": [0.500, 0.88], "elec": [0.470, 0.24]},
}

ZONE_ORDER = ["front", "cab", "engine", "chassis", "rear", "elec"]


def _box_to_frac(points, bbox, face):
    """A point in bounding-box fractions -> image fractions."""
    bx0, by0, bx1, by1 = bbox
    bw, bh = bx1 - bx0, by1 - by0
    u = (1.0 - points[0]) if face == "right" else points[0]
    return [round(bx0 + u * bw, 5), round(by0 + points[1] * bh, 5)]


def _rect(x0, y0, x1, y1, bbox, face):
    """A rectangle in bounding-box fractions -> an image-fraction polygon."""
    pts = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
    return [_box_to_frac(p, bbox, face) for p in pts]


def build_zones():
    """The six zones per vehicle, as polygons in fractions of the image."""
    out = {}
    for key, fit in FIT.items():
        bbox, face, kind = fit["bbox"], fit["face"], fit["kind"]
        zones = {}
        for zone, (x0, x1, y0, y1) in ZONES_BOX[kind].items():
            zones[zone] = [_rect(x0, y0, x1, y1, bbox, face)]
        e2 = ELEC_SECOND[kind]
        zones["elec"] = zones["elec"] + [_rect(e2[0], e2[2], e2[1], e2[3],
                                               bbox, face)]
        out[key] = zones
    return out


def build_anchors():
    out = {}
    for key, fit in FIT.items():
        a = ANCHORS_BOX[fit["kind"]]
        out[key] = {z: _box_to_frac(p, fit["bbox"], fit["face"]) for z, p in a.items()}
    return out


def build_media():
    zones = build_zones()
    anchors = build_anchors()
    media = {}
    for key, path in PICTURES.items():
        if not os.path.exists(path):
            raise SystemExit(f"vehicle picture missing for {key}: {path}")
        with open(path, "rb") as f:
            raw = f.read()
        ext = os.path.splitext(path)[1].lower().lstrip(".")
        mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
        media[key] = {
            "src": f"data:{mime};base64," + base64.b64encode(raw).decode("ascii"),
            "credit": CREDIT[key],
            "depicts": DEPICTS[key],
            "bytes": len(raw),
            "bbox": FIT[key]["bbox"],
            "face": FIT[key]["face"],
            "zones": zones[key],
            "anchors": anchors[key],
        }
    return media


def main():
    m = build_media()
    total = sum(v["bytes"] for v in m.values())
    for k, v in m.items():
        print(f"{k:6s} {v['bytes']/1e3:6.0f} KB  {len(v['zones'])} zones  {v['depicts']}")
    print(f"total picture bytes {total/1e6:.2f} MB")
    with open(os.path.join(HERE, "vehicle_media.json"), "w", encoding="utf-8") as f:
        json.dump(m, f, separators=(",", ":"))
    print("wrote vehicle_media.json")


ANCHORS = build_anchors()

if __name__ == "__main__":
    main()
