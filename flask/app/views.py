from cgi import test
from urllib import response
from flask import Flask, request, jsonify
from app import app
from flask_cors import CORS
import bcrypt
import pymongo
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity, get_current_user, current_user, get_jwt, create_refresh_token
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timedelta, timezone
from flask_mail import Mail, Message
from threading import Thread
from bson import json_util
import os
import random
import numpy as np
import json
# import pdfkit



CORS(app, supports_credentials=True, origins='*')
# while running docker compose
# app.config["MONGO_URI"] = 'mongodb://' + os.environ['MONGODB_USERNAME'] + ':' + \
#     os.environ['MONGODB_PASSWORD'] + '@' + \
#     os.environ['MONGODB_HOSTNAME'] + ':27017'

# while developing
app.config['MONGO_URI'] = 'mongodb://flaskuser:flaskpassword@localhost:27017'

app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
app.config['JWT_SECRET_KEY'] = b'u\xefB@2\xc3\xdbU\xa2S T\xbe\xdc\xe2\xa9'
# allow query string jwt token
app.config['JWT_TOKEN_LOCATION'] = ['headers', 'query_string']
jwt = JWTManager(app)

client = pymongo.MongoClient(app.config["MONGO_URI"])

# db = client.get_default_database()
db = client['flaskdb']
users = db.users

mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": 'icecream.app.dev@gmail.com',
    "MAIL_PASSWORD": 'app.dev@gmail',
    # default sender
    "MAIL_DEFAULT_SENDER": 'Dev App <icecream.app.dev@gmail.com>'
}


mail = Mail(app)

SIGNALS = {
    'BAD_REQUEST': 400,
    'UNAUTHORIZED': 401,
    'FORBIDDEN': 403,
    'NOT_FOUND': 404,
    'METHOD_NOT_ALLOWED': 405,
    'NOT_ACCEPTABLE': 406,
    'REQUEST_TIMEOUT': 408,
    'CONFLICT': 409,
    'GONE': 410,
    'OK': 200,
    'INTERNAL_SERVER_ERROR': 500,
}

USER_TYPES = {
    'SUPER_ADMIN': 0,  # complete edit access
    'ADMIN': 1,  # complete view access
    'DOCTOR': 2,
    'PATIENT': 3,
}

# helper functions :-----------------------------------------------------


def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            print(e)


def send_reset_email(user):
    # create a reset token
    reset_token = create_access_token(
        identity=user, expires_delta=timedelta(minutes=30), fresh=True)
    msg = Message('Password Reset', recipients=[
                  user], body="You can reset your password using this link: http://localhost:3000/resetpassword?jwt=" + reset_token)
    Thread(target=send_async_email, args=(app, msg)).start()
    pass


def send_password_update_email(user):
    msg = Message('Password Update', recipients=[user], body="Your password has been updated",
                  )
    Thread(target=send_async_email, args=(app, msg)).start()
    pass


# routes :---------------------------------------------------------------------------------------------------------

# Register a callback function that takes whatever object is passed in as the
# identity when creating JWTs and converts it to a JSON serializable format


@jwt.user_identity_loader
def user_identity_lookup(user):
    print("user", user)
    return user

# Register a callback function that loads a user from your database whenever
# a protected route is accessed. This should return any python object on a
# successful lookup, or None if the lookup failed for any reason (for example
# if the user has been deleted from the database).


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    email = jwt_data['sub']
    return db.users.find_one({"email": email})


# ---------------------------------------------------------------------------------------------------------------------

# We are using the `refresh=True` options in jwt_required to only allow
# refresh tokens to access this route.
@app.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify(access_token=access_token)


@ app.route("/dashboard", methods=['GET'])
@ jwt_required()
def dashboard():
    return jsonify({"message": "Welcome to the dashboard", "user": current_user.get('username')}), SIGNALS['OK']


