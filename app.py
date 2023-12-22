#Rojin Radmehr
from flask import Flask,render_template,redirect,url_for,g ,flash,abort, session, request, send_file
import sqlite3
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, EmailField, PasswordField, SubmitField, IntegerField, DateField, RadioField, TimeField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from flask_login import LoginManager,UserMixin, login_user, logout_user, current_user
from flask_login import login_required
from flask_mail import Mail,Message
from pymongo.mongo_client import MongoClient
from bson import ObjectId
from gridfs import GridFS
from io import BytesIO
import os
import json
from dotenv import load_dotenv
from random import randrange
import time
from flask_babel import Babel, _
import folium
import re



load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"

client = MongoClient(os.getenv('MONGO_DB_URL'))
client_db = client['rides']
ride_collection = client_db['data']

app.config['MAIL_SERVER']=os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER')
DATABASE = os.getenv('DATABASE')


babel = Babel(app)

def get_locale():
    user_language = request.args.get('lang','en')
    if user_language not in app.config['LANGUAGES']:
        user_language = 'en'
    return user_language

babel.init_app(app, locale_selector=get_locale)

app.config['LANGUAGES'] = {
    'en' : 'English',
    'fr' : 'French',
    'es' : 'Spanish'
}

app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

mail= Mail(app)


vehicles = [
    'Sedan',
    'Coupe',
    'Hatchback',
    'Convertible',
    'SUV (Sports Utility Vehicle)',
    'Crossover',
    'Minivan',
    'Pickup Truck',
    'Electric Car',
    'Hybrid Car',
    'Cruiser',
    'Sport Bike',
    'Touring Bike',
    'Dual Sport Bike',
    'Scooter',
    'Dirt Bike',
    'Chopper',
    'Box Truck',
    'Semi-truck (Tractor-trailer)',
    'Tow Truck',
    'Dump Truck',
    'Concrete Mixer Truck',
    'Road Bike',
    'Mountain Bike',
    'Hybrid Bike',
    'Cruiser Bike',
    'Folding Bike',
    'Ambulance',
    'Fire Truck',
    'Police Car',
    'Military Vehicles',
    'Ice Cream Truck',
    'Food Truck',
    'Recreational Vehicle (RV)',
    'Camper Van',
    'Boat',
    'Yacht',
    'Sailboat',
    'Jet Ski',
    'Canoe',
    'Kayak',
    'Submarine',
    'Airplane',
    'Helicopter',
    'Glider',
    'Hot Air Balloon',
    'Drone',
    'Bulldozer',
    'Excavator',
    'Crane',
    'Forklift',
    'Grader',
    'ATV (All-Terrain Vehicle)',
    'Dune Buggy',
    'Off-road Truck',
    'Dirt Bike'
]




class User(UserMixin):
    def __init__(self,id,username,password,email,display_name,role,car):
        self.id = id
        self.username = username
        self.password = password
        self.email = email
        self.display_name = display_name
        self.role =role
        self.car = car


@app.before_request
def before_request():
    g.start_time = time.time()
    print(f"Request started for {request.path} at {g.start_time}")


@app.after_request
def after_request(response):
    end_time = time.time()
    elapsed_time = end_time - g.start_time
    print(f"Request ended for {request.path} at {end_time}")
    print(f"Elapsed time: {elapsed_time} seconds")
    print(f"Status Code: {response.status_code}")
    print(f"Request Method: {request.method}")
    return response  

     
def get_db():
    db = getattr(g,'_database',None)
    if db is None:
        db = g._database = sqlite3.connect(os.getenv('SQLITE_DB'))
        create_table(db)
    return db
def create_table(db):
        cursor = db.cursor()
        #create table and insert entry
        cursor.execute('''CREATE TABLE IF NOT EXISTS users
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   username TEXT NOT NULL,
                   password TEXT NOT NULL,
                   email TEXT,
                   display_name TEXT NOT NULL,
                   role TEXT NOT NULL,
                   car TEXT)
                   ''')
        db.commit()


        
class loginform(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=100)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Login')

class userregistrationform(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=100)])
    email = EmailField('Email', validators=[DataRequired(),Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(),EqualTo('password')])
    display_name = StringField('Display Name', validators=[DataRequired(), Length(min=2, max=100)])
    submit = SubmitField('Add New User')
    
    
class driverregistrationform(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=100)])
    email = EmailField('Email', validators=[DataRequired(),Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(),EqualTo('password')])
    display_name = StringField('Display Name', validators=[DataRequired(), Length(min=2, max=100)])
    vehicle = StringField('Vehicle Model', validators=[DataRequired(), Length(min=2, max=100)])
    submit = SubmitField('Add New User')
    

    
    
def log_in(username, password):
    db=get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    if user:
        return True
    else:
        return False
    
def get_users():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    return users

@login_manager.user_loader
def load_user(user_id):
    # Convert user_id to int
    user_id = int(user_id)
    users = get_users()
    for user in users:
        if user[0] == user_id:
            return User(id=user[0],username=user[1],password=user[2],email=user[3],display_name=user[4],role=user[5],car=user[6])
    return None

