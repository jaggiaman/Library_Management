import Connection

def search_books(search=False):
    connection = Connection.get_connection()
    cursor = connection.cursor()
    cursor.execute("use library")
    new_search = search.replace("'", "")
    lower_search = new_search.lower()
    words = lower_search.split()
    new_search_words = []
    prev_word = ""
    remove_word = ""
    is_isbn = False
    is_first_word = False
    is_preposition = False
    isbns_search = []
    list_of_words = ["what", "into", "other", "know", "this", "it", "be", "to", "for", "by", "at", "who", "and", "they",
                     "how", "the", "why", "when", "in", "of", "on", "or", "up", "a", "i", "here", "there", "where",
                     "now", "an", "if"]
    new_word = ""

    for current_word in words:
        if (len(current_word) == 10 and any(char.isdigit() for char in current_word)):
            is_first_word = False
            is_preposition = False
            new_word = current_word
            is_isbn = True
            isbns_search.append(new_word)
        elif ((current_word in list_of_words) and not (any(char.isdigit() for char in current_word))):
            is_preposition = True
            if (prev_word == "" and not (len(words) == 1)):
                is_first_word = True
                remove_word = current_word
                new_word = current_word
            else:
                is_first_word = False
                new_word = prev_word + " " + current_word
                remove_word = prev_word
        else:
            if (is_preposition == True):
                new_word = prev_word + " " + current_word
                remove_word = prev_word
            else:
                new_word = current_word
            is_first_word = False
            is_preposition = False

        prev_word = new_word

        if (not is_first_word):
            new_search_words.append(new_word)

        if remove_word in new_search_words:
            new_search_words.remove(remove_word)

    statement = ""

    if (is_isbn == True):
        new_search_words = list(isbns_search)

    for i in new_search_words:
        statement = statement + " select b.isbn from book b join book_authors ba on ba.isbn=b.isbn join authors a on a.author_id=ba.author_id where b.isbn like '%{0}%' or a.name like '%{0}%' or b.title like '%{0}%' UNION".format(
            i)

    statement = statement.rsplit(' ', 1)[0]
    query = statement + ";"

    cursor.execute(query)
    results = cursor.fetchall()
    connection.close()
    isbns = [x[0] for x in results]
    no_duplicate_isbns = list(set(isbns))
    books = book_details(no_duplicate_isbns)

    return books


def book_details(isbns):
    connection = Connection.get_connection()
    cursor = connection.cursor()
    cursor.execute("use library")
    books = []
    for isbn in isbns:
        cursor.execute("select Title from BOOK where Isbn='{0}'".format(isbn))
        title = cursor.fetchall()[0][0]
        cursor.execute(
            "select Name from AUTHORS AS A join (select Author_id from BOOK_AUTHORS as BA where isbn='{0}') as x on x.Author_id=A.Author_id;".format(
                isbn))
        authors = [x[0] for x in cursor.fetchall()]
        authors = ",".join(authors)

        cursor.execute("select Isbn from BOOK_LOANS where Isbn='{0}' and Date_in is NULL;".format(isbn))
        count = len(cursor.fetchall())
        if count:
            cursor.execute("select Date_out from BOOK_LOANS where Isbn='{0}' and Date_in is NULL".format(isbn))
            dateout = cursor.fetchall()[0][0]
            cursor.execute("select Due_date from BOOK_LOANS where Isbn='{0}' and Date_in is NULL".format(isbn))
            datedue = cursor.fetchall()[0][0]
            cursor.execute(
                "select Bname from BORROWER as B join (select Card_id from BOOK_LOANS where Isbn='{0}' and Date_in is NULL) as S on B.Card_id=S.Card_id;".format(
                    isbn))
            borrower = cursor.fetchall()[0][0]

        meta = {
            "isbn": isbn,
            "title": title,
            "authors": authors,
            "status": "Checked out" if count else "Available",
            "dateout": dateout if count else "",
            "datedue": datedue if count else "",
            "borrower": borrower if count else ""
        }

        books.append(meta)

    connection.close()
    return books


def search_booksc(isbn=False, cardid=False, name=False):
    connection = Connection.get_connection()
    cursor = connection.cursor()
    cursor.execute("use library")
    query = ""
    books = []
    if not (isbn or cardid or name):
        return True, books
    else:
        if isbn:
            query = "select Isbn from BOOK_LOANS where Isbn='{0}' and Date_in is NULL".format(isbn)
        elif cardid:
            query = "select Isbn from BOOK_LOANS where Card_id='{0}' and Date_in is NULL".format(cardid)
        elif name:
            query = "select Isbn from BOOK_LOANS B join(select Card_id from BORROWER where Bname like '%{0}%') as A where A.Card_id=B.Card_id and Date_in is NULL;".format(
                name)
        cursor.execute(query)
        results = cursor.fetchall()
        connection.close()
        isbns = [x[0] for x in results]
        books = book_details(isbns)
        return False, books