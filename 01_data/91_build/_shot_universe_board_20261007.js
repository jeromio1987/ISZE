const fs = require("fs");
const path = require("path");
const {execFileSync} = require("child_process");
const html = process.argv[2];
const hero = process.argv[3];
const full = process.argv[4];
const chrome = process.argv[5];
const uri = "file:///" + html.replace(/\\/g, "/");
function shot(out, w, h) {
  const args = [
    "--headless=new",
    "--disable-gpu",
    "--hide-scrollbars",
    `--window-size=${w},${h}`,
    `--screenshot=${out}`,
    uri
  ];
  execFileSync(chrome, args, {stdio:"inherit"});
}
shot(hero, 1400, 900);
shot(full, 1400, 2200);
console.log("wrote", hero, full);
