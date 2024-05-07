import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# Database initialization
conn = sqlite3.connect('clade_ai.db', check_same_thread=False)
c = conn.cursor()

def create_tables():
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            role TEXT,
            email TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT,
            assigned_to TEXT,
            deadline DATETIME,
            status TEXT,
            description TEXT,
            priority TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            username TEXT,
            comment TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

create_tables()

# Password hashing
def hash_password(password):
    return hashlib.sha1(password.encode()).hexdigest()

# Authentication
def authenticate(username, password):
    c.execute('SELECT password, role FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    if user and user[0] == hash_password(password):
        return True, user[1]
    return False, None

# Main application function
def main():
    st_autorefresh(interval=5000, key='datarefresh')  # Refresh every 5 seconds

    if "user" not in st.session_state:
        login_page()
    else:
        dashboard()

def login_page():
    with st.sidebar:
        st.title("Login to Clade AI")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            auth, role = authenticate(username, password)
            if auth:
                st.session_state["user"] = username
                st.session_state["role"] = role
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")

def dashboard():
    st.title(f"Clade AI Dashboard - Welcome {st.session_state['user']}")
    tab1, tab2, tab3 = st.tabs(["Task Management", "Analytics", "User Profiles"])

    with tab1:
        manage_tasks()
        view_comments()

    with tab2:
        task_analytics()

    with tab3:
        manage_profiles()

# User and Task Management
def manage_tasks():
    st.subheader("Create and Manage Tasks")
    with st.form("task_form"):
        cols = st.columns(2)
        task_name = cols[0].text_input("Task Name")
        description = cols[1].text_area("Task Description")
        assigned_to = cols[0].selectbox("Assign To", pd.read_sql('SELECT username FROM users', conn)['username'])
        priority = cols[1].selectbox("Priority", ["High", "Medium", "Low"])
        deadline = cols[0].date_input("Deadline", min_value=datetime.now())
        submitted = st.form_submit_button("Create Task")
        if submitted:
            c.execute('INSERT INTO tasks (task_name, assigned_to, deadline, status, description, priority) VALUES (?, ?, ?, "Pending", ?, ?)',
                      (task_name, assigned_to, deadline, description, priority))
            conn.commit()
            st.success("Task created successfully!")

# Task Comments
def view_comments():
    task_id = st.selectbox("Select Task to View Comments", pd.read_sql('SELECT task_id FROM tasks', conn)['task_id'])
    comments = pd.read_sql('SELECT username, comment, timestamp FROM comments WHERE task_id = ?', conn, params=(task_id,))
    st.write(comments)

# Task Analytics
def task_analytics():
    st.subheader("Task Analytics")
    tasks = pd.read_sql('SELECT * FROM tasks', conn)
    status_fig = px.pie(tasks, names='status', title='Task Status Distribution')
    priority_fig = px.bar(tasks, x='task_name', y='priority', color='status', title='Tasks by Priority and Status')
    st.plotly_chart(status_fig)
    st.plotly_chart(priority_fig)

# User Profiles
def manage_profiles():
    st.subheader("User Profiles and Settings")
    user_details = pd.read_sql('SELECT * FROM users WHERE username = ?', conn, params=(st.session_state['user'],))
    st.json(user_details.to_json(orient='records'))

if __name__ == "__main__":
    main()