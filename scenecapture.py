# -*- coding: utf-8 -*-
"""
Documentation:
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Union

from Qt import QtCompat, QtCore, QtGui, QtWidgets

import bpy

from .blender_helper import LaunchQtApp
from . import api
from .ui.icons_rc import *

__version__ = "0.0.1"


def get_pwd():
    try:
        if hasattr(bpy.data, "filepath"):
            return os.path.dirname(bpy.data.filepath)
        return os.path.dirname(bpy.data.filepath)
    except:
        raise AssertionError("Save The File First.")


class Constants:
    WindowTitle = "RFH Scene Capture v" + __version__
    Attributes = [
        "location",
        "rotation_euler",
        "scale",
    ]
    BackupDir = os.path.join(get_pwd(), "backups")
    BaseFileName = "snapshot",
    CaptureId = "1"


class LaunchScreenCapture(LaunchQtApp):
    bl_idname = "wm.pll_screencapture"
    bl_label = "Screen Capture..."
    _tool_name = "screencapture"

    def execute(self, contex):
        self._window = SceneCaptureUI(contex=contex)

        origin_flags = self._window.windowFlags()
        on_top_flags = origin_flags | QtCore.Qt.WindowStaysOnTopHint
        self._window.setWindowFlags(on_top_flags)
        self._window.show()

        return {'FINISHED'}


def on_comment_changed(timer):
    timer.start(1000)


class SceneCaptureUI(QtWidgets.QDialog):
    uiDir = Path(os.path.dirname(__file__)).joinpath('ui')

    def __init__(self, contex=None, parent=None):
        super(SceneCaptureUI, self).__init__(parent=parent)

        self.current_collect = None
        self.current_camera = None

        self.context = contex
        self.init_ui()
        self.connect_signals()
        self.refresh()

    def init_ui(self):
        self.ui = QtCompat.loadUi(self.uiDir.joinpath('scenecapture.ui').as_posix(), self)
        with open(self.uiDir.joinpath('stylesheet.qss'), "r") as fh:
            self.setStyleSheet(fh.read())

        self.setWindowTitle(Constants.WindowTitle)
        self.setWindowFlags(QtCore.Qt.Tool)

        self.setProperty("saveWindowPref", True)

        self.ui.capture_toolButton.setIcon(QtGui.QIcon(":/icons/capture.png"))
        self.ui.xformCopy_pushButton.setIcon(QtGui.QIcon(':/icons/copy.png'))
        self.ui.xformPaste_pushButton.setIcon(QtGui.QIcon(':/icons/paste.png'))
        self.ui.xformSwap_pushButton.setIcon(QtGui.QIcon(':/icons/swap.png'))
        self.ui.import_pushButton.setIcon(QtGui.QIcon(':/icons/import.png'))
        self.ui.export_pushButton.setIcon(QtGui.QIcon(':/icons/export.png'))
        self.ui.delData_pushButton.setIcon(QtGui.QIcon(':/icons/delete.png'))

        self.ui.filetype_comboBox.hide()
        self.ui.setEditor_pushButton.hide()
        self.ui.tabWidget.removeTab(2)

    def connect_signals(self):

        # Connect signals & slots
        self.ui.capture_toolButton.clicked.connect(self.on_capture)
        # self.ui.btn_renderNone.released.connect(partial(self.on_handle_render_state, 0))
        # self.ui.btn_renderAll.released.connect(partial(self.on_handle_render_state, 1))
        # self.ui.btn_renderInvert.released.connect(partial(self.on_handle_render_state, 2))

        # self.ui.captureName_lineEdit.returnPressed.connect()
        # self.ui.xformCopy_pushButton.clicked.connect()
        # self.ui.xformPaste_pushButton.clicked.connect()
        # self.ui.xformSwap_pushButton.clicked.connect()

        self.ui.import_pushButton.clicked.connect(self.on_import_json)
        self.ui.export_pushButton.clicked.connect(self.on_export_json)
        self.ui.delData_pushButton.clicked.connect(self.on_delete_data)

        self.ui.set_comboBox.currentIndexChanged.connect(self.on_collect_cb_changed)

    def refresh(self):

        # update combobox
        self.ui.set_comboBox.addItems(api.get_collections())
        self.ui.snapCam_comboBox.addItems(api.get_cameras())

        self.on_collect_cb_changed()
        self.on_camera_cb_changed()

        # Delete existing items
        layout = self.ui.captures_verticalLayout
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i).widget()
            if item:
                item.deleteLater()

        for capture_id, capture_data in api.get_collect_data(self.current_collect).items():
            self.add_snapshot(capture_data)

    def on_capture(self):
        data = {
            "data": api.get_scene_data(self.current_collect),
            "name": self.ui.captureName_lineEdit.text(),
        }

        if not data["name"]:
            msg = QtWidgets.QMessageBox.warning(
                self,
                "Missing Info!",
                "You should set the name of the snapshot!"
            )
            return

        data_id = api.update_collect_data(self.current_collect, data)
        thumbnail = api.capture_viewport(self.context, data_id)
        data["thumbnail"] = thumbnail
        data["id"] = data_id

        api.override_collect_data(self.current_collect, data)
        self.add_snapshot(data)

    def add_snapshot(self, data: Dict):
        ui_item = QtCompat.loadUi(self.uiDir.joinpath('capture_item.ui').as_posix())

        ui_item.setProperty(Constants.CaptureId, data)

        ui_item.recap_toolButton.setIcon(QtGui.QIcon(':/icons/capture.png'))
        ui_item.delete_toolButton.setIcon(QtGui.QIcon(':/icons/delete.png'))
        ui_item.render_toolButton.setIcon(QtGui.QIcon(':/icons/render.png'))

        thumb = QtGui.QPixmap(self.uiDir.joinpath('placeholder_thumb.png').as_posix())
        if data.get("thumbnail"):
            thumb = QtGui.QPixmap(data.get("thumbnail"))

        ui_item.name_lineEdit.setText(data.get("name", ""))
        ui_item.capture_toolButton.setIcon(thumb)
        ui_item.capture_toolButton.setText(data.get("time", ""))
        ui_item.mTe_comments.setPlainText(data.get("comment", ""))
        ui_item.mLb_colorFlag.setStyleSheet(data.get("color", ""))

        self.ui.captures_verticalLayout.addWidget(ui_item)

        # Signals
        ui_item.capture_toolButton.clicked.connect(lambda: self.on_apply_snapshot(ui_item))

        # Timer for detecting when editing is finished
        ui_item.editTimer = QtCore.QTimer(self)
        ui_item.editTimer.setSingleShot(True)

        ui_item.mTe_comments.textChanged.connect(lambda: on_comment_changed(ui_item.editTimer))
        ui_item.editTimer.timeout.connect(
            lambda: self.on_comment_finished(ui_item.mTe_comments, ui_item))

        ui_item.mBtn_N.clicked.connect(lambda: self.on_color_triggered(ui_item.mBtn_N, ui_item))
        ui_item.mBtn_R.clicked.connect(lambda: self.on_color_triggered(ui_item.mBtn_R, ui_item))
        ui_item.mBtn_O.clicked.connect(lambda: self.on_color_triggered(ui_item.mBtn_O, ui_item))
        ui_item.mBtn_G.clicked.connect(lambda: self.on_color_triggered(ui_item.mBtn_G, ui_item))
        ui_item.mBtn_B.clicked.connect(lambda: self.on_color_triggered(ui_item.mBtn_B, ui_item))

        ui_item.delete_toolButton.clicked.connect(lambda: self.on_delete_widget_item(ui_item))
        ui_item.recap_toolButton.clicked.connect(lambda: self.on_recapture(ui_item))

    def on_collect_cb_changed(self):
        self.current_collect = self.ui.set_comboBox.currentText()

    def on_camera_cb_changed(self):
        self.current_camera = self.ui.snapCam_comboBox.currentText()

    def on_import_json(self):
        file_filter = "JSON Files (*.json)"
        filepath = QtWidgets.QFileDialog.getOpenFileName(
            self, "Import JSON", Constants.BackupDir, file_filter)

        if not filepath:
            return

        with open(filepath[0], "r") as f:
            api.set_all_collect_data(self.current_collect, json.load(f))
        self.refresh()

    def on_export_json(self):
        data = api.get_all_collect_data(self.current_collect)

        file_filter = "JSON Files (*.json)"
        filepath = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export JSON", Constants.BackupDir, file_filter)
        if not filepath:
            return
        with open(filepath[0], "w") as f:
            json.dump(data, f)

    def on_delete_data(self):
        api.clear_all_collect_data(self.current_collect)
        self.refresh()

    def on_apply_snapshot(self, ui_item):
        data = ui_item.property(Constants.CaptureId).get('data', {})
        api.set_scene_data(data)

    def on_color_triggered(self, btn, ui_item):
        stylesheet = btn.styleSheet()
        ui_item.mLb_colorFlag.setStyleSheet(stylesheet)

        data = ui_item.property(Constants.CaptureId)
        data["color"] = stylesheet

        ui_item.setProperty(Constants.CaptureId, data)

        api.override_collect_data(self.current_collect, data)

    def on_comment_finished(self, textedit, ui_item):

        data = ui_item.property(Constants.CaptureId)
        data["comment"] = textedit.toPlainText()

        ui_item.setProperty(Constants.CaptureId, data)

        api.override_collect_data(self.current_collect, data)

    def on_delete_widget_item(self, ui_item):
        data = ui_item.property(Constants.CaptureId)
        api.delete_collect_data(self.current_collect, data)
        ui_item.deleteLater()

    def on_recapture(self, ui_item):

        data = ui_item.property(Constants.CaptureId)
        thumbnail = api.capture_viewport(self.context, data["id"])
        data["thumbnail"] = thumbnail
        api.override_collect_data(self.current_collect, data)

        ui_item.capture_toolButton.setIcon(QtGui.QPixmap(thumbnail))