@ app.route("/register", methods=['POST'])
def register():
    print("register")
    if request.method == 'POST':
        if request.is_json:
            email = request.json['email']
        else:
            email = request.form['email']

    user_exists = db.users.find_one({"email": email})
    print("user_exists", user_exists)
    if user_exists:
        return jsonify({"message": "User already exists"}), SIGNALS['CONFLICT']
    else:
        if request.is_json:
            username = request.json['username']
            password = request.json['password']
            usertype = request.json['usertype']
        else:
            username = request.form['username']
            password = request.form['password']
            usertype = request.form['usertype']
        # encrypt password

        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt())
        user_data = {"email": email, "username": username,
                     "password": hashed_password, "usertype": usertype}
        try:
            db.users.insert_one(user_data)
            return jsonify({"message": "User created successfully"}), SIGNALS['OK']
        except Exception as e:
            print("Exception registering new user", user_data)
            print("error", e)


@ app.route("/login", methods=['POST'])
def login():
    if request.method == 'POST':
        if request.is_json:
            email = request.json['email']
            password = request.json['password']
        else:
            email = request.form['email']
            password = request.form['password']

    user_exists = db.users.find_one({"email": email})
    if user_exists:
        if bcrypt.checkpw(password.encode('utf-8'), user_exists['password']):
            access_token = create_access_token(
                identity=email, )
            refresh_token = create_refresh_token(
                identity=email)
            response = jsonify({"message": "Login successful",
                                "user": json_util.dumps(user_exists), "access_token": access_token, "refresh_token": refresh_token}), SIGNALS['OK']
            # add user info to the response
            return response
        else:
            return jsonify({"message": "Incorrect password"}), SIGNALS['UNAUTHORIZED']
    else:
        return jsonify({"message": "User does not exist"}), SIGNALS['NOT_FOUND']


@ app.route("/forgotpassword", methods=['POST'])
def forgot_password():
    if request.method == 'POST':
        if request.is_json:
            email = request.json['email']
        else:
            email = request.form['email']
    user_exists = db.users.find_one({"email": email})
    if user_exists:
        send_reset_email(user_exists['email'])
    return jsonify({"message": "Password reset link sent to your email"}), SIGNALS['OK']


@ app.route("/resetpassword", methods=['POST'])
@jwt_required(fresh=True, locations=['query_string'])
def reset_password():
    # get token from query params
    password = request.args.get('password')
    # verify token
    try:
        # email = jwt.decode(token, app.config['SECRET_KEY'])
        # get identity from token using flask_jwt_extended
        email = get_jwt_identity()
    except:
        return jsonify({"message": "Invalid or expired token"}), SIGNALS['UNAUTHORIZED']
    # get user from db
    user_exists = db.users.find_one({"email": email})
    if user_exists:
        # update user password
        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt())
        # check if previous password matches
        if bcrypt.checkpw(password.encode('utf-8'), user_exists['password']):
            return jsonify({"message": "You cannot use your previous password"}), SIGNALS['CONFLICT']
        db.users.update_one({"email": email}, {
                            "$set": {"password": hashed_password}})
        send_password_update_email(user_exists['email'])
        return jsonify({"message": "Password reset successful"}), SIGNALS['OK']
    else:
        return jsonify({"message": "User does not exist"}), SIGNALS['NOT_FOUND']


@app.route("/logout", methods=['POST'])
def logout():
    response = jsonify({"msg": "logout successful"})
    return response, SIGNALS['OK']


@app.route("/")
def index():
    return {"message": "Welcome to the Dockerized Flask MongoDB API!"}, SIGNALS['OK']


# TESTS
# @app.route("/dummytest", methods=['GET', 'POST'])
# @jwt_required()
# def test():
#     if request.method == 'POST':
#         if request.is_json:
#             data = request.json
#         else:
#             data = request.form
#         print(data)
#         return jsonify({"test_data": data}), SIGNALS['OK']
#     else:
#         doctor_email = request.args.get('patient')
#         patient_email = request.args.get('patient')
#         if doctor_email:
#             tests = db.tests.find({"doctor": doctor_email})
#         elif patient_email:
#             tests = db.tests.find({"patient": patient_email})
#         else:
#             tests = db.tests.find()
#         return jsonify({"tests": json_util.dumps(tests)}), SIGNALS['OK']


