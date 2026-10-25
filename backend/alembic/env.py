import os
from logging.config import fileConfig

from alembic import context
from geoalchemy2 import alembic_helpers
from sqlalchemy import create_engine, pool

from app.db.models import metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _database_url() -> str:
    url = config.attributes.get("database_url") or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return url


def _include_object(obj, name, type_, reflected, compare_to):  # type: ignore[no-untyped-def]
    # PostGIS-managed objects (spatial_ref_sys, tiger/topology schemas) are not ours.
    if type_ == "table" and name in {"spatial_ref_sys"}:
        return False
    return alembic_helpers.include_object(obj, name, type_, reflected, compare_to)


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        target_metadata=metadata,
        literal_binds=True,
        include_object=_include_object,
        render_item=alembic_helpers.render_item,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(_database_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=metadata,
            include_object=_include_object,
            process_revision_directives=alembic_helpers.writer,
            render_item=alembic_helpers.render_item,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
