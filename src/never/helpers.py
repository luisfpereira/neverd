
import json
import tkinter as tk

from never.objects import GeometricCanvas
from never.objects import TYPE2OBJ


def load_from_json(filename, holder=None):

    with open(filename, 'r') as file:
        data = json.load(file)

    return load_from_dict(data, holder=holder)


def load_from_dict(data, holder=None):
    if holder is None:
        holder = tk.Tk()

    canvas = GeometricCanvas(holder)
    canvas.pack(fill='both', expand=True)

    update_canvas_from_dict(canvas, data)

    return canvas


def update_canvas_from_dict(canvas, data):

    metadata = data.get('metadata', {})
    width = metadata.get('width', 800)
    height = metadata.get('height', 600)

    canvas.width = width
    canvas.height = height

    # calibrate
    calibration_info = data.get('calibration', None)
    if calibration_info is not None:
        canvas.calibrate(**calibration_info)
    else:
        return canvas

    # add image
    image_info = data.get('image', None)
    if image_info is not None:
        canvas.add_image(**image_info)

    # add objects
    objects_info = data.get('objects', None)
    if objects_info is not None:
        _add_objects_from_dict(canvas, objects_info)


def _add_objects_from_dict(canvas, objects_info):
    for obj_type in ['Line', 'Slider', 'Point']:  # because order matters
        _add_objects_by_type(canvas, objects_info, obj_type)


def _add_objects_by_type(canvas, objects_info, obj_type):

    for object_info in objects_info:
        if object_info.get('type') != obj_type:
            continue

        object_info, show = _transform_obj_dict(canvas, object_info)
        obj = TYPE2OBJ[obj_type](**object_info)
        canvas.add_object(obj)


def _transform_obj_dict(canvas, obj_info):
    TYPE2TRANFORM = {'Slider': _transform_slider_dict}

    obj_type = obj_info.get('type')
    del obj_info['type']

    show = obj_info.get('show', None)
    if show is not None:
        show = True
        del obj_info['show']

    # further transform
    obj_info = TYPE2TRANFORM.get(obj_type, lambda canvas, obj_info: obj_info)(canvas, obj_info)

    return obj_info, show


def _transform_slider_dict(canvas, obj_info):
    del obj_info['coords']

    anchor_name = obj_info.get('anchor')
    obj_info['anchor'] = canvas.get_by_name(anchor_name)
    return obj_info