@app.route("/question", methods=['GET', 'POST'])
@jwt_required()
def getQuestion():
    # query params
    if request.method == 'POST':
        if request.is_json:
            data = request.json
        else:
            data = request.form

        try:
            new_question = data['question']
        except KeyError:
            return jsonify({"message": "No question found"}), SIGNALS['NOT_FOUND']

        # insert new question into db
        try:
            db.questions.insert_one({'question': new_question})
            return jsonify({"message": "Question added successfully"}), SIGNALS['OK']
        except Exception as e:
            print("Exception adding new question {}:{}").format(new_question, e)

    else:
        # get list of ids seperated by commas as a string as a query param
        ids = request.args.get('qids')
        # convert string to list
        if (ids is not None) and (ids != ""):
            ids = ids.split(',')
        else:
            ids = []

        # select a random question from the database without repeating questions and id not in ids
        ids = [ObjectId(i) for i in ids]

        try:
            question = db.questions.aggregate(
                [{'$sample': {'size': 1}}, {'$match': {'_id': {'$nin': ids}}}])
            return jsonify({"question": json_util.dumps(question)}), SIGNALS['OK']
        except Exception as e:
            print(e)


@app.route("/passage", methods=['GET', 'POST'])
# @jwt_required
def getPassage():
    # query params
    if request.method == 'POST':
        if request.is_json:
            data = request.json
        else:
            data = request.form

        try:
            new_question = data['passage']
        except KeyError:
            return jsonify({"message": "No passage found"}), SIGNALS['NOT_FOUND']

        # insert new question into db
        try:
            db.passages.insert_one({'passage': new_question})
            return jsonify({"message": "Passage added successfully"}), SIGNALS['OK']
        except Exception as e:
            print("Exception adding new passage {}:{}").format(new_question, e)
            return jsonify({"message": "Passage already exists"}), SIGNALS['CONFLICT']

    else:
        # get list of ids seperated by commas as a string as a query param
        ids = request.args.get('pids')
        # convert string to list
        if (ids is not None) and (ids != ""):
            ids = ids.split(',')
        else:
            ids = []

        # select a random passage from the database without repeating passage and id not in ids
        ids = [ObjectId(i) for i in ids]

        try:
            question = db.passages.aggregate(
                [{'$sample': {'size': 1}}, {'$match': {'_id': {'$nin': ids}}}])
            return jsonify({"passage": json_util.dumps(question)}), SIGNALS['OK']
        except Exception as e:
            print(e)


@app.route('/newtest', methods=['POST'])
@jwt_required()
def newTest():
    if request.method == 'POST':

        if request.is_json:
            data = request.json
        else:
            data = request.data

        new_test = data['test']

        # print("new test", new_test)

        # convert source webm to wav
        for question in new_test['questions']:
            del question['src']
            # question['source'] = convert_webm_to_wav(question['source'])
        for passage in new_test['passages']:
            del passage['src']
            # passage['source'] = convert_webm_to_wav(passage['source'])

        # TODO run ML model on new test
        # dummy data
        for question in new_test['questions']:
            question['score'] = random.randint(10, 100)
        for passage in new_test['passages']:
            passage['score'] = random.randint(10, 100)

        # dummy total score
        new_test['total_score'] = int(np.sum([question['score'] for question in new_test['questions']]) + np.sum([
            passage['score'] for passage in new_test['passages']]))

        try:
            new_test['doctor'] = get_jwt_identity()
            new_test['date'] = datetime.now()
            # check if already exists using case number
            print("num", new_test['case_number'])
            test_exists = db.tests.find_one(
                {"case_number": new_test['case_number']})
            print("exists", test_exists)
            if test_exists:
                return jsonify({"message": "Test number already exists"}), SIGNALS['CONFLICT']

            db.tests.insert_one(new_test)
            id = db.tests.find_one({"case_number": new_test['case_number']})
            # id: string of ObjectId
            id = str(id['_id'])
            return jsonify({"message": "Test added successfully", "id": id}), SIGNALS['OK']
        except Exception as e:
            # print("Exception adding new test", new_test)
            print("Error", e)

            return jsonify({"message": "Error in processing test"}), SIGNALS['INTERNAL_SERVER_ERROR']


