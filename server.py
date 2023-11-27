
"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python3 server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, abort, flash, request, jsonify, url_for, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import secrets
from datetime import datetime, date, timedelta
from sqlalchemy.exc import IntegrityError

class User(UserMixin):
    def __init__(self, account_id, pronouns, move_in_date):
        self.account_id = account_id
        self.pronouns = pronouns
        self.move_in_date = move_in_date

    def get_id(self):
        return self.account_id

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

# Set a secret key for session management
app.secret_key = secrets.token_hex(16)

# Create the LoginManager instance
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(account_id):
    user_data = g.conn.execute("SELECT * FROM CU_User WHERE account_id = %s", account_id).fetchone()
    if user_data:
        return User(user_data['account_id'], user_data['pronouns'], user_data['move_in_date'])
    return None

def get_all_houses(conn, sort_by='flat_no', order='asc'):
    """
    Retrieve all houses from the database and apply sorting.

    Parameters:
    - conn: SQLAlchemy database connection.
    - sort_by: Column to sort by.
    - order: Sorting order ('asc' or 'desc').

    Returns:
    - List of houses.
    """
    try:
        valid_columns = ['flat_no', 'bldg_address', 'bedrooms', 'bathrooms', 'price', 'sq_footage', 'furnishing_status']
        column = sort_by if sort_by in valid_columns else 'flat_no'

        valid_orders = ['asc', 'desc']
        order = order if order in valid_orders else 'asc'
        
        query = text(f"SELECT * FROM House_Belongs_To_Brokered_By ORDER BY {column} {order}")
        
        result = conn.execute(query)
        houses = [dict(row) for row in result]

        return houses
    
    except Exception as e:
        print(f"Error fetching houses: {str(e)}")
        return []

def filter_houses(houses, filter_params):
    filtered_houses = houses

    addresses_to_filter = filter_params.get('bldg_address', [])
    if addresses_to_filter:
        filtered_houses = [house for house in filtered_houses if house['bldg_address'] in addresses_to_filter]

    bedrooms_to_filter = filter_params.get('bedrooms', [])
    if bedrooms_to_filter:
        filtered_houses = [house for house in filtered_houses if str(house['bedrooms']) in bedrooms_to_filter]

    bathrooms_to_filter = filter_params.get('bathrooms', [])
    if bathrooms_to_filter:
        filtered_houses = [house for house in filtered_houses if str(house['bathrooms']) in bathrooms_to_filter]

    furnishing_status_to_filter = filter_params.get('furnishing_status', [])
    if furnishing_status_to_filter:
        filtered_houses = [house for house in filtered_houses if house['furnishing_status'] in furnishing_status_to_filter]

    max_price = filter_params.get('max_price')
    if max_price:
        try:
            max_price = float(max_price)
            filtered_houses = [house for house in filtered_houses if house['price'] <= max_price]
        except ValueError:
            pass

    return filtered_houses

def get_availability_date(flat_no, bldg_address):
    query = "SELECT lease_end_date FROM Lease_Info_Rented_By WHERE flat_no = %s AND bldg_address = %s ORDER BY lease_end_date DESC LIMIT 1"
    latest_lease_end_date = g.conn.execute(query, (flat_no, bldg_address)).fetchone()

    if latest_lease_end_date and latest_lease_end_date[0]:
        availability_date = latest_lease_end_date[0] + timedelta(days=1)
    else:
        availability_date = date.today() + timedelta(days=1)

    return availability_date

def update_profile(field, value, user_id):

    if field == 'pronouns':
        g.conn.execute("UPDATE CU_User SET pronouns = %s WHERE account_id = %s", value, user_id)
    elif field == 'move_in_date':
            g.conn.execute("UPDATE CU_User SET move_in_date = %s WHERE account_id = %s", value, user_id)
    elif field == 'citizenship':
            g.conn.execute("UPDATE Student SET citizenship = %s WHERE account_id = %s", value, user_id)
    elif field == 'degree_type':
            g.conn.execute("UPDATE Student SET degree_type = %s WHERE account_id = %s", value, user_id)
    elif field == 'family':
            g.conn.execute("UPDATE Non_Student SET family = %s WHERE account_id = %s", value, user_id)
    elif field == 'designation':
            g.conn.execute("UPDATE Non_Student SET designation = %s WHERE account_id = %s", value, user_id)

#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of:
#
#     postgresql://USER:PASSWORD@34.75.94.195/proj1part2
#
# For example, if you had username gravano and password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://gravano:foobar@34.75.94.195/proj1part2"
#
DATABASEURI = "postgresql://mb5144:993320@34.74.171.121/proj1part2"

#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
conn = engine.connect()

@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

  if current_user.is_authenticated:
      g.user = current_user
  else:
      g.user = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass

@app.route('/')
def index():

    g.conn.execute("UPDATE Lease_Info_Rented_By SET lease_end_date = '2026-03-01' WHERE lease_no = 22 AND flat_no = 1 AND bldg_address = '236 Amsterdam Ave'")

    sort_by = request.args.get('sort_by', 'flat_no')
    order = request.args.get('order', 'asc')

    houses = get_all_houses(g.conn, sort_by, order)

    for house in houses:
        house['availability_date'] = get_availability_date(house['flat_no'], house['bldg_address'])

    filter_move_in_date = 'filter_move_in_date' in request.args

    filtered_houses = []
    for house in houses:
        if filter_move_in_date and current_user.is_authenticated and current_user.move_in_date >= house['availability_date']:
            filtered_houses.append(house)
        elif not filter_move_in_date:
            filtered_houses.append(house)

    filter_params = {
        'bldg_address': request.args.getlist('bldg_address'),
        'bedrooms': request.args.getlist('bedrooms'), 
        'bathrooms': request.args.getlist('bathrooms'),
        'furnishing_status': request.args.getlist('furnishing_status'),
        'max_price': request.args.get('max_price'),
        'min_sq_footage': request.args.get('min_sq_footage'),
    }
    filtered_houses = filter_houses(filtered_houses, filter_params)

    unique_bldg_addresses = g.conn.execute("SELECT DISTINCT bldg_address FROM House_Belongs_To_Brokered_By ORDER BY bldg_address ASC").fetchall()
    unique_bldg_addresses = [row[0] for row in unique_bldg_addresses]
    unique_bedroom_counts = g.conn.execute("SELECT DISTINCT bedrooms FROM House_Belongs_To_Brokered_By ORDER BY bedrooms ASC").fetchall()
    unique_bedroom_counts = [row[0] for row in unique_bedroom_counts]
    unique_bathroom_counts = g.conn.execute("SELECT DISTINCT bathrooms FROM House_Belongs_To_Brokered_By ORDER BY bathrooms ASC").fetchall()
    unique_bathroom_counts = [row[0] for row in unique_bathroom_counts]
    unique_furnishing_statuses = g.conn.execute("SELECT DISTINCT furnishing_status FROM House_Belongs_To_Brokered_By ORDER BY furnishing_status ASC").fetchall()
    unique_furnishing_statuses = [row[0] for row in unique_furnishing_statuses]

    return render_template('index.html', houses=filtered_houses, sort_by=sort_by, order=order,
                           unique_bldg_addresses=unique_bldg_addresses,
                           unique_bedroom_counts=unique_bedroom_counts,
                           unique_bathroom_counts=unique_bathroom_counts,
                           unique_furnishing_statuses=unique_furnishing_statuses,
                           filter_params=filter_params)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        account_id = request.form['account_id']
        user = load_user(account_id)

        if user:
            login_user(user)
            flash('Login successful!', 'success')

            next_url = session.pop('next', None)

            return redirect(next_url) if next_url else redirect(url_for('index'))
        else:
            flash('This Account ID does not exist. Please enter a valid Account ID or create a new account.', 'error')
            return redirect('/login')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    next_url = session.pop('next', None)

    return redirect(next_url) if next_url else redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        account_id = request.form['account_id']
        pronouns = request.form['pronouns']
        move_in_date = request.form['move_in_date']
        user_type = request.form['user_type']

        if not all([account_id, pronouns, move_in_date]):
            flash('Please fill in all fields.', 'error')
            return redirect('/register')

        if load_user(account_id) is None:
            try:
                g.conn.execute("INSERT INTO CU_User(account_id, pronouns, move_in_date) VALUES (%s, %s, %s)",
                               (account_id, pronouns, move_in_date))

                if user_type == 'student':
                    if not all([request.form['citizenship'], request.form['degree_type']]):
                        flash('Please fill in all fields.', 'error')
                        return redirect('/register')

                    g.conn.execute("INSERT INTO Student(account_id, citizenship, degree_type) VALUES (%s, %s, %s)",
                                   (account_id, request.form['citizenship'], request.form['degree_type']))
                elif user_type == 'non_student':
                    if not all([request.form['family'], request.form['designation']]):
                        flash('Please fill in all fields.', 'error')
                        return redirect('/register')

                    g.conn.execute("INSERT INTO Non_Student(account_id, family, designation) VALUES (%s, %s, %s)",
                                   (account_id, request.form['family'], request.form['designation']))

                user = User(account_id, pronouns, move_in_date)
                login_user(user)

                flash('Registration successful!', 'success')
                return redirect('/profile')
            except Exception as e:
                flash(f'Registration failed. Please enter valid details.', 'error')
                return redirect('/register')
        else:
            flash('Account ID already exists. Please choose a different one.', 'error')
            return redirect('/register')

    current_date = date.today().isoformat()
    return render_template('register.html', current_date=current_date)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():

    if request.method == 'POST':
        
        bldg_address = request.args.get('bldg')
        srating = request.form.get('srating')
        erating = request.form.get('erating')
     
        if srating != None:
            flat_no = request.args.get('flat')

            g.conn.execute(
                        "INSERT INTO Gave_Safety_Rating (score, account_id, flat_no, bldg_address) VALUES (%s, %s, %s, %s)",
                        (srating, current_user.account_id, flat_no, bldg_address)
                    )

            new_safety_score = g.conn.execute("SELECT AVG(score) FROM Gave_Safety_Rating WHERE flat_no = %s AND bldg_address = %s", flat_no, bldg_address).scalar()
            g.conn.execute(
                "UPDATE House_Belongs_To_Brokered_By SET safety_rating = %s WHERE flat_no = %s AND bldg_address = %s", 
                new_safety_score, flat_no, bldg_address)

        elif erating != None:
            g.conn.execute(
                        "INSERT INTO Gave_Entertainment_Rating (score, account_id, bldg_address) VALUES (%s, %s, %s)",
                        (erating, current_user.account_id, bldg_address)
                    )

            new_entertainment_score = g.conn.execute("SELECT ROUND(AVG(CAST(score AS numeric)), 2) FROM Gave_Entertainment_Rating WHERE bldg_address = %s", bldg_address).scalar()
            
            g.conn.execute(
                "UPDATE Building SET entertainment_rating  = %s WHERE bldg_address = %s", 
                new_entertainment_score, bldg_address)
   
        return redirect('/profile')

    lease_rating = conn.execute(
        "SELECT L.lease_no, L.lease_start_date, L.lease_end_date, L.flat_no, L.bldg_address, G.score, E.score AS escore FROM Lease_Info_Rented_By L LEFT OUTER JOIN Gave_Safety_Rating G ON L.account_id = G.account_id AND G.flat_no = L.flat_no AND G.bldg_address=L.bldg_address LEFT OUTER JOIN Gave_Entertainment_Rating E ON L.account_id = E.account_id AND E.bldg_address=L.bldg_address WHERE L.account_id = %s", 
        current_user.account_id)
    lease_ratings = [dict(row) for row in lease_rating]

    user_details = g.conn.execute(
        "SELECT C.account_id, C.pronouns, C.move_in_date, S.degree_type, S.citizenship FROM CU_User C, Student S WHERE C.account_id = S.account_id AND C.account_id = %s", 
        current_user.account_id).fetchone()
    if user_details:
        student = 1
    else:
        user_details = g.conn.execute(
            "SELECT C.account_id, C.pronouns, C.move_in_date, N.family, N.designation FROM CU_User C, Non_Student N WHERE C.account_id = N.account_id AND C.account_id= %s", 
            current_user.account_id).fetchone()
        student = 0

    return render_template('profile.html', user=user_details, leases=lease_ratings, is_student = student);

@app.route('/details')
def details():
    flat = request.args.get('flat')
    bldg = request.args.get('bldg')
  
    bldg_name = bldg.replace('_', ' ')

    session['next'] = url_for('details', flat=flat, bldg=bldg)

    house_details = g.conn.execute("SELECT flat_no, bedrooms, bathrooms, price, lease_duration, sq_footage, furnishing_status, availability_status,pet_friendly, parking_space, safety_rating, contact FROM House_Belongs_To_Brokered_By WHERE flat_no = %s AND bldg_address = %s", flat, bldg_name).fetchone()
    bldg_details = g.conn.execute("SELECT bldg_address, elevator, laundry, super, dist_to_cu, dist_to_public_transport, prox_to_groc_store, entertainment_rating FROM Building WHERE bldg_address = %s", bldg_name).fetchone()
    broker_details = g.conn.execute("SELECT name, company, contact, rating FROM Broker WHERE contact = %s", house_details.contact).fetchone()
    
    student_details = conn.execute(
        "SELECT C.account_id, C.pronouns, S.degree_type, S.citizenship, G.score AS sscore, E.score AS escore FROM CU_User C, Student S, Lease_Info_Rented_By L LEFT OUTER JOIN Gave_Safety_Rating G ON L.account_id = G.account_id AND G.flat_no = L.flat_no AND G.bldg_address=L.bldg_address LEFT OUTER JOIN Gave_Entertainment_Rating E ON L.account_id = E.account_id AND E.bldg_address=L.bldg_address WHERE C.account_id = S.account_id AND L.account_id = S.account_id AND L.flat_no = %s AND L.bldg_address = %s",
        flat, bldg_name)

    nonstudent_details = conn.execute(
        "SELECT C.account_id, C.pronouns, N.family, N.designation, G.score AS sscore, E.score AS escore FROM CU_User C, Non_Student N, Lease_Info_Rented_By L LEFT OUTER JOIN Gave_Safety_Rating G ON L.account_id = G.account_id AND G.flat_no = L.flat_no AND G.bldg_address=L.bldg_address LEFT OUTER JOIN Gave_Entertainment_Rating E ON L.account_id = E.account_id AND E.bldg_address=L.bldg_address WHERE C.account_id = N.account_id AND L.account_id = N.account_id AND L.flat_no = %s AND L.bldg_address = %s",
        flat, bldg_name)
  
    students = [dict(row) for row in student_details] 
    nonstudents = [dict(row) for row in nonstudent_details] 
    return render_template("details.html", bldg=bldg_details, house=house_details, broker=broker_details, student=students, staff=nonstudents)

