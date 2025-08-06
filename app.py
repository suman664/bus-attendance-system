# app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import os
from datetime import datetime
import calendar
from nepali_datetime import date as nepali_date
import nepali_datetime

app = Flask(__name__)
CORS(app)

# Configuration - Use Render's environment or local
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_FILE = os.path.join(BASE_DIR, 'bus_attendance.xlsx')

# Initialize Excel file with empty routes if it doesn't exist
def initialize_excel():
    if not os.path.exists(EXCEL_FILE):
        # Create empty sheets for each route
        with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
            routes = ['Route A', 'Route B', 'Route C', 'Route D']
            
            for route_name in routes:
                # Create DataFrame with Name, Status, and Archive Date columns
                df = pd.DataFrame({
                    'Name': [],
                    'Status': [],
                    'Archive Date': []
                })
                df.to_excel(writer, sheet_name=route_name, index=False)

# [Include ALL your existing functions here - copy from previous complete app.py]
# Functions: get_all_routes, get_students_for_route, save_attendance, 
# archive_student_from_route, restore_student, get_student_history, etc.

# Get all route names
def get_all_routes():
    initialize_excel()
    try:
        xls = pd.ExcelFile(EXCEL_FILE)
        return xls.sheet_names
    except Exception as e:
        print(f"Error reading routes: {e}")
        return []

# Get all routes and students
def get_all_routes_and_students():
    initialize_excel()
    routes = {}
    
    # Load the Excel file
    xls = pd.ExcelFile(EXCEL_FILE)
    
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name)
        students = []
        for idx, row in df.iterrows():
            # Only include active students
            status = row.get('Status', 'Active')
            if status == 'Active':
                students.append({
                    'id': f"{sheet_name}_{idx}",
                    'name': row['Name'],
                    'route': sheet_name
                })
        routes[sheet_name] = students
    
    return routes

# Get students for a specific route (active only by default)
def get_students_for_route(route_name, include_archived=False):
    initialize_excel()
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=route_name)
        students = []
        
        for idx, row in df.iterrows():
            # Check if we should include archived students or only active ones
            status = row.get('Status', 'Active')  # Default to Active if Status column doesn't exist
            is_archived = status == 'Archived'
            
            if include_archived or not is_archived:
                students.append({
                    'id': f"{route_name}_{idx}",
                    'name': row['Name'],
                    'status': status,
                    'archive_date': row.get('Archive Date', None) if is_archived else None
                })
        return students
    except Exception as e:
        print(f"Error reading route {route_name}: {e}")
        return []

# Get attendance for a specific route and date
def get_attendance(route_name, date_str):
    initialize_excel()
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=route_name)
        
        # Check if date column exists
        if date_str in df.columns:
            attendance = {}
            for idx, row in df.iterrows():
                # Only include active students in attendance
                status = row.get('Status', 'Active')
                if status == 'Active':
                    student_id = f"{route_name}_{idx}"
                    # Assuming 'P' for present, 'A' for absent, or empty for no record
                    status_value = row[date_str] if pd.notna(row[date_str]) else 'P'
                    attendance[student_id] = status_value == 'P'
            return attendance
        else:
            # No attendance recorded for this date
            return {}
    except Exception as e:
        print(f"Error reading attendance for {route_name} on {date_str}: {e}")
        return {}

# Save attendance for a specific route and date
def save_attendance(route_name, date_str, attendance):
    initialize_excel()
    try:
        # Read existing data
        with pd.ExcelFile(EXCEL_FILE) as xls:
            sheets = {}
            for sheet in xls.sheet_names:
                sheets[sheet] = pd.read_excel(xls, sheet)
        
        # Get the specific route sheet
        df = sheets[route_name].copy()
        
        # Add date column if it doesn't exist
        if date_str not in df.columns:
            df[date_str] = ''  # Initialize with empty values
        
        # Update attendance values
        for student_id, is_present in attendance.items():
            # Extract index from student_id (format: "Route_X")
            try:
                idx = int(student_id.split('_')[1])
                # Only update if student is active
                student_status = df.at[idx, 'Status'] if 'Status' in df.columns else 'Active'
                if student_status == 'Active':
                    df.at[idx, date_str] = 'P' if is_present else 'A'
            except (IndexError, ValueError):
                continue
        
        # Save all sheets back to Excel
        with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
            for sheet_name, sheet_df in sheets.items():
                if sheet_name == route_name:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                else:
                    sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        return True
    except Exception as e:
        print(f"Error saving attendance for {route_name} on {date_str}: {e}")
        return False

# Add student to a route
def add_student_to_route(route_name, student_name):
    initialize_excel()
    try:
        # Read existing data
        with pd.ExcelFile(EXCEL_FILE) as xls:
            sheets = {}
            for sheet in xls.sheet_names:
                sheets[sheet] = pd.read_excel(xls, sheet)
        
        # Get the specific route sheet
        df = sheets[route_name].copy()
        
        # Add new student with Active status
        new_row = pd.DataFrame({
            'Name': [student_name],
            'Status': ['Active'],
            'Archive Date': ['']
        })
        df = pd.concat([df, new_row], ignore_index=True)
        
        # Save all sheets back to Excel
        with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
            for sheet_name, sheet_df in sheets.items():
                if sheet_name == route_name:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                else:
                    sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        return True
    except Exception as e:
        print(f"Error adding student to {route_name}: {e}")
        return False

# Archive student from a route (instead of deleting)
def archive_student_from_route(student_id):
    initialize_excel()
    try:
        route_name, student_idx = student_id.split('_')
        student_idx = int(student_idx)
        
        # Read existing data
        with pd.ExcelFile(EXCEL_FILE) as xls:
            sheets = {}
            for sheet in xls.sheet_names:
                sheets[sheet] = pd.read_excel(xls, sheet)
        
        # Get the specific route sheet
        df = sheets[route_name].copy()
        
        # Update student status to Archived
        if 'Status' not in df.columns:
            df['Status'] = 'Active'  # Add Status column if it doesn't exist
        if 'Archive Date' not in df.columns:
            df['Archive Date'] = ''  # Add Archive Date column if it doesn't exist
            
        df.at[student_idx, 'Status'] = 'Archived'
        df.at[student_idx, 'Archive Date'] = datetime.now().strftime('%Y-%m-%d')
        
        # Save all sheets back to Excel
        with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
            for sheet_name, sheet_df in sheets.items():
                if sheet_name == route_name:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                else:
                    sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        return True
    except Exception as e:
        print(f"Error archiving student {student_id}: {e}")
        return False

# Restore archived student
def restore_student(student_id):
    initialize_excel()
    try:
        route_name, student_idx = student_id.split('_')
        student_idx = int(student_idx)
        
        # Read existing data
        with pd.ExcelFile(EXCEL_FILE) as xls:
            sheets = {}
            for sheet in xls.sheet_names:
                sheets[sheet] = pd.read_excel(xls, sheet)
        
        # Get the specific route sheet
        df = sheets[route_name].copy()
        
        # Update student status to Active
        if 'Status' in df.columns:
            df.at[student_idx, 'Status'] = 'Active'
            df.at[student_idx, 'Archive Date'] = ''
        
        # Save all sheets back to Excel
        with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
            for sheet_name, sheet_df in sheets.items():
                if sheet_name == route_name:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                else:
                    sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        return True
    except Exception as e:
        print(f"Error restoring student {student_id}: {e}")
        return False

# Get archived students for a route
def get_archived_students(route_name):
    return get_students_for_route(route_name, include_archived=True)

# Get student history
def get_student_history(student_id):
    initialize_excel()
    try:
        route_name, student_idx = student_id.split('_')
        student_idx = int(student_idx)
        
        df = pd.read_excel(EXCEL_FILE, sheet_name=route_name)
        history = []
        
        # Iterate through all date columns (excluding 'Name', 'Status', 'Archive Date')
        for col in df.columns:
            if col not in ['Name', 'Status', 'Archive Date']:
                if col in df.columns and pd.notna(df.at[student_idx, col]):
                    status = df.at[student_idx, col]
                    history.append({
                        'date': col,
                        'status': status == 'P'
                    })
        
        return history
    except Exception as e:
        print(f"Error getting history for student {student_id}: {e}")
        return []

# Get date history
def get_date_history(date_str):
    initialize_excel()
    try:
        xls = pd.ExcelFile(EXCEL_FILE)
        history = []
        
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name)
            
            if date_str in df.columns:
                for idx, row in df.iterrows():
                    # Only include active students in date history
                    status = row.get('Status', 'Active')
                    if status == 'Active' and pd.notna(row[date_str]):
                        status_value = row[date_str]
                        history.append({
                            'student_name': row['Name'],
                            'route': sheet_name,
                            'status': status_value == 'P'
                        })
        
        return history
    except Exception as e:
        print(f"Error getting history for date {date_str}: {e}")
        return []

# Get Nepali date for today
def get_nepali_date():
    today = datetime.today()
    nepali_dt = nepali_date.from_datetime_date(today.date())
    return nepali_dt.strftime('%Y-%m-%d')

# Sync offline data endpoint
@app.route('/api/sync', methods=['POST'])
def sync_offline_data():
    """Endpoint to sync offline data when connection is restored"""
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

# API Routes
@app.route('/api/routes')
def get_routes():
    try:
        routes = get_all_routes()
        return jsonify({'routes': routes})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students')
def get_all_students():
    try:
        routes = get_all_routes_and_students()
        all_students = []
        for route_students in routes.values():
            all_students.extend(route_students)
        return jsonify({'students': all_students})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/<route_name>')
def get_route_students(route_name):
    try:
        # By default, only return active students
        include_archived = request.args.get('archived', 'false').lower() == 'true'
        students = get_students_for_route(route_name, include_archived)
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
            # Return updated summary
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
def archive_student(student_id):
    try:
        if archive_student_from_route(student_id):
            return jsonify({'message': 'Student archived successfully'})
        else:
            return jsonify({'error': 'Failed to archive student'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/<student_id>/restore', methods=['POST'])
def restore_archived_student(student_id):
    try:
        if restore_student(student_id):
            return jsonify({'message': 'Student restored successfully'})
        else:
            return jsonify({'error': 'Failed to restore student'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/<route_name>/archived')
def get_archived_students_route(route_name):
    try:
        students = get_archived_students(route_name)
        # Filter to only archived students
        archived_students = [s for s in students if s['status'] == 'Archived']
        return jsonify({'students': archived_students})
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

if __name__ == '__main__':
    # Initialize the Excel file
    initialize_excel()
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))