# def create_pdf(test):
#     from fpdf import FPDF
#     # create pdf
#     pdf = FPDF()
#     pdf.add_page()
#     pdf.set_font("Arial", size=12)
#     pdf.cell(200, 10, txt="Test Case Number: " +
#              test['case_number'], ln=1, align="C")
#     pdf.cell(200, 10, txt="Test Case Name: " +
#              test['case_name'], ln=1, align="C")
#     pdf.cell(200, 10, txt="Patient: " + test['email'], ln=1, align="C")
#     # TODO age, gender, contact number, martial status, occupation, medical history, duration
#     pdf.cell(200, 10, txt="Doctor: " + test['doctor'], ln=1, align="C")
#     pdf.cell(200, 10, txt="Date: " + test['date'], ln=1, align="C")
#     pdf.cell(200, 10, txt="Total Score: " +
#              str(test['total_score']), ln=1, align="C")
#     pdf.cell(200, 10, txt="", ln=1, align="C")
#     pdf.cell(200, 10, txt="Questions:", ln=1, align="C")
#     for question in test['questions']:
#         pdf.cell(200, 10, txt=question['question'], ln=1, align="C")
#         pdf.cell(200, 10, txt="Score: " +
#                  str(question['score']), ln=1, align="C")
#         pdf.cell(200, 10, txt="", ln=1, align="C")
#     pdf.cell(200, 10, txt="Passages:", ln=1, align="C")
#     for passage in test['passages']:
#         pdf.cell(200, 10, txt=passage['passage'], ln=1, align="C")
#         pdf.cell(200, 10, txt="Score: " +
#                  str(passage['score']), ln=1, align="C")
#         pdf.cell(200, 10, txt="", ln=1, align="C")
#     pdf.cell(200, 10, txt="", ln=1, align="C")

#     return pdf



@app.route('/allTests', methods=['GET'])
# @jwt_required()
def getAllTests():
    try:
        tests = None
        tests = db.tests.find()
        print(tests)
        tests = [{"case_name": test['case_name'], "case_number": test['case_number'],
                    "date": test['date'],
                    "email": test['email'], "id": str(test['_id'])} for test in tests]
        print(tests)
        return jsonify({"tests": tests}), SIGNALS['OK']
    except InvalidId:
        return jsonify({"message": "Invalid test id"}), SIGNALS['UNAUTHORIZED']
    except Exception as e:
        print(type(e))
        return jsonify({"message": "Error in processing test"}), SIGNALS['CONFLICT']


# @app.route('/allTests', methods=['GET'])
# # @jwt_required()
# def getAllTests():
#     try:
#         tests = None
#         tests = db.tests.find()
#         tests = [{"case_name": test['case_name'], "case_number": test['case_number'],
#                       "date": test['date'],
#                       "email": test['email'], "id": str(test['_id'])} for test in tests]
#         print("abc")
#         # tests = db.tests.find().sort('date', -1)
#         print(tests)
#         return jsonify({"tests": tests}), SIGNALS['OK']
#     except InvalidId:
#         return jsonify({"message": "Invalid test id"}), SIGNALS['UNAUTHORIZED']
#     except Exception as e:
#         print(type(e))
#         return jsonify({"message": "Error in processing test"}), SIGNALS['CONFLICT']



@app.route('/doctors', methods=['GET'])
@jwt_required()
def getdoctors():
    # print("oyoyoyo")
    user = get_current_user()
    role = user['usertype']
    print(user)
    try:
        doctors = None
        doctors = db.users.find(
            {"usertype": 2}).sort([("date", -1)])
        doctors  = [{"username": doctor['username'], 
                      "email": doctor['email'] ,
                      "id": str(doctor['_id'])} for doctor in doctors]
        print(doctors)
        # TODO: filter details for patient
        # TODO: generate pdf for patient based on request not here
        # print("patient", test)
        # return jsonify({"test": json_util.dumps(test)}), SIGNALS['OK']
        response =jsonify({"doctors": doctors})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return jsonify({"doctors": doctors}), SIGNALS['OK']
    except InvalidId:
        return jsonify({"message": "Invalid test id"}), SIGNALS['UNAUTHORIZED']
    except Exception as e:
        print(type(e))
        return jsonify({"message": "Error in processing test"}), SIGNALS['CONFLICT']


