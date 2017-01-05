'''
Class handling the inspoection of a SQL database via the SqlAlchemy `inspection` 
Created on Dec 2, 2016

@author: riccardo zaccarelli, PhD <riccardo.zaccarelli@gmail.com>

@license:

@copyright:
'''
import os
from collections import OrderedDict as odict
from copy import copy
from sqlalchemy import create_engine, MetaData, Table, inspect, desc
from sqlalchemy.orm import Session
from sqlalchemy.engine import reflection
from sqlalchemy.exc import NoSuchTableError, SQLAlchemyError, OperationalError, ProgrammingError
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.schema import CreateTable
from sqlalchemy.sql.expression import func, nullsfirst, asc, nullslast
from sqlalchemy.sql.sqltypes import NullType
from sqlalchemy.engine.url import make_url
from sqlalchemy.pool import NullPool
currentdb = None

# drivers installed: psycopg2 (postgres), and don't remember (mysql). sqlite3 is present by default

# references:
# http://docs.sqlalchemy.org/en/latest/orm/extensions/automap.html
# http://stackoverflow.com/questions/22689895/list-of-databases-in-sqlalchemy
# http://docs.sqlalchemy.org/en/latest/core/reflection.html


# copied from
# http://sqlalchemy-utils.readthedocs.io/en/latest/_modules/sqlalchemy_utils/functions/database.html#database_exists
def database_exists(url):
    """Check if a database exists.

    :param url: A SQLAlchemy engine URL.

    Performs backend-specific testing to quickly determine if a database
    exists on the server. ::

        database_exists('postgres://postgres@localhost/name')  #=> False
        create_database('postgres://postgres@localhost/name')
        database_exists('postgres://postgres@localhost/name')  #=> True

    Supports checking against a constructed URL as well. ::

        engine = create_engine('postgres://postgres@localhost/name')
        database_exists(engine.url)  #=> False
        create_database(engine.url)
        database_exists(engine.url)  #=> True

    """

    url = copy(make_url(url))
    database = url.database
    if url.drivername.startswith('postgresql'):
        url.database = 'template1'
    else:
        url.database = None

    engine = create_engine(url)

    if engine.dialect.name == 'postgresql':
        text = "SELECT 1 FROM pg_database WHERE datname='%s'" % database
        return bool(engine.execute(text).scalar())

    elif engine.dialect.name == 'mysql':
        text = ("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA "
                "WHERE SCHEMA_NAME = '%s'" % database)
        return bool(engine.execute(text).scalar())

    elif engine.dialect.name == 'sqlite':
        if database:
            return database == ':memory:' or os.path.exists(database)
        else:
            # The default SQLAlchemy database is in memory,
            # and :memory is not required, thus we should support that use-case
            return True

    else:
        text = 'SELECT 1'
        try:
            url.database = database
            engine = create_engine(url)
            engine.execute(text)
            return True

        except (ProgrammingError, OperationalError):
            return False


