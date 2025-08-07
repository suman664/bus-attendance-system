# app.py - Complete version without pandas
from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
from datetime import datetime
import csv
from nepali_datetime import date as nepali_date
import nepali_datetime

app = Flask(__name__)
CORS(app)

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'bus_data')
ROUTES_FILE = os.path.join(DATA_DIR, 'routes.json')

# Initialize data directory and files
def initialize_data():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    # Create initial routes if file doesn't exist
    if not os.path.exists(ROUTES_FILE):
        initial_data = {
            'Route A': [],
            'Route B': [],
            'Route C': [],
            'Route D': []
        }
        with open(ROUTES_FILE, 'w') as f:
            json.dump(initial_data, f, indent=2)

# Load routes data
def load_routes():
    initialize_data()
    with open(ROUTES_FILE, 'r') as f:
        return json.load(f)

# Save routes data
def save_routes(data):
    with open(ROUTES_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# Get CSV filename for a route
def get_csv_filename(route_name):
    safe_name = route_name.replace(' ', '_').replace('/', '_')
    return os.path.join(DATA_DIR, f"{safe_name}.csv")

# Initialize CSV file for a route
def initialize_route_csv(route_name):
    csv_file = get_csv_filename(route_name)
    if not os.path.exists(csv_file):
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['student_id', 'name', 'status', 'archive_date'])

