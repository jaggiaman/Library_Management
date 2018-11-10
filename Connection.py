
import mysql.connector as mc
from datetime import timedelta as td
from datetime import datetime as dt
from flask import *


hostname = 'localhost'
username = 'root'
password = 'root'
def get_connection():
    connection = mc.connect(host=hostname,
                            user=username,
                            passwd=password,
                            charset='utf8',
                            use_unicode=True,
                            )
    return connection