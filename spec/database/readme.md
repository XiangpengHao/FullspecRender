###### Illuminant
The `rbg` and `xyz` is computed directly for caching.

###### Reflectance
The `rgb` and `xyz` is computed under D65

###### Notes
When match a sRGB value to a spectrum, if the sRGB value is a reflectance, we assume it's computed under `D65`.

In both cases, the `XYZ` value should NOT be scaled, because we need that `Y` value later.
 
