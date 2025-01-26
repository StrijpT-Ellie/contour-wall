import { sleep } from "https://deno.land/x/sleep/mod.ts"
import { create, all } from 'npm:mathjs';

export class ContourWall {
  private lib
  private cw_core_ptr: null|Deno.UnsafePointer;
  private baudrate: number; 
  private math = create(all);
  pixels = this.math.zeros(40, 60, 3)
  pushed_frames: number = 0;

  constructor(baudrate = 2_000_000) {
    
    let libSuffix = "";
    switch (Deno.build.os) {
      case "windows":
        libSuffix = "dll";
        break;
      case "darwin":
        libSuffix = "dylib";
        break;
      case "linux":
        libSuffix = "so";
        break;
      default:
        throw new Error(`'${Deno.build.os}' is not a supported operating system`)
    }

    const contourwall_path = `contourwall_core.${libSuffix}`;
    this.lib = Deno.dlopen(
      contourwall_path,
      {
        "new": {parameters: ["u32"], result: "pointer"},
        "new_with_ports": { parameters: ["pointer", "pointer", "pointer", "pointer", "pointer", "pointer", "u32"], result: "pointer" },
        "single_new_with_port": { parameters: ["pointer", "u32"], result: "pointer" },
        "show": { parameters: ["pointer"], result: "void" },
        "update_all": { parameters: ["pointer", "pointer", "bool"], result: "void"},
        "solid_color": { parameters: ["pointer", "u8", "u8", "u8"], result: "void"},
        "drop": { parameters: ["pointer"], result: "void"},
      } as const,
    );
    this.cw_core_ptr = null;
    this.baudrate = baudrate
  }

  new(){
    // Create a new instance of ContourWallCore, using the default baudrate of 2_000_000.

    // This function is used to create a new instance of ContourWallCore when the COM ports are unknown. 
    // The function will automaticaly search for available comports, if no COM ports are found a error will be returned.
    
    this.lib.symbols.new(this.baudrate)
  }

  new_with_ports(port1: string, port2: string, port3: string, port4: string, port5: string, port6: string) {
    const ptr: Deno.UnsafePointer = this.lib.symbols.new_with_ports(
      // Create a new instance of ContourWallCore, using the default baudrate of 2_000_000 and defining the COM ports for 6 tiles.
      // This function is used to create a new instance of ContourWallCore when the COM ports are known.

          this.string_to_ptr(port1), 
          this.string_to_ptr(port2), 
          this.string_to_ptr(port3), 
          this.string_to_ptr(port4), 
          this.string_to_ptr(port5), 
          this.string_to_ptr(port6), 
          this.baudrate) as Deno.UnsafePointer;
    this.cw_core_ptr = ptr;
  }
  

  single_new_with_port(port: string) {
    //This function is used to create a new instance of ContourWallCore when a single COM port is known.

    this.cw_core_ptr = this.lib.symbols.single_new_with_port(
      this.string_to_ptr(port),
      this.baudrate
    ) as Deno.UnsafePointer;
  }


  show(sleep_ms: number) { 
  
    // Show the current state of the pixel array on the ContourWall.

    // This function is used to show the current state of the pixel array on the ContourWall. 
    // The function will push the current state of the pixel array to the ContourWall and will show the pushed frame on the ContourWall.

    // const buffer = this.pixels.buffer;  

    const math = create(all);
    const m = math.zeros([40, 60, 3]);
    let arr = m.valueOf();
    console.log(arr);
    const flattened = new Uint8Array(arr.flat(2));

    const framebuffer_ptr = Deno.UnsafePointer.of(flattened.buffer)

    this.lib.symbols.update_all(this.cw_core_ptr as Deno.PointerObject, framebuffer_ptr, false) 
    this.lib.symbols.show(this.cw_core_ptr as Deno.PointerObject)
    this.pushed_frames += 1

    sleep(sleep_ms/1000)
  }


  drop() {
    this.lib.symbols.drop(this.cw_core_ptr as Deno.PointerObject);
  }

  private string_to_ptr(str: string) {
    const encoder = new TextEncoder();

    // Encodes the input string and appends a null terminator ("\0"),
    // which is required for many C-style string manipulations.
    const stringBuffer = encoder.encode(str + "\0");
        // Creates a new Uint8Array from the encoded string buffer.

    const buf = new Uint8Array(stringBuffer);
    // Converts the Uint8Array into a raw pointer using Deno's UnsafePointer API.
    const ptr = Deno.UnsafePointer.of(buf);
    return ptr
  }
}
