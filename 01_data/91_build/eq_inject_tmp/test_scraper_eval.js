const fs = require("fs");
const path =
  "C:/Users/jerom/Desktop/claude/ISZE/01_data/90_INBOX/_eq_hit_overnight_scraper_20260919.js";
const s = fs.readFileSync(path, "utf8");
// provide window stub
global.window = global;
try {
  eval(s);
  console.log("OK full", typeof window.__eqDoubtLookup, typeof window.__eqDoubtRun);
} catch (e) {
  console.log("ERR full", e.message);
}
const s2 = s.replace(/"scraper_v2_ok";\s*$/, "");
try {
  eval(s2);
  console.log("OK stripped", typeof window.__eqDoubtLookup);
} catch (e) {
  console.log("ERR stripped", e.message);
}
