###### Illuminant
The `rbg` and `xyz` is computed directly for caching.

###### Reflectance
The `rgb` and `xyz` is computed under D65

###### Notes
1. When match a sRGB value to a spectrum, if the sRGB value is a reflectance, we assume it's computed under `D65`.

2. In both cases, the `XYZ` value should NOT be scaled, because we need that `Y` value later.
 
3. We should really ignore the `type_max` property, it's bad defined.
 
