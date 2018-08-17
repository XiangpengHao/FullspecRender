const spectrum = require("./spectrum.json");
const fs = require("fs");
const renamed = spectrum.map(item => {
  return {
    name: item.name,
    type: item.type,
    start_nm: item.start_nm,
    end_nm: item.end_nm,
    resolution: item.resolution,
    data: item.data,
    rgb: item.rgb_d65,
    xyz: item.xyz_d65
  };
});
fs.writeFile("./spectrum.json", JSON.stringify(renamed), err => {
  console.log("saved!");
});
