# Migrations

Unfortunately because there is no [`alembic`](https://alembic.sqlalchemy.org/en/latest/) style system for migrations or
backfills for any database type, the scripts contained in the `scripts` directory will have to be run one at a time
from the point the CDP instance is at to the desired version. These migrations will follow a stripped down version of
`alembic`.

Each migration script will follow the naming convention:

    {version_a}-{version_b}_{short-description}

Where `version_a` and `version_b` are two versions you want to go up or down from one another.

So if trying to upgrade a CDP instance from 2.0.2 to 2.0.3, you would look for `2.0.2-2.0.3_hello-world...` for example.

Migrations may not be needed for every minor or patch version of CDP, so there may be a `2.0.2` and a `2.0.4` but no
`2.0.3` for example. In this case just run to the matching migration: `2.0.2-2.0.4_hello-world...`.

Every migration will have a `downgrade` and an `upgrade` function, the default will be to upgrade, you can specify which
one with a parameter (`--down` or `--up`).
