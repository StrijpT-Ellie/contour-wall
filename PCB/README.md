# ELLIE Panel PCB

> **DO NOT RELOCATED THIS PAGE TO A DIFFERENT URL, A QR CODE ON THE PCB POINTS TO THIS**

All files to order more PCB's can be found in this directory. Ordered and assembled from JLCPCB with LCSC as part supplier.

# Tech spec & info

- **LED type:** WS2812B ([datasheet](https://cdn-shop.adafruit.com/datasheets/WS2812B.pdf))
  - **Total current:** 60mA * 25 = 1500mA. However, in reality, one full-white WS2812B LED only uses 36mA. Therefore one board uses about 900mA.
- **Dimensions (WxH):** 220mm x 220mm (30mm space between the PCB's)
- **Mounting hole grid size:** 125mm
- **Mounting hole size:** 3mm
- **Decoupling capacitor**: 100nF
- **Big Capacitor:** 1000uF capacitor pin holes (Not placed be default, solder by hand if needed.)
- **Coppper Thickness:** 1oz Copper layer
- **Trace Width:** 5v trace has 7.5mm width. Can handle max of 10A
- **Assembled PCB Weigth:** ~180 grams (Including all SMD components)

# Dimensions

> NOTE: Dimensions image is not to scale

![dimensions](img/pcb_dimensions.png)

# Electrical Schematic

![schematic](img/Schematic_ELLIE_DISPLAY_PANEL.png)

# PCB

Front of PCB                | Back of PCB
--------------------------- | -------------------------
![pcb_front](img/front.png) | ![pcb_back](img/back.png)
