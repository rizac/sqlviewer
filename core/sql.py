'''
Created on Dec 2, 2016

@author: riccardo
'''
from sqlalchemy import create_engine, MetaData, Table, inspect
from sqlalchemy.orm import Session
from sqlalchemy.engine import reflection
from sqlalchemy.exc import NoSuchTableError, SQLAlchemyError
from collections import OrderedDict as odict
from sqlalchemy import desc
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.schema import CreateTable
from sqlalchemy.sql.expression import func
from sqlalchemy import inspect
from sqlalchemy.sql.sqltypes import NullType

currentdb = None

_cache_address = None

def set_chache_address(address):
    global _cache_address
    _cache_address = address
# drivers installed: psycopg2 (postgres)

# references:
# http://docs.sqlalchemy.org/en/latest/orm/extensions/automap.html
# http://stackoverflow.com/questions/22689895/list-of-databases-in-sqlalchemy
# http://docs.sqlalchemy.org/en/latest/core/reflection.html

class Db(odict):

    def __init__(self, dburl):
        super(Db, self).__init__()
        self.dburl = dburl
        self.engine = create_engine(dburl)
        self._session = None
        session = Session(self.engine)
        insp = inspect(self.engine)
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
        session.close()

    def close(self):
        if self._session:
            self._session.close()

    def __eq__(self, other):
        return isinstance(other, Db) and other.dburl == self.dburl

    def get_table(self, schema, tablename):
        tables = self.get(schema, None)
        if not tables:
            return None
        return tables.get(tablename, None)

    @property
    def session(self):
        if not self._session:
            self._session = Session(self.engine)
        return self._session

    def rollback(self):
        if self._session:
            self._session.rollback()

    def query(self, *args, **kwargs):
        return self.session.query(*args, **kwargs)


# dburi: specify a database uri
# Usually, it is a sqlite database, in which case just write the path to your local file
# PREPENED with 'sqlite:///' (e.g., 'sqlite:////home/my_folder/db.sqlite')
# Otherwise, the syntax is:
# dialect+driver://username:password@host:port/database
# (for info see: http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls)
# EG: 'postgresql://riccardo:@localhost/s2s'  # 'sqlite:///./mydb.sqlite_nov_2016'
#
def getdb(address):
    global currentdb
    if not currentdb or currentdb.dburl != address:
        if currentdb:
            currentdb.close()
        if not address:
            global _cache_address
            address = _cache_address
            set_chache_address(None)
        currentdb = None if not address else Db(address)
    return {} if not currentdb else currentdb


def get_table_count(table):
    global currentdb
    if not currentdb:
        return 0
    return currentdb.query(table).count()


def get_types(schemaname, tablename):
    conn = currentdb.engine.connect()

    res = conn.execute("""SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE
TABLE_SCHEMA = '%s' AND TABLE_NAME = '%s' """ % (schemaname, tablename))

    return{row[0]: row[1] for row in res}


def get_table(schemaname, tablename, order_colname=None, order_ascending=True, start_at=0,
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
                    return None

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
            query = currentdb.query(table).order_by(desc(orderbyfilt) if not order_ascending
                                                    else orderbyfilt)
        else:
            query = currentdb.query(table)

        res = query[start_at:start_at+num_results]
        ret = []
        if res:
            for dbrow in res:
                row = []
                for colname in colnames:
                    typ = types[colname]
                    val = getattr(dbrow, colname)
                    if val is None:
                        val = "NULL"
                    elif typ.python_type == bytes:
                        val = "[byte data: %.3f Kb]" % (0 if not val else len(val)/1000.0)
                    elif typ.python_type not in (int, float):
                        val = str(val)
                    row.append(val)
                ret.append(row)
#         ret.insert(0, [str(types[c]) for c in colnames])
#         ret.insert(0, colnames)
        return {'data': ret,
                'types': [str(types[c]) for c in colnames],
                'columns': colnames,
                'uc': currentdb.insp.get_unique_constraints(tablename, schemaname),
                 # 'pk': currentdb.insp.get_primary_keys(tablename, schemaname),
                'pk': currentdb.insp.get_pk_constraint(tablename, schemaname),
                'idx': currentdb.insp.get_indexes(tablename, schemaname),
                'fk': currentdb.insp.get_foreign_keys(tablename, schemaname), #
                'cc': currentdb.insp.get_check_constraints(tablename, schemaname),
                }
    except SQLAlchemyError as _:
        currentdb.rollback()
        raise
    # return last_result[last_result.keys()[0]][start_at:start_at+num_results]


# def get_python_type(type):
#     try:
#         return type.python_type
#     except NotImplementedError:  # if type is instanceof NullType. e.g. type polygon for postgresql
#         return None
# 
# 
# def type2str(type):
#     try:
#         return str(type)
#     except SQLAlchemyError:  # if type is instanceof NullType. e.g. type polygon for postgresql
#         return "UNRECOGNIZED TYPE"

# http://stackoverflow.com/questions/2128717/sqlalchemy-printing-raw-sql-from-create
# def get_create_raw_sql(engine, table):
#     return CreateTable(table.__table__).compile(engine)

# if __name__ == "__main__":
#     getdb('postgresql://riccardo:@localhost/test')
