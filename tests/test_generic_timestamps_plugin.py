import datetime
import types
import unittest

from pyhindsight.plugins import generic_timestamps

UTC = datetime.timezone.utc


def _item(value, row_type='cookie (created)'):
    return types.SimpleNamespace(row_type=row_type, value=value, interpretation=None)


def _session(items):
    return types.SimpleNamespace(parsed_artifacts=items, parsed_storage=[])


class TestGenericTimestampsPlugin(unittest.TestCase):
    """The plugin decodes a value by the unit its digit count pins down.

    It used to route everything through the magnitude heuristic, which read a
    13-digit millisecond value from before 2010 as epoch *seconds* -- a date so
    far out of range it was clamped to 1970-01-01.
    """

    def test_13_digit_milliseconds_before_2010(self):
        ms = str(int(datetime.datetime(2009, 11, 20, 18, 0, tzinfo=UTC).timestamp() * 1000))
        item = _item(ms)
        generic_timestamps.plugin(analysis_session=_session([item]))
        self.assertEqual(item.interpretation, '2009-11-20 18:00:00.000 [potential timestamp]')

    def test_10_digit_seconds_and_17_digit_webkit(self):
        seconds = _item(str(int(datetime.datetime(2009, 11, 20, 18, 0,
                                                  tzinfo=UTC).timestamp())))
        webkit = _item(str(12888182400000000))  # 2009-05-30 18:40:00 as WebKit µs
        generic_timestamps.plugin(analysis_session=_session([seconds, webkit]))
        self.assertEqual(seconds.interpretation, '2009-11-20 18:00:00 [potential timestamp]')
        self.assertEqual(webkit.interpretation, '2009-05-30 18:40:00.000000 [potential timestamp]')

    def test_non_timestamp_values_are_left_alone(self):
        item = _item('not a timestamp')
        generic_timestamps.plugin(analysis_session=_session([item]))
        self.assertIsNone(item.interpretation)


if __name__ == '__main__':
    unittest.main()
