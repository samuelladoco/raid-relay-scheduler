# Import
# -----------------------------------------------------------------------------
from __future__ import annotations
import dataclasses
import datetime as dt
import mip
#
from classes import RunnersAndTW, Runner, TimeWindow
from params import ParamSet
# -----------------------------------------------------------------------------


# Classes
# -----------------------------------------------------------------------------
# ----------------------------------------------------------------------
@dataclasses.dataclass(frozen=True, )
class MIPModel:
    """問題例を解くMIPモデル"""

    R: RunnersAndTW

    def solve_feasibility_and_min_s1_interval(self, 
            max_parallel_sessions: int, 
            can_stop_time_be_outside_tw_to: bool, 
            time_limit_s: int, 
            ) -> dict[Runner, tuple[int, TimeWindow]]:
        """走者のセッション番号・時間の割り当てを行う。
        ただし、最大同時開催セッションの数を超えないものとする。
        また、若いセッション番号にできるだけ空白時間がないように割り当てる

        Parameters
        ----------
        max_parallel_sessions : int
            最大同時開催セッションの数
        can_stop_time_be_outside_tw_to : bool
            各走者の終了時刻が時間枠の外にでてもよいか否か
        time_limit_s : int
            最大許容計算時間

        Returns
        -------
        dict[Runner, tuple[int, TimeWindow]]
            走者のセッション番号・時間の割り当て(ない場合は {} )
        """

        # Additional input
        J: list[int] = [j for j in range(1, max_parallel_sessions + 1)]

        # Model
        m: mip.Model = mip.Model(
            name=f'MIP_{self.R}', 
            # solver_name=mip.CBC, 
        )

        #   Variables
        t: dict[Runner, mip.Var] = {
            r: m.add_var(
                lb=0, ub=self.__to_int(self.R.tw.to - r.est_all), 
                var_type=mip.CONTINUOUS, name=f't({r.id})', 
            ) for r in self.R.runners
        }
        #
        w: dict[tuple[Runner, TimeWindow], mip.Var] = {
            (r, i): m.add_var(
                var_type=mip.BINARY, name=f'w({r.id})', 
            ) for r in self.R.runners 
            for i in r.tws
        }
        #
        s: dict[tuple[Runner, int], mip.Var] = {
            (r, j): m.add_var(
                var_type=mip.BINARY, name=f's({r.id})', 
            ) for r in self.R.runners 
            for j in J
        }
        z: dict[tuple[Runner, Runner], mip.Var] = {
            (r1, r2): m.add_var(
                var_type=mip.BINARY, name=f'z({r1.id},{r2.id})', 
            ) for r1 in self.R.runners 
            for r2 in [rb for rb in self.R.runners if r1 != rb]
        }

        # ★ ジャンルまとめたい
        # ★ 並列時間固めたい (バックアップは最初か最後に)
        # ★ 並列深夜避けたい
        #   Objective
        weight: dict[int, int] = {
            j: 10 ** (
                len(str(self.__to_int(self.R.tw.to))) * (len(J) - 2 - J.index(j))
            ) 
            for j in J
        }
        weight[J[-1]] = 0
        #
        m.objective = mip.minimize(
            mip.xsum(
                weight[j] * (
                    self.__to_int(self.R.tw.to) 
                    - mip.xsum(
                        self.__to_int(self.R.tw.fr + r.est_all) * s[r, j] 
                        for r in self.R.runners
                    )
                )
                for j in J
            )
        )
        m.add_constr(
            mip.xsum(
                weight[j] * (
                    self.__to_int(self.R.tw.to) 
                    - mip.xsum(
                        self.__to_int(self.R.tw.fr + r.est_all) * s[r, j] 
                        for r in self.R.runners
                    )
                )
                for j in J
            )
            >= 0, 
            f'objective_lower_bound'
        )

        #   Constraints
        for r in self.R.runners:
            m.add_constr(
                mip.xsum(w[r, i] for i in r.tws) == 1, f'sum_w({r.id})'
            )
            m.add_constr(
                mip.xsum(s[r, j] for j in J) == 1, f'sum_s({r.id})'
            )
        del r
        #
        for r in self.R.runners:
            for i in r.tws:
                m.add_constr(
                    t[r] >= self.__to_int(i.fr) - self.__to_int(self.R.tw.to - r.est_all) * (1 - w[r, i]), 
                    f't_geq({r.id},{i})'
                )
                #
                if can_stop_time_be_outside_tw_to is True:
                    td_min: dt.timedelta = min(r.est_all, ParamSet.MINIMUM_INTERVAL_FROM_TW_TO)
                    m.add_constr(
                        t[r] + self.__to_int(self.R.tw.fr + td_min) <= self.__to_int(i.to) + self.__to_int(self.R.tw.to) * (1 - w[r, i]), 
                        f't_leq({r.id},{i})'
                    )
                    del td_min
                else:
                    m.add_constr(
                        t[r] + self.__to_int(self.R.tw.fr + r.est_all) <= self.__to_int(i.to) + self.__to_int(self.R.tw.to) * (1 - w[r, i]), 
                        f't_leq({r.id},{i})'
                    )
            del i
        del r
        #
        for r1 in self.R.runners:
            for r2 in [rb for rb in self.R.runners if r1 < rb]:
                for j in J:
                    m.add_constr(
                        z[r1, r2] + z[r2, r1] >= s[r1, j] + s[r2, j] - 1,
                        f'zs_geq({r1.id},{r2.id},{j})'
                    )
                    m.add_constr(
                        z[r1, r2] + z[r2, r1] <= 1,
                        f'zs_leq({r1.id},{r2.id},{j})'
                    )
                del j
            if len([rb for rb in self.R.runners if r1 < rb]) > 0:
                del r2
        del r1
        #
        for r1 in self.R.runners:
            for r2 in [rb for rb in self.R.runners if r1 != rb]:
                m.add_constr(
                    t[r1] + self.__to_int(self.R.tw.fr + r1.est_all) <= t[r2] + self.__to_int(self.R.tw.to) * (1 - z[r1, r2]),
                    f'tz({r1.id},{r2.id})'
                )
            del r2
        del r1

        # Run
        m.max_seconds = time_limit_s
        status: mip.OptimizationStatus = m.optimize()

        # Solution
        solution_assignment: dict[Runner, tuple[int, TimeWindow]] = {}
        if status == mip.OptimizationStatus.OPTIMAL or status == mip.OptimizationStatus.FEASIBLE:
            for r in self.R.runners:
                for j in J:
                    if s[r, j].x > 1.0 - m.integer_tol:
                        fr: dt.datetime = self.__to_datetime(
                            int(t[r].x + m.infeas_tol)
                        )
                        solution_assignment[r] = (j, TimeWindow(fr, fr + r.est_all))
                        del fr
                        break
                del j
            del r
        elif status == mip.OptimizationStatus.NO_SOLUTION_FOUND:
            print(f'指定された時間( {time_limit_s} 秒)内に答えが見つかりませんでした')
        elif status == mip.OptimizationStatus.INFEASIBLE:
            print(f'答えが存在しないことが判明しました')

        return solution_assignment


    def __to_int(self, d: dt.datetime) -> int:
        """日時を開催開始時刻を 0 、1単位を Param.EST_ALL_MINIMUM_UNIT とする経過値に変換する

        Parameters
        ----------
        d : dt.datetime
            日時

        Returns
        -------
        int
            開催開始時刻を 0 、1単位を Param.EST_ALL_MINIMUM_UNIT とする経過値
        """

        return int(
            ((d - self.R.tw.fr).total_seconds())
            / ParamSet.EST_ALL_MINIMUM_UNIT.total_seconds()
        )


    def __to_datetime(self, i: int) -> dt.datetime:
        """開催開始時刻を 0 、1単位を Param.EST_ALL_MINIMUM_UNIT とする経過値を日時に変換する

        Parameters
        ----------
        i : int
            開催開始時刻を 0 、1単位を Param.EST_ALL_MINIMUM_UNIT とする経過値

        Returns
        -------
        dt.datetime
            日時
        """

        return (
            i * ParamSet.EST_ALL_MINIMUM_UNIT + self.R.tw.fr
        )


    def __repr__(self) -> str:
        return f'{self.R}'
# ----------------------------------------------------------------------
# -----------------------------------------------------------------------------
