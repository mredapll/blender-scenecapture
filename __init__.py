# -*- coding: utf-8 -*-
"""
Documentation:
"""
import bpy

from . blender_helper import LaunchQtApp, TopbarPLL, draw_pll_menu
from . scenecapture import LaunchScreenCapture, SceneCaptureUI

bl_info = {
    "name": "RFH",
    "category": "Object",
    "version": (0, 1, 0),
    "author": "Pixel Logic Link",
    "blender": (4, 0, 0),
}


classes = [
    LaunchQtApp,
    LaunchScreenCapture,
    TopbarPLL,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_editor_menus.append(draw_pll_menu)


def unregister():
    bpy.types.TOPBAR_MT_editor_menus.remove(draw_pll_menu)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


def main():
    register()


if __name__ == '__main__':
    main()
