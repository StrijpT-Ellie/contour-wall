// Implement sleep_ms field parameter for show function
// Find numpy alternative for the pixels field. You want a high-level 3D matrix, not a low-level byte array
import time 

class ContourWall {
  private lib
  private cw_core_ptr: null|Deno.UnsafePointer;
  private baudrate: number; 
  pixels = new Uint8Array(7200); 
  pushed_frames: number = 0;

  constructor(baudrate = 2000000) {
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

    const contourwall_path = `./contourwall_core.${libSuffix}`;

    this.lib = Deno.dlopen(
      contourwall_path,
      {
        "new": {parameters: ["u32"], result: "pointer"},
        "new_with_ports": { parameters: ["pointer", "pointer", "pointer", "pointer", "pointer", "pointer", "u32"], result: "pointer" },
        "single_new_with_port": { parameters: ["pointer", "u32"], result: "pointer" },
        "show": { parameters: ["pointer"], result: "void" },
        "update_all": { parameters: ["pointer", "pointer", "bool"], result: "void"},
        "solid_color": { parameters: ["pointer", "u8", "u8", "u8"], result: "void"},
        "drop": { parameters: ["pointer"], result: "void"}
      } as const,
    );
    this.cw_core_ptr = null;
    this.baudrate = baudrate
  }

  new(){
    this.lib.symbols.new(this.baudrate)
  }

  new_with_ports(port1: string, port2: string, port3: string, port4: string, port5: string, port6: string) {
    const ptr: Deno.UnsafePointer = this.lib.symbols.new_with_ports(
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
    this.cw_core_ptr = this.lib.symbols.single_new_with_port(
      this.string_to_ptr(port),
      this.baudrate
    ) as Deno.UnsafePointer;
  }


  show( sleep_ms:number=0,) {
    const buffer = this.pixels.buffer;  
    const framebuffer_ptr = Deno.UnsafePointer.of(buffer);

    this.lib.symbols.update_all(this.cw_core_ptr, framebuffer_ptr, false)
    this.lib.symbols.show(this.cw_core_ptr)
    this.pushed_frames += 1
    time.sleep(sleep_ms/1000)
  }



  drop() {
    this.lib.symbols.drop(this.cw_core_ptr);
  }

  private string_to_ptr(str: string) {
    const encoder = new TextEncoder();
    const stringBuffer = encoder.encode(str + "\0"); // Add null terminator

    const buf = new Uint8Array(stringBuffer);

    const ptr = Deno.UnsafePointer.of(buf);
    return ptr
  }
}
