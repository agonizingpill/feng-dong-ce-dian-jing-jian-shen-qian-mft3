import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
url=os.environ['DATABASE_URL']
# MySQL 用 READ COMMITTED 保证等锁后读到最新提交；SQLite（本地开发/测试）不支持该级别
opts={'pool_pre_ping':True}|({} if url.startswith('sqlite') else {'isolation_level':'READ COMMITTED'})
engine = create_engine(url, **opts)
Session = sessionmaker(engine, expire_on_commit=False)
class Base(DeclarativeBase): pass
def db_session():
    with Session() as s:
        yield s
