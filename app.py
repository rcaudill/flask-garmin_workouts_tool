import tempfile
from datetime import timedelta, date

from flask import Flask, session, render_template, request, flash, redirect, url_for
from flask import send_file
from flask.ext.session import Session
from wtforms import Form, TextAreaField, validators
from wtforms_html5 import DateField, IntegerField, DateRange

from garmin_service import *


class UploadForm(Form):
    workout_json = TextAreaField('Workout JSON')

class GeneratePlanForm(Form):
    cts_heart_rate = IntegerField('CTS Test Heart Rate', [
        validators.NumberRange(min=120, max=200, message='Heart rate average must be betweek 100 and 200')])
    start_date = DateField('Plan Start Date',
                           validators=[validators.DataRequired(), DateRange(date(2016, 1, 1), date(2017, 1, 1))])


class ScheduledWorkoutsForm(Form):
    start_date = DateField('Start Date')
    end_date = DateField('Finish Date')

# Initialize the Flask application
app = Flask(__name__)
# Check Configuration section for more details
SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)

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

        return render_template('index.html', result=result.encode('ascii', 'ignore').decode('ascii'), json_obj=json_obj)

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


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'garmin_session' not in session or session['garmin_session'] is None:
        # No garmin connect session, redirect to login
        flash('You need to enter Garmin Connect credentials in order to upload a workout')
        return redirect(url_for('login'))

    upload_form = UploadForm()
    if request.method == 'POST' and upload_form.validate():
        flash(
                'Successfully uploaded: ' + session['garmin_session'].create_workout(
                    json_str=request.form['workout_json']))
        return redirect(url_for('index'))

    return render_template('upload.html', upload_form=upload_form)

@app.route('/delete/<workoutId>')
def delete(workoutId):
    session['garmin_session'].delete_workout(workoutId=workoutId)
    flash('Workout '+workoutId+' deleted')
    return redirect(url_for('index'))


@app.route('/generateplan', methods=['GET', 'POST'])
def generateplan():
    if 'garmin_session' not in session or session['garmin_session'] is None:
        # No garmin connect session, redirect to login
        flash('You need to enter Garmin Connect credentials in order to create a workout plan')
        return redirect(url_for('login'))

    generate_plan_form = GeneratePlanForm()
    if request.method == 'POST' and generate_plan_form.validate():
        flash('Workout plan submitted')
        return redirect(url_for('index'))

    return render_template('generateplan.html', generate_plan_form=generate_plan_form)


@app.route('/scheduledworkouts', methods=['GET', 'POST'])
def scheduledworkouts():
    if 'garmin_session' not in session or session['garmin_session'] is None:
        # No garmin connect session, redirect to login
        flash('You need to enter Garmin Connect credentials in order to view scheduled workouts')
        return redirect(url_for('login'))

    result = ""
    json_obj = ""

    scheduled_workouts_form = ScheduledWorkoutsForm()
    if request.method == 'POST' and scheduled_workouts_form.validate():
        flash('DISPLAY FILTERED LIST')
        return render_template('scheduledworkouts.html', scheduled_workouts_form=scheduled_workouts_form,
                               result=result.encode('ascii', 'ignore').decode('ascii'), json_obj=json_obj)

    flash('DISPLAY FULL LIST')
    return render_template('scheduledworkouts.html', scheduled_workouts_form=scheduled_workouts_form,
                           result=result.encode('ascii', 'ignore').decode('ascii'), json_obj=json_obj)

# Run
if __name__ == '__main__':
    #logging.basicConfig(filename='error.log',level=logging.DEBUG)
    app.run(
        debug = True,
        host = "0.0.0.0",
        port = 8080
    )

