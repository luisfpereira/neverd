import json
import tkinter as tk

from tk_2d_dialog.objects import Canvas
from tk_2d_dialog.objects import CalibrationPoint
from tk_2d_dialog.objects import Calibration
from tk_2d_dialog.objects import Point
from tk_2d_dialog.objects import Line


def main(filename):

    holder = tk.Tk()

    # create canvas
    width = 800
    height = 400

    cal_pt1 = CalibrationPoint(canvas=(0, 0), real=(-20., 10))
    cal_pt2 = CalibrationPoint(canvas=(800, 400), real=(20, -10))
    calibration = Calibration(cal_pt1, cal_pt2)

    canvas = Canvas(holder, calibration, width=width, height=height)
    canvas.pack()

    # objects
    point = Point('point1', (0.0, 0.0), show=True)
    canvas.add_object(point)

    line = Line('line1', ((-10., -5), (0., -5), (10., 5.)), width=1)
    canvas.add_object(line)

    tk.mainloop()
