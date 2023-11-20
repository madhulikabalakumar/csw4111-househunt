
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
from flask import Flask, request, render_template, g, redirect, Response, abort, flash, request, jsonify, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import secrets
from datetime import datetime
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
        # Ensure the requested column is valid, default to flat_no if not
        valid_columns = ['flat_no', 'bldg_address', 'bedrooms', 'bathrooms', 'price', 'sq_footage', 'furnishing_status', 'availability_status','details']
        column = sort_by if sort_by in valid_columns else 'flat_no'

        # Determine the order direction
        valid_orders = ['asc', 'desc']
        order = order if order in valid_orders else 'asc'

        """# Toggle the order direction if the same column is clicked again
        if sort_by == column:
            order = 'asc' if order == 'asc' else 'asc'
        else:
            order = order if order in ['asc', 'desc'] else 'asc'"""
        
        query = text(f"SELECT * FROM House_Belongs_To_Brokered_By ORDER BY {column} {order}")
        
        result = conn.execute(query)
        houses = [dict(row) for row in result]

        return houses
    
    except Exception as e:
        print(f"Error fetching houses: {str(e)}")
        return []

def filter_houses(houses, filter_params):
    filtered_houses = houses

    # Building Address Filter
    addresses_to_filter = filter_params.get('bldg_address', [])
    if addresses_to_filter:
        filtered_houses = [house for house in filtered_houses if house['bldg_address'] in addresses_to_filter]

    # Bedrooms Filter
    bedrooms_to_filter = filter_params.get('bedrooms', [])
    if bedrooms_to_filter:
        filtered_houses = [house for house in filtered_houses if str(house['bedrooms']) in bedrooms_to_filter]

    # Bathrooms Filter
    bathrooms_to_filter = filter_params.get('bathrooms', [])
    if bathrooms_to_filter:
        filtered_houses = [house for house in filtered_houses if str(house['bathrooms']) in bathrooms_to_filter]

    # Furnishing Status Filter
    furnishing_status_to_filter = filter_params.get('furnishing_status', [])
    if furnishing_status_to_filter:
        filtered_houses = [house for house in filtered_houses if house['furnishing_status'] in furnishing_status_to_filter]

    # Availability Status Filter
    availability_status_to_filter = filter_params.get('availability_status', [])
    if availability_status_to_filter:
        filtered_houses = [house for house in filtered_houses if house['availability_status'] in availability_status_to_filter]

    # Price Filter
    max_price = filter_params.get('max_price')
    if max_price:
        try:
            max_price = float(max_price)
            filtered_houses = [house for house in filtered_houses if house['price'] <= max_price]
        except ValueError:
            pass  # Handle invalid input gracefully

    return filtered_houses


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


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
#
# see for routing: https://flask.palletsprojects.com/en/2.0.x/quickstart/?highlight=routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
    """
    request is a special object that Flask provides to access web request information:

    request.method:   "GET" or "POST"
    request.form:     if the browser submitted a form, this contains the data in the form
    request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

    See its API: https://flask.palletsprojects.com/en/2.0.x/api/?highlight=incoming%20request%20data

    """

    # DEBUG: this is debugging code to see what request looks like
    print(request.args)

    sort_by = request.args.get('sort_by', 'flat_no')
    order = request.args.get('order', 'asc')

    houses = get_all_houses(g.conn, sort_by, order)

    # Handle filtering logic
    filter_params = {
        'bldg_address': request.args.getlist('bldg_address'),
        'bedrooms': request.args.getlist('bedrooms'), 
        'bathrooms': request.args.getlist('bathrooms'),
        'furnishing_status': request.args.getlist('furnishing_status'),
        'availability_status': request.args.getlist('availability_status'),
        'max_price': request.args.get('max_price'),
        'min_sq_footage': request.args.get('min_sq_footage'),
    }
    houses = filter_houses(houses, filter_params)

    # Get unique filter values
    unique_bldg_addresses = g.conn.execute("SELECT DISTINCT bldg_address FROM House_Belongs_To_Brokered_By ORDER BY bldg_address ASC").fetchall()
    unique_bldg_addresses = [row[0] for row in unique_bldg_addresses]
    unique_bedroom_counts = g.conn.execute("SELECT DISTINCT bedrooms FROM House_Belongs_To_Brokered_By ORDER BY bedrooms ASC").fetchall()
    unique_bedroom_counts = [row[0] for row in unique_bedroom_counts]
    unique_bathroom_counts = g.conn.execute("SELECT DISTINCT bathrooms FROM House_Belongs_To_Brokered_By ORDER BY bathrooms ASC").fetchall()
    unique_bathroom_counts = [row[0] for row in unique_bathroom_counts]
    unique_furnishing_statuses = g.conn.execute("SELECT DISTINCT furnishing_status FROM House_Belongs_To_Brokered_By ORDER BY furnishing_status ASC").fetchall()
    unique_furnishing_statuses = [row[0] for row in unique_furnishing_statuses]
    unique_availability_statuses = g.conn.execute("SELECT DISTINCT availability_status FROM House_Belongs_To_Brokered_By ORDER BY availability_status ASC").fetchall()
    unique_availability_statuses = [row[0] for row in unique_availability_statuses]

    return render_template('index.html', houses=houses, sort_by=sort_by, order=order,
                           unique_bldg_addresses=unique_bldg_addresses,
                           unique_bedroom_counts=unique_bedroom_counts,
                           unique_bathroom_counts=unique_bathroom_counts,
                           unique_furnishing_statuses=unique_furnishing_statuses,
                           unique_availability_statuses=unique_availability_statuses,
                           filter_params=filter_params)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        account_id = request.form['account_id']
        # Replace this with your database query to retrieve user data
        user = load_user(account_id)
        
        if user:
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(request.args.get('next') or url_for('index'))
        else:
            flash('This Account ID does not exist. Please enter valid Account ID or create a new account.', 'error')
            return redirect('/login')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        account_id = request.form['[p]]']
        # Check if the account_id is unique
        if load_user(account_id) is None:
            # Create a new user in the database
            g.conn.execute("INSERT INTO CU_User(account_id, pronouns, move_in_date) VALUES (%s)", (account_id, pronouns, move_in_date))

            # Log in the new user
            user = User(account_id, pronouns, move_in_date)
            login_user(user)

            flash('Registration successful!', 'success')
            return redirect('/profile')
        else:
            flash('Account ID already exists. Please choose a different one.', 'error')
            return redirect('/register')

    return render_template('register.html')

