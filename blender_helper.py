# -*- coding: utf-8 -*-
"""
Documentation:
"""

import os
import sys
import platform
import time
import traceback
import collections

from Qt import QtCompat, QtCore, QtGui, QtWidgets

import bpy


class GlobalClass:

    app = None
    main_thread_callbacks = collections.deque()
    is_windows = platform.system().lower() == "windows"
    menuname = "RFH"

    menu = [
        {
            "name": "wm.pll_screencapture",
            "label": "Screen Capture..."
        }
    ]


def _process_app_events():
    timer_interval = 0.01 if platform.system() == "Windows" else 0.1
    while GlobalClass.main_thread_callbacks:
        main_thread_item = GlobalClass.main_thread_callbacks.popleft()
        main_thread_item.execute()
        if main_thread_item.exception is not MainThreadItem.not_set:
            _clc, val, tb = main_thread_item.exception
            msg = str(val)
            detail = "\n".join(traceback.format_exception(_clc, val, tb))
            dialog = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Warning,
                "Error",
                msg)
            dialog.setMinimumWidth(500)
            dialog.setDetailedText(detail)
            dialog.exec_()

        app = GlobalClass.app
        if app._instance:
            app.processEvents()
            return timer_interval
    return timer_interval


def draw_pll_menu(self, context):
    self.layout.menu(TopbarPLL.bl_idname)


class BlenderApplication(QtWidgets.QApplication):
    _instance = None
    _app = None
    blender_windows = {}

    def __init__(self, *args, **kwargs):
        super(BlenderApplication, self).__init__(*args, **kwargs)
        self.setQuitOnLastWindowClosed(False)

        self.lastWindowClosed.connect(self.__class__.reset)

    @classmethod
    def get_app(cls):
        if cls._app is None:
            cls._app = QtWidgets.QApplication.instance()
            if not cls._app:
                cls._app = QtWidgets.QApplication(sys.argv)
        return cls._app

    @classmethod
    def reset(cls):
        cls._instance = None

    @classmethod
    def store_window(cls, identifier, window):
        current_window = cls.get_window(identifier)
        cls.blender_windows[identifier] = window
        if current_window:
            current_window.close()

    @classmethod
    def get_window(cls, identifier):
        return cls.blender_windows.get(identifier)


class MainThreadItem:
    not_set = object()
    sleep_time = 0.1

    def __init__(self, callback, *args, **kwargs):
        self.done = False
        self.exception = self.not_set
        self.result = self.not_set
        self.callback = callback
        self.args = args
        self.kwargs = kwargs

    def execute(self):
        if self.done:
            print("- item is already processed")
            return

        callback = self.callback
        args = self.args
        kwargs = self.kwargs

        try:
            result = callback(*args, **kwargs)
            self.result = result

        except Exception:
            self.exception = sys.exc_info()

        finally:
            self.done = True

    def wait(self):
        while not self.done:
            print(self.done)
            time.sleep(self.sleep_time)

        if self.exception is self.not_set:
            return self.result
        raise self.exception


class LaunchQtApp(bpy.types.Operator):
    bl_idname = "wm.pllqt"
    bl_label = "LaunchQtApp"
    _app = None
    _window = None

    def __init__(self):
        if self.bl_idname is None:
            raise NotImplementedError("Attribute `bl_idname` must be set!")

        self._app = BlenderApplication.get_app()
        GlobalClass.app = self._app

        if not bpy.app.timers.is_registered(_process_app_events):
            bpy.app.timers.register(
                _process_app_events,
                persistent=True
            )

    def execute(self, context):
        return {'FINISHED'}

    def before_window_show(self):
        pass


class TopbarPLL(bpy.types.Menu):
    bl_idname = "TopbarPLL"
    bl_label = GlobalClass.menuname

    def draw(self, context):
        layout = self.layout

        layout.separator()

        for item in GlobalClass.menu:
            layout.operator(item["name"], text=item["label"])
