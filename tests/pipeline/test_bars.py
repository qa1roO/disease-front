import io
import unittest
import urllib.error
import urllib.parse

from pipeline import bars

ALS = {"D000690": "Amyotrophic Lateral Sclerosis"}
MND = {"D000690": "Amyotrophic Lateral Sclerosis", "D016472": "Motor Neuron Disease"}
SINCE = "2016-10-29"


def counter(by_phase):
    """A fake count(params): trials per phase filter ("" for no phase filter), recording each query."""
    calls = []

    def count(params):
        calls.append(params)
        advanced = params["filter.advanced"]
        phase = advanced.split("AREA[Phase]")[1] if "AREA[Phase]" in advanced else ""
        return by_phase.get(phase, 0)
    count.calls = calls
    return count


class QueryTest(unittest.TestCase):
    def test_since_is_ten_years_before_the_data_date(self):
        self.assertEqual(bars.since("2026-10-29T09:00:05"), "2016-10-29")
        self.assertEqual(bars.since("2028-02-29T00:00:00"), "2018-02-28")

    def test_condition_searches_each_mesh_heading_exactly(self):
        self.assertEqual(bars.condition(MND), 'AREA[ConditionMeshTerm]"Amyotrophic Lateral Sclerosis" OR '
                                              'AREA[ConditionMeshTerm]"Motor Neuron Disease"')

    def test_params_ask_for_interventional_trials_still_running_registered_since(self):
        p = bars.params(ALS, SINCE, "PHASE2")
        self.assertEqual(p["query.cond"], 'AREA[ConditionMeshTerm]"Amyotrophic Lateral Sclerosis"')
        self.assertEqual(p["filter.overallStatus"], "RECRUITING|NOT_YET_RECRUITING|ENROLLING_BY_INVITATION|ACTIVE_NOT_RECRUITING")
        self.assertEqual(p["filter.advanced"], "AREA[StudyType]INTERVENTIONAL AND "
                                               "AREA[StudyFirstPostDate]RANGE[2016-10-29,MAX] AND AREA[Phase]PHASE2")
        self.assertEqual((p["countTotal"], p["pageSize"]), ("true", "1"))
        self.assertNotIn("AREA[Phase]", bars.params(ALS, SINCE)["filter.advanced"])

    def test_search_url_opens_the_same_search_on_the_website(self):
        url = bars.search_url(ALS, SINCE)
        base, query = url.split("?")
        self.assertEqual(base, "https://clinicaltrials.gov/search")
        self.assertEqual(dict(urllib.parse.parse_qsl(query)), {
            "cond": 'AREA[ConditionMeshTerm]"Amyotrophic Lateral Sclerosis"',
            "aggFilters": "status:rec not enr act,studyType:int", "firstPost": "2016-10-29_"})


class BarTest(unittest.TestCase):
    def test_the_bar_is_the_furthest_phase_with_a_trial(self):
        count = counter({"": 40, "(PHASE3 OR PHASE4)": 0, "PHASE2": 12, "(PHASE1 OR EARLY_PHASE1)": 9})
        self.assertEqual(bars.bar(ALS, count, SINCE),
                         {"phase": "phase2", "trials": 40, "url": bars.search_url(ALS, SINCE)})

    def test_it_stops_asking_once_a_phase_has_trials(self):
        count = counter({"": 40, "(PHASE3 OR PHASE4)": 3, "PHASE2": 12})
        self.assertEqual(bars.bar(ALS, count, SINCE)["phase"], "phase3")
        self.assertEqual(len(count.calls), 2)

    def test_phase_4_counts_as_phase_3_and_early_phase_1_as_phase_1(self):
        self.assertEqual(bars.bar(ALS, counter({"": 2, "(PHASE3 OR PHASE4)": 2}), SINCE)["phase"], "phase3")
        self.assertEqual(bars.bar(ALS, counter({"": 2, "(PHASE1 OR EARLY_PHASE1)": 1}), SINCE)["phase"], "phase1")

    def test_trials_without_a_phase_or_no_trials_read_no_registered_trial(self):
        count = counter({"": 5})
        self.assertEqual(bars.bar(ALS, count, SINCE)["phase"], "none")
        empty = counter({})
        self.assertEqual(bars.bar(ALS, empty, SINCE), {"phase": "none", "trials": 0,
                                                           "url": bars.search_url(ALS, SINCE)})
        self.assertEqual(len(empty.calls), 1)

    def test_the_bar_is_never_approved_only_held_provinces_are_in_stage_8(self):
        count = counter({"": 40, "(PHASE3 OR PHASE4)": 3})
        self.assertEqual(bars.bar(MND, count, SINCE)["phase"], "phase3")
        self.assertNotIn("COMPLETED", count.calls[0]["filter.overallStatus"])


