import time

from rad.memory import Memory


def test_add_and_recall(home):
    m = Memory(home)
    m.add("semantic", "user prefers dark mode in their editor", tags=["prefs"])
    m.add("episodic", "user deployed the rad agent repo on 2026-09-17")
    found = m.recall("what does the user prefer for their editor?")
    assert any("dark mode" in e.text for e in found)


def test_dedupe_strengthen(home):
    m = Memory(home)
    e1 = m.add("semantic", "user prefers dark mode in their editor")
    e2 = m.add("semantic", "the user prefers dark mode in their editor")
    assert e1 is not None
    # second near-duplicate should not create a new file
    assert len(m.scan("semantic")) == 1


def test_decay_archives_old(home):
    m = Memory(home)
    e = m.add("episodic", "one time rad helped ship a website")
    # age it past the archive threshold
    e.last_used = time.time() - 200 * 86400
    m._save(e)
    faded, archived = m.decay_and_archive()
    assert archived == 1
    assert not e.path.exists()
    assert list((home.root / "memory" / "archive").glob("*.md"))


def test_sleep_heuristic(home):
    m = Memory(home)
    p = m.short_path()
    p.write_text(
        "[10:00:00] user: hello\n"
        "[10:00:05] rad: hi there\n"
        "[10:01:00] user: remember: my home server is called atlas\n"
        "[10:02:00] user: skill: use uv for python installs, not pip\n")
    report = m.sleep(consolidator=None)
    assert report["added"] == 2
    texts = [e.text for e in m.scan()]
    assert any("atlas" in t for t in texts)
    assert any("uv" in e.text for e in m.scan("procedural"))


def test_mark_slept_keeps_only_new(home):
    from datetime import datetime
    m = Memory(home)
    p = m.short_path()
    p.write_text("[09:00:00] user: old line\n")
    slept_at = datetime.now().replace(hour=11, minute=0, second=0, microsecond=0).timestamp()
    m.mark_slept(at=slept_at)
    p.write_text(p.read_text() + "[12:00:00] user: new line after sleep\n")
    unslept = m.unslept_short_text()
    assert "old line" not in unslept
    assert "new line after sleep" in unslept
