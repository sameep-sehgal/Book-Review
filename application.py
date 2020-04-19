import os
import csv
import requests

from flask import Flask, session,render_template,request,redirect,url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker



app = Flask(__name__)



# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def index():
    #checking if user is already logged in
    if 'username_login' in session:
        return redirect(url_for('home',username=session['username_login']))
    return render_template('index.html',title='Book Pile')

@app.route('/home/<username>')
def home(username):
    #checking if user is already logged in
    if 'username_login' not in session:
        return redirect(url_for('index'))
    #extracting search input
    search_input=request.args.get('search_input')
    if search_input is not None:
        #when search input is not empty
        books=db.execute("SELECT * FROM books WHERE isbn LIKE '%"+search_input+"%' OR name LIKE '%"+search_input+"%' OR author LIKE '%"+search_input+"%' LIMIT 100")
        books_count=books.rowcount  #keep the count of number of books after search 
    else:
        #when search input is empty displaying all books
        books=db.execute("SELECT * FROM books WHERE isbn LIKE '%"+''+"%' OR name LIKE '%"+''+"%' OR author LIKE '%"+''+"%' LIMIT 100")
        books_count=books.rowcount #keep the count of number of books after search
    return render_template('home.html',title='Home',books=books,books_count=books_count)


@app.route('/book/<username>/<book_id>/',methods=['GET','POST'])
def bookpage(username,book_id):
    #checking if user is already logged in
    if 'username_login' not in session:
        return redirect(url_for('index'))
    #extracting book data from database
    book_details=db.execute("SELECT * FROM books WHERE id=:book_id",{'book_id':book_id})
    #checking if user has already reviewed the book
    if db.execute("SELECT * FROM reviews WHERE username=:username AND book_id=:book_id",{'username':session['username_login'],'book_id':book_id}).rowcount==0:
        review_entered = False
        if request.method=='POST':
            #extracting review and rating user entered
            rating=request.form.get('rating')
            review=request.form.get('review')
            if review is not None:
                #saving the review in reviews table in database
                db.execute('INSERT INTO reviews (username,book_id,review,rating) VALUES (:username,:book_id,:review,:rating)',{'username':session['username_login'],'book_id':book_id,'review':review,'rating':int(rating)})
                db.commit()
    else:
        review_entered = True
    
    #extracting reviews for requested book
    user_reviews=db.execute('SELECT * FROM reviews WHERE book_id=:book_id',{'book_id':book_id})
    return render_template('bookpage.html',book_details=book_details,user_reviews=user_reviews,review_entered=review_entered)


@app.route('/signup')
def signup():
    #checking if user is already logged in
    if 'username_login' in session:
        return redirect(url_for('home',username=session['username_login']))
    return render_template('signup.html',title='Sign Up')
    

@app.route('/result',methods=['GET','POST'])
def result():
    #Getting sign up form data
    name = request.form.get("name")
    name=name.capitalize()
    username_signup = request.form.get("username_signup")
    email = request.form.get('email')
    password_signup = request.form.get('password_signup')
    successful_signup = False #To check whether signup is successful or not(Avoid repeated emails and username)
    unique_email=False
    unique_username=False
     
    # checking if username already exists 
    if db.execute("SELECT * FROM users WHERE username=:username_signup",{'username_signup':username_signup}).rowcount == 0: 
        # username entered is unique
        unique_username = True
        #Checking if email already exists

        if db.execute("SELECT * FROM users WHERE email=:email",{'email':email}).rowcount == 0:
            # email entered is also unique
            unique_email=True
            successful_signup = True
            # updating database with user info
            db.execute("INSERT INTO users (name,username,email,password) VALUES (:name,:username_signup,:email,:password_signup)",{'name':name,
                                                                                'username_signup':username_signup,
                                                                                'email':email,
                                                                                'password_signup':password_signup})
            #Commiting changes to database on Heroku
            db.commit()
        
    else:
        #username is not unique. Now checking uniqueness of email to display valid error message.
        if db.execute("SELECT * FROM users WHERE email=:email",{'email':email}).rowcount == 0:
            unique_email=True

    return render_template('result.html',title='Result',successful_signup=successful_signup,
                            name=name,username_signup=username_signup,unique_email=unique_email,
                            unique_username=unique_username)


@app.route('/loginagain',methods=['POST'])
def loginagain():
    #checking if user is already logged in
    if 'username_login' in session:
        return redirect(url_for('home',username=session['username_login']))
    #getting data entered by user at login page.
    username_login = request.form.get("username_login")
    password_login = request.form.get("password_login")

    if db.execute('SELECT username,password FROM users WHERE username=:username_login AND password=:password_login',{'username_login':username_login,'password_login':password_login}).rowcount == 1:
        #login successful. assigning username to session object.
        session['username_login']=username_login
        return redirect(url_for('home',username=session['username_login']))

    return render_template('loginagain.html')


@app.route('/<username>')
def userprofile(username):
    #checking if user is already logged in
    if 'username_login' not in session:
        return redirect(url_for('index'))
    #importing user data from database to show in profile.
    user_credentials_list=db.execute('SELECT * FROM users WHERE username=:username_login',{'username_login':session['username_login']})
    for user_credentials in user_credentials_list:
        name=user_credentials.name
        email=user_credentials.email
        username=user_credentials.username
    return render_template('userprofile.html',name=name,username=username,email=email,title='Profile: '+name)


@app.route('/loggedout')
def loggedout():
    #delete session for the user
    session.pop('username_login')
    return render_template('loggedout.html')