@app.route('/doctors/edit', methods=['POST'])
@jwt_required()
def getdoctorsedit():
    # print("oyoyoyo")
    inp= request.get_json()
    curr = inp["param"]
    # print(curr)

    tochange = inp["param2"]
    try:
        doctors = None
        doctors = (db.users.find_one({"username": curr}))
        print(type(doctors['username']))
        doctors = db.users.find_one_and_update(
            {'username': curr},
            {
            "$set": {
                'username':tochange
            }

            }
        )
        print("yo")
        print(doctors)
        # TODO: filter details for patient
        # TODO: generate pdf for patient based on request not here
        # print("patient", test)
        # return jsonify({"test": json_util.dumps(test)}), SIGNALS['OK']
        # response =jsonify({"doctors": doctors}), SIGNALS['OK']
        # response.headers.add('Access-Control-Allow-Origin', '*')
        return jsonify({"doctors": "good"}), SIGNALS['OK']
    except InvalidId:
        return jsonify({"message": "Invalid test id"}), SIGNALS['UNAUTHORIZED']
    except Exception as e:
        print(type(e))
        return jsonify({"message": "Error in processing test"}), SIGNALS['CONFLICT']
@app.route('/doctors/edit2', methods=['POST'])
@jwt_required()
def getdoctorsedit2():
    # print("oyoyoyo")
    inp= request.get_json()
    curr = inp["param"]
    # print(curr)

    tochange = inp["param2"]
    # print(tochange)
    # user = get_current_user()
    # role = user['usertype']
    # print(user)
    try:
        doctors = None
        doctors = (db.users.find_one({"email": curr}))
        print(type(doctors['email']))
        doctors = db.users.find_one_and_update(
            {'email': curr},
            {
            "$set": {
                'email':tochange
            }

            }
        )
        print("yo")
        print(doctors)
        # TODO: filter details for patient
        # TODO: generate pdf for patient based on request not here
        # print("patient", test)
        # return jsonify({"test": json_util.dumps(test)}), SIGNALS['OK']
        # response =jsonify({"doctors": doctors}), SIGNALS['OK']
        # response.headers.add('Access-Control-Allow-Origin', '*')
        return jsonify({"doctors": "good"}), SIGNALS['OK']
    except InvalidId:
        return jsonify({"message": "Invalid test id"}), SIGNALS['UNAUTHORIZED']
    except Exception as e:
        print(type(e))
        return jsonify({"message": "Error in processing test"}), SIGNALS['CONFLICT']

@app.route('/patients', methods=['GET'])
@jwt_required()
def getpatients():
    user = get_current_user()
    role = user['usertype']
    print(user)
    try:
        patients = None
        patients = db.users.find(
            {"usertype": 3}).sort([("date", -1)])
        patients  = [{"username": patient['username'], 
                      "email": patient['email'],
                      "id": str(patient['_id'])} for patient in patients]
        print(patients)
        # TODO: filter details for patient
        # TODO: generate pdf for patient based on request not here
        # print("patient", test)
        # return jsonify({"test": json_util.dumps(test)}), SIGNALS['OK']
        response =jsonify({"patients": patients})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return jsonify({"patients": patients}), SIGNALS['OK']
    except InvalidId:
        return jsonify({"message": "Invalid test id"}), SIGNALS['UNAUTHORIZED']
    except Exception as e:
        print(type(e))
        return jsonify({"message": "Error in processing test"}), SIGNALS['CONFLICT']


@app.route('/test/<id>', methods=['GET'])
# @jwt_required()
def getTest(id):
    # user = get_current_user()
    print(id)
    # role = user['usertype']
    # print(db.users.find_one({"email": user}))
    try:
        # if role in [0, 1, 2,3]:
        test = db.tests.find_one({"_id": ObjectId(id)})
            # create pdf
            # pdf = create_pdf(test)
            # TODO: verify pdf, return pdf
        return jsonify({"test": json_util.dumps(test)}), SIGNALS['OK']
        # else:
        #     return jsonify({"message": "You are not authorized to view this test"}), SIGNALS['UNAUTHORIZED']
    except InvalidId:
        return jsonify({"message": "Invalid test id"}), SIGNALS['NOT_FOUND']
    except Exception as e:
        print(type(e))
        return jsonify({"message": "Error in processing test"}), SIGNALS['CONFLICT']
