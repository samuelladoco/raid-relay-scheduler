# Import
# -----------------------------------------------------------------------------
from __future__ import annotations
import datetime as dt
from typing import ClassVar
# -----------------------------------------------------------------------------


# Classes
# -----------------------------------------------------------------------------
# ----------------------------------------------------------------------
class ParamSet:
    """パラメーター値の集まり"""

    # 各走者のEST(走り自体)に加算されるバッファー時間
    # （レイド受け + 前説 + 後説 + レイド渡し）
    BUFFER_TIME_ADDED_TO_EST_RUN: ClassVar[dt.timedelta] = dt.timedelta(
        minutes=(1 + 1 + 1 + 1)
    )
    # 各走者のEST(全体)の時間の最小単位
    EST_ALL_MINIMUM_UNIT: ClassVar[dt.timedelta] = dt.timedelta(
        minutes=5
    )
    # 各走者の終了時刻が時間枠の外にでてもよい場合
    # (can_stop_time_be_outside_tw_to == True)に、
    # 開始時刻を時間枠の右端から最低限どれだけ離すか
    # (ESTがこの値より小さい場合は、この値は適用されず、終了時刻 <= 時間帯の右端 となる)
    MINIMUM_INTERVAL_FROM_TW_TO: ClassVar[dt.timedelta] = dt.timedelta(
        minutes=60
    )
# ----------------------------------------------------------------------
# -----------------------------------------------------------------------------