@app.route('/profile')
@login_required
def profile():
    lease = conn.execute("SELECT lease_no, lease_start_date, lease_end_date, flat_no, bldg_address FROM Lease_Info_Rented_By WHERE account_id = %s;", current_user.account_id)
    leases = [dict(row) for row in lease]

    user_details = g.conn.execute("SELECT C.account_id, C.pronouns, C.move_in_date, S.degree_type, S.citizenship FROM CU_User C, Student S WHERE C.account_id = S.account_id AND C.account_id = %s", current_user.account_id).fetchone()
    if user_details:
        student = 1
    else:
        user_details = g.conn.execute("SELECT C.account_id, C.pronouns, C.move_in_date, N.family, N.designation FROM CU_User C, Non_Student N WHERE C.account_id = N.account_id AND C.account_id= %s", current_user.account_id).fetchone()
        student = 0

    return render_template('profile.html', user=user_details, leases=leases, is_student = student);

@app.route('/details')
def details():

    flat = request.args.get('flat')
    bldg = request.args.get('bldg')
  
    bldg_name = bldg.replace('_', ' ')

    print(bldg_name)
    house_details = g.conn.execute("SELECT flat_no, bedrooms, bathrooms, price, lease_duration, sq_footage, furnishing_status, availability_status,pet_friendly, parking_space, safety_rating, contact FROM House_Belongs_To_Brokered_By WHERE flat_no = %s AND bldg_address = %s", flat, bldg_name).fetchone()
    bldg_details = g.conn.execute("SELECT bldg_address, elevator, laundry, super, dist_to_CU, dist_to_public_transport, prox_to_groc_store, entertainment_rating FROM Building WHERE bldg_address = %s", bldg_name).fetchone()
    broker_details = g.conn.execute("SELECT name, company, rating FROM Broker WHERE contact = %s", house_details.contact).fetchone()
    
    userid = conn.execute("SELECT account_id FROM Lease_Info_Rented_By WHERE flat_no = %s AND bldg_address = %s", flat, bldg_name).fetchall()
    student_details = conn.execute("SELECT C.account_id, C.pronouns, S.degree_type, S.citizenship FROM CU_User C, Student S WHERE C.account_id = S.account_id AND C.account_id IN (SELECT account_id FROM Lease_Info_Rented_By WHERE flat_no = %s AND bldg_address = %s)", flat, bldg_name)
    nonstudent_details = conn.execute("SELECT C.account_id, C.pronouns, N.family, N.designation FROM CU_User C, Non_Student N WHERE C.account_id = N.account_id AND C.account_id IN (SELECT account_id FROM Lease_Info_Rented_By WHERE flat_no = %s AND bldg_address = %s)", flat, bldg_name)

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

            print(existing_lease, lease_start_date)
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
            # Handle integrity constraint violation (e.g., duplicate entry)
            flash("Error: Integrity constraint violation. Please check your input.", "error")
            # You might want to log the exception for debugging purposes
            print(f"IntegrityError: {e}")

        except Exception as e:
            # Handle other exceptions
            flash(f"An error occurred: {str(e)}", "error")
            # You might want to log the exception for debugging purposes
            print(f"Exception: {e}")

    return render_template('rent_form.html', flat_no=flat_no, bldg_address=bldg_address)

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=9140, type=int)
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