# Add student to route
def add_student_to_route(route_name, student_name):
    # Load current routes
    routes = load_routes()
    
    if route_name not in routes:
        return False
    
    # Add student to routes JSON
    student_id = f"{route_name}_{len(routes[route_name])}"
    routes[route_name].append({
        'id': student_id,
        'name': student_name
    })
    save_routes(routes)
    
    # Initialize CSV file for this route
    initialize_route_csv(route_name)
    
    # Add student to CSV
    csv_file = get_csv_filename(route_name)
    with open(csv_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([student_id, student_name, 'Active', ''])
    
    return True

# Get students for route
def get_students_for_route(route_name):
    routes = load_routes()
    if route_name in routes:
        return routes[route_name]
    return []

# Archive student
def archive_student(student_id):
    try:
        route_name, student_idx = student_id.split('_')
        route_name = route_name + '_' + student_idx.split('_')[0]  # Reconstruct if needed
        # Find the correct route
        routes = load_routes()
        for route, students in routes.items():
            for i, student in enumerate(students):
                if student['id'] == student_id:
                    # Update CSV file
                    csv_file = get_csv_filename(route)
                    if os.path.exists(csv_file):
                        # Read all rows
                        rows = []
                        with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                            reader = csv.reader(f)
                            rows = list(reader)
                        
                        # Update the student row
                        if len(rows) > int(student_idx) + 1:  # +1 for header
                            rows[int(student_idx) + 1][2] = 'Archived'  # status column
                            rows[int(student_idx) + 1][3] = datetime.now().strftime('%Y-%m-%d')  # archive date
                        
                        # Write back
                        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerows(rows)
                    return True
        return False
    except:
        return False

# Restore student
def restore_student(student_id):
    try:
        routes = load_routes()
        for route, students in routes.items():
            for i, student in enumerate(students):
                if student['id'] == student_id:
                    # Update CSV file
                    csv_file = get_csv_filename(route)
                    if os.path.exists(csv_file):
                        # Read all rows
                        rows = []
                        with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                            reader = csv.reader(f)
                            rows = list(reader)
                        
                        # Update the student row
                        student_idx = i
                        if len(rows) > student_idx + 1:  # +1 for header
                            rows[student_idx + 1][2] = 'Active'  # status column
                            rows[student_idx + 1][3] = ''  # clear archive date
                        
                        # Write back
                        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerows(rows)
                    return True
        return False
    except:
        return False

# Save attendance
def save_attendance(route_name, date_str, attendance):
    csv_file = get_csv_filename(route_name)
    if not os.path.exists(csv_file):
        initialize_route_csv(route_name)
    
    # Read existing data
    rows = []
    headers = []
    student_data = {}
    
    if os.path.exists(csv_file):
        with open(csv_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)  # Read header
            for row in reader:
                student_data[row[0]] = row  # student_id as key
                rows.append(row)
    
    # Add date column if not exists
    if date_str not in headers:
        headers.append(date_str)
    
    # Update attendance for each student
    for student_id, is_present in attendance.items():
        if student_id in student_data:
            student_row = student_data[student_id]
            # Ensure row has enough columns
            while len(student_row) <= len(headers) - 1:
                student_row.append('')
            # Set attendance value
            date_col_index = headers.index(date_str)
            student_row[date_col_index] = 'P' if is_present else 'A'
    
    # Write back to file
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in student_data.values():
            writer.writerow(row)
    
    return True

# Get attendance
def get_attendance(route_name, date_str):
    csv_file = get_csv_filename(route_name)
    if not os.path.exists(csv_file):
        return {}
    
    attendance = {}
    with open(csv_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        
        if date_str in headers:
            date_col_index = headers.index(date_str)
            for row in reader:
                # Only include active students
                if len(row) > 2 and row[2] == 'Active':
                    student_id = row[0]
                    status = 'P' if (len(row) > date_col_index and row[date_col_index] == 'P') else 'A'
                    attendance[student_id] = status == 'P'
    
    return attendance

# Get student history
def get_student_history(student_id):
    try:
        route_name = student_id.split('_')[0] + '_' + student_id.split('_')[1].split('_')[0]
        # Find the correct route
        routes = load_routes()
        for route in routes:
            csv_file = get_csv_filename(route)
            if os.path.exists(csv_file):
                history = []
                with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    headers = next(reader)
                    for i, row in enumerate(reader):
                        if row[0] == student_id and len(row) > 2 and row[2] == 'Active':
                            # Check all date columns
                            for j in range(4, len(headers)):  # Skip first 4 columns (id, name, status, archive_date)
                                if len(row) > j and row[j]:
                                    history.append({
                                        'date': headers[j],
                                        'status': row[j] == 'P'
                                    })
                            break
                return history
        return []
    except:
        return []

# Get date history
def get_date_history(date_str):
    history = []
    routes = load_routes()
    
    for route_name in routes:
        csv_file = get_csv_filename(route_name)
        if os.path.exists(csv_file):
            with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader)
                
                if date_str in headers:
                    date_col_index = headers.index(date_str)
                    for row in reader:
                        if len(row) > 2 and row[2] == 'Active' and len(row) > date_col_index:
                            history.append({
                                'student_name': row[1],
                                'route': route_name,
                                'status': row[date_col_index] == 'P'
                            })
    
    return history

# Get Nepali date
def get_nepali_date():
    today = datetime.today()
    nepali_dt = nepali_date.from_datetime_date(today.date())
    return nepali_dt.strftime('%Y-%m-%d')

# API Routes
@app.route('/api/routes')
def get_routes():
    try:
        routes = load_routes()
        return jsonify({'routes': list(routes.keys())})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students')
def get_all_students():
    try:
        routes_data = load_routes()
        all_students = []
        for route_name, students in routes_data.items():
            for student in students:
                all_students.append({
                    'id': student['id'],
                    'name': student['name'],
                    'route': route_name
                })
        return jsonify({'students': all_students})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/<route_name>')
def get_route_students(route_name):
    try:
        students = get_students_for_route(route_name)
        return jsonify({'students': students})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/attendance/<route_name>/<date>')
def get_route_attendance(route_name, date):
    try:
        attendance = get_attendance(route_name, date)
        present = sum(1 for status in attendance.values() if status)
        total = len(attendance)
        return jsonify({
            'attendance': attendance,
            'present': present,
            'total': total
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/attendance', methods=['POST'])
def save_route_attendance():
    try:
        data = request.get_json()
        route_name = data['route']
        date_str = data['date']
        attendance = data['attendance']
        
        if save_attendance(route_name, date_str, attendance):
            present = sum(1 for status in attendance.values() if status)
            total = len(attendance)
            return jsonify({
                'message': 'Attendance saved successfully',
                'present': present,
                'total': total
            })
        else:
            return jsonify({'error': 'Failed to save attendance'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students', methods=['POST'])
def add_student():
    try:
        data = request.get_json()
        route_name = data['route']
        student_name = data['name']
        
        if add_student_to_route(route_name, student_name):
            return jsonify({'message': 'Student added successfully'})
        else:
            return jsonify({'error': 'Failed to add student'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/<student_id>/archive', methods=['POST'])
def archive_student_endpoint(student_id):
    try:
        if archive_student(student_id):
            return jsonify({'message': 'Student archived successfully'})
        else:
            return jsonify({'error': 'Failed to archive student'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/<student_id>/restore', methods=['POST'])
def restore_student_endpoint(student_id):
    try:
        if restore_student(student_id):
            return jsonify({'message': 'Student restored successfully'})
        else:
            return jsonify({'error': 'Failed to restore student'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/student/<student_id>')
def get_student_attendance_history(student_id):
    try:
        history = get_student_history(student_id)
        return jsonify({'history': history})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/date/<date>')
def get_date_attendance_history(date):
    try:
        history = get_date_history(date)
        return jsonify({'history': history})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/nepali-date')
def get_current_nepali_date():
    try:
        nepali_date_str = get_nepali_date()
        return jsonify({'nepali_date': nepali_date_str})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Sync offline data endpoint
@app.route('/api/sync', methods=['POST'])
def sync_offline_data():
    try:
        data = request.get_json()
        offline_records = data.get('records', [])
        
        synced_count = 0
        for record in offline_records:
            route = record['route']
            date = record['date']
            attendance = record['attendance']
            
            if save_attendance(route, date, attendance):
                synced_count += 1
        
        return jsonify({
            'message': f'Successfully synced {synced_count} records',
            'synced_count': synced_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    initialize_data()
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))