@app.route('/rent_form/<int:flat_no>/<string:bldg_address>', methods=['GET', 'POST'])
@login_required
def rent_form(flat_no, bldg_address):
    if request.method == 'POST':
        max_lease_no = g.conn.execute("SELECT MAX(lease_no) FROM Lease_Info_Rented_By").scalar()
        g.conn.execute(f"SELECT setval('lease_info_rented_by_lease_no_seq', {max_lease_no + 1})")

        lease_start_date = request.form.get('lease_start_date')
        lease_end_date = request.form.get('lease_end_date')
        lease_start_date = datetime.strptime(lease_start_date, '%Y-%m-%d').date()
        lease_end_date = datetime.strptime(lease_end_date, '%Y-%m-%d').date()
        account_id = current_user.account_id

        try:
            existing_lease = g.conn.execute(
                "SELECT MAX(lease_end_date) FROM Lease_Info_Rented_By WHERE flat_no = %s AND bldg_address = %s",
                (flat_no, bldg_address.replace('_', ' '))
            ).fetchone()

            if existing_lease and existing_lease[0] and lease_start_date <= existing_lease[0]:
                flash("Error: Lease start date overlaps with an existing lease for this house.")
            else:
                g.conn.execute(
                    "INSERT INTO Lease_Info_Rented_By (lease_start_date, account_id, flat_no, bldg_address) VALUES (%s, %s, %s, %s)",
                    (lease_start_date, account_id, flat_no, bldg_address.replace('_', ' '))
                )
                flash("Lease created successfully!")
                return redirect(url_for('index'))

        except IntegrityError as e:
            flash("Error: Integrity constraint violation. Please check your input.", "error")
            print(f"IntegrityError: {e}")

        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")
            print(f"Exception: {e}")

    availability_date = get_availability_date(flat_no, bldg_address.replace('_', ' '))
    house_details = g.conn.execute(
        "SELECT lease_duration FROM House_Belongs_To_Brokered_By WHERE flat_no = %s AND bldg_address = %s",
        (flat_no, bldg_address.replace('_', ' '))
    ).fetchone()

    current_date = date.today().isoformat()
    return render_template('rent_form.html', flat_no=flat_no, bldg_address=bldg_address, current_date=current_date, availability_date=availability_date, lease_duration=house_details['lease_duration'] if house_details else None)

@app.route('/editprofile', methods=['GET', 'POST'])
def editprofile():

    is_student = request.args.get('is_student')

    if request.method == 'POST':
        val = request.form['pronouns']
        if val:
            update_profile('pronouns', val, current_user.account_id)

        val = request.form['move_in_date']
        if val:
            update_profile('move_in_date', val, current_user.account_id)
        
        if is_student=='1':
            val = request.form['degree_type']
            if val:
                update_profile('degree_type', val, current_user.account_id)
            
            val = request.form['citizenship']
            if val:
               update_profile('citizenship', val, current_user.account_id)
        else:
            val = request.form['family']
            if val:
                update_profile('family', val, current_user.account_id)

            val = request.form['designation']
            if val:
                update_profile('designation', val, current_user.account_id)

        return redirect('/profile')

    user_id = request.args.get('id')

    if is_student == '1':
        isstudent = 1
        user_details = g.conn.execute("SELECT C.account_id, C.pronouns, C.move_in_date, S.degree_type, S.citizenship FROM CU_User C, Student S WHERE C.account_id = S.account_id AND C.account_id = %s", current_user.account_id).fetchone()
    else:
        isstudent = 0
        user_details = g.conn.execute("SELECT C.account_id, C.pronouns, C.move_in_date, N.family, N.designation FROM CU_User C, Non_Student N WHERE C.account_id = N.account_id AND C.account_id= %s", current_user.account_id).fetchone()

    return render_template('editprofile.html', user=user_details, is_student=isstudent)

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=5305, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python3 server.py

    Show the help text using:

        python3 server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  run()
