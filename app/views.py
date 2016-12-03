'''
Created on Dec 2, 2016

@author: riccardo
'''


from app import app
from core.sql import getdb, get_table_count, get_table
from flask.templating import render_template
from flask.globals import request
import json
from flask import jsonify


@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html")


@app.route('/query_db', methods=['POST'])
def query_db():
    data = json.loads(request.data.decode())
    address = data['url']
    if address == 'test':
        address = 'postgresql://riccardo:@localhost/s2s'
    data = getdb(address)
    ret = []
    for tablename, table in data.items():
        ret.append((tablename, get_table_count(table)))
    return jsonify(ret)


@app.route('/query_table', methods=['POST'])
def query_table():
    data = json.loads(request.data.decode())
    tablename = data['name']
    start_at = data.get('start_at', 0)
    num_results = data.get('num_results', None)
    order_colname = data.get('order_colname', None)
    order_ascending = data.get('order_ascending', True)
    data = get_table(tablename, order_colname, order_ascending, start_at, num_results)
#    ret = []
#     for tablename, table in data.items():
#         ret.append((tablename, get_table_count(table)))
    return jsonify(data)