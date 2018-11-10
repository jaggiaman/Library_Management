from datetime import timedelta as td
from datetime import datetime as dt
from flask import *
import Connection
import Search

app = Flask(__name__,
            static_folder="./static",
            template_folder="./templates")



def books_borrowed(cardid):
    connection = Connection.get_connection()
    cursor = connection.cursor()
    cursor.execute("use library")
    cursor.execute("select * from BOOK_LOANS where Card_id='{0}' and date_in is null".format(cardid))
    isbns = [x[0] for x in cursor.fetchall()]
    connection.commit()
    connection.close()
    count = len(isbns)
    return isbns


def valid_cardid(cardid):
    connection = Connection.get_connection()
    cursor = connection.cursor()
    cursor.execute("use library")
    cursor.execute("select * from BORROWER where Card_id='{0}'".format(cardid))
    ids = cursor.fetchall()
    count = len(ids)
    connection.close()
    return bool(count)

@app.route("/updatefines")
def update_fines():
    connection = Connection.get_connection()
    cursor = connection.cursor()
    cursor.execute("use library")
    cursor.execute("DELETE from FINES where Paid=0")
    cursor.execute("select * from BOOK_LOANS;")
    loans = cursor.fetchall()
    for loan in loans:
        lid, isbn, cid, dateout, datedue, datein = loan
        datedue = dt.strptime(str(datedue), "%Y%m%d")
        if datein == None:
            datein = dt.now()
        else:
            datein = dt.strptime(str(datein), '%Y%m%d')

        diff = datein - datedue
        diff = diff.days

        if diff > 0:
            fine = diff * .25
            query = "INSERT IGNORE INTO FINES (Loan_id, Fine_amt, Paid) values ('{}','{}','{}')".format(lid,
                                                                                                        fine,
                                                                                                        '0')
            cursor.execute(query)

    connection.commit()
    connection.close()
    return render_template("checkout_s.html",
                           msg="Updated")


def checkout_book(isbn, cardid):
    connection = Connection.get_connection()
    cursor = connection.cursor()
    cursor.execute("use library")
    dateout = dt.now()
    datedue = dateout + td(days=14)
    dateout = dateout.strftime("%Y%m%d")
    datedue = datedue.strftime("%Y%m%d")
    cursor.execute(
        """INSERT INTO BOOK_LOANS (Isbn, Card_id, Date_out, Due_date) values ('{}','{}','{}','{}')""".format(isbn,
                                                                                                             cardid,
                                                                                                             dateout,
                                                                                                             datedue))
    connection.commit()
    connection.close()


@app.route("/")
def main():
    return render_template("home.html")



@app.route("/results", methods=["GET", "POST"])
def results():
    form = request.form
    search = form.get('search')
    t = Search.search_books(search=search)
    if t:
        return render_template("results.html",
                               books=t)
    else:
        return render_template("checkout_s.html",
                               msg="No matching results found")


@app.route("/checkin", methods=["GET", "POST"])
def checkin():
    form = request.form
    isbn = form.get('isbn')
    datein = form.get('datein').replace('-', '')

    connection = Connection.get_connection()
    cursor = connection.cursor()
    cursor.execute("use library")
    cursor.execute("update BOOK_LOANS SET Date_in='{0}' where Isbn='{1}' and Date_in is NULL".format(datein, isbn))
    connection.commit()
    connection.close()
    update_fines()
    return render_template("checkout_s.html",
                           msg="Checkin successful!")


@app.route("/fetchfines")
def fetchfines():
    update_fines()
    connection = Connection.get_connection()
    cursor = connection.cursor()
    cursor.execute("use library")
    cursor.execute(
        "select B.Card_id, sum(F.Fine_amt) from BOOK_LOANS as B join (select Loan_id,Fine_amt from FINES where Paid=0) as F where F.Loan_id=B.Loan_id  group by B.Card_id;")
    fines = [(x, str(y) + " USD") for x, y in cursor.fetchall()]
    connection.commit()
    connection.close()
    if (len(fines) == 0):
        return render_template("checkout_s.html",
                               msg="All dues settled!")
    else:
        return render_template("fines.html",
                               fines=fines)


