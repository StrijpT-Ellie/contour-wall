from contourwall import ContourWall

# Path: lib/wrappers/python-new/demo.py
# Compare this snippet from lib/wrappers/python/contourwall.py:
#     def solid_color(self, red: int, green: int, blue: int):
#         self.pixels[:] = [blue % 256, green % 256, red % 256]
#         self._command_1_solid_color(ctypes.byref(self._cw_core), red % 256, green % 256, blue % 256)
#         return self._command_0_show(ctypes.byref(self._cw_core))

cw = ContourWall(2_000_000)

cw.single_new_with_port(b"COM6")

cw.fill_solid(255, 0, 0)

# cw.pixels[:] = [0, 255, 0]
# cw.show()
