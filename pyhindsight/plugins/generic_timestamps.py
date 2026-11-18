###################################################################################################
#
# generic_timestamps.py
#   If cookie data looks like it might be a timestamp, try to decode it
#
# Plugin Author: Ryan Benson (ryan@hindsig.ht)
#
###################################################################################################

# Config
friendlyName = "Generic Timestamp Decoder"
description = "Attempts to detect and decode potential epoch second, epoch millisecond, and Webkit timestamps"
artifactTypes = ("cookie (created)", "cookie (accessed)", "local storage", "indexeddb")
remoteLookups = 0
browser = "Chrome"
browserVersion = 1
version = "20260905"
parsedItems = 0


def plugin(analysis_session=None):
    from pyhindsight.utils import friendly_date, to_datetime
    import re
    if analysis_session is None:
        return

    timestamp_re = re.compile(r'^(1(\d{9}|\d{12}|\d{16}))$')
    ls_timestamp_re = re.compile(r'timestamp.*?(\d{10,17})')
    global parsedItems
    parsedItems = 0

    # The digit count is the only unit hint a loose value gives, so declare it:
    # routing a 13-digit millisecond value through the magnitude heuristic instead
    # misreads anything before 2010 as epoch seconds and reports it as 1970.
    formats_by_digits = {10: 'epoch_s', 13: 'epoch_ms', 16: 'epoch_us', 17: 'webkit_us'}

    def decode(item, value):
        """Set an interpretation if the value looks like a timestamp. Returns 1 if it did."""
        m = re.search(timestamp_re, value)
        if m:
            raw = m.group(0)
            decoded = to_datetime(int(raw), format=formats_by_digits[len(raw)])
            if decoded is not None:
                item.interpretation = friendly_date(decoded) + ' [potential timestamp]'
                return 1
            return 0
        ls_m = re.search(ls_timestamp_re, value)
        if ls_m:
            raw = ls_m.group(1)
            fmt = formats_by_digits.get(len(raw))
            decoded = to_datetime(int(raw), format=fmt) if fmt else to_datetime(int(raw))
            if decoded is not None:
                item.interpretation = friendly_date(decoded) + ' [potential timestamp]'
                return 1
        return 0

    for item in analysis_session.parsed_artifacts:
        if item.row_type.startswith(artifactTypes):
            if item.interpretation is None:
                parsedItems += decode(item, item.value)

    # 'local storage' and 'indexeddb' rows live in parsed_storage, never in
    # parsed_artifacts, so naming them in artifactTypes did nothing on its own: this
    # plugin had only ever seen cookies, and ls_timestamp_re -- written for Local
    # Storage -- had never once run against a Local Storage value.
    for item in analysis_session.parsed_storage:
        if not item.row_type.startswith(artifactTypes):
            continue
        if item.interpretation is not None:
            continue

        # Read once: an IndexedDB value is rendered from its deserialized object on
        # access, so repeating item.value repeats the rendering.
        value = item.value
        if not isinstance(value, str):
            # Deleted records carry None in place of a value.
            continue

        parsedItems += decode(item, value)

    # Description of what the plugin did
    return "{} timestamps parsed".format(parsedItems)
