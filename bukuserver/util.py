from collections import Counter
from urllib.parse import urlparse
import re

get_netloc = lambda x: urlparse(x).netloc  # pylint: disable=no-member
select_filters = lambda args: {k: v for k, v in args.items() if re.match(r'flt.*_', k)}

JINJA_FILTERS = {'flt': select_filters, 'netloc': get_netloc}


def chunks(arr, n):
    n = max(1, n)
    return [arr[i : i + n] for i in range(0, len(arr), n)]

def sorted_counter(keys, *, min_count=0):
    data = Counter(keys)
    return Counter({k: v for k, v in sorted(data.items()) if v > min_count})
