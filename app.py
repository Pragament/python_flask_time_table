from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import pandas as pd
import os
from werkzeug.utils import secure_filename
import json
from datetime import datetime, timedelta
import re
from dateutil.rrule import rrule, WEEKLY, DAILY, MO, TU, WE, TH, FR, SA, SU
from dateutil.parser import parse as date_parse

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Global variables to store data
teachers_data = []
timetable_data = []

# Day mapping for RRULE
DAY_MAPPING = {
    'monday': MO, 'mon': MO,
    'tuesday': TU, 'tue': TU,
    'wednesday': WE, 'wed': WE,
    'thursday': TH, 'thurs': TH, 'thu': TH,
    'friday': FR, 'fri': FR,
    'saturday': SA, 'sat': SA,
    'sunday': SU, 'sun': SU
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def clean_subject_name(subject):
    """Extract subject name by removing numbers from the end"""
    if pd.isna(subject):
        return ""
    return re.sub(r'\d+$', '', str(subject)).strip()

def parse_time_slot(time_slot):
    """Parse time slot and return start and end times"""
    if pd.isna(time_slot):
        return None, None
    try:
        parts = time_slot.split(' to ')
        if len(parts) == 2:
            start_time = parts[0].strip()
            end_time = parts[1].strip()
            return start_time, end_time
    except:
        pass
    return None, None

def detect_clashes(timetable_df):
    """Detect time clashes where multiple teachers have same class at same time"""
    clashes = []
    
    # Group by Day, Period, and Class/Activity
    grouped = timetable_df.groupby(['Day', 'Period', 'Class/Activity'])
    
    for (day, period, class_activity), group in grouped:
        if len(group) > 1:
            teachers_involved = group['Teacher Name'].tolist()
            subjects_involved = group['Subject'].tolist()
            time_slots = group['Time Slot'].tolist()
            
            clash_teachers = list(set(group['Teacher Name']))
            clash_subjects = list(set(group['Subject']))
            
            clash_info = {
                'day': day,
                'period': period,
                'class_activity': class_activity,
                'teachers': teachers_involved,
                'subjects': subjects_involved,
                'time_slot': time_slots[0] if time_slots else '',
                'count': len(group)
            }
            clashes.append(clash_info)
    
    return clashes

def generate_rrule_events(timetable_df, start_date, end_date):
    """Generate calendar events using RRULE for recurring timetable entries"""
    # Remove exact duplicate timetable rows based on key columns
    timetable_df = timetable_df.drop_duplicates(
        subset=['Teacher Name', 'Subject', 'Day', 'Period', 'Time Slot', 'Class/Activity']
    )
    events = []
    
    for idx, row in timetable_df.iterrows():
        day_name = str(row['Day']).lower()
        
        # Map day name to rrule day
        rrule_day = None
        for key, value in DAY_MAPPING.items():
            if day_name.startswith(key):
                rrule_day = value
                break
        
        if not rrule_day:
            continue
        
        # Parse time slot
        start_time_str, end_time_str = parse_time_slot(row['Time Slot'])
        if not start_time_str or not end_time_str:
            continue
        
        try:
            # Create RRULE for weekly recurrence
            rule = rrule(
                WEEKLY,
                byweekday=rrule_day,
                dtstart=start_date,
                until=end_date
            )
            
            # Generate events for each occurrence
            for dt in rule:
                # Parse time components
                start_hour, start_min = map(int, start_time_str.split(':'))
                end_hour, end_min = map(int, end_time_str.split(':'))
                
                event_start = dt.replace(hour=start_hour, minute=start_min)
                event_end = dt.replace(hour=end_hour, minute=end_min)
                
                event = {
                    'id': f"{idx}_{dt.strftime('%Y%m%d')}",
                    'title': f"{row['Teacher Name']} - {clean_subject_name(row['Subject'])}",
                    'start': event_start.isoformat(),
                    'end': event_end.isoformat(),
                    'teacher': row['Teacher Name'],
                    'subject': clean_subject_name(row['Subject']),
                    'class': row['Class/Activity'],
                    'period': row['Period'],
                    'day': row['Day'],
                    'backgroundColor': get_color_for_teacher(row['Teacher Name']),
                    'borderColor': get_color_for_teacher(row['Teacher Name']),
                    'extendedProps': {
                        'teacher': row['Teacher Name'],
                        'subject': clean_subject_name(row['Subject']),
                        'class': row['Class/Activity'],
                        'period': row['Period'],
                        'timeSlot': row['Time Slot']
                    }
                }
                events.append(event)
        
        except Exception as e:
            print(f"Error generating event for row {idx}: {e}")
            continue
    
    # Remove duplicate events
    unique_events = []
    seen = set()
    for event in events:
        key = (
            event['title'],
            event['start'],
            event['end'],
            event.get('teacher'),
            event.get('subject'),
            event.get('class'),
            event.get('period'),
            event.get('timeSlot'),
        )
        if key not in seen:
            seen.add(key)
            unique_events.append(event)
    
    return unique_events

def get_color_for_teacher(teacher_name):
    """Generate consistent color for each teacher"""
    colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
    ]
    hash_value = hash(teacher_name) % len(colors)
    return colors[hash_value]

