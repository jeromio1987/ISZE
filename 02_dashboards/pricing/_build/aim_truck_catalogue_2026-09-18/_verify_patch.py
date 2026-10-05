import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
s = io.open(os.path.join(HERE, "build_truck_page.py"), encoding="utf-8").read()

for t in ["__VEHICLE_LAYER__", "__MEDIA__", 'id="media"', "MEDIA_JSON",
          "var MEDIA", "window.truckPhoto", "window.truckZoom",
          "window.truckFit", "switchVehicle", "truckCam",
          "import os", "temperature", "__GEOM__", "vehicle_geometry"]:
    print(t.ljust(24), s.count(t))

print()
print("still references old engine:",
      any(k in s for k in ("drawFaces", "extrude(", "projectZ(", "CAM.az")))
