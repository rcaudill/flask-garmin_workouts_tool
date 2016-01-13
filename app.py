from __future__ import print_function # In python 2.7
import sys
from flask import Flask, session, render_template, request, flash, redirect, url_for
from flask.ext.session import Session
import json
from datetime import timedelta
from flask import send_file
import tempfile
import StringIO
from wtforms import Form, TextField, TextAreaField
import logging
from garmin_service import *

class UploadForm(Form):
    workout_json = TextAreaField('Workout JSON')

# Initialize the Flask application
app = Flask(__name__)
# Check Configuration section for more details
SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)

# Set session secret key
app.secret_key = 'some_secret'

# Set the timeout for our session to 10 minuntes
app.permanent_session_lifetime = timedelta(minutes=10)

# Route '/' and '/index' to `index`
@app.route('/')
def index():
    
    if 'garmin_session' not in session or session['garmin_session'] is None:
        # No garmin connect session, redirect to login
        flash('You need to enter Garmin Connect credentials in order to view workouts')
        return redirect(url_for('login'))
    else:
        # garmin connect session is good, get workout list
        result = session['garmin_session'].get_workouts()
        json_obj = json.loads(result)
        
        upload_form = UploadForm()

        return render_template('index.html', result=result.encode('ascii', 'ignore').decode('ascii'), json_obj=json_obj, upload_form=upload_form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        session['garmin_session'] = GarminService(request.form['username'], request.form['password'])
        
        if 'garmin_session' in session and session['garmin_session'] is not None:
            # Login successfully, flash message
            flash('You were successfully logged in')
            return redirect(url_for('index'))
        else:
            # Login error, flash message
            flash('Invalid credentials')

    if 'garmin_session' in session and session['garmin_session'] is not None:
        flash('['+session['garmin_session'].get_email()+'] Garmin Connect session already open')
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session['garmin_session'] = None
    flash('Garmin Connect session data cleared')
    return redirect(url_for('login'))

@app.route('/download/<workoutId>')
def download(workoutId):
    #re-enable this flash if you can figure out how to make it fade away afer a few seconds
    #flash('Download started for workoutId: ' + workoutId)
    
    #create tempfile and send to client
    temp = tempfile.NamedTemporaryFile()
    try:
        temp.write(session['garmin_session'].get_workout_string(workoutId=workoutId))
        temp.seek(0)
    finally:
        return send_file(temp.name, attachment_filename=workoutId+".json", as_attachment=True)
        #figure out how to properly close file...
        temp.close()
    
    #this is never reached... okay for now, figure out how to refresh index later.
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    session['garmin_session'].create_workout(json_str=request.form['workout_json'])
    flash('Successfully uploaded')
    return redirect(url_for('index'))

@app.route('/delete/<workoutId>')
def delete(workoutId):
    session['garmin_session'].delete_workout(workoutId=workoutId)
    flash('Workout '+workoutId+' deleted')
    return redirect(url_for('index'))

# Run
if __name__ == '__main__':
    logging.basicConfig(filename='error.log',level=logging.DEBUG)
    app.run(
        debug = False,
        host = "0.0.0.0",
        port = 80
    )
