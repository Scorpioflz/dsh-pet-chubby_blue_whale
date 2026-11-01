"""dsh_self_talk 定时计划逻辑测试。

覆盖 _parse_hhmm / _clean_weekdays / _next_schedule_after /
_should_run_now / next_check_delay_ms 的各场景。
"""

import time

import pytest

from pet.dsh_self_talk import (
    _parse_hhmm,
    _clean_weekdays,
    _next_schedule_after,
    _should_run_now,
    next_check_delay_ms,
)


class FakeConfig:
    def __init__(self, **kwargs):
        self._data = kwargs

    def get(self, key, default=None):
        return self._data.get(key, default)


def _ts(year, month, day, hour, minute=0):
    return time.mktime((year, month, day, hour, minute, 0, 0, 0, -1))


class TestParseHhmm:
    def test_valid(self):
        assert _parse_hhmm("08:00") == (8, 0)
        assert _parse_hhmm("23:59") == (23, 59)
        assert _parse_hhmm("00:00") == (0, 0)
        assert _parse_hhmm("12:30") == (12, 30)

    def test_invalid(self):
        assert _parse_hhmm("") is None
        assert _parse_hhmm("25:00") is None
        assert _parse_hhmm("08:60") is None
        assert _parse_hhmm("abc") is None
        assert _parse_hhmm(None) is None
        assert _parse_hhmm("08-00") is None
        assert _parse_hhmm("08:00:00") is None

    def test_single_digit(self):
        assert _parse_hhmm("8:0") == (8, 0)


