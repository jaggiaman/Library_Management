import mysql.connector as mc

hostname = 'localhost'
username = 'root'
password = 'root'

connection = mc.connect (host = hostname,
                         user = username,
                         passwd = password,
                         charset='utf8',
                         use_unicode=True,
                         )
cursor = connection.cursor()
cursor.execute("drop database if exists library")
cursor.execute("Create database library")
cursor.execute("use library")
cursor.execute("drop table if exists BOOK")
cursor.execute("""
create table BOOK(
  Isbn VARCHAR(14) NOT NULL,
  Title VARCHAR(250),
  PRIMARY KEY (Isbn)
)
""")
cursor.execute("drop table if exists AUTHORS")
cursor.execute("""
create table AUTHORS(
  Author_id INT(10) NOT NULL AUTO_INCREMENT,
  Name VARCHAR(50),
  PRIMARY KEY (Author_id),
  UNIQUE (Name)
)
""")
cursor.execute("drop table if exists BOOK_AUTHORS")
cursor.execute("""
create table BOOK_AUTHORS(
  Author_id INT(10),
  Isbn VARCHAR(14),
  PRIMARY KEY (Author_id, Isbn),
  FOREIGN KEY fk_auth_id(Author_id) REFERENCES AUTHORS(Author_id),
  FOREIGN KEY fk_auth_isbn(Isbn) REFERENCES BOOK(Isbn)
)
""")
cursor.execute("drop table if exists SEQ")
cursor.execute("""
create table SEQ(
   id INT(10) NOT NULL AUTO_INCREMENT PRIMARY KEY
)
""")

cursor.execute("drop table if exists BORROWER")
cursor.execute("""
create table BORROWER(
  Card_id VARCHAR(10) NOT NULL,
  Ssn VARCHAR(10),
  Bname Varchar(50),
  Address Varchar(70),
  Phone VARCHAR(12),
  PRIMARY KEY (Card_id),
  UNIQUE (Ssn)
)
""")

cursor.execute("""
    create trigger borrower_insert
    before insert on BORROWER
    for each row
    begin
    insert into SEQ values (null);
    set new.Card_id = concat('ID', lpad(last_insert_id(), 6, '0'));
    end
    """)

cursor.execute("drop table if exists BOOK_LOANS")
cursor.execute("""
create table BOOK_LOANS(
  Loan_id INT(10) NOT NULL AUTO_INCREMENT,
  Isbn VARCHAR(14),
  Card_id VARCHAR(10),
  Date_out INT(8),
  Due_date INT(8),
  Date_in INT(8),
  PRIMARY KEY (Loan_id),
  FOREIGN KEY fk_cid(Card_id) REFERENCES BORROWER(Card_id),
  FOREIGN KEY fk_bl_isbn(Isbn) REFERENCES BOOK(Isbn)
)
""")
cursor.execute("drop table if exists FINES")
cursor.execute("""
create table FINES(
  Loan_id INT(10) NOT NULL AUTO_INCREMENT,
  Fine_amt DOUBLE(8,2),
  Paid INT(2) DEFAULT 0,
  PRIMARY KEY (Loan_id),
  FOREIGN KEY fk_lid(Loan_id) REFERENCES BOOK_LOANS(Loan_id)
)
""")

row = cursor.fetchone()

books=[]
with open('books.csv', encoding= 'utf8') as f:
    lines = f.readlines()
    for line in lines[1:]:
        books.append(line.strip().split('\t'))

# Insert into book.csv
for book in books[:]:
    isbn=book[0]
    title=book[2].replace("'","\\'")
    authors=book[3].split(',')
    if "Thief" in title:
        print(""""INSERT INTO BOOK (Isbn, Title) values ('{}','{}')""".format(isbn,title))
    cursor.execute("""INSERT INTO BOOK (Isbn, Title) values ('{}','{}')""".format(isbn,title))

    authors=list(set(authors))
    #print authors
    for author in authors:
        author=author.replace("'","\\'").strip().replace(';','\\;')
        cursor.execute(u"""INSERT IGNORE INTO AUTHORS (Name) values (N'{}')""".format(author))
        print("""INSERT IGNORE INTO AUTHORS (Name) values (N'{}')""".format(author))
        cursor.execute(u"""select Author_id from AUTHORS where Name=N'{}'""".format(author))
        print("""select Author_id from AUTHORS where Name=N'{}'""".format(author))
        author_id = cursor.fetchone()[0]
        cursor.execute("""INSERT IGNORE INTO BOOK_AUTHORS (Author_id,Isbn) values ('{}','{}')""".format(author_id,isbn))
        print("""INSERT IGNORE INTO BOOK_AUTHORS (Author_id,Isbn) values ('{}','{}')""".format(author_id,isbn))


# Insert borrower.csv
borrowers=[]
with open('borrowers.csv', encoding= 'utf8') as f:
    lines = f.readlines()
    for line in lines[1:]:
        borrowers.append(line.strip().split(','))

for borrower in borrowers[:]:
    cid=(borrower[0])
    ssn=int(borrower[1].replace('-',''))
    name=borrower[2]+' '+borrower[3]
    address=borrower[5]+', '+borrower[6]+', '+borrower[7]
    phone=int(borrower[8].replace('-','').replace('(','').replace(')','').replace(' ',''))
    phone = str(phone)
    cursor.execute("""INSERT INTO BORROWER (Card_id,Ssn,Bname,Address,Phone) values ('{}','{}','{}','{}','{}')""".format(cid,ssn,name,address,phone))
    print("""INSERT INTO BORROWER (Card_id,Ssn,Bname,Address,Phone) values ('{}','{}','{}','{}','{}')""".format(cid,ssn,name,address,phone))


connection.commit()
print("done")

connection.close()
