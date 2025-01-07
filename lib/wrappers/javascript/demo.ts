import { ContourWall } from "./contourwall.ts"; 

  const cw = new ContourWall();

  // Initialize with multiple ports
  cw.new_with_ports(
    "/dev/cu.usbmodem564D0089331",
    "/dev/cu.usbmodem578E0070891",
    "/dev/cu.usbmodem578E0073621",
    "/dev/cu.usbmodem578E0073631",
    "/dev/cu.usbmodem578E0070441",
    "/dev/cu.usbmodem578E0073651"
  );

  cw.pixels.set([255, 255, 255]); // Set all pixels to white
  cw.show(100); 