class TestCleanWeekdays:
    def test_empty(self):
        assert _clean_weekdays([]) == []
        assert _clean_weekdays(None) == []
        assert _clean_weekdays("abc") == []

    def test_valid(self):
        assert _clean_weekdays([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]
        assert _clean_weekdays([6, 7]) == [6, 7]

    def test_filtered(self):
        assert _clean_weekdays([0, 8, 1, 9, 3]) == [1, 3]
        assert _clean_weekdays([1.0, 2.0]) == [1, 2]


class TestNextScheduleAfter:
    def test_same_day_before_target(self):
        after = _ts(2026, 1, 15, 7, 0)
        expected = _ts(2026, 1, 15, 8, 0)
        assert _next_schedule_after(after, 8, 0, []) == expected

    def test_same_day_after_target(self):
        after = _ts(2026, 1, 15, 9, 0)
        expected = _ts(2026, 1, 16, 8, 0)
        assert _next_schedule_after(after, 8, 0, []) == expected

    def test_exactly_at_target(self):
        after = _ts(2026, 1, 15, 8, 0)
        expected = _ts(2026, 1, 16, 8, 0)
        assert _next_schedule_after(after, 8, 0, []) == expected

    def test_weekday_filter_skips_weekend(self):
        # 2026-01-16 是周五，weekdays=[1-5] → 跳过周六周日，下周一
        after = _ts(2026, 1, 16, 9, 0)
        expected = _ts(2026, 1, 19, 8, 0)
        assert _next_schedule_after(after, 8, 0, [1, 2, 3, 4, 5]) == expected

    def test_weekend_only(self):
        # 2026-01-16 周五 09:00, weekdays=[6,7] → 周六 08:00
        after = _ts(2026, 1, 16, 9, 0)
        expected = _ts(2026, 1, 17, 8, 0)
        assert _next_schedule_after(after, 8, 0, [6, 7]) == expected

    def test_empty_weekdays_every_day(self):
        after = _ts(2026, 1, 15, 9, 0)
        expected = _ts(2026, 1, 16, 8, 0)
        assert _next_schedule_after(after, 8, 0, []) == expected


class TestShouldRunNow:
    def test_first_run_past_midnight(self):
        # schedule=00:00，首次运行（午夜已过）→ True
        cfg = FakeConfig(dsh_self_talk_schedule="00:00")
        assert _should_run_now(cfg, {"last_generated": 0}) is True

    def test_first_run_no_last_generated(self):
        cfg = FakeConfig(dsh_self_talk_schedule="00:00")
        assert _should_run_now(cfg, {}) is True

    def test_just_generated_now(self):
        # 刚生成过（last_run=now）→ False
        now = time.time()
        cfg = FakeConfig(dsh_self_talk_schedule="08:00")
        assert _should_run_now(cfg, {"last_generated": now}) is False

    def test_just_generated_one_second_ago(self):
        now = time.time()
        cfg = FakeConfig(dsh_self_talk_schedule="00:00")
        assert _should_run_now(cfg, {"last_generated": now - 1}) is False

    def test_missed_multiple_days(self):
        # 3 天前生成过，schedule=00:00 → True
        now = time.time()
        three_days_ago = now - 3 * 86400
        cfg = FakeConfig(dsh_self_talk_schedule="00:00")
        assert _should_run_now(cfg, {"last_generated": three_days_ago}) is True

    def test_missed_one_day(self):
        # 25h 前生成过，schedule=00:00 → True
        now = time.time()
        cfg = FakeConfig(dsh_self_talk_schedule="00:00")
        assert _should_run_now(cfg, {"last_generated": now - 25 * 3600}) is True

    def test_legacy_interval_overdue(self):
        # schedule 为空 → 旧行为，25h 前 → True
        now = time.time()
        cfg = FakeConfig(dsh_self_talk_schedule="")
        assert _should_run_now(cfg, {"last_generated": now - 25 * 3600}) is True

    def test_legacy_interval_recent(self):
        # 旧行为，1h 前 → False
        now = time.time()
        cfg = FakeConfig(dsh_self_talk_schedule="")
        assert _should_run_now(cfg, {"last_generated": now - 3600}) is False

    def test_legacy_interval_first_run(self):
        # 旧行为，首次运行 → True
        cfg = FakeConfig(dsh_self_talk_schedule="")
        assert _should_run_now(cfg, {"last_generated": 0}) is True

    def test_invalid_schedule_falls_back_to_legacy(self):
        now = time.time()
        cfg = FakeConfig(dsh_self_talk_schedule="invalid")
        assert _should_run_now(cfg, {"last_generated": now - 25 * 3600}) is True
        assert _should_run_now(cfg, {"last_generated": now - 3600}) is False

    def test_weekday_filter_not_today(self):
        # 构造 last_run 使得下一个计划点在不匹配的星期
        # 2026-01-16 周五 09:00 生成过，weekdays=[6,7]（仅周末）
        # next = 周六 08:00，如果 now < 周六 08:00 → False
        last_run = _ts(2026, 1, 16, 9, 0)
        now = _ts(2026, 1, 16, 10, 0)
        # 用 monkeypatch 替换 time.time
        import pet.dsh_self_talk as mod
        orig = mod.time.time
        mod.time.time = lambda: now
        try:
            cfg = FakeConfig(dsh_self_talk_schedule="08:00", dsh_self_talk_weekdays=[6, 7])
            assert _should_run_now(cfg, {"last_generated": last_run}) is False
        finally:
            mod.time.time = orig

    def test_weekday_filter_today_matches(self):
        # 2026-01-17 周六 09:00 生成过，weekdays=[6,7]
        # next = 周日 08:00，now = 周日 10:00 → True
        last_run = _ts(2026, 1, 17, 9, 0)
        now = _ts(2026, 1, 18, 10, 0)
        import pet.dsh_self_talk as mod
        orig = mod.time.time
        mod.time.time = lambda: now
        try:
            cfg = FakeConfig(dsh_self_talk_schedule="08:00", dsh_self_talk_weekdays=[6, 7])
            assert _should_run_now(cfg, {"last_generated": last_run}) is True
        finally:
            mod.time.time = orig

    def test_first_run_weekday_not_matching(self):
        # 首次运行，今天是周三，weekdays=[6,7]（仅周末）→ False
        # 2026-01-20 是周二... 让我找个周三
        # 2026-01-21 是周三
        now = _ts(2026, 1, 21, 10, 0)
        import pet.dsh_self_talk as mod
        orig = mod.time.time
        mod.time.time = lambda: now
        try:
            cfg = FakeConfig(dsh_self_talk_schedule="08:00", dsh_self_talk_weekdays=[6, 7])
            assert _should_run_now(cfg, {"last_generated": 0}) is False
        finally:
            mod.time.time = orig

    def test_first_run_weekday_matching(self):
        # 首次运行，今天是周六，已过 08:00，weekdays=[6,7] → True
        # 2026-01-17 是周六
        now = _ts(2026, 1, 17, 10, 0)
        import pet.dsh_self_talk as mod
        orig = mod.time.time
        mod.time.time = lambda: now
        try:
            cfg = FakeConfig(dsh_self_talk_schedule="08:00", dsh_self_talk_weekdays=[6, 7])
            assert _should_run_now(cfg, {"last_generated": 0}) is True
        finally:
            mod.time.time = orig


class TestNextCheckDelayMs:
    def test_legacy_mode(self):
        cfg = FakeConfig(dsh_self_talk_schedule="")
        assert next_check_delay_ms(cfg) == 600000

    def test_invalid_schedule(self):
        cfg = FakeConfig(dsh_self_talk_schedule="abc")
        assert next_check_delay_ms(cfg) == 600000

    def test_schedule_mode_capped(self):
        cfg = FakeConfig(dsh_self_talk_schedule="23:59")
        delay = next_check_delay_ms(cfg)
        assert 1000 <= delay <= 600000

    def test_schedule_mode_minimum(self):
        # schedule=00:00，现在接近午夜 → delay 很小但 >= 1000
        cfg = FakeConfig(dsh_self_talk_schedule="00:00")
        delay = next_check_delay_ms(cfg)
        assert 1000 <= delay <= 600000