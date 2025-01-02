# app.py
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
from database.database_factory import DatabaseHandler, DatabaseType
from dotenv import load_dotenv
import os
import openai
from functools import wraps

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key")
CORS(app)

# Set OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")




# Global variable for database handler
db_handler = None

def get_db_handler():
    """Helper function to get or recreate database handler"""
    global db_handler
    
    try:
        if db_handler and db_handler.db.validate_connection():
            return db_handler
    except:
        if db_handler:
            db_handler.disconnect()
            db_handler = None

    if 'db_credentials' in session and 'db_type' in session:
        try:
            db_handler = DatabaseHandler(session['db_type'])
            success, _ = db_handler.connect(session['db_credentials'])
            if success:
                return db_handler
        except:
            return None
    
    return None

def require_db_connection(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if get_db_handler() is None:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    """Serve the landing page with database options"""

    return render_template(
        "landing.html", 
        databases=[db.value for db in DatabaseType]
    )

@app.route("/login/<db_type>")
def login(db_type):
    """Serve the login page for specific database type"""
    # Convert db_type to lowercase for comparison
    db_type_lower = db_type.lower()
    # Check if the database type is valid
    valid_types = [db.value for db in DatabaseType]
    if db_type_lower not in valid_types:
        return redirect(url_for('index'))
    if 'db_credentials' in session:
        return redirect(url_for('dashboard'))
    return render_template("login.html", db_type=db_type_lower)

@app.route("/connect", methods=["POST"])
def connect_db():
    """Handle database connection"""
    global db_handler
    
    if db_handler:
        db_handler.disconnect()
        db_handler = None
        
    try:
         # Debug logging
        app.logger.info("Form data received:")
        app.logger.info(request.form)

        db_type = request.form.get("db_type")
        app.logger.info(f"DB Type received: {db_type}")
        if not db_type:
            return jsonify({"error": "Database type is required"}), 400
            
        db_type = db_type.lower()
        print("db_type", db_type)
        # Get database name/connection string
        db_name = request.form.get("db_name")
        if not db_name:
            return jsonify({"error": "Database name or connection string is required"}), 400
        if db_type == "sqlite":
            connection_string = request.form.get("db_name")
            print("Connection_string",connection_string)
            if not connection_string:
                return jsonify({"error": "SQLite connection string is required"}), 400
            credentials = {"dbname": connection_string}
        else:

            credentials = {
            "dbname": request.form.get("db_name"),
            "user": request.form.get("db_user"),
            "password": request.form.get("db_password"),
            "host": request.form.get("db_host"),
            "port": request.form.get("db_port")
            }

        # Log credentials (excluding password)
            safe_credentials = {**credentials, 'password': '****'}
            app.logger.info(f"Credentials: {safe_credentials}")
        # Validate all required fields are present
            if not all([credentials['dbname'], credentials['user'], 
                   credentials['password'], credentials['host'], 
                   ]):
                return jsonify({"error": "All connection fields are required"}), 400
        
        db_handler = DatabaseHandler(db_type)
        print("db_handler", db_handler)
        success, error = db_handler.connect(credentials)
        
        if success:
            session['db_credentials'] = credentials
            session['db_type'] = db_type
            return jsonify({
                "message": f"Connected to {db_type} database successfully!",
                "redirect": url_for('dashboard')
            }), 200
        else:
            app.logger.error(f"Database connection failed: {error}")
            return jsonify({"error": f"Database connection failed: {error}"}), 400
            
    except Exception as e:
        app.logger.error(f"Unexpected error in connect_db: {str(e)}")
        app.logger.error(f"Request form data: {request.form}")
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@app.route("/dashboard")
@require_db_connection
def dashboard():
    """Display database dashboard"""
    tables = db_handler.get_tables()
    db_name = session.get('db_credentials', {}).get('dbname', 'Unknown')
    return render_template(
        "dashboard.html", 
        tables=tables, 
        db_name=db_name,
        db_type=session.get('db_type')
    )

@app.route("/table-data/<table_name>")
@require_db_connection
def get_table_data(table_name):
    """Get data for specific table"""
    try:
        data = db_handler.get_table_data(table_name)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/execute-query", methods=["POST"])
@require_db_connection
def execute_query():
    """Execute database query"""
    prompt = request.form.get("prompt")
    if not prompt:
        return jsonify({"error": "Query prompt is required"}), 400

    try:
        # Generate SQL using GPT
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a pymongo expert. Generate only the pymongo query without any explanation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        sql_query = response.choices[0].message.content.strip()
        print(sql_query)
        
        # Execute query
        result = db_handler.execute_query(sql_query)
        result['query'] = sql_query  # Include the generated query in response
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/disconnect")
def disconnect():
    """Disconnect from database"""
    global db_handler
    if db_handler:
        db_handler.disconnect()
        db_handler = None
    session.clear()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)