---
title: Module Hardware V2
---

### Overview
If I were to make new PCB, I would try to use.STL files from the Digikey design, so that before ordering the PCB, I know how my component aligns properly with the footprint. The footprint for the inductor was quite different than the actual size of the inductor I used. I would start my PCB design earlier, as most of my PCB problems were because I started it a bit late. 

I would also try to use Cadence next time with its auto-tracing feature, or trace components better on KiCad. My traces were too small, and this could have affected my motor driver. The power was not coming to my motor driver, even if I made 3 PCBs.

I would try to make my LEDs and resistors a bit bigger, allowing me to solder more easily, and since there are bigger surface-mount components available. I will try to research more on different sizes of components, allowing me to have a better design. 

I would also choose bigger wheels and bigger motors with high torque and more RPM. Also, I would try to use I2C based motor drivers instead of SPI for my motors since my motors were working fine without daisy chain. But when I was getting commands for motor movements, my motors would move endlessly and not accept other commands.

