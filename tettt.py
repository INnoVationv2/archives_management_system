from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pymysql

da = 7
with pymysql.connect(host='localhost', user='root', password='681201', port=3306, database='profiling_system') as conn:
    conn.execute("update archives set name='dd' where id=" + str(da))
