### Model checklist:

* All emissions should use illuminant spectrum

* turn-off every emission and test if the result is empty

* No color ramp

* No Hue saturation value

* Mix between color and Texture not work

* Nodes to take care:

    Principled BSDF

    Mix
    
* Textures must be none-color data

* Clean world texture is necessary

* Be careful when dealing with random



### Render pass
For each scene we divide the render passes into three types:
1. Render result, render for each geometry, each light setting, each view point, 20 renders
2. Geometry, render for each geometry, ignore light settings: Diffuse, Glossy, Transmission, Ambient Occlusion, 20 renders
3. Geometry, render for each geometry, ignore light settings: Depth, Normal, 1 renders

