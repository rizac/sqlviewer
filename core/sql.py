'''
Created on Dec 2, 2016

@author: riccardo
'''
from sqlalchemy import desc
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.schema import CreateTable
from collections import OrderedDict as odict
from sqlalchemy.sql.expression import func

Base = automap_base()

engine = None

tables = odict()

session = None


# dburi: specify a database uri
# Usually, it is a sqlite database, in which case just write the path to your local file
# PREPENED with 'sqlite:///' (e.g., 'sqlite:////home/my_folder/db.sqlite')
# Otherwise, the syntax is:
# dialect+driver://username:password@host:port/database
# (for info see: http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls)
# EG: 'postgresql://riccardo:@localhost/s2s'  # 'sqlite:///./mydb.sqlite_nov_2016'
#
def getdb(address):

    global engine, tables, session, last_result

    if hasattr(engine, 'url') and address == str(engine.url):
        return tables

    if session:
        session.close()
        session = None

    # engine, suppose it has two tables 'user' and 'address' set up
    engine = create_engine(address)

    # reflect the tables
    Base.prepare(engine, reflect=True)

    # iterate over tables:
    for tablename in Base.metadata.tables:
        table = getattr(Base.classes, tablename)
        # create_raw_sql = CreateTable(table.__table__).compile(engine)
        tables[tablename] = table

    return tables
    # mapped classes are now created with names by default
    # matching that of the table name.
#     User = Base.classes.user
#     Address = Base.classes.address
# 
#     session = Session(engine)
# 
#     # rudimentary relationships are produced
#     session.add(Address(email_address="foo@bar.com", user=User(name="foo")))
#     session.commit()

    # collection-based relationships are by default named
    # "<classname>_collection"
    # print (u1.address_collection)


def get_table(tablename, order_colname=None, order_ascending=True, start_at=0, num_results=20):
    global session, last_result
    if not tablename:
        return []
    cols = tables[tablename].__table__.columns
    colnames = cols.keys()
    types = [c.type for c in cols]
    if not session:
        session = Session(engine)
    if order_colname and order_colname in cols:
        col = cols[order_colname]
        typ = col.type
        orderbyfilt = func.length(col) if typ.python_type == bytes else col
        query = session.query(tables[tablename]).order_by(desc(orderbyfilt) if not order_ascending
                                                          else orderbyfilt)
    else:
        query = session.query(tables[tablename])

    res = query[start_at:start_at+num_results]
    ret = []
    if res:
        for dbrow in res:
            row = []
            for col, typ in zip(colnames, types):
                val = getattr(dbrow, col)
                if val is None:
                    val = "NULL"
                elif typ.python_type == bytes:
                    val = "[byte data: %.3f Kb]" % (0 if not val else len(val)/1000.0)
                elif typ.python_type not in (int, float):
                    val = str(val)
                row.append(val)
            ret.append(row)
    ret.insert(0, [str(t) for t in types])
    ret.insert(0, colnames)
    return ret
    # return last_result[last_result.keys()[0]][start_at:start_at+num_results]


def get_table_count(table):
    global session
    if not session:
        session = Session(engine)

    return session.query(table).count()


# http://stackoverflow.com/questions/2128717/sqlalchemy-printing-raw-sql-from-create
def get_create_raw_sql(engine, table):
    return CreateTable(table.__table__).compile(engine)

if __name__ == "__main__":
    pass
    # read_db('postgresql://riccardo:@localhost/s2s')