@app.route("/payfine", methods=["GET", "POST"])
def payfine():
    form = request.form
    cid = form.get('cid')
    connection = Connection.get_connection()
    cursor = connection.cursor()
    cursor.execute("use library")
    cursor.execute("select Loan_id from BOOK_LOANS where Card_id='{}' and Date_in is not NULL;".format(cid))
    loans = [x[0] for x in cursor.fetchall()]

    for loan in loans:
        query = "update FINES set Paid=1 where Loan_id='{}';".format(loan)
        cursor.execute(query)

    cursor.execute(
        "select b.Loan_id from BOOK_LOANS b join FINES f on b.loan_id = f.loan_id where b.Card_id='{}' and b.Date_in is NULL and f.paid = 0;".format(
            cid))
    loans = [x[0] for x in cursor.fetchall()]
    connection.commit()
    connection.close()
    if (not len(loans) == 0):
        return render_template("checkout_s.html",
                               msg="Payment updated only for books returned. The user with cardid " + cid + " has fines related to unreturned books.Books should be checked in first, to pay fine.")
    else:
        return render_template("checkout_s.html",
                               msg="Payment successful!")


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    form = request.form
    isbn = form.get('isbn')
    cardid = form.get('cardid')
    name = form.get('name')
    is_empty, t = Search.search_booksc(isbn=isbn, cardid=cardid, name=name)

    if ((not t) or is_empty):
        if is_empty:
            return render_template("checkout_f.html",
                                   msg="No input is entered,enter atleast one search criteria!")
        else:
            return render_template("checkout_s.html",
                                   msg="No matching results found")

    else:
        return render_template("results_checkin.html",
                               books=t)


@app.route("/checkoutstatus", methods=["GET", "POST"])
def checkoutstatus():
    form = request.form
    isbn = form.get('isbn')
    cardid = form.get('cardid')
    if not valid_cardid(cardid):
        msg = "Invalid card_id - " + cardid
        return render_template("checkout_f.html",
                               msg=msg)

    if len(books_borrowed(cardid)) >= 3:
        msg = "The card holder already checked out his quota of 3 books"
        return render_template("checkout_f.html",
                               msg=msg)
    book =Search.book_details([isbn])[0]
    if book["status"] == "Checked out":
        msg = "This book has already been checked out"
        return render_template("checkout_f.html",
                               msg=msg)

    checkout_book(isbn, cardid)

    return render_template("checkout_s.html",
                           msg="Checkout successful!")


def isnewssn(ssn):
    connection =Connection.get_connection()
    cursor = connection.cursor()
    cursor.execute("use library")
    cursor.execute("select * from BORROWER where ssn='{0}'".format(ssn))
    ids = cursor.fetchall()
    count = len(ids)
    connection.close()
    return not bool(count)


@app.route("/addborrower", methods=["GET", "POST"])
def addborrower():
    form = request.form
    name = form.get('name')
    ssn = form.get('ssn')
    phone = form.get('phone')
    street = form.get('street')
    city = form.get('city')
    state = form.get('state')
    address = street + ', ' + city + ', ' + state
    address = address[:65]
    name = name[:48]

    if not isnewssn(ssn):
        return render_template("checkout_f.html",
                               msg="SSN already exists in db")

    if len(phone) != len("2147483647"):
        return render_template("checkout_f.html",
                               msg="Invalid phone number.")

    connection = Connection.get_connection()
    cursor = connection.cursor()
    cursor.execute("use library")
    cursor.execute(
        """INSERT INTO BORROWER (Ssn,Bname,Address,Phone) values ('{}','{}','{}','{}')""".format(ssn, name, address,
                                                                                                 phone))
    connection.commit()
    connection.close()
    return render_template("checkout_s.html",
                           msg="Add successful!")


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)