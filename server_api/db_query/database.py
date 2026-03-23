"""
Database interaction API endpoints (MySQL, SQLite, PostgreSQL).
"""

import sqlite3
from flask import Blueprint, request, jsonify
import pymysql
#import psycopg2

api_database_bp = Blueprint("database", __name__)

@api_database_bp.route("/api/tools/mysql", methods=["POST"])
def mysql_query():
    data = request.json
    host = data.get("host")
    user = data.get("user")
    password = data.get("password", "")
    database = data.get("database")
    query = data.get("query")

    try:
        conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
        conn.close()
        return jsonify({"success": True, "result": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@api_database_bp.route("/api/tools/sqlite", methods=["POST"])
def sqlite_query():
    data = request.json
    db_path = data.get("db_path")
    query = data.get("query")
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(query)
        result = cur.fetchall()
        columns = [desc[0] for desc in cur.description] if cur.description else []
        cur.close()
        conn.close()
        return jsonify({"success": True, "columns": columns, "result": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# @api_database_bp.route("/api/tools/postgresql", methods=["POST"])
# def postgresql_query():
#     data = request.json
#     host = data.get("host")
#     user = data.get("user")
#     password = data.get("password", "")
#     database = data.get("database")
#     query = data.get("query")
#     try:
#         conn = psycopg2.connect(
#             host=host,
#             user=user,
#             password=password,
#             dbname=database
#         )
#         cur = conn.cursor()
#         cur.execute(query)
#         result = cur.fetchall()
#         columns = [desc[0] for desc in cur.description] if cur.description else []
#         cur.close()
#         conn.close()
#         return jsonify({"success": True, "columns": columns, "result": result})
#     except Exception as e:
#         return jsonify({"success": False, "error": str(e)})