class Db(odict):
    """
    An OrderedDict reflecting an inspected SQL Database. Its key are the db schema names,
    mapped to the relative tables. The tables are in turn OrderedDict's where the keys are
    the table name and the values are `sqlalchemy.sql.schema.Table`s objects

    An Object of this class opens an sqlalchemy session which must be closed via the `.close()`
    method.

    Example:
    ```
        d = Db(address)
        d.keys() # -> schema names
        schema1 = d.keys()[0]
        tables = d[schema1] # -> OrderedDict
        tables.keys()  # -> table names
        tables.values()  # -> `sqlalchemy.sql.schema.Table`s objects
    ```
    """
    def __init__(self, dburl):
        """
        Initialized a new Db object with the given dburl. If the latter is empty or points to a
        non existent database, the object returned evaluates to False (as it has no keys). Otherwise
        this object keys are the schema names and the values are in turn `OrderedDict`s with table
        names (string) mapped to `sqlalchemy.sql.schema.Table`s objects (the schema tables)

        :param dburl: a database url. The syntax is:
        ```dialect+driver://username:password@host:port/database```
        (For sqlite databases, is` sqlite:///filepath`)
        For info see: http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls.
        Examples:
            Db('postgresql://me:@localhost/s2s')
            Db('sqlite:///./mydb.sqlite_nov_2016')
        """
        super(Db, self).__init__()
        self.dburl = dburl
        if hasattr(self, "_session") and self._session:
            self._session.close()  # disposes also the engine (see below create_engine)
        if not dburl or not database_exists(dburl):
            # it is necessary to check existence of db cause e.g., with sqlite the file
            # is created if does not exist (not tested with other dialects, presumably is not so
            # with postgresql)
            return
            # if we return, this class evaluates to False. so it's safe to write: "if currentdb:".
            # From
            # https://docs.python.org/3/reference/datamodel.html#object.__bool__
            # object.__bool__(self) is called to implement truth value testing and the built-in
            # operation bool(); should return False or True. **When this method is not defined,
            # __len__() is called**, if it is defined (it is, we are subclassing dict), and the
            # object
            # is considered true if its result is nonzero. If a class defines neither __len__() nor
            # __bool__(), all its instances are considered true.

        # make an engine which is disposed every time we close the session
        # see http://stackoverflow.com/questions/21738944/how-to-close-a-sqlalchemy-session
        self.engine = create_engine(dburl, poolclass=NullPool)
        self._session = Session(self.engine)
        session = self._session
        insp = inspect(self.engine)  # this line creates the db if doesnt exists with sqlite!
        self.insp = insp
        schemas = insp.get_schema_names()
        for schema in schemas:
            tables = odict()
            self[schema] = tables
            tablenames = insp.get_table_names(schema, order_by="foreign_key")
            for tname in tablenames:
                meta = MetaData(schema=schema)  # bind=engine, schema=dd)
                table = Table(tname, meta)
                try:
                    insp.reflecttable(table, None)
                    # do a query to check (FIXME: remove?)
                    session.query(table).first()
                    tables[tname] = table
                except (SQLAlchemyError) as _:
                    pass

    def __eq__(self, other):
        """
        equality implementation: compares the database urls. FIXME: is it used? is it consistent?
        """
        return isinstance(other, Db) and other.dburl == self.dburl

    def get_table(self, schema, tablename):
        """Returns the `sqlalchemy.sql.schema.Table` of the specified schema and with given name, or
        None if no such table.
        :param schema: the table schema (string)
        :param tablename: the table name (string)
        :return the table named `tablename` under the schema named `schema`, or None if no such
        table
        """
        tables = self.get(schema, None)
        if not tables:
            return None
        return tables.get(tablename, None)

    def query(self, *args, **kwargs):
        """Convenience method that returns a query object from the underlying session
        ```self.query(*a, **v) == self._session.query(*a, **v)```
        """
        return self._session.query(*args, **kwargs)

    def get_sql_create(self, tablename, schemaname):
        """Returns a string which represents the raw sql from create. Returns an empty string
        if no table was found.
        :param tablename: string, The tablename
        :param schemaname: string the table schema
        """
        # http://stackoverflow.com/questions/2128717/sqlalchemy-printing-raw-sql-from-create
        tbl = self.get_table(schemaname, tablename)
        return "" if tbl is None else CreateTable(tbl).compile(self.engine)

    def get_row_count(self, table):
        """returns the number of rows of the current table object, or 0 if the current
            such table.
            :param table: the `sqlalchemy.sql.schema.Table` object. If you have the schema name S
            and table name T:
            ```
                self.get_row_count(self.get_table(S, T))
            ```
            """
        if not self:
            return 0
        return currentdb.query(table).count()


def getdb(address):
    """Returns a Db object from the given address. The returned object can be iterated as it
    subclasses `OrderedDict`:
    ```
        d = getdb(address)
        d.keys() # -> schema names
        schema1 = d.keys()[0]
        tables = d[schema1] # -> OrderedDict
        tables.keys()  # -> table names
        tables.values()  # -> `sqlalchemy.sql.schema.Table`s objects
    ```
    :param address: a valid db address
    (see http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls)
    """
    global currentdb
    if not currentdb or currentdb.dburl != address:
        if currentdb:
            currentdb.close()
        currentdb = Db(address)
        if address and not currentdb:
            raise ValueError("database does not exist")
    return currentdb


