"""Reconcile legacy database labels with the ORM's configured representation."""
from sqlalchemy import Enum, inspect, text
from sqlalchemy.dialects.postgresql import ENUM as PostgreSQLEnum


def normalize_legacy_enum_labels(engine, metadata):
    changed = 0
    quote = engine.dialect.identifier_preparer.quote
    with engine.begin() as connection:
        inspector = inspect(connection)
        for table in metadata.sorted_tables:
            actual_columns = {column["name"]: column for column in inspector.get_columns(table.name, schema=table.schema)}
            table_name = quote(table.name)
            if table.schema:
                table_name = quote(table.schema) + "." + table_name
            for column in table.columns:
                enum_type = column.type
                if not isinstance(enum_type, Enum) or not enum_type.enum_class:
                    continue
                column_name = quote(column.name)
                actual = actual_columns[column.name]
                physical_type = actual["type"]
                # The production bills columns are VARCHAR(20), not native enums.
                # Older local installations may still have the native enum columns.
                # Convert only those two legacy columns, preserving every value.
                if table.name == "bills" and column.name in ("status", "type") and not enum_type.native_enum:
                    if isinstance(physical_type, PostgreSQLEnum):
                        if actual.get("default") is not None:
                            raise RuntimeError("Legacy bills enum has a database default; review migration before conversion.")
                        connection.execute(text(
                            f"ALTER TABLE {table_name} ALTER COLUMN {column_name} "
                            f"TYPE VARCHAR(20) USING CAST({column_name} AS VARCHAR(20))"
                        ))
                        physical_type = None
                # SQLAlchemy normally stores member.name; values_callable can instead
                # explicitly store member.value. Use the actual configured labels.
                for member, canonical in zip(enum_type.enum_class, enum_type.enums):
                    for legacy in {member.name, member.value} - {canonical}:
                        if isinstance(physical_type, PostgreSQLEnum):
                            if legacy not in physical_type.enums:
                                continue
                            if canonical not in physical_type.enums:
                                raise RuntimeError(f"Missing canonical enum label for {table.name}.{column.name}")
                            type_name = quote(physical_type.name)
                            if physical_type.schema:
                                type_name = quote(physical_type.schema) + "." + type_name
                            assignment = f"CAST(:canonical AS {type_name})"
                        else:
                            assignment = ":canonical"
                        result = connection.execute(text(
                            f"UPDATE {table_name} SET {column_name} = {assignment} "
                            f"WHERE CAST({column_name} AS TEXT) = :legacy"
                        ), {"canonical": canonical, "legacy": legacy})
                        changed += result.rowcount
    return changed
