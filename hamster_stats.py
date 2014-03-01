import datetime as dt
import itertools

def minutes(facts):
    time = dt.timedelta()
    for fact in facts:
        time += fact.delta
    return time.total_seconds() / 60.0

class Stats(object):
    def __init__(self, facts, toplevel_group=None):
        self.groups = None # we run top-level groups on first call
        self.toplevel_group = toplevel_group
        self._facts = facts

        self._range_start = None
        self._range_end = None
        self._update_groups()


    @property
    def facts(self):
        return self._facts

    @facts.setter
    def set_facts(self, facts):
        self._facts = facts
        self._update_groups()

    def _update_groups(self):
        for fact in self.facts:
            self._range_start = min(fact.date, self._range_start or fact.date)
            self._range_end = max(fact.date, self._range_end or fact.date)

        if not self.toplevel_group:
            # in case when we have no grouping, we are looking for totals
            self.groups = facts
        else:
            key_func = self.toplevel_group
            self.groups = {key: list(facts) for key, facts in
                               itertools.groupby(sorted(self.facts, key=key_func), key_func)}


    def group(self, key_func):
        # return the nested thing
        res = {}
        for key, facts in self.groups.iteritems():
            res[key] = {nested_key: list(nested_facts) for nested_key, nested_facts in
                         itertools.groupby(sorted(facts, key=key_func), key_func)}
        return res



    def by_week(self):
        """return series by week, fills gaps"""
        year_week = lambda date: (date.year, int(date.strftime("%W")))

        weeks = []
        start, end = self._range_start, self._range_end
        for i in range(0, (end - start).days, 7):
            weeks.append(year_week(start + dt.timedelta(days=i)))

        # group and then fill gaps and turn into a list
        res = self.group(lambda fact: year_week(fact.date))
        for key, group in res.iteritems():
            res[key] = [minutes(group.get(week, [])) for week in weeks]

        return res


    def by_weekday(self):
        """return series by weekday, fills gaps"""
        res = self.group(lambda fact: fact.date.weekday())
        for key, group in res.iteritems():
            res[key] = [minutes(group.get(weekday, [])) for weekday in range(7)]
        return res


    def by_hour(self):
        """return series by hour, stretched for the duration"""
        res = defaultdict(lambda: defaultdict(float))
        for key, facts in self.groups.iteritems():
            for fact in facts:
                minutes = fact.delta.total_seconds() / 60.0
                hours = int(minutes // 60)
                minutes = round(minutes - hours * 60)

                for i in range(hours):
                    res[key][(fact.start_time + dt.timedelta(hours=i)).hour] += 1

                res[key][(fact.start_time + dt.timedelta(hours=hours)).hour] += minutes / 60.0

        hours = range(24)
        hours = hours[6:] + hours[:6]
        for key in res.keys():
            res[key] = [res[key][i] for i in hours]

        return res

    def sum_durations(self, keys):
        """returns summed durations of the specified keys iterable"""
        res = []
        for key in keys:
            res_delta = dt.timedelta()
            for fact in (facts_dict.get(key) or []):
                res_delta += fact.delta
            res.append(round(res_delta.total_seconds() / 60.0))
        return res
