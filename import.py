import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open('books.csv')
    reader=csv.reader(f)
    for isbn,name,author,published in reader:
        db.execute("INSERT INTO books (isbn,name,author,published) VALUES(:isbn,:name,:author,:published)",
        {'name':name,'isbn':isbn,'author':author,'published':published})
    db.commit()


if __name__=='__main__':
    main()