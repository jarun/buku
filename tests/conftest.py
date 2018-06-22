import sys
import warnings


if sys.version_info.major == 3 and sys.version_info.minor == 6:
    warnings.simplefilter('error')