@app.route('/')
def index():
    return render_template('index.html', 
                         teachers_count=len(teachers_data),
                         timetable_count=len(timetable_data))

@app.route('/upload', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        # Handle teachers list upload
        if 'teachers_file' in request.files:
            teachers_file = request.files['teachers_file']
            if teachers_file and allowed_file(teachers_file.filename):
                try:
                    df = pd.read_csv(teachers_file)
                    global teachers_data
                    teachers_data = df.to_dict('records')
                    flash(f'Teachers list uploaded successfully! ({len(teachers_data)} teachers)', 'success')
                except Exception as e:
                    flash(f'Error uploading teachers file: {str(e)}', 'error')
        
        # Handle timetable upload
        if 'timetable_file' in request.files:
            timetable_file = request.files['timetable_file']
            if timetable_file and allowed_file(timetable_file.filename):
                try:
                    df = pd.read_csv(timetable_file)
                    # Clean subject names
                    df['Subject'] = df['Subject'].apply(clean_subject_name)
                    global timetable_data
                    timetable_data = df.to_dict('records')
                    flash(f'Timetable uploaded successfully! ({len(timetable_data)} entries)', 'success')
                except Exception as e:
                    flash(f'Error uploading timetable file: {str(e)}', 'error')
        
        return redirect(url_for('upload_files'))
    
    return render_template('upload.html')

@app.route('/timetable')
def view_timetable():
    if not timetable_data:
        flash('No timetable data available. Please upload timetable CSV first.', 'warning')
        return redirect(url_for('upload_files'))
    
    # Get unique values for filters
    df = pd.DataFrame(timetable_data)
    teachers = sorted([t for t in df['Teacher Name'].dropna().unique() if isinstance(t, str)])
    subjects = sorted(df['Subject'].unique())
    classes = sorted(df['Class/Activity'].unique())
    
    # Detect clashes
    clashes = detect_clashes(df)
    
    return render_template('timetable.html', 
                         timetable=timetable_data,
                         teachers=teachers,
                         subjects=subjects,
                         classes=classes,
                         clashes=clashes)

@app.route('/calendar')
def calendar_view():
    if not timetable_data:
        flash('No timetable data available. Please upload timetable CSV first.', 'warning')
        return redirect(url_for('upload_files'))
    
    # Get unique values for filters
    df = pd.DataFrame(timetable_data)
    teachers = sorted([t for t in df['Teacher Name'].dropna().unique() if isinstance(t, str)])
    subjects = sorted([s for s in df['Subject'].dropna().unique() if isinstance(s, str)])
    classes = sorted([c for c in df['Class/Activity'].dropna().unique() if isinstance(c, str)])
    
    return render_template('calendar.html',
                         teachers=teachers,
                         subjects=subjects,
                         classes=classes)

@app.route('/api/events')
def get_events():
    if not timetable_data:
        return jsonify([])
    
    # Get query parameters for filtering
    teacher_filter = request.args.get('teacher', '')
    subject_filter = request.args.get('subject', '')
    class_filter = request.args.get('class', '')
    start_date = request.args.get('start', '')
    end_date = request.args.get('end', '')
    
    # Create DataFrame
    df = pd.DataFrame(timetable_data)
    
    # Apply filters
    if teacher_filter:
        df = df[df['Teacher Name'] == teacher_filter]
    if subject_filter:
        df = df[df['Subject'] == subject_filter]
    if class_filter:
        df = df[df['Class/Activity'] == class_filter]
    
    # Parse date range
    try:
        start_dt = datetime.fromisoformat(start_date.replace('Z', '')) if start_date else datetime.now()
        end_dt = datetime.fromisoformat(end_date.replace('Z', '')) if end_date else (datetime.now() + timedelta(days=30))
    except:
        start_dt = datetime.now()
        end_dt = datetime.now() + timedelta(days=30)
    
    # Generate events using RRULE
    events = generate_rrule_events(df, start_dt, end_dt)
    
    return jsonify(events)

@app.route('/api/clashes')
def get_clashes():
    if not timetable_data:
        return jsonify([])
    
    df = pd.DataFrame(timetable_data)
    clashes = detect_clashes(df)
    return jsonify(clashes)

@app.route('/edit_timetable', methods=['GET', 'POST'])
def edit_timetable():
    if request.method == 'POST':
        try:
            # Get form data
            entry_id = int(request.form.get('entry_id'))
            teacher_name = request.form.get('teacher_name')
            subject = request.form.get('subject')
            day = request.form.get('day')
            period = request.form.get('period')
            time_slot = request.form.get('time_slot')
            class_activity = request.form.get('class_activity')
            
            # Update the timetable data
            if 0 <= entry_id < len(timetable_data):
                timetable_data[entry_id].update({
                    'Teacher Name': teacher_name,
                    'Subject': subject,
                    'Day': day,
                    'Period': period,
                    'Time Slot': time_slot,
                    'Class/Activity': class_activity
                })
                flash('Timetable entry updated successfully!', 'success')
            else:
                flash('Invalid entry ID', 'error')
        
        except Exception as e:
            flash(f'Error updating entry: {str(e)}', 'error')
        
        return redirect(url_for('view_timetable'))
    
    # GET request - show edit form
    entry_id = request.args.get('id', type=int)
    if entry_id is None or entry_id >= len(timetable_data):
        flash('Invalid entry ID', 'error')
        return redirect(url_for('view_timetable'))
    
    entry = timetable_data[entry_id]
    return render_template('edit_timetable.html', entry=entry, entry_id=entry_id)

@app.route('/generate_rrule')
def generate_rrule():
    """Generate RRULE strings for timetable entries"""
    if not timetable_data:
        return jsonify({'error': 'No timetable data available'})
    
    df = pd.DataFrame(timetable_data)
    df = df.fillna('')  # <-- Add this line to replace NaN with empty string
    rrule_data = []
    
    for idx, row in df.iterrows():
        day_name = str(row['Day']).lower()
        
        # Map day to RRULE format
        rrule_day = None
        for key, value in DAY_MAPPING.items():
            if day_name.startswith(key):
                rrule_day = key.upper()[:2]  # Convert to MO, TU, WE, etc.
                break
        
        if rrule_day:
            # Generate RRULE string
            rrule_string = f"RRULE:FREQ=WEEKLY;BYDAY={rrule_day}"
            
            rrule_entry = {
                'teacher': row['Teacher Name'],
                'subject': clean_subject_name(row['Subject']),
                'class': row['Class/Activity'],
                'day': row['Day'],
                'period': row['Period'],
                'time_slot': row['Time Slot'],
                'rrule': rrule_string
            }
            rrule_data.append(rrule_entry)
    
    return jsonify(rrule_data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)