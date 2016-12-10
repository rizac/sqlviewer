'''
Created on Dec 2, 2016

@author: riccardo
'''


from app import app
from core.sql import getdb, get_table_count, get_table
from flask.templating import render_template
from flask.globals import request
import json
from flask import jsonify, g as flask_g


@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html")


@app.route('/query_db', methods=['POST'])
def query_db():
    data = json.loads(request.data.decode())
    address = data['url']
    data = getdb(address)
    ret = []
    for schemaname, tables in data.items():
        tbls = []
        for tablename in tables:
            tbls.append((tablename, get_table_count(tables[tablename])))
        ret.append([schemaname, tbls])
    return jsonify({'dburl': data.dburl, 'schemas': ret})


@app.route('/query_table', methods=['POST'])
def query_table():
    data = json.loads(request.data.decode())
    schemaname = data['schema_name']
    tablename = data['table_name']
    start_row = data.get('start_row', 0)
    num_results = data.get('num_results', None)
    order_colname = data.get('order_colname', None)
    order_ascending = data.get('order_ascending', True)
    data = get_table(schemaname, tablename, order_colname, order_ascending, start_row, num_results)
#    ret = []
#     for tablename, table in data.items():
#         ret.append((tablename, get_table_count(table)))
    return jsonify(data)


@app.errorhandler(Exception)
def exception_handler(error):
    response = jsonify({'message': "%s: %s" % (str(error.__class__.__name__), str(error))})
    response.status_code = 500
    return response
    # return "!!!!" + repr(error)
