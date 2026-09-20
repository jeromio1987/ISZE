import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, "qa_truck_catalogue.py")
s = io.open(p, encoding="utf-8").read()

before = s.count("window.truckZones.map(z => z.name") + \
         s.count("window.truckZones.forEach(z =>\n") + \
         s.count("window.truckZones[h[0]].name")

s = s.replace("window.truckZones.map(z => z.name.split(',')[0])",
              "window.truckZoneMeta().map(z => z.name.split(',')[0])")
s = s.replace("window.truckZones.forEach(z => perZone[z.name.split(',')[0]] = 0);",
              "window.truckZoneMeta().forEach(z => perZone[z.name.split(',')[0]] = 0);")
s = s.replace("perZone[window.truckZones[h[0]].name.split(',')[0]]++",
              "perZone[window.truckZoneMeta()[h[0]].name.split(',')[0]]++")

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("occurrences before:", before)
print("remaining truckZones name lookups:",
      s.count("truckZones.map(z => z.name"),
      s.count("truckZones.forEach(z =>"),
      s.count("truckZones[h[0]].name"))
print("truckZoneMeta uses:", s.count("truckZoneMeta()"))