def get_user(username):
        users = get_users()
        for user in users:
            if user[1] == username:
                return User(id=user[0],username=user[1],password=user[2],email=user[3],display_name=user[4],role=user[5],car=user[6])
        return None
    
    
def register_user(username, password, email, display_name, role, car):
    db=get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    if cursor.fetchone():
        return False  # Username already exists
    else:
        cursor.execute("INSERT INTO users (username, password, email, display_name, role, car) VALUES (?, ?, ?, ?, ?, ?)", (username, password, email, display_name, role, car))
            
        db.commit()
        return True
    

def check_coor(coor):
    
    coordinate_pattern = r"Latitude:\s*(-?\d+\.\d+)\s*Longitude:\s*(-?\d+\.\d+)"

    # Find all matches in the text
    matches = re.findall(coordinate_pattern, coor)

    for match in matches:
        x, y = map(float, match)
    return (x,y)

 
@app.errorhandler(404)
def not_found_error(error):
    selected_language = request.args.get('lan','en')
    return render_template(f'notfound_{selected_language}.html')

@app.errorhandler(500)
def internal_server_error(error):
    selected_language = request.args.get('lan','en')
    return render_template(f'servererror_{selected_language}.html')

@app.route('/trigger_error')
def trigger_error():
    # Simulate an internal server error
    abort(500)
    
@app.route('/')
def welcome_page():
    if not current_user.is_authenticated :
        return redirect('/login')
    else :
        return redirect('/main')
    


@app.route('/main',methods=['GET','POST'])
def main_page():
    if current_user.role == "user":
        
            
        return render_template(f'home_user.html', user=current_user)
    elif current_user.role == "admin":
        return render_template(f'home_admin.html', user=current_user)
    elif current_user.role == "driver":
        rides = ride_collection.find({'status':'waiting'})
        return render_template(f'home_driver.html', user=current_user, rides=rides)



@app.route('/request',methods=['GET','POST'])
@login_required  
def request_ride():
    if current_user.role == "user":
        if request.method == 'POST':
            start_coor=request.form['start']
            start=check_coor(start_coor)
            end_coor=request.form['end']
            end=check_coor(end_coor)
            date=request.form['date']
            time=request.form['time']
            car=request.form['car']
            description=request.form['description']
            ride = {
                        'posted_by': current_user.username,
                        'start': start,
                        'end': end,
                        'date': date,
                        'time' : time,
                        'car': car,
                        'description': description,
                        'status': 'waiting',
                        'price': randrange(10, 100),
            }
            idobj = ride_collection.insert_one(ride)
            id = str(idobj.inserted_id)
            return redirect('/wait_user/'+id)
        map_obj = folium.Map(location=[49.048670, 10.195313], zoom_start=3)
        folium.LatLngPopup().add_to(map_obj)
        return render_template('request_ride.html', user=current_user, cars=vehicles, map=map_obj._repr_html_())
    else:
        flash('Drivers can not request rides. If you want to request a ride, make another profile to do so','danger')
        return redirect('/main')
    


@app.route('/wait_user/<ride_id>',methods=['GET','POST'])
@login_required
def wait_user(ride_id):
    if current_user.role == "user":
        ride = ride_collection.find_one({'_id': ObjectId(ride_id)})
        if ride['status'] == "in-route":
            return redirect('/riding/'+ride_id)
        return render_template('wait_user.html', user=current_user, ride=ride)
    else:
        flash('Drivers can not request rides. If you want to request a ride, make another profile to do so','danger')
        return redirect('/main')
    
    
@app.route('/cancel_ride/<ride_id>',methods=['GET','POST'])
@login_required
def cancel_ride(ride_id):
    if current_user.role == "user":
        ride_collection.update_one({'_id': ObjectId(ride_id)}, {'$set': {'status': 'cancelled'}})
        return redirect('/main')
    elif current_user.role == "driver":
        ride_collection.update_one({'_id': ObjectId(ride_id)}, {'$set': {'status': 'waiting'}})
        return redirect('/main')    

@app.route('/take_ride/<ride_id>')
@login_required
def take_ride (ride_id):
    if current_user.role == "driver":
        ride_collection.update_one({'_id': ObjectId(ride_id)}, {'$set': {'status': 'in-route'}})
        return redirect('/riding/'+ride_id)
    else:
        flash('Only drivers can take rides','danger')
        return redirect('/main')
    
@app.route('/riding/<ride_id>')
@login_required
def riding (ride_id):
        ride = ride_collection.find_one({'_id': ObjectId(ride_id)})
        return render_template('riding.html', user=current_user, ride=ride)

@app.route('/finish_ride/<ride_id>')
@login_required
def finish_ride (ride_id):
    if current_user.role == "driver":
        ride_collection.update_one({'_id': ObjectId(ride_id)}, {'$set': {'status': 'finished'}})
        return redirect('/main')
    else:
        flash('Only drivers can finish rides','danger')
        return redirect('/main')  
    
@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    from authentication import auth_blueprint
    app.register_blueprint(auth_blueprint)
    app.run(debug=True)