class FakeClock:
    def __init__(self):
        self.now, self.slept = 0.0, []

    def __call__(self):
        return self.now

    def sleep(self, s):
        self.slept.append(s)
        self.now += s


def http_error(code, retry_after=None):
    headers = {"Retry-After": retry_after} if retry_after else {}
    return urllib.error.HTTPError("https://x", code, "err", headers, io.BytesIO(b""))


class PoliteTest(unittest.TestCase):
    def test_requests_are_spaced_at_least_the_interval_apart(self):
        clock = FakeClock()
        get = bars.Polite(lambda url: url, interval=1.0, clock=clock, sleep=clock.sleep)
        get("a")
        clock.now += 0.25
        get("b")
        get("c")
        self.assertEqual(clock.slept, [0.75, 1.0])

    def test_429_backs_off_honouring_retry_after_then_doubling(self):
        clock, answers = FakeClock(), [http_error(429, "7"), http_error(429), http_error(503), "ok"]

        def flaky(url):
            a = answers.pop(0)
            if isinstance(a, Exception):
                raise a
            return a
        get = bars.Polite(flaky, interval=1.0, backoff=5.0, clock=clock, sleep=clock.sleep)
        self.assertEqual(get("a"), "ok")
        self.assertEqual(clock.slept, [7.0, 10.0, 20.0])

    def test_gives_up_after_the_last_try(self):
        clock = FakeClock()

        def always_429(url):
            raise http_error(429)
        get = bars.Polite(always_429, interval=1.0, backoff=1.0, tries=3, clock=clock, sleep=clock.sleep)
        with self.assertRaises(urllib.error.HTTPError):
            get("a")
        self.assertEqual(len(clock.slept), 2)

    def test_other_client_errors_are_not_retried(self):
        clock = FakeClock()

        def bad(url):
            raise http_error(400)
        get = bars.Polite(bad, clock=clock, sleep=clock.sleep)
        with self.assertRaises(urllib.error.HTTPError):
            get("a")
        self.assertEqual(clock.slept, [])


class CacheTest(unittest.TestCase):
    def test_counts_are_cached_per_query_for_one_data_timestamp(self):
        asked, saved = [], []
        cache = bars.CountCache({"dataTimestamp": "T1", "counts": {}}, "T1", lambda p: asked.append(p) or 4,
                                save=saved.append)
        p = bars.params(ALS, SINCE)
        self.assertEqual((cache(p), cache(p)), (4, 4))
        self.assertEqual(len(asked), 1)
        self.assertEqual(len(saved), 1)

    def test_a_new_data_timestamp_starts_afresh(self):
        old = {"dataTimestamp": "T0", "counts": {bars.cache_key(bars.params(ALS, SINCE)): 99}}
        cache = bars.CountCache(old, "T1", lambda p: 4)
        self.assertEqual(cache(bars.params(ALS, SINCE)), 4)
        self.assertEqual(cache.data["dataTimestamp"], "T1")


class RunTest(unittest.TestCase):
    def test_only_causes_with_reviewed_terms_get_a_bar(self):
        out = bars.run({554: ALS}, counter({"": 3, "PHASE2": 1}), SINCE)
        self.assertEqual(out, {"554": {"phase": "phase2", "trials": 3, "url": bars.search_url(ALS, SINCE)}})


if __name__ == "__main__":
    unittest.main()
