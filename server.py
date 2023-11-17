
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
from flask import Flask, request, render_template, g, redirect, Response, abort, flash, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import secrets

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

def does_account_id_exist(account_id):
    # Execute a SELECT query to check if the account_id exists
    result = g.conn.execute("SELECT COUNT(*) FROM CU_User WHERE account_id = %s", account_id).fetchone()

    # If result is not None and the count is greater than 0, account_id exists
    return result is not None and result[0] > 0

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
        valid_columns = ['flat_no', 'bldg_address', 'bedrooms', 'bathrooms', 'price', 'sq_footage', 'furnishing_status', 'availability_status']
        column = sort_by if sort_by in valid_columns else 'flat_no'

        # Determine the order direction
        valid_orders = ['asc', 'desc']
        direction = order if order in valid_orders else 'asc'

        query = text(f"SELECT * FROM House_Belongs_To_Brokered_By ORDER BY {column} {direction}")
        
        result = conn.execute(query)
        houses = [dict(row) for row in result]

        return houses
    
    except Exception as e:
        print(f"Error fetching houses: {str(e)}")
        return []

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

conn.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
conn.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


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


  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #
  #     # creates a <div> tag for each element in data
  #     # will print:
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #

  sort_by = request.args.get('sort_by', 'flat_no')
  order = request.args.get('order', 'asc')
  
  houses = get_all_houses(g.conn, sort_by=sort_by, order=order)

  unique_bldg_addresses = [row[0] for row in g.conn.execute("SELECT DISTINCT bldg_address FROM House_Belongs_To_Brokered_By")]
  unique_bedroom_counts = [row[0] for row in g.conn.execute("SELECT DISTINCT bedrooms FROM House_Belongs_To_Brokered_By")]
  unique_bathroom_counts = [row[0] for row in g.conn.execute("SELECT DISTINCT bathrooms FROM House_Belongs_To_Brokered_By")]
  unique_furnishing_statuses = [row[0] for row in g.conn.execute("SELECT DISTINCT furnishing_status FROM House_Belongs_To_Brokered_By")]
  unique_availability_statuses = [row[0] for row in g.conn.execute("SELECT DISTINCT availability_status FROM House_Belongs_To_Brokered_By")]
  
  return render_template("index.html", houses=houses,
                         unique_bldg_addresses=unique_bldg_addresses,
                         unique_bedroom_counts=unique_bedroom_counts,
                         unique_bathroom_counts=unique_bathroom_counts,
                         unique_furnishing_statuses=unique_furnishing_statuses,
                         unique_availability_statuses=unique_availability_statuses)

# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  g.conn.execute('INSERT INTO test(name) VALUES (%s)', name)
  return redirect('/')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        account_id = request.form['account_id']
        # Replace this with your database query to retrieve user data
        user = load_user(account_id)
        
        if user:
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(request.args.get('next') or '/profile')
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
        account_id = request.form['account_id']
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
    return render_template('profile.html', user=current_user)

@app.route('/apply_filters', methods=['POST'])
def apply_filters():
    filters = {
        'bldg_address': request.json.get('bldg_address'),
        'bedrooms': request.json.get('bedrooms'),
        'bathrooms': request.json.get('bathrooms'),
        'furnishing_status': request.json.get('furnishing_status'),
        'availability_status': request.json.get('availability_status'),
        'max_price': request.json.get('max_price'),
        'min_sq_footage': request.json.get('min_sq_footage'),
    }

    try:
        # Build the base SQL query
        query = "SELECT * FROM House_Belongs_To_Brokered_By WHERE 1=1"

        # Add conditions for each filter if they are provided
        if filters['bldg_address']:
            query += f" AND bldg_address = '{filters['bldg_address']}'"

        if filters['bedrooms']:
            query += f" AND bedrooms = '{filters['bedrooms']}'"

        if filters['bathrooms']:
            query += f" AND bathrooms = '{filters['bathrooms']}'"

        if filters['furnishing_status']:
            query += f" AND furnishing_status = '{filters['furnishing_status']}'"

        if filters['availability_status']:
            query += f" AND availability_status = '{filters['availability_status']}'"

        if filters['max_price']:
            query += f" AND price <= {filters['max_price']}"

        if filters['min_sq_footage']:
            query += f" AND sq_footage >= {filters['min_sq_footage']}"

        # Execute the query and fetch the filtered houses
        result = g.conn.execute(query)
        filtered_houses = [dict(row) for row in result]

        return jsonify({'houses': filtered_houses})

    except Exception as e:
        return jsonify({'error': str(e)})


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
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
