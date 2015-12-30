# -*- coding: utf-8 -*-
from functools import reduce
from lib.sql import *
from lib.db import DB


class FieldError(Exception):
    pass


class ModelError(Exception):
    pass


class Field(object):
    def __init__(self, name, column_type, default, primary_key, auto):
        self.name = name
        self.column_type = column_type
        self.default = default
        self.primary_key = primary_key
        self.auto = auto
        if self.primary_key:
            self.auto = True

    def __str__(self):
        return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)


class CharField(Field):
    def __init__(self, name=None, column_type='char(50)', default=None, primary_key=False, auto=False):
        super().__init__(name, column_type, default, primary_key, auto)


class VarcharField(Field):
    def __init__(self, name=None, column_type='varchar(100)', default=None, primary_key=False, auto=False):
        super().__init__(name, column_type, default, primary_key, auto)


class IntField(Field):
    def __init__(self, name=None, column_type='int(11)', default=None, primary_key=False, auto=False):
        super().__init__(name, column_type, default, primary_key, auto)


class TimestampField(Field):
    def __init__(self, name=None, column_type='TIMESTAMP', default=None, primary_key=False, auto=False):
        super().__init__(name, column_type, default, primary_key, auto)


class DateField(Field):
    def __init__(self, name=None, column_type='DATE', default=None, primary_key=False, auto=False):
        super().__init__(name, column_type, default, primary_key, auto)


class DbModelMetaclass(type):
    def __new__(mcs, name, bases, attrs):
        if name == 'DbModel':
            return type.__new__(mcs, name, bases, attrs)

        table_name = attrs.get('__table__') or name
        mappings = dict()
        fields = []
        auto_fields = []
        primary_key = None
        for k, v in attrs.items():
            if isinstance(v, Field):
                mappings[k] = v
                if v.auto or v.primary_key:
                    auto_fields.append(k)
                if v.primary_key:
                    if primary_key:
                        raise RuntimeError('Duplicate primary key (%s) for field: %s.' % (primary_key, k))
                    primary_key = k
                else:
                    fields.append(k)
        if not primary_key:
            raise RuntimeError('primary key not found.')
        for k in mappings.keys():
            attrs.pop(k)
        attrs['__mappings__'] = mappings
        attrs['__table__'] = table_name
        attrs['__primary_key__'] = primary_key
        attrs['__fields__'] = fields
        attrs['__auto_fields__'] = auto_fields
        return type.__new__(mcs, name, bases, attrs)


