from collections import Counter
from urllib.parse import urlparse
from enum import StrEnum, auto
import sys
import re

IS_WINDOWS = sys.platform == 'win32'

get_netloc = lambda x: urlparse(x).netloc  # pylint: disable=no-member
select_filters = lambda args: {k: v for k, v in args.items() if re.match(r'flt.*_', k)}

JINJA_FILTERS = {'flt': select_filters, 'netloc': get_netloc}


is_filename_valid = lambda name: not IS_WINDOWS or not re.search(r'[<>:"|?*]', name)

def chunks(arr, n):
    n = max(1, n)
    return [arr[i : i + n] for i in range(0, len(arr), n)]

def sorted_counter(keys, *, min_count=0):
    data = Counter(keys)
    return Counter({k: v for k, v in sorted(data.items()) if v > min_count})


UrlRenderMode = StrEnum('UrlRenderMode', ['FULL', 'NETLOC', 'NETLOC_TAG'])

class DbSwitchMode(StrEnum):
    DISABLED = auto()
    SAME_DIR = auto()
    SAME_DIR_EXISTING = auto()

    @property
    def allow_new(self):
        return self.name != 'DISABLED' and not self.name.endswith('_EXISTING')