@app.route('/user/<id>', methods=['GET'])
@jwt_required()
def getuser(id):
    print(id)
    # response = jsonify({"message": "Invalid test id"})
    # response.headers.add('Access-Control-Allow-Origin', '*')
    # return response,SIGNALS['CONFLICT']
    user = get_current_user()
    role = user['usertype']
    print(user)
    print(db.users.find_one({"email": user['email']}))
    try:
        test = None
        USER = None
        if role == 1:
            USER = db.users.find_one({"_id": ObjectId(id)})
            print(USER)
            if USER['usertype'] == 2:
                tests = db.tests.find({'doctor': USER['email']})
                tests = [{"case_name": test['case_name'], "case_number": test['case_number'],
                        "date": test['date'],
                        "email": test['email'], "id": str(test['_id'])} for test in tests]
            elif USER['usertype'] == 3:
                tests = db.tests.find({'email': USER['email']})
                tests = [{"case_name": test['case_name'], "case_number": test['case_number'],
                        "date": test['date'],
                        "email": test['email'], "id": str(test['_id'])} for test in tests]
            return jsonify({"tests": tests}), SIGNALS['OK']
        else:
            return jsonify({"message": "You are not authorized to view this test"}), SIGNALS['UNAUTHORIZED']
    except InvalidId:
        return jsonify({"message": "Invalid test id"}), SIGNALS['NOT_FOUND']
    except Exception as e:
        print(type(e))
        return jsonify({"message": "Error in processing test"}), SIGNALS['CONFLICT']
@app.route('/username/<id>', methods=['GET'])
@jwt_required()
def getusername(id):
    print(id)
    # response = jsonify({"message": "Invalid test id"})
    # response.headers.add('Access-Control-Allow-Origin', '*')
    # return response,SIGNALS['CONFLICT']
    user = get_current_user()
    role = user['usertype']
    print(user)
    print(db.users.find_one({"email": user['email']}))
    try:
        test = None
        USER = None
        if role == 1:
            USER = db.users.find_one({"_id": ObjectId(id)})
            print(USER)
            return jsonify({"username": USER["username"]}), SIGNALS['OK']
        else:
            return jsonify({"message": "You are not authorized to view this test"}), SIGNALS['UNAUTHORIZED']
    except InvalidId:
        return jsonify({"message": "Invalid test id"}), SIGNALS['NOT_FOUND']
    except Exception as e:
        print(type(e))
        return jsonify({"message": "Error in processing test"}), SIGNALS['CONFLICT']
 