class DbModel(dict, metaclass=DbModelMetaclass):
    def __init__(self, **kwargs):
        super(DbModel, self).__init__(**kwargs)

    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value

    def get_value(self, key):
        return getattr(self, key, None)

    def get_value_default(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                setattr(self, key, value)
        return value

    def db_add(self, db: DB):
        insertid = self.db_insert(db, self)
        if insertid:
            self[self.__primary_key__] = insertid
        return insertid

    def db_save(self, db: DB):
        if self.__primary_key__ in self.keys():
            self.db_update(db, self)
        else:
            self.db_add(db)
        return self[self.__primary_key__]

    def db_remove(self, db: DB):
        return self.db_delete(db, self[self.__primary_key__])

    @classmethod
    def sql_insert(cls, model_object):
        if not isinstance(model_object, cls):
            raise ModelError('%s is not %s' % (type(model_object), type(cls)))
        for k, v in model_object.items():
            if k == cls.__primary_key__ or k in cls.__auto_fields__:
                raise FieldError('key %s is primary_key or auto_field' % k)
        return str(Sql().insert().table(cls.__table__).set(**model_object))

    @classmethod
    def db_insert(cls, db: DB, model_object):
        if not isinstance(model_object, cls):
            raise ModelError('%s is not %s' % (type(model_object), type(cls)))
        for k, v in model_object.items():
            if k == cls.__primary_key__ or k in cls.__auto_fields__:
                raise FieldError('key %s is primary_key or auto_field' % k)
        rows = db.execute(str(Sql().insert().table(cls.__table__).set(**model_object)))
        if rows:
            return db.insertid()
        return -1

    @classmethod
    def db_insert_many(cls, db: DB, *model_object_list):
        return [cls.db_insert(db, **model_object) for model_object in model_object_list]

    @classmethod
    def sql_delete(cls, primary_key_value):
        return str(Sql().delete().table(cls.__table__).where(**{cls.__primary_key__: primary_key_value}))

    @classmethod
    def db_delete(cls, db: DB, primary_key_value):
        return db.execute(str(Sql().delete().table(cls.__table__).where(**{cls.__primary_key__: primary_key_value})))

    @classmethod
    def db_delete_many(cls, db: DB, *primary_key_list):
        return reduce(lambda x, y: x + y,
                      [cls.db_delete(db, primary_key) for primary_key in primary_key_list])

    @classmethod
    def sql_update(cls, model_object):
        if not isinstance(model_object, cls):
            raise ModelError('%s is not %s' % (type(model_object), type(cls)))
        data = {k: v for k, v in model_object.items() if k != cls.__primary_key__ and k not in cls.__auto_fields__}
        return str(Sql().update()
                   .table(cls.__table__)
                   .set(**data)
                   .where(**{cls.__primary_key__: model_object[cls.__primary_key__]}))

    @classmethod
    def db_update(cls, db: DB, model_object):
        if not isinstance(model_object, cls):
            raise ModelError('%s is not %s' % (type(model_object), type(cls)))
        data = {k: v for k, v in model_object.items() if k != cls.__primary_key__ and k not in cls.__auto_fields__}
        return db.execute(str(Sql().update().table(cls.__table__).set(
                **data).where(
            **{cls.__primary_key__: model_object[cls.__primary_key__]})))

    @classmethod
    def db_update_many(cls, db: DB, *model_object_list):
        return reduce(lambda x, y: x + y,
                      [cls.db_update(db, **each) for each in model_object_list])

    @classmethod
    def sql_get(cls, primary_key_value):
        return str(Sql().select(*cls.__mappings__.keys()).table(cls.__table__).where(
            **{cls.__primary_key__: primary_key_value}))

    @classmethod
    def db_get(cls, db: DB, primary_key_value):
        get = db.execute(str(Sql().select(*cls.__mappings__.keys()).table(cls.__table__).where(
            **{cls.__primary_key__: primary_key_value})))
        if get:
            return cls(**db.fetchone())

    @classmethod
    def sql_find(cls, **kwargs):
        return str(Sql().select(*cls.__mappings__.keys()).table(cls.__table__).where(**kwargs))

    @classmethod
    def db_find(cls, db: DB, **kwargs):
        find = db.execute(str(Sql().select(*cls.__mappings__.keys()).table(cls.__table__).where(**kwargs)))
        if find:
            return [cls(**each) for each in db.fetchall()]

    @classmethod
    def sql_find_many(cls, *wheres, **kwargs):
        return str(Sql().select(*cls.__mappings__.keys()).table(cls.__table__).where(*wheres, **kwargs))

    @classmethod
    def db_find_many(cls, db: DB, *wheres, **kwargs):
        find = db.execute(str(Sql().select(*cls.__mappings__.keys()).table(cls.__table__).where(*wheres, **kwargs)))
        if find:
            return [cls(**each) for each in db.fetchall()]

    @classmethod
    def sql_list(cls, top=0, skip=0):
        return str(Sql().select(*cls.__mappings__.keys()).table(cls.__table__).limit(top, skip))

    @classmethod
    def db_list(cls, db: DB, top=0, skip=0):
        rows = db.execute(str(Sql().select(*cls.__mappings__.keys()).table(cls.__table__).limit(top, skip)))
        if rows:
            return [cls(**each) for each in db.fetchall()]