def get_types(schemaname, tablename):
    """
    Returns the types of the gievn table with name `tablename` under the schema `schemaname`.
    The types are a list of column types"""
    conn = currentdb.engine.connect()

    res = conn.execute("""SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE
TABLE_SCHEMA = '%s' AND TABLE_NAME = '%s' """ % (schemaname, tablename))

    return{row[0]: row[1] for row in res}


def get_table_data(schemaname, tablename, order_colname=None, order_ascending=True, start_at=0,
                   num_results=20):
    global currentdb
    table = currentdb.get_table(schemaname, tablename) if currentdb else None
    if table is None:
        return []

    cols = table.columns
    # colnames is a iterable of quoted names (Python unicode/str subclass). see
    # http://docs.sqlalchemy.org/en/latest/core/sqlelement.html#sqlalchemy.sql.elements.quoted_name
    colnames = cols.keys()
    ctypes = [c.type for c in cols]

    # types might be NullType, which has three problems:
    # 1) the original db column type name is "lost",
    # 2) str(type) and 3) type.python_type (used below) raise exceptions.
    # Workaround:
    _coltypes_cache = None
    types = {}
    for typ, cname in zip(ctypes, colnames):
        if isinstance(typ, NullType):
            if _coltypes_cache is None:
                try:
                    _coltypes_cache = get_types(schemaname, tablename)
                except (SQLAlchemyError, KeyError, IndexError):
                    _coltypes_cache = {}
            typname = _coltypes_cache.get(cname, None)

            class MyNullType(object):
                def __init__(self, str_):
                    self._str = str_

                def __str__(self):
                    return self._str

                def python_type(self):
                    return None.__class__

            if typname:
                typ = MyNullType(typname)
            else:
                typ = MyNullType("UNRECOGNIZED TYPE")

        types[cname] = typ

    try:
        if order_colname and order_colname in cols:
            col = cols[order_colname]
            typ = types[order_colname]
            orderbyfilt = func.length(col) if typ.python_type == bytes else col
            orderbyfilt = asc(orderbyfilt) if order_ascending else desc(orderbyfilt)
            # sqlite does not offer "nullfirst" and "nulllast" functionality. See
            # https://bitbucket.org/zzzeek/sqlalchemy/issues/3231/nullsfirst-nullslast-broken-with-sqlite
            if currentdb.engine.name != 'sqlite':
                orderbyfilt = nullsfirst(orderbyfilt) if order_ascending else nullslast(orderbyfilt)
            query = currentdb.query(table).order_by(orderbyfilt)
        else:
            query = currentdb.query(table)

        res = query[start_at:start_at+num_results]
        ret = []
        # typezz = {}
        if res:
            for dbrow in res:
                row = []
                for colname in colnames:
                    typ = types[colname]
                    val = getattr(dbrow, colname)
                    value = {'val': val}
                    if typ.python_type == bytes and val is not None:
                        value['val'] = len(val) / 1000.0
                    elif typ.python_type == str and val is not None and "\n" in val:
                        value['newline'] = True
                    row.append(value)
                ret.append(row)
        return {'data': ret,
                'sql_create': str(currentdb.get_sql_create(tablename, schemaname)),
                'types': [str(types[c]) for c in colnames],
                'python_types': [types[c].python_type.__name__ for c in colnames],
                'columns': colnames,
                'uc': currentdb.insp.get_unique_constraints(tablename, schemaname),
                'pk': currentdb.insp.get_pk_constraint(tablename, schemaname),
                'idx': currentdb.insp.get_indexes(tablename, schemaname),
                'fk': currentdb.insp.get_foreign_keys(tablename, schemaname),
                'cc': currentdb.insp.get_check_constraints(tablename, schemaname),  # list of dicts
                }
    except SQLAlchemyError as _:
        # currentdb.rollback()
        raise

