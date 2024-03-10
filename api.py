# -*- coding: utf-8 -*-
"""
Documentation:
"""
import os
import json
import time
import uuid
from typing import Dict
import bpy


def get_pwd():
    try:
        if hasattr(bpy.data, "filepath"):
            return os.path.dirname(bpy.data.filepath)
        return os.path.dirname(bpy.data.filepath)
    except:
        raise AssertionError("Save The File First.")


class Constants:
    Attributes = [
        "location",
        "rotation_euler",
        "scale",
    ]
    BackupDir = os.path.join(get_pwd(), "backups")
    BaseFileName = "snapshot"
    CollectAttr = "ppl_scene_data"


def get_collections():
    return sorted([c.name for c in bpy.data.collections], key=lambda x: x[0])


def get_cameras():
    return sorted([c.name for c in bpy.context.scene.objects
                   if c.type == "CAMERA"])


def get_scene_data(collection: str):
    collections = bpy.data.collections
    all_objects = collections[collection].all_objects
    # all_objects = bpy.data.objects

    scene_data = {}
    for obj in all_objects:
        unique_id = uuid.uuid4()

        _id = obj.get("uuid")

        if _id is None:
            obj["uuid"] = str(unique_id)
            _id = obj["uuid"]

        scene_data[_id] = {}
        scene_data[_id]["name"] = obj.name
        scene_data[_id]["type"] = obj.type
        if eval(obj.get("locked", "False")):
            continue

        attrs = {}
        for attr in Constants.Attributes:
            attrs[attr] = tuple(getattr(obj, attr))

        scene_data[_id]["attrs"] = {}
        scene_data[_id]["attrs"]["values"] = attrs

    return scene_data


def set_scene_data(data):
    if not data:
        return

    all_objects = bpy.data.objects

    for obj in all_objects:
        _id = obj.get("uuid")

        obj_data = data.get(_id)
        if not obj_data:
            continue

        if eval(obj.get("locked", "False")):
            continue

        attr_data = obj_data['attrs']
        for attr, values in attr_data["values"].items():
            if eval(obj.get("locked", "False")):
                continue

            if hasattr(obj, attr):
                try:
                    obj.__setattr__(attr, values)
                except:
                    print(
                        f"Can not set value of object: {obj_data['name']} attr: {attr} value: {values}")


def update_collect_data(collect_name: str, new_data: Dict):
    collect = bpy.data.collections.get(collect_name)

    if not collect:
        print("Not valid collection name: {}".format(collect_name))
        return

    collect_data_str = collect.get(Constants.CollectAttr)

    if not collect_data_str:
        collect[Constants.CollectAttr] = "{}"
        collect_data_str = "{}"

    collect_data: dict = json.loads(str(collect_data_str))

    new_data["time"] = time.strftime("%d/%m/%Y %H:%M")
    new_data["id"] = str(uuid.uuid4())
    collect_data[new_data["id"]] = new_data

    collect[Constants.CollectAttr] = json.dumps(collect_data)
    return new_data["id"]


def override_collect_data(collect_name: str, data: Dict):
    collect = bpy.data.collections.get(collect_name)

    if not collect:
        print("Not valid collection name: {}".format(collect_name))
        return

    collect_data_str = collect.get(Constants.CollectAttr)

    if not collect_data_str:
        collect[Constants.CollectAttr] = "{}"
        collect_data_str = "{}"

    collect_data: dict = json.loads(str(collect_data_str))

    collect_data[data["id"]] = data

    collect[Constants.CollectAttr] = json.dumps(collect_data)


def delete_collect_data(collect_name: str, data: Dict):
    collect = bpy.data.collections.get(collect_name)

    if not collect:
        print("Not valid collection name: {}".format(collect_name))
        return

    collect_data_str = collect.get(Constants.CollectAttr)

    if not collect_data_str:
        collect[Constants.CollectAttr] = "{}"
        collect_data_str = "{}"

    collect_data: dict = json.loads(str(collect_data_str))

    del collect_data[data["id"]]

    collect[Constants.CollectAttr] = json.dumps(collect_data)


def get_collect_data(collect_name: str) -> Dict:
    collect = bpy.data.collections.get(collect_name)

    if not collect:
        print("Not valid collection name: {}".format(collect_name))
        return {}

    collect_data_str = collect.get(Constants.CollectAttr)

    if not collect_data_str:
        collect[Constants.CollectAttr] = "{}"
        collect_data_str = "{}"

    return json.loads(str(collect_data_str))


def clear_all_collect_data(collect_name):
    collect = bpy.data.collections.get(collect_name)

    if not collect:
        print("Not valid collection name: {}".format(collect_name))
        return
    collect[Constants.CollectAttr] = "{}"



def set_all_collect_data(collect_name, data):
    collect = bpy.data.collections.get(collect_name)

    if not collect:
        print("Not valid collection name: {}".format(collect_name))
        return

    collect_data_str = collect.get(Constants.CollectAttr)

    if not collect_data_str:
        collect[Constants.CollectAttr] = "{}"

    collect[Constants.CollectAttr] = json.dumps(data)


def get_all_collect_data(collect_name) -> Dict:
    collect = bpy.data.collections.get(collect_name)

    if not collect:
        print("Not valid collection name: {}".format(collect_name))
        return {}

    collect_data_str = collect.get(Constants.CollectAttr)

    if not collect_data_str:
        collect[Constants.CollectAttr] = "{}"

    collect_data_str = collect.get(Constants.CollectAttr)
    return json.loads(str(collect_data_str))



def capture_viewport(context, snap_id, camera="PERSP"):
    file_path = os.path.join(Constants.BackupDir, "screenshot", f"snap_{snap_id}.png")
    sce = context.scene.name
    bpy.data.scenes[sce].render.filepath = file_path

    for window in bpy.data.window_managers[0].windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == "VIEW_3D":
                area.spaces[0].region_3d.view_perspective = camera

                with context.temp_override(window=window):
                    bpy.ops.render.opengl(write_still=True)
                break

    # bpy.context.scene.render.engine = "CYCLES"
    # bpy.ops.render.render(write_still=True)
    return file_path
