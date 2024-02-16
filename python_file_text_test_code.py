#!/usr/bin/python3
import os

def freecad_script_execution(freecad_3d_cube_script_file_name):
  return os.system(f"/home/creditizens/freecad_lm-studio/freecadus/AppRun freecadcmd /home/creditizens/freecad_lm-studio/freecadus/{freecad_3d_cube_script_file_name}")


freecad_script_execution("testcube_and_cessna_part.py")
