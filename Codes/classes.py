# Import
# -----------------------------------------------------------------------------
from __future__ import annotations
import dataclasses
import datetime as dt
import enum
#
from params import ParamSet
# -----------------------------------------------------------------------------


# Classes
# -----------------------------------------------------------------------------
# ----------------------------------------------------------------------
@dataclasses.dataclass(frozen=True, )
class RunnersAndTW:
    """イベントにおける、走者の集まりと開始・終了日時"""

    runners: list[Runner] = dataclasses.field(compare=False, )
    tw: TimeWindow = dataclasses.field(compare=False, )

    def __repr__(self) -> str:
        return f'#runners={len(self.runners)}, tw={self.tw}'
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
@dataclasses.dataclass(frozen=True, order=True, )
class Runner:
    """走者(名前, EST(走り単体, 全体), 参加可能時間枠など)"""

    id: int
    name: str = dataclasses.field(compare=False, )
    game: str = dataclasses.field(compare=False, )
    category: str = dataclasses.field(compare=False, ) 
    est_run: dt.timedelta = dataclasses.field(compare=False, )
    est_all: dt.timedelta = dataclasses.field(init=False, compare=False, )
    __genre_str: dataclasses.InitVar[str]
    genre: Genre = dataclasses.field(init=False, compare=False, )
    tws: list[TimeWindow] = dataclasses.field(compare=False, )
    url: str = dataclasses.field(compare=False, )
    ad: str = dataclasses.field(compare=False, )
    note: str = dataclasses.field(compare=False, )

    def __post_init__(self, __genre_str: str) -> None:
        # 前後の時間の加算
        td: dt.timedelta = (
            self.est_run + ParamSet.BUFFER_TIME_ADDED_TO_EST_RUN
        )
        # 最小時間単位で切り上げ
        if td % ParamSet.EST_ALL_MINIMUM_UNIT > dt.timedelta():
            td += (
                ParamSet.EST_ALL_MINIMUM_UNIT 
                - td % ParamSet.EST_ALL_MINIMUM_UNIT
            )
        object.__setattr__(self, 'est_all', td)
        #
        for g in Genre:
            if g.value == __genre_str:
                object.__setattr__(self, 'genre', g)
                break
        else:
            raise ValueError(f'{__genre_str} に対応する列挙帯が未定義です')

    def __repr__(self) -> str:
        return (
            f'{self.id:03d}: {self.name}'
        )
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
@dataclasses.dataclass(frozen=True, order=True, )
class TimeWindow:
    """時間枠（From, To）"""

    fr: dt.datetime
    to: dt.datetime

    def __repr__(self) -> str:
        return f'{self.fr}--{self.to}'
# ----------------------------------------------------------------------



# ----------------------------------------------------------------------
@enum.unique
class Genre(enum.Enum):
    """(列挙帯)ゲームジャンル"""

    RPG = 'ロールプレイングゲーム'
    STG = 'シューティングゲーム（FPS, TPS含む）'
    ACG = 'アクションゲーム'
    PZL = 'パズルゲーム'
    RCG = 'レースゲーム'
    SLG = 'シミュレーションゲーム（RTS系含む）'
    KKG = '対戦格闘ゲーム'
    OTG = '音楽ゲーム'
    OTH = 'その他'
# ----------------------------------------------------------------------
# -----------------------------------------------------------------------------