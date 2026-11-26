"""Normalize persisted enum labels to the representation used by SQLAlchemy."""
from sqlalchemy import Enum, text


def normalize_legacy_enum_labels(engine, metadata):
    changed = 0
    quote = engine.dialect.identifier_preparer.quote
    with engine.begin() as connection:
        for table in metadata.sorted_tables:
            for column in table.columns:
                enum_type = column.type
                if not isinstance(enum_type, Enum) or not enum_type.enum_class:
                    continue
                table_name = quote(table.name)
                column_name = quote(column.name)
                # Identifiers come exclusively from the application's model metadata.
                for member in enum_type.enum_class:
                    if member.value == member.name:
                        continue
                    result = connection.execute(text(
                        f"UPDATE {table_name} SET {column_name} = :canonical "
                        f"WHERE CAST({column_name} AS TEXT) = :legacy"
                    ), {"canonical": member.name, "legacy": member.value})
                    changed += result.rowcount
    return changed

