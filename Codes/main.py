# Import
# -----------------------------------------------------------------------------
from __future__ import annotations
import datetime as dt
import os
import pathlib
#
from models import MIPModel
from classes import RunnersAndTW, Runner, TimeWindow
from rw import RW
# -----------------------------------------------------------------------------


# Files & Instance values
# -----------------------------------------------------------------------------
# Base folder
base_folder: pathlib.Path = pathlib.Path(
    rf'{os.path.abspath(os.path.dirname(__file__))}'
).parents[0]
# Instance
instance_file: pathlib.Path = base_folder / 'Input' / 'instance.csv'
instance_date_tws: list[TimeWindow] = [
    TimeWindow(
        dt.datetime(2022,  8, 15, 19,  0,  0, ), 
        dt.datetime(2022,  8, 16,  0,  0,  0, )
    ), 
    TimeWindow(
        dt.datetime(2022,  8, 16,  0,  0,  0, ), 
        dt.datetime(2022,  8, 17,  0,  0,  0, )
    ), 
    TimeWindow(
        dt.datetime(2022,  8, 17,  0,  0,  0, ), 
        dt.datetime(2022,  8, 18,  0,  0,  0, )
    ), 
]
# Solution
solution_file: pathlib.Path = base_folder / 'Output' / 'soluiton.csv'
solution_assignment: dict[Runner, tuple[int, TimeWindow]] = {}
del base_folder
# -----------------------------------------------------------------------------


# Settings
# -----------------------------------------------------------------------------
# Maximum nummber of parallel sessions
max_parallel_sessions: int = 2
# Can the stop time be outside a time window (to)?
can_stop_time_be_outside_tw_to: bool = True
# Calculation time limit (seconds)
time_limit_s: int = 600
# -----------------------------------------------------------------------------


# Main
# -----------------------------------------------------------------------------
instance: RunnersAndTW = RW.read_instance(instance_file, instance_date_tws)
del instance_file, instance_date_tws

model: MIPModel = MIPModel(instance)
solution_assignment = model.solve_feasibility_and_min_s1_interval(
    max_parallel_sessions, can_stop_time_be_outside_tw_to, time_limit_s
)
del model

RW.write_solution(
    solution_file, instance.tw, max_parallel_sessions, solution_assignment
)
del instance, max_parallel_sessions
del solution_file, solution_assignment
# -----------------------------------------------------------------------------
