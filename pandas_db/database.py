from uuid import uuid4
import pandas as pd
import os

from .utils import (
    assert_datatypes,
    column_filters,
    handle_limit,
    handle_sort,
    hydrate,
    is_datetime,
    parse_datatype,
)

from .models import ModelManager, Model

pd.options.mode.chained_assignment = None


class Database:
    def __init__(self, models: ModelManager = ModelManager(), path: str = 'data/', archive_path: str = 'archive/',
                 archive_limit: int = 0):
        '''
        Simple in-memory database built with pandas to store data in ram.
        This is a "Pandas Database".
        '''
        self.models = models
        # TODO ensure this is OS compatible.
        self.path = path
        self.archive_path = archive_path
        self.archive_limit = archive_limit

        self.load()

    def __setitem__(self, key, value):
            self.__dict__[key] = value

    def __getitem__(self, key):
        return self.__dict__[key]

    def has(self, model_name: str) -> bool:
        if hasattr(self, model_name):
            if isinstance(self[model_name], pd.DataFrame):
                return True

        return False

    def create(self, model_name, **kwargs) -> Model:
        instance = self.models[model_name](**kwargs)
        datatypes = instance._schema.datatypes()
        for key, value in kwargs.items():
            assert_datatypes(self, datatypes[key], value, key)

        df = instance._to_df()

        if self.has(model_name):
            self[model_name] = self[model_name].append(df, ignore_index=True)
        else:
            self[model_name] = df
        return instance

    def query(self, model_name: str, **kwargs) -> pd.DataFrame:
        if self.has(model_name):
            df = self[model_name]

            kwargs, df = handle_sort(kwargs, df)
            kwargs, df = handle_limit(kwargs, df)

            for field, value in kwargs.items():

                if '__' in field:

                    column, operator = field.split('__', 1)

                    # FK lookup.
                    if (foreign_model := self.models[model_name]()._schema.datatypes().get(column)) in self.models:
                        assert (
                            operator not in column_filters.keys()
                        ), f'Unspecified field in foreign key lookup. Did you mean "{column}__pk__{operator}=..."?'

                        fk_series = self.query(foreign_model.__name__, **{operator: value}).pk
                        temp_column_suffix = f'_{uuid4()}'
                        df = pd.merge(left=df, right=fk_series, how='right', left_on=column, right_on='pk',
                                      suffixes=(None, temp_column_suffix))
                        df.drop(f'pk{temp_column_suffix}', inplace=True, axis=1)

                    # Special filters
                    else:
                        df = column_filters[operator](df, column, value)

                    if is_datetime(value):
                        df[column] = df[column].dt.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    df = df[df[field] == value]
            return df
        else:
            return pd.DataFrame()

    def get(self, model_name, *args, **kwargs):
        # If a pk has been given, find model by that pk
        if args:
            pk = args[0]
            df = self.query(model_name, pk=pk)
            if not df.empty:
                return self.models[model_name](**df.iloc[0].to_dict())

        # If not, find it by kwargs
        else:
            df = self.query(model_name, **kwargs)
            if (num_models := df.shape[0]) == 1:
                return self.models[model_name](**df.iloc[0].to_dict())
            elif num_models == 0:
                return None
            else:
                raise ValueError(f'{num_models} {model_name} models found.')

    def update(self, model_name: str, query: pd.DataFrame, **kwargs):
        if query.empty:
            return query

        datatypes = self.models[model_name]()._schema.datatypes()

        for field, value in kwargs.items():
            assert_datatypes(self, datatypes[field], value, field)
            self[model_name][field].iloc[query.index] = [value]

        return self[model_name].iloc[query.index]

    def drop(self, model_name: str, query: pd.DataFrame, cascade: list[str, ...] = []) -> pd.DataFrame:
        '''
        Deletes entries from the databse based on the input query's index.
        :param cascade: list of strings representing fk fields to cascade the drop method to.
        '''
        if query.empty:
            return

        if cascade:
            datatypes = self.models[model_name]()._schema.datatypes()
            nested_field = None
            for field in cascade:
                if '__' in field:
                    field, nested_field = field.split('__', 1)
                if datatypes[field] in self.models:
                    foreign_model_name = datatypes[field].__name__
                    foreign_model_pk = query[field].iloc[0]
                    if not (foreign_query := self.query(foreign_model_name, pk=foreign_model_pk)).empty:
                        if nested_field:
                            self.drop(foreign_model_name, foreign_query, cascade=[nested_field])
                        else:
                            self.drop(foreign_model_name, foreign_query)

        self[model_name].drop(index=query.index, inplace=True)

    def archive(self, model_name: str, query: pd.DataFrame, cascade=False):
        assert self.models[model_name], f'Uknown model "{model_name}"'

        if self.archive_limit > 0:
            query = query.tail(self.archive_limit)

        if not query.empty:
            json_file_path = os.path.join(self.archive_path, f'{model_name}.json')
            query.to_json(json_file_path, orient='records', indent=4)
            self.drop(model_name, '')


    def hydrate(self, model_name: str, **kwargs):
        return hydrate(self, model_name, self.query(model_name, **kwargs))

    def init_table(self, model):
        self[model.__name__] = model()._to_df().iloc[0:0]

    def audit_tables(self):
        for model in self.models:
            if not self.has(model.__name__):
                self.init_table(model)

    def audit_nulls(self):
        for model in self.models:
            instance = model()
            for field, datatype in instance._schema.datatypes().items():
                nulls_index = self[instance._name][field].isnull()
                if nulls_index.sum() and datatype not in self.models:
                    self[instance._name].loc[nulls_index, field] = pd.Series([datatype()] * nulls_index.sum())

    def init_datatypes(self, model):
        instance = model()
        for field, datatype, default_value in instance._schema.items():
            self[instance._name][field].apply(lambda value: parse_datatype(self, datatype, value))

    def audit_datatypes(self):
        for model in self.models:
            self.init_datatypes(model)

    def init_fields(self, model):
        instance = model()
        if self.has(instance._name):
            loaded_fields = set(self[instance._name].columns)
        else:
            loaded_fields = set()
        model_fields = set([field for field in instance._schema.fields()])
        new_fields = model_fields.difference(loaded_fields)
        removed_fields = loaded_fields.difference(model_fields)

        for field in new_fields:
            self[instance._name][field] = None

        for field in removed_fields:
            self[instance._name] = self[instance._name].drop(field, axis=1)

    def audit_fields(self):
        for model in self.models:
            self.init_fields(model)

    def migrate(self):
        self.audit_tables()
        self.audit_fields()
        self.audit_nulls()
        self.audit_datatypes()

    def save(self):
        for model in self.models:
            json_file_path = os.path.join(self.path, f'{model.__name__}.json')
            self[model.__name__].to_json(json_file_path, orient='records', indent=4)

    def load(self):
        for model in self.models:
            json_file_path = os.path.join(self.path, f'{model.__name__}.json')
            if os.path.isfile(json_file_path):
                datatypes = model()._schema.datatypes()
                self[model.__name__] = pd.read_json(json_file_path, orient='records', convert_dates=False,
                                                    dtype=datatypes)
