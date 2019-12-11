from enum import Enum

from flask_admin.model import filters


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

    EQUAL = {'func': equal_func, 'text':'equals'}
    NOT_EQUAL = {'func': not_equal_func, 'text':'not equal'}
    GREATER = {'func': greater_func, 'text':'greater than'}
    SMALLER = {'func': smaller_func, 'text':'smaller than'}
    IN_LIST = {'func': in_list_func, 'text':'in list'}
    NOT_IN_LIST = {'func': not_in_list_func, 'text':'not in list'}
    TOP_X = {'func': top_x_func, 'text': 'top x'}
    BOTTOM_X = {'func': bottom_x_func, 'text': 'bottom x'}


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
        if operation_text in ('in list', 'not in list'):
            super().__init__(name, options, data_type='select2-tags')
        else:
            super().__init__(name, options, data_type)
        if name == 'name':
            self.index = 0
        elif name == 'usage_count':
            self.index = 1
        else:
            raise ValueError('name: {}'.format(name))
        self.filter_type = None
        if filter_type:
            self.apply_func = filter_type.value['func']
            self.operation_text = filter_type.value['text']
            self.filter_type = filter_type
        else:
            self.apply_func = apply_func
            self.operation_text = operation_text

    def clean(self, value):
        if (
                self.filter_type in (FilterType.IN_LIST, FilterType.NOT_IN_LIST) and
                self.name == 'usage_count'):
            value = [int(v.strip()) for v in value.split(',') if v.strip()]
        elif self.filter_type in (FilterType.IN_LIST, FilterType.NOT_IN_LIST):
            value = [v.strip() for v in value.split(',') if v.strip()]
        elif self.name == 'usage_count':
            value = int(value)
            if self.filter_type in (FilterType.TOP_X, FilterType.BOTTOM_X) and value < 1:
                raise ValueError
        if isinstance(value, str):
            return value.strip()
        return value


class BookmarkBukuFilter(BaseFilter):

    def __init__(self, *args, **kwargs):
        self.keys = {
            'all_keywords': 'match all',
            'deep': 'deep',
            'regex': 'regex'
        }
        for key, value in kwargs.items():
            if key in self.keys and value:
                setattr(self, key, value)
            else:
                setattr(self, key, False)
        list(map(lambda x: kwargs.pop(x), self.keys))
        super().__init__('buku', *args, **kwargs)

    def operation(self):
        parts = []
        for key, value in self.keys.items():
            if getattr(self, key):
                parts.append(value)
        if not parts:
            return 'search'
        return 'search ' + ', '.join(parts)

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
        if operation_text in ('in list', 'not in list'):
            super().__init__(name, options, data_type='select2-tags')
        else:
            super().__init__(name, options, data_type)
        bm_fields_dict = {x.name.lower(): x.value for x in BookmarkField}
        if name in bm_fields_dict:
            self.index = bm_fields_dict[name]
        else:
            raise ValueError('name: {}'.format(name))
        self.filter_type = None
        if filter_type:
            self.apply_func = filter_type.value['func']
            self.operation_text = filter_type.value['text']
        else:
            self.apply_func = apply_func
            self.operation_text = operation_text

    def clean(self, value):
        if (
                self.filter_type in (FilterType.IN_LIST, FilterType.NOT_IN_LIST) and
                self.name == BookmarkField.ID.name.lower()):
            value = [int(v.strip()) for v in value.split(',') if v.strip()]
        elif self.filter_type in (FilterType.IN_LIST, FilterType.NOT_IN_LIST):
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

        self. apply_func = apply_func


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
