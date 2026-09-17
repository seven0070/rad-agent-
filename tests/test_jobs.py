import time

from rad import jobs


def test_parse_when_relative():
    base = time.time()
    w = jobs.parse_when("in 5m")
    assert w is not None and 290 < (w - base) <= 310
    w = jobs.parse_when("2h")
    assert w is not None and 7100 < (w - base) <= 7300
    w = jobs.parse_when("45s")
    assert w is not None and 40 < (w - base) <= 50


def test_parse_when_hhmm():
    w = jobs.parse_when("23:59")
    assert w is not None and w > time.time()


def test_parse_when_bad():
    assert jobs.parse_when("next tuesday at lunchtime") is None


def test_add_and_list_jobs(home):
    job = jobs.add_job(home, "note", time.time() + 3600, "take out the trash")
    assert job["id"]
    listing = jobs.list_jobs(home)
    assert "take out the trash" in listing
    assert jobs.cancel_job(home, job["id"])
    assert jobs.list_jobs(home) == "  no pending jobs"
