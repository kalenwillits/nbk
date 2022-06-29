from uuid import uuid4
import pandas as pd
from .utils import to_snake, Schema


class Model:
    def __init__(self, **kwargs):
        self._schema = Schema(self)
        self._name = self.__class__.__name__
        self.__dict__.update(self._schema.default_values())
        for field in self._schema.fields():
            # If the field is a property and does not have a setter, skip it.
            class_value = vars(self.__class__).get(field)
            if isinstance(class_value, property) and class_value.fset is None:
                continue

            if value := kwargs.get(field):
                setattr(self, field, value)

    @property
    def pk(self) -> str:
        if not hasattr(self, '_pk'):
            self._pk = str(uuid4())

        return self._pk

    @pk.setter
    def pk(self, value):
        self._pk = value

    @property
    def _snake_name(self) -> str:
        return to_snake(self._name)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def _to_dict(self) -> dict:
        instance_values = {}
        for field in self._schema.fields():
            instance_values[field] = self[field]

        return instance_values

    def _to_df(self) -> pd.DataFrame:
        df = pd.DataFrame([self._to_dict()])
        return df

    def __repr__(self):
        df = self._to_df().transpose()
        df.columns = [self._name]
        return df.to_string()

    def __str__(self):
        return self._name


class ModelManager:
    def __init__(self, *models):
        self.__models__ = models
        self._model_names = [model.__name__ for model in models]
        for model in models:
            setattr(self, model.__name__, model)

    def __iter__(self):
        for model in self.__models__:
            yield model

    def __contains__(self, other):
        if type(other) is str:
            return other in self._model_names
        return other in self.__models__

    def __getitem__(self, key_or_index):
        if isinstance(key_or_index, int):
            return self.__models__[key_or_index]
        else:
            return getattr(self, key_or_index)
