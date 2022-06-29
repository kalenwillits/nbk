from uuid import UUID


def resolve_foreign_key(model_name: str, foreign_key: UUID, db):
    return db.get(model_name, foreign_key)._to_dict()


