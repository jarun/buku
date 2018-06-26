from flask_admin.model import filters


class TagBaseFilter(filters.BaseFilter):

    def __init__(self, name, operation_text, apply_func, options=None, data_type=None):
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
        self.apply_func = apply_func
        self.operation_text = operation_text

    def operation(self):
        return self.operation_text

    def clean(self, value):
        if self.operation_text in ('in list', 'not in list') and self.name == 'usage_count':
            value = [int(v.strip()) for v in value.split(',') if v.strip()]
        elif self.operation_text in ('in list', 'not in list'):
            value = [v.strip() for v in value.split(',') if v.strip()]
        elif self.name == 'usage_count':
            value = int(value)
            if self.operation_text in ('top x', 'bottom x') and value < 1:
                raise ValueError
        return value

    def apply(self, query, value):
        return self.apply_func(query, value, self.index)
