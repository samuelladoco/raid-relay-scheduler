# Import
# -----------------------------------------------------------------------------
from __future__ import annotations
import datetime as dt
import pandas as pd
import pathlib
#
from classes import RunnersAndTW, Runner, TimeWindow
from params import ParamSet
# -----------------------------------------------------------------------------


# Classes
# -----------------------------------------------------------------------------
# ----------------------------------------------------------------------
class RW:
    """入出力(クラスメソッドのみ)"""

    @classmethod
    def read_instance(cls, 
            file: pathlib.Path, date_tws: list[TimeWindow], 
            ) -> RunnersAndTW:
        """入力ファイルを読み込みインスタンスを生成する

        Parameters
        ----------
        file : pathlib.Path
            入力ファイルのパス
        date_tws : list[TimeWindow]
            日ごとの開催時間枠

        Returns
        -------
        RunnersAndTW
            インスタンス
        """

        runners: list[Runner] = []
        #
        df: pd.DataFrame = pd.read_csv(file)
        # データ数が少ないのでfor文で回しても遅くない
        for i, r in df.iterrows():
            id: int = int(i) + 1
            name: str = str(r['走者名'].strip())
            if str(r['一緒に走る方の名前']).strip() not in ['', 'nan', 'None']:
                name += f", {str(r['一緒に走る方の名前']).strip()}"
            game: str = str(r['タイトル'].strip())
            category: str = str(r['カテゴリ'].strip())
            #
            h, m, s = map(int, str(r['EST']).strip().split(':'))
            est_run: dt.timedelta = dt.timedelta(
                hours=h, minutes=m, seconds=s, 
            )
            del h, m, s
            #
            genre_str: str = str(
                r['ゲームジャンル　＊厳密でなくて大丈夫です、難しい場合はフィーリングで']
            ).strip()
            #
            date_hour_cols: list[list[int]] = []
            date_hour_cols.append(
                cls.__to_hours(str(r['参加可能時間 [8/15]']).strip())
            )
            date_hour_cols.append(
                cls.__to_hours(str(r['参加可能時間 [8/16]']).strip())
            )
            date_hour_cols.append(
                cls.__to_hours(str(r['参加可能時間 [8/17]']).strip())
            )
            #
            url: str = str(r['配信URL'].strip())
            ad: str = f"{str(r['宣伝用情報']).strip()}"
            if str(r['一緒に走る方の宣伝用情報']).strip() not in ['', 'nan', 'None']:
                ad += f"　＋　{str(r['一緒に走る方の宣伝用情報']).strip()}"
            note: str = str(r['参加にあたって一言']).strip()
            #
            runners.append(
                Runner(
                    id, name, game, category, est_run, genre_str, 
                    cls.__to_tws(date_tws, date_hour_cols), 
                    url, ad, note, 
                )
            )
            del id, name, game, category, est_run ,genre_str, date_hour_cols
            del url, ad, note
        del i, r
        #
        return RunnersAndTW(
            runners, TimeWindow(date_tws[0].fr, date_tws[-1].to)
        )


    @classmethod
    def __to_hours(cls, s: str) -> list[int]:
        """参加可能な時間(時)の羅列の文字列から時の数字のリストを生成する

        Parameters
        ----------
        s : str
            時刻の羅列の文字列('全OK', '全NG' を含む)

        Returns
        -------
        list[int]
            時の数字のリスト
        """

        if s == '全OK':
            return [h for h in range(24)]
        elif s == '全NG':
            return []
        else:
            return [int(h) for h in s.replace(' ', '').split(',')]


    @classmethod
    def __to_tws(cls, 
            date_tws: list[TimeWindow], date_hour_cols: list[list[int]], 
            ) -> list[TimeWindow]:
        """日ごとの開催時間枠・参加可能時間(時)から、統合した参加可能時間枠のリストを生成する

        Parameters
        ----------
        date_tws : list[TimeWindow]
            日ごとの開催時間枠
        date_hour_cols : list[list[int]]
            日ごとの参加可能時間(時)

        Returns
        -------
        list[TimeWindow]
            統合した参加可能時間枠のリスト

        Raises
        ------
        ValueError
            date_tws と date_hour_cols の要素数(日数)があわない場合に発生
        """

        if len(date_tws) != len(date_hour_cols):
            raise ValueError(f'{date_tws} と {date_hour_cols} のサイズが違います')
        #
        tws_unmerged: list[TimeWindow] = []
        #
        for date_tw, date_hour_col in zip(date_tws, date_hour_cols):
            fr: dt.datetime | None = None
            to: dt.datetime | None = None
            for h in range(24):
                if fr is None:
                    if h < date_tw.fr.hour:
                        continue
                    elif h == date_tw.fr.hour:
                        if h in date_hour_col:
                            fr = date_tw.fr
                            if h == (date_tw.to - dt.timedelta(seconds=1)).hour:
                                to = date_tw.to
                                tws_unmerged.append(TimeWindow(fr, to))
                                break
                            else:
                                continue
                        else:
                            continue
                    elif h <= (date_tw.to - dt.timedelta(seconds=1)).hour:
                        if h in date_hour_col:
                            fr = date_tw.fr.replace(hour=h, minute=0, second=0)
                            if h == (date_tw.to - dt.timedelta(seconds=1)).hour:
                                to = date_tw.to
                                tws_unmerged.append(TimeWindow(fr, to))
                                break
                            else:
                                continue
                        else:
                            continue
                    else:
                        continue
                else:
                    if h < (date_tw.to - dt.timedelta(seconds=1)).hour:
                        if h in date_hour_col:
                            continue
                        else:
                            to = (
                                date_tw.to - dt.timedelta(seconds=1)
                            ).replace(hour=h, minute=0, second=0)
                            tws_unmerged.append(TimeWindow(fr, to))
                            fr = None
                            to = None
                            continue
                    if h == (date_tw.to - dt.timedelta(seconds=1)).hour:
                        if h in date_hour_col:
                            to = date_tw.to
                            tws_unmerged.append(TimeWindow(fr, to))
                            break
                        else:
                            to = (
                                date_tw.to - dt.timedelta(seconds=1)
                            ).replace(hour=h, minute=0, second=0)
                            tws_unmerged.append(TimeWindow(fr, to))
                            break
                    else:
                        break
            del h
            del fr, to
        del date_tw, date_hour_col
        #
        tws_merged: list[TimeWindow] = []
        fr_merged: dt.datetime | None = None
        for i, tw in enumerate(tws_unmerged):
            if fr_merged == None:
                fr_merged = tw.fr
            if i == len(tws_unmerged) - 1 or tw.to != tws_unmerged[i + 1].fr:
                tws_merged.append(TimeWindow(fr_merged, tw.to))
                fr_merged = None
        del i, tw
        del fr_merged
        #
        return tws_merged


    @classmethod
    def write_solution(cls, 
            file: pathlib.Path, 
            tw: TimeWindow, 
            max_parallel_sessions: int, 
            assignment: dict[Runner, tuple[int, TimeWindow]], 
            ) -> None:
        """走者のセッション番号・時間の割り当てを出力ファイルに書き込む

        Parameters
        ----------
        file : pathlib.Path
            出力ファイルのパス
        tw : TimeWindow
            開催時間枠
        max_parallel_sessions : int
            最大同時開催セッションの数
        assignment : dict[Runner, tuple[int, TimeWindow]]
            走者のセッション番号・時間の割り当て(ない場合は {} )
        """

        if len(assignment) == 0:
            return
        #
        col: list[str] = ['日付', '時刻']
        col.extend([f'レイド {s}' for s in range(1, max_parallel_sessions + 1)])
        df: pd.DataFrame = pd.DataFrame(index=[], columns=col)
        #
        d: dt.datetime = tw.fr
        while d < tw.to:
            row: list[str] = [
                d.strftime('%Y/%m/%d') 
                if d == tw.fr or d == tw.to or (d.hour == 0 and d.minute == 0)
                else '', 
                d.strftime('%H:%M'), 
            ]
            row.extend(['' for _ in range(max_parallel_sessions)])
            for r, s_tw in assignment.items():
                if d == s_tw[1].fr:
                    row[1 + s_tw[0]] = (
                        f'[{r.id:02d}] {r.name}  ' + 
                        f'{r.game}, {r.genre.name}, {r.category}, {r.est_run}  ' +
                        # f'[{r.id:02d}] 走者名 | {r.name}  ' + 
                        # f'ゲーム名・カテゴリ・ゲームEST | {r.game}, {r.category}, {r.est_run}  ' +
                        # f'配信URL | {r.url}  ' +
                        # f'宣伝 | {r.ad}  ひと言 | {r.note}' +
                        f''
                    )
                if d == s_tw[1].to - ParamSet.EST_ALL_MINIMUM_UNIT:
                    row[1 + s_tw[0]] = f'[{r.id:02d}]'
            del r, s_tw
            df = pd.concat(
                [df, pd.DataFrame(data=[{c: r for c, r in zip(col, row)}])], 
                ignore_index=True
            )
            d += ParamSet.EST_ALL_MINIMUM_UNIT
        #
        df.to_csv(file, encoding='utf-8-sig', index=False)
# ----------------------------------------------------------------------
# -----------------------------------------------------------------------------
