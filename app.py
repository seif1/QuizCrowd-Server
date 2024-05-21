from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin, fresh_login_required

from datetime import datetime
import json
import uuid
import bcrypt
import random

salt = bcrypt.gensalt()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'INSERT_SECRET_HERE'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
db = SQLAlchemy(app)

def randomInt():
    return random.randint(-2^(31), (2^(31))-1)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    changeable_id = db.Column(db.Integer, unique=True, default=randomInt)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_name = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    created_quizes = db.relationship('Quiz', backref='user')
    achieved_scores = db.relationship('Score', backref='user')
    given_ratings = db.relationship('Rating', backref='user')
    given_suggestions = db.relationship('Suggestion', backref='user')

    def get_id(self):
        return str(self.changeable_id)
    def get_db_id(self):
        return self.id

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    json = db.Column(db.String, nullable=False)
    ratings = db.relationship('Rating', backref='quiz')
    suggestions = db.relationship('Suggestion', backref='quiz')
    scores = db.relationship('Score', backref='quiz')

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    answer_json = db.Column(db.String, nullable=False)

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)

class Suggestion(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    suggestion = db.Column(db.String, nullable=False)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

# Sets up the login manager for the user for Flask Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(changeable_id=user_id).first()

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/list')
def list_quiz():
    # Get the quiz data
    raw_quizes = Quiz.query.order_by(Quiz.date_created).all()

    quizes=[]

    # Extract the data from json in database
    for quiz in raw_quizes:
        quiz_object = json.loads(quiz.json)
        quiz_object["id"] = quiz.id

        user_obj = User.query.filter_by(id=quiz.creator_id).first()
        quiz_object["creator"] = user_obj.user_name
        quiz_object["creator_db_id"] = user_obj.get_db_id()

        quiz_object["summed_scores"] = 0
        quiz_object["times_taken"] = 0
        quiz_object["summed_ratings"] = 0
        quiz_object["times_rated"] = 0

        for score in quiz.scores:
            quiz_object["summed_scores"] += score.score
            quiz_object["times_taken"] += 1

        for rating in quiz.ratings:
            quiz_object["summed_ratings"] += rating.rating
            quiz_object["times_rated"] += 1

        quizes.append(quiz_object)
        
    return render_template('quiz_list.html', quizes=quizes)

@app.route('/quiz_delete/<int:id>')
@login_required
def quiz_delete(id):
    quiz_to_delete = Quiz.query.get_or_404(id)

    if (current_user.get_db_id() == quiz_to_delete.creator_id):
        try:
            Quiz.query.filter_by(id=id).delete()
            #Score.query.filter_by(quiz_id=id).delete()
            #Rating.query.filter_by(quiz_id=id).delete()
            #db.session.delete(quiz_to_delete)
            db.session.commit()
            return redirect('/profile/'+str(current_user.get_db_id()))
        except:
            return 'There was a problem deleting that task'
    else:
        return "Not Authorized", 401

@app.route('/create', methods=['POST','GET'])
@login_required
def create_quiz():
    if request.method == 'GET':
        return render_template('create.html')
    else:
        # Try to read the data from the request
        try:
            json.loads(request.data)
        except:
            return 422
        
        # Create quiz object from json data
        new_quiz = Quiz(json=request.data, creator_id=current_user.get_db_id())
        try:
            db.session.add(new_quiz)
            db.session.commit()
            return redirect('/list')
        except:
            return 'There was an issue adding the task.'

@app.route('/quiz/<int:quiz_id>', methods=["GET", "POST"])
@login_required
def quiz_load(quiz_id):
    if request.method == 'GET':
        # If the user has a score, show them their existing score instead
        existing_score = Score.query.filter_by(user_id=current_user.get_db_id()).filter_by(quiz_id=quiz_id).first()
        if existing_score:
            flash("You have already taken, and rated this quiz, here are your results.")
            return render_template("quiz_results.html", quiz=json.loads(existing_score.answer_json))

        # Load quiz from id
        quiz_to_load = Quiz.query.get_or_404(quiz_id)

        # ensure the object has id to be able to submit
        quiz_object = json.loads(quiz_to_load.json)
        quiz_object["id"] = quiz_to_load.id
        
        user_obj = User.query.filter_by(id=quiz_to_load.creator_id).first()
        quiz_object["creator"] = user_obj.user_name
        quiz_object["creator_db_id"] = user_obj.get_db_id()

        return render_template('quiz_take.html', quiz=quiz_object)
    else:
        # If the user has a score, show them their existing score instead
        existing_score = Rating.query.filter_by(user_id=current_user.get_db_id()).filter_by(quiz_id=quiz_id).first()
        if existing_score:
            flash("You have already taken, and rated this quiz, here are your results.")
            return render_template("quiz_results.html", quiz=json.loads(existing_score.answer_json))

        # Load data from the database
        answers = request.form
        quiz =  json.loads(Quiz.query.filter_by(id=quiz_id).first().json)

        print(quiz)

        wrong_questions = 0

        # Iterate over each question, and get the list of answers they gave for each (to handle checkbox)
        for question in quiz["questions"]:
            marked = False

            # Gets the list of proper answers
            response_for_question = answers.getlist(question)

            for answer in response_for_question:
                quiz['questions'][question]["answers"][answer]["value"] = True

                if quiz['questions'][question]["answers"][answer]["answer"] == True:
                    quiz['questions'][question]["answers"][answer]["is_correct"] = True
                else:
                    quiz['questions'][question]["answers"][answer]["is_correct"] = False

            for check_answer in quiz['questions'][question]["answers"]:
                try:
                    value = quiz['questions'][question]["answers"][check_answer]["value"]
                except:
                    value = False
                
                if value != quiz['questions'][question]["answers"][check_answer]["answer"]:
                    if marked == False:
                        marked = True
                        wrong_questions+=1
                            
        quiz["max_score"] = len(quiz['questions'])
        quiz["score_value"] =  quiz["max_score"] - wrong_questions

            #for answer in response_for_question:
            #    answer_object = quiz['questions'][question]["answers"][answer]
            #    if answer_object["answer"] == True:
            #        correct_answers += 1


        return render_template("quiz_rating.html", quiz_id=quiz_id, json=json.dumps(quiz))
        #return render_template("quiz_results.html", quiz=quiz)

@app.route('/rate_and_submit/<int:quiz_id>', methods=["POST"])
@login_required
def rate_and_submit(quiz_id):
    form = request.form
    quiz = json.loads(form.get("json"))

    if form.get("suggestions"):
        new_suggestion = Suggestion(user_id=current_user.get_db_id(), quiz_id=quiz_id, suggestion=form.get("suggestions"))
        try:
            db.session.add(new_suggestion)
            db.session.commit()
        except:
            return 'There was an issue adding the suggestion.'

    quiz_db = Quiz.query.get(quiz_id)
    try:
        print(quiz_db)

        db.session.commit()
    except:
        return 'There was a problem retrieving the quiz taken'

    new_rating = Rating(user_id=current_user.get_db_id(), quiz_id=quiz_id, rating=form.get('rating'))
    new_score = Score(user_id=current_user.get_db_id(), quiz_id=quiz_id, score=quiz["score_value"], answer_json=form.get('json'))
    try:
        db.session.add(new_rating)
        db.session.add(new_score)
        db.session.commit()
        
        return render_template("quiz_results.html", quiz=quiz)
    except:
        return 'There was an issue adding the quiz rating or score.'

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == 'GET':
        if current_user.is_authenticated:
            flash("You are already logged in")
            return redirect("/")
        
        return render_template('register.html')
    else:
        user_name = request.form['user_name']
        user = User.query.filter_by(user_name=user_name).first()
        if user:
            flash("Error: User name taken")
            return redirect('/register')
        
        hash_pw = bcrypt.hashpw(request.form['password'].encode(), salt).decode()

        new_user = User(user_name=user_name, password = hash_pw)

        db.session.add(new_user)
        db.session.commit()

        return redirect('/login')

@app.route('/profile/')
@login_required
def profile_index():
    return redirect('/profile/'+str(current_user.get_db_id()))

@app.route('/profile/<int:id>')
@login_required
def profile(id):
    user = User.query.filter_by(id=id).first()
    raw_quizes = Quiz.query.filter_by(creator_id=user.get_db_id()).order_by(Quiz.date_created).all()
    
    quizes=[]

    # Extract the data from json in database
    for quiz in raw_quizes:
        quiz_object = json.loads(quiz.json)
        quiz_object["id"] = quiz.id

        user_obj = User.query.filter_by(id=quiz.creator_id).first()
        quiz_object["creator"] = user_obj.user_name
        quiz_object["creator_db_id"] = user_obj.get_db_id()

        quizes.append(quiz_object)    

    return render_template('profile.html', user=user, quizes=quizes)


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == 'GET':
        if current_user.is_authenticated:
            flash("You are already logged in")
            return redirect("/")

        return render_template('login.html')
    else:
        next = request.args.get('next')

        user_name = request.form['user_name']
        user = User.query.filter_by(user_name=user_name).first()

        if not user or not bcrypt.checkpw(request.form['password'].encode("utf-8"), user.password.encode("utf-8")):
            flash("Error: invalid user/password combination")
            return redirect('/login')

        if user:
            try:
                login_user(user, remember=request.form["remember"])
            except:
                login_user(user, remember=False)

            return redirect(next or '/')
        else:
            return redirect(next)

@app.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash("Logged out.")
        return redirect("/login")
    else:
        flash("Not logged in.")
        return redirect("/login")    

@app.route('/pass_change')
def temp():
    if current_user.is_authenticated:
        user = User.query.filter_by(id=current_user.get_db_id()).first()
        user.changeable_id = randomInt()
        db.session.commit()

        flash("Session Invalidated")
        return redirect("/login")
    else:
        flash("Not logged in.")
        return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)