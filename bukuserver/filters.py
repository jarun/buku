from flask_admin.babel import lazy_gettext
from flask_admin.model import filters


class TagBaseFilter(filters.BaseFilter):

    def __init__(self, name, options=None, data_type=None):
        super().__init__(name, options, data_type)
        if name == 'name':
            self.index = 0
        elif name == 'usage_count':
            self.index = 1
        else:
            raise ValueError('name: {}'.format(name))

    def operation(self):
        raise NotImplementedError

    def clean(self, value):
        if self.name == 'usage_count':
            return int(value)
        return value


class TagEqualFilter(TagBaseFilter):

    def apply(self, query, value):
        return filter(lambda x: x[self.index] == value, query)

    def operation(self):
        return lazy_gettext('equals')


class TagNotEqualFilter(TagBaseFilter):

    def apply(self, query, value):
        return filter(lambda x: x[self.index] == value, query)

    def operation(self):
        return lazy_gettext('not equal')
