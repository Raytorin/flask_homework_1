from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy import Column, Integer, String, DateTime, func

engine = create_engine('postgresql://postgres:postgres_pwd@postgredb:5432/netology_flask')
Session = sessionmaker(bind=engine)

Base = declarative_base(bind=engine)


class User(Base):

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String, nullable=False, unique=True, index=True)
    user_email = Column(String, nullable=False, unique=True)
    user_password = Column(String, nullable=False)
    creation_time = Column(DateTime, server_default=func.now())

    advertisement = relationship('Advertisement', cascade='all,delete', back_populates='user')


class Advertisement(Base):

    __tablename__ = 'advertisements'

    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    title = Column(String, nullable=False, unique=False)
    description = Column(String, nullable=False, unique=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship('User', back_populates='advertisement')


Base.metadata.create_all()