#  {'method': 'POST', 'scheme': 'http', 'server': ('127.0.0.1', 5000), 'root_path': '', 'path': '/doctors/edit', 'query_string': b'', 'headers': EnvironHeaders([('Host', 'localhost:5000'), ('Connection', 'keep-alive'), ('Content-Length', '43'), ('Sec-Ch-Ua', '"Google Chrome";v="95", "Chromium";v="95", ";Not A Brand";v="99"'), ('Sec-Ch-Ua-Mobile', '?0'), ('Authorization', 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY1MTQ0MzI1MCwianRpIjoiOTQwMjRmYTktOWU1Zi00OTFhLThkZGItYTA4YzRlZWFlNzk4IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6ImRpbmVzaC5nYXJnQHN0dWRlbnRzLmlpaXQuYWMuaW4iLCJuYmYiOjE2NTE0NDMyNTAsImV4cCI6MTY1MTQ0Njg1MH0.xkUARl6DBLcg-Ml7b6Pp1Epy9hLfWLdV7VQbvj_e3aE'), ('Accept', 'application/json, text/plain, */*'), ('Content-Type', 'application/json'), ('Access-Control-Allow-Origin', '*'), ('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36'), ('Sec-Ch-Ua-Platform', '"Linux"'), ('Origin', 'http://localhost:3000'), ('Sec-Fetch-Site', 'same-site'), ('Sec-Fetch-Mode', 'cors'), ('Sec-Fetch-Dest', 'empty'), ('Referer', 'http://localhost:3000/'), ('Accept-Encoding', 'gzip, deflate, br'), ('Accept-Language', 'en-US,en;q=0.9')]), 'remote_addr': '127.0.0.1', 'environ': {'wsgi.version': (1, 0), 'wsgi.url_scheme': 'http', 'wsgi.input': <_io.BufferedReader name=7>, 'wsgi.errors': <_io.TextIOWrapper name='<stderr>' mode='w' encoding='utf-8'>, 'wsgi.multithread': True, 'wsgi.multiprocess': False, 'wsgi.run_once': False, 'werkzeug.server.shutdown': <function WSGIRequestHandler.make_environ.<locals>.shutdown_server at 0x7fef12b70160>, 'werkzeug.socket': <socket.socket fd=7, family=AddressFamily.AF_INET, type=SocketKind.SOCK_STREAM, proto=0, laddr=('127.0.0.1', 5000), raddr=('127.0.0.1', 39760)>, 'SERVER_SOFTWARE': 'Werkzeug/2.0.3', 'REQUEST_METHOD': 'POST', 'SCRIPT_NAME': '', 'PATH_INFO': '/doctors/edit', 'QUERY_STRING': '', 'REQUEST_URI': '/doctors/edit', 'RAW_URI': '/doctors/edit', 'REMOTE_ADDR': '127.0.0.1', 'REMOTE_PORT': 39760, 'SERVER_NAME': '127.0.0.1', 'SERVER_PORT': '5000', 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_HOST': 'localhost:5000', 'HTTP_CONNECTION': 'keep-alive', 'CONTENT_LENGTH': '43', 'HTTP_SEC_CH_UA': '"Google Chrome";v="95", "Chromium";v="95", ";Not A Brand";v="99"', 'HTTP_SEC_CH_UA_MOBILE': '?0', 'HTTP_AUTHORIZATION': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY1MTQ0MzI1MCwianRpIjoiOTQwMjRmYTktOWU1Zi00OTFhLThkZGItYTA4YzRlZWFlNzk4IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6ImRpbmVzaC5nYXJnQHN0dWRlbnRzLmlpaXQuYWMuaW4iLCJuYmYiOjE2NTE0NDMyNTAsImV4cCI6MTY1MTQ0Njg1MH0.xkUARl6DBLcg-Ml7b6Pp1Epy9hLfWLdV7VQbvj_e3aE', 'HTTP_ACCEPT': 'application/json, text/plain, */*', 'CONTENT_TYPE': 'application/json', 'HTTP_ACCESS_CONTROL_ALLOW_ORIGIN': '*', 'HTTP_USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36', 'HTTP_SEC_CH_UA_PLATFORM': '"Linux"', 'HTTP_ORIGIN': 'http://localhost:3000', 'HTTP_SEC_FETCH_SITE': 'same-site', 'HTTP_SEC_FETCH_MODE': 'cors', 'HTTP_SEC_FETCH_DEST': 'empty', 'HTTP_REFERER': 'http://localhost:3000/', 'HTTP_ACCEPT_ENCODING': 'gzip, deflate, br', 'HTTP_ACCEPT_LANGUAGE': 'en-US,en;q=0.9', 'werkzeug.request': <Request 'http://localhost:5000/doctors/edit' [POST]>}, 'shallow': False, 'url_rule': <Rule '/doctors/edit' (POST, OPTIONS) -> getdoctorsedit>, 'view_args': {}, 'host': 'localhost:5000', 'url': 'http://localhost:5000/doctors/edit'}


# @app.route('/downloadpdf/<id>', methods=['GET'])
# # @jwt_required()
# def downloadpdf(id):
    
#     pdfkit.from_url("https://localhost:3000/test/" + str(id), "out.pdf")
#     # os.system("wkhtmtopdf https://localhost:3000/test/" + str(id) + " output.pdf")
    
#     return jsonify({"test": json_util.dumps(id)}), SIGNALS['OK']
    
#     # user = get_current_user()
#     # print(id)
#     # # role = user['usertype']
#     # # print(db.users.find_one({"email": user}))
#     # try:
#     #     # if role in [0, 1, 2,3]:
#     #     test = db.tests.find_one({"_id": ObjectId(id)})
#     #         # create pdf
#     #         # pdf = create_pdf(test)
#     #         # TODO: verify pdf, return pdf
#     #     return jsonify({"test": json_util.dumps(test)}), SIGNALS['OK']
#     #     # else:
#     #     #     return jsonify({"message": "You are not authorized to view this test"}), SIGNALS['UNAUTHORIZED']
#     # except InvalidId:
#     #     return jsonify({"message": "Invalid test id"}), SIGNALS['NOT_FOUND']
#     # except Exception as e:
#     #     print(type(e))
#     #     return jsonify({"message": "Error in processing test"}), SIGNALS['CONFLICT']