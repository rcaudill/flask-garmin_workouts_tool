from __future__ import print_function  # In python 2.7

import tempfile
from datetime import timedelta

from flask import Flask, session, render_template, request, flash, redirect, url_for
from flask import send_file
from flask.ext.session import Session
from wtforms import Form, TextAreaField, StringField
from wtforms_html5 import DateField, IntegerField

from garmin_service import *


class UploadForm(Form):
    workout_json = TextAreaField('Workout JSON')

class GeneratePlanForm(Form):
    # cts_heart_rate = IntegerField('CTS Test Heart Rate', [validators.NumberRange(min=120, max=200, message='Heart rate average must be betweek 100 and 200')])
    cts_heart_rate = IntegerField('CTS Test Heart Rate')
    # start_date = DateField('Plan Start Date', validators=[validators.DataRequired(), DateRange(date(2016, 1, 1), date(2017, 1, 1))])
    start_date = DateField('Plan Start Date')

class ScheduledWorkoutsForm(Form):
    start_date = DateField('Start Date')
    end_date = DateField('Finish Date')


class ScheduleWorkoutForm(Form):
    workoutId = StringField('Workout ID')
    calendarDate = DateField('Schedule Workout on Date')

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
    flash('Download started for workoutId: ' + workoutId)

    #create tempfile and send to client
    temp = tempfile.NamedTemporaryFile()
    try:
        workout_string = session['garmin_session'].get_workout_string(workoutId=workoutId)
        flash(workout_string)
        temp.write(workout_string)
        temp.seek(0)
        return send_file(temp.name, attachment_filename=workoutId + ".json", as_attachment=True)
    finally:
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


@app.route('/deletescheduledworkout/<scheduleId>')
def deletescheduledworkout(scheduleId):
    result = session['garmin_session'].delete_scheduled_workout(scheduleId=scheduleId)
    flash(result)
    flash('Scheduled workout ' + scheduleId + ' deleted')
    return redirect(url_for('scheduledworkouts'))

@app.route('/generateplan', methods=['GET', 'POST'])
def generateplan():
    if 'garmin_session' not in session or session['garmin_session'] is None:
        # No garmin connect session, redirect to login
        flash('You need to enter Garmin Connect credentials in order to create a workout plan')
        return redirect(url_for('login'))

    generate_plan_form = GeneratePlanForm(request.form)

    if request.method == 'POST' and generate_plan_form.validate():
        flash('Workout plan submitted' + str(generate_plan_form.data['cts_heart_rate']))
        return redirect(url_for('index'))

    return render_template('generateplan.html', generate_plan_form=generate_plan_form)

@app.route('/scheduledworkouts', methods=['GET', 'POST'])
def scheduledworkouts():
    if 'garmin_session' not in session or session['garmin_session'] is None:
        # No garmin connect session, redirect to login
        flash('You need to enter Garmin Connect credentials in order to view scheduled workouts')
        return redirect(url_for('login'))

    scheduled_workouts_form = ScheduledWorkoutsForm(request.form)
    if request.method == 'POST' and scheduled_workouts_form.validate():
        result = session['garmin_session'].get_schedule(
            startCalendarDate=str(scheduled_workouts_form.data['start_date']),
            endCalendarDate=str(scheduled_workouts_form.data['end_date']))
        json_obj = json.loads(result)
        # code for filtering by trainingPlanId
        # for i in json_obj['ExportableWorkoutScheduleResult']['workoutScheduleList']:
        #    if i['ExportableWorkoutSchedule']['trainingPlanId']=="XXX":
        #        i.pop("ExportableWorkoutSchedule")
        return render_template('scheduledworkouts.html', scheduled_workouts_form=scheduled_workouts_form,
                               result=result.encode('ascii', 'ignore').decode('ascii'), json_obj=json_obj)

    result = session['garmin_session'].get_schedule()
    json_obj = json.loads(result)
    return render_template('scheduledworkouts.html', scheduled_workouts_form=scheduled_workouts_form,
                           result=result.encode('ascii', 'ignore').decode('ascii'), json_obj=json_obj)


@app.route('/scheduleworkout', methods=['GET', 'POST'])
def scheduleworkout():
    if 'garmin_session' not in session or session['garmin_session'] is None:
        # No garmin connect session, redirect to login
        flash('You need to enter Garmin Connect credentials in order to view scheduled workouts')
        return redirect(url_for('login'))

    result = session['garmin_session'].get_workouts()
    json_obj = json.loads(result)

    schedule_workout_form = ScheduleWorkoutForm(request.form)
    if request.method == 'POST' and schedule_workout_form.validate():
        result = session['garmin_session'].set_workoutschedule(workoutId=schedule_workout_form.data['workoutId'],
                                                               calendarDate=schedule_workout_form.data['calendarDate'])
        flash(result)
        return render_template('scheduleworkout.html', schedule_workout_form=schedule_workout_form, json_obj=json_obj)

    return render_template('scheduleworkout.html', schedule_workout_form=schedule_workout_form, json_obj=json_obj)
# Run
if __name__ == '__main__':
    #logging.basicConfig(filename='error.log',level=logging.DEBUG)
    app.run(
        debug = True,
        host = "0.0.0.0",
        port = 8080
    )

