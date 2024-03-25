# -*- coding: utf-8 -*-
"""
Documentation:
"""
import sys
import os
import json
import bpy

root_path = os.path.dirname(__file__)

sys.path.insert(0, root_path)

import api

data = {}

if "--" in sys.argv:
    custom_args = sys.argv[sys.argv.index("--") + 1:]
    data = json.loads(custom_args[0])

    api.set_scene_data(data.get("data", {}))

    if data.get("res_w"):
        bpy.context.scene.render.resolution_x = data.get("res_w")

    if data.get("res_h"):
        bpy.context.scene.render.resolution_y = data.get("res_h")

    bpy.context.scene.camera = bpy.data.objects.get(data.get("camera"))
