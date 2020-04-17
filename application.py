import os
import csv

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
    return render_template('home.html',title='Home')

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


@app.route('/userprofile')
def userprofile():
    #checking if user is already logged in
    if 'username_login' not in session:
        return redirect(url_for('index'))
    #importing user data from database to show in profile.
    user_credentials_list=db.execute('SELECT * FROM users WHERE username=:username_login',{'username_login':session['username_login']})
    for user_credentials in user_credentials_list:
        name=user_credentials.name
        email=user_credentials.email
        username=user_credentials.username
    return render_template('userprofile.html',name=name,username=username,email=email)


@app.route('/loggedout')
def loggedout():
    #delete session for the user
    session.pop('username_login')
    return render_template('loggedout.html')