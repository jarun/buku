from enum import Enum

from flask_admin.model import filters
from bukuserver import _l, _key


class BookmarkField(Enum):
    ID = 0
    URL = 1
    TITLE = 2
    TAGS = 3
    DESCRIPTION = 4


def equal_func(query, value, index):
    return filter(lambda x: x[index] == value, query)


def not_equal_func(query, value, index):
    return filter(lambda x: x[index] != value, query)


def contains_func(query, value, index):
    return filter(lambda x: value in x[index], query)


def not_contains_func(query, value, index):
    return filter(lambda x: value not in x[index], query)


def greater_func(query, value, index):
    return filter(lambda x: x[index] > value, query)


def smaller_func(query, value, index):
    return filter(lambda x: x[index] < value, query)


def in_list_func(query, value, index):
    return filter(lambda x: x[index] in value, query)


def not_in_list_func(query, value, index):
    return filter(lambda x: x[index] not in value, query)


def top_x_func(query, value, index):
    items = sorted(set(x[index] for x in query), reverse=True)
    top_x = items[:value]
    return filter(lambda x: x[index] in top_x, query)


def bottom_x_func(query, value, index):
    items = sorted(set(x[index] for x in query), reverse=False)
    top_x = items[:value]
    return filter(lambda x: x[index] in top_x, query)


class FilterType(Enum):

    EQUAL = {'func': equal_func, 'text': _l('equals')}
    NOT_EQUAL = {'func': not_equal_func, 'text': _l('not equals')}
    CONTAINS = {'func': contains_func, 'text': _l('contains')}
    NOT_CONTAINS = {'func': not_contains_func, 'text': _l('not contains')}
    GREATER = {'func': greater_func, 'text': _l('greater than')}
    SMALLER = {'func': smaller_func, 'text': _l('smaller than')}
    IN_LIST = {'func': in_list_func, 'text': _l('in list')}
    NOT_IN_LIST = {'func': not_in_list_func, 'text': _l('not in list')}
    TOP_X = {'func': top_x_func, 'text': _l('top X')}
    BOTTOM_X = {'func': bottom_x_func, 'text': _l('bottom X')}


class BaseFilter(filters.BaseFilter):

    def operation(self):
        return getattr(self, 'operation_text')

    def apply(self, query, value):
        return getattr(self, 'apply_func')(query, value, getattr(self, 'index'))


class TagBaseFilter(BaseFilter):

    def __init__(
            self,
            name,
            operation_text=None,
            apply_func=None,
            filter_type=None,
            options=None,
            data_type=None):
        try:
            self.index = ['name', 'usage_count'].index(name)
        except ValueError as e:
            raise ValueError(f'name: {name}') from e
        self.filter_type = filter_type
        if filter_type:
            self.apply_func = filter_type.value['func']
            self.operation_text = filter_type.value['text']
        else:
            self.apply_func = apply_func
            self.operation_text = operation_text
        if _key(self.operation_text) in ('in list', 'not in list'):
            super().__init__(name, options, data_type='select2-tags')
        else:
            super().__init__(name, options, data_type)

    def clean(self, value):
        on_list = self.filter_type in (FilterType.IN_LIST, FilterType.NOT_IN_LIST)
        if on_list and self.name == 'usage_count':
            value = [int(v.strip()) for v in value.split(',') if v.strip()]
        elif on_list:
            value = [v.strip() for v in value.split(',') if v.strip()]
        elif self.name == 'usage_count':
            value = int(value)
            if self.filter_type in (FilterType.TOP_X, FilterType.BOTTOM_X) and value < 1:
                raise ValueError
        if isinstance(value, str):
            return value.strip()
        return value


class BookmarkOrderFilter(BaseFilter):
    DIR_LIST = [('asc', _l('natural')), ('desc', _l('reversed'))]
    FIELDS = ['index', 'url', 'netloc', 'title', 'description', 'tags']

    def __init__(self, field, *args, **kwargs):
        self.field = field
        super().__init__('order', *args, options=self.DIR_LIST, **kwargs)

    def operation(self):
        return _l(f'by {self.field}')

    def apply(self, query, value):
        return query

    @staticmethod
    def value(filters, values):
        return [('-' if value == 'desc' else '+') + filters[idx].field
                for idx, key, value in values if key == 'order']


class BookmarkBukuFilter(BaseFilter):
    KEYS = {
        'markers': 'markers',
        'all_keywords': 'match all',
        'deep': 'deep',
        'regex': 'regex',
    }

    def __init__(self, *args, **kwargs):
        self.params = {key: kwargs.pop(key, False) for key in self.KEYS}
        super().__init__('buku', *args, **kwargs)

    def operation(self):
        parts = ', '.join(v for k, v in self.KEYS.items() if self.params[k])
        key = 'search' + (parts and ' ' + parts)
        return _l(key)

    def apply(self, query, value):
        return query


class BookmarkBaseFilter(BaseFilter):

    def __init__(
            self,
            name,
            operation_text=None,
            apply_func=None,
            filter_type=None,
            options=None,
            data_type=None):
        bm_fields_dict = {x.name.lower(): x.value for x in BookmarkField}
        if name in bm_fields_dict:
            self.index = bm_fields_dict[name]
        else:
            raise ValueError(f'name: {name}')
        self.filter_type = None
        if filter_type:
            self.apply_func = filter_type.value['func']
            self.operation_text = filter_type.value['text']
        else:
            self.apply_func = apply_func
            self.operation_text = operation_text
        if _key(self.operation_text) in ('in list', 'not in list'):
            super().__init__(name, options, data_type='select2-tags')
        else:
            super().__init__(name, options, data_type)

    def clean(self, value):
        on_list = _key(self.operation_text) in ('in list', 'not in list')
        if on_list and self.name == BookmarkField.ID.name.lower():
            value = [int(v.strip()) for v in value.split(',') if v.strip()]
        elif on_list:
            value = [v.strip() for v in value.split(',') if v.strip()]
        elif self.name == BookmarkField.ID.name.lower():
            value = int(value)
            if self.filter_type in (FilterType.TOP_X, FilterType.BOTTOM_X) and value < 1:
                raise ValueError
        if isinstance(value, str):
            return value.strip()
        return value


class BookmarkTagNumberEqualFilter(BookmarkBaseFilter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        def apply_func(query, value, index):
            for item in query:
                tags = [tag for tag in item[index].split(',') if tag]
                if len(tags) == value:
                    yield item

        self.apply_func = apply_func

    def clean(self, value):
        value = int(value)
        if value < 0:
            raise ValueError
        return value


class BookmarkTagNumberGreaterFilter(BookmarkTagNumberEqualFilter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        def apply_func(query, value, index):
            for item in query:
                tags = [tag for tag in item[index].split(',') if tag]
                if len(tags) > value:
                    yield item

        self.apply_func = apply_func


class BookmarkTagNumberNotEqualFilter(BookmarkTagNumberEqualFilter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        def apply_func(query, value, index):
            for item in query:
                tags = [tag for tag in item[index].split(',') if tag]
                if len(tags) != value:
                    yield item

        self.apply_func = apply_func


class BookmarkTagNumberSmallerFilter(BookmarkBaseFilter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        def apply_func(query, value, index):
            for item in query:
                tags = [tag for tag in item[index].split(',') if tag]
                if len(tags) < value:
                    yield item

        self.apply_func = apply_func

    def clean(self, value):
        value = int(value)
        if value < 1:
            raise ValueError
        return value
