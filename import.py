import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open('books.csv')
    reader=csv.reader(f)
    i=0
    for isbn,name,author,published in reader:
        i+=1
        if i>1:
            db.execute("INSERT INTO books (isbn,name,author,published) VALUES(:isbn,:name,:author,:published)",
            {'name':name,'isbn':isbn,'author':author,'published':int(published)})
    db.commit()

if __name__=='__main__':
    main()