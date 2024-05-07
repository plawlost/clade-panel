import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# Initialize database connection
conn = sqlite3.connect('clade_ai.db', check_same_thread=False)
c = conn.cursor()

# Ensure all required tables are created
def setup_database():
    with conn:
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
        c.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                action TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

setup_database()

# CSS styling
def load_css():
    """Load the CSS for dark mode, typewriter fonts, and other custom styles."""
    with open('styles.css', 'r') as file:
        st.markdown(f'<style>{file.read()}</style>', unsafe_allow_html=True)
        
# Utility functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username, password):
    c.execute('SELECT password, role, email FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    if user and user[0] == hash_password(password):
        return True, user[1], user[2]
    return False, None, None

def log_user_action(username, action):
    with conn:
        c.execute('INSERT INTO logs (username, action, timestamp) VALUES (?, ?, ?)',
                  (username, action, datetime.now()))

# Application main functions
def main():
    load_css()
    st_autorefresh(interval=60000, key='datarefresh')  # Refresh every minute for updates

    if "user" not in st.session_state:
        login_page()
    else:
        homepage()

def login_page():
    with st.sidebar:
        st.title("Login to Clade AI")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            auth, role, email = authenticate(username, password)
            if auth:
                st.session_state["user"] = username
                st.session_state["role"] = role
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")

def homepage():
    st.title(f"Clade AI Dashboard - Welcome, {st.session_state['user']}!")
    tab1, tab2, tab3 = st.tabs(["Dashboard", "Tasks", "Profiles"])

    with tab1:
        dashboard_view()
    with tab2:
        task_management()
    with tab3:
        user_profiles()

def dashboard_view():
    st.header("Project Overview")
    display_project_stats()
    display_user_activity()

def task_management():
    st.header("Manage Tasks")
    create_task_form()
    update_task_status()
    task_comments_section()

def user_profiles():
    st.header("User Profile Management")
    display_user_profiles()

# More detailed implementations of features
def display_project_stats():
    tasks = pd.read_sql('SELECT * FROM tasks', conn)
    fig = px.pie(tasks, names='status', title='Task Completion Status')
    st.plotly_chart(fig)

def display_user_activity():
    logs = pd.read_sql('SELECT * FROM logs ORDER BY timestamp DESC LIMIT 10', conn)
    st.write("Recent Activity Logs:")
    st.dataframe(logs)

def create_task_form():
    with st.form(key='task_form'):
        cols = st.columns((1, 2, 1))
        task_name = cols[0].text_input("Task Name")
        description = cols[1].text_area("Description")
        assigned_to = cols[2].selectbox("Assign To", pd.read_sql('SELECT username FROM users', conn)['username'])
        priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        deadline = st.date_input("Deadline", min_value=datetime.now())
        submit_button = st.form_submit_button("Create Task")
        if submit_button:
            with conn:
                c.execute('INSERT INTO tasks (task_name, assigned_to, deadline, status, description, priority) VALUES (?, ?, ?, "Pending", ?, ?)',
                          (task_name, assigned_to, deadline, description, priority))
            st.success("Task created successfully!")

def update_task_status():
    tasks = pd.read_sql('SELECT task_id, task_name FROM tasks', conn)
    task_id = st.selectbox("Select Task to Update", tasks['task_id'], format_func=lambda x: tasks.loc[tasks['task_id'] == x, 'task_name'].iloc[0])
    new_status = st.selectbox("New Status", ["Pending", "In Progress", "Completed"])
    if st.button("Update Status"):
        with conn:
            c.execute('UPDATE tasks SET status = ? WHERE task_id = ?', (new_status, task_id))
        st.success("Task status updated!")

def task_comments_section():
    st.subheader("Task Comments")
    task_id = st.selectbox("Select Task for Comments", pd.read_sql('SELECT task_id FROM tasks', conn)['task_id'])
    comments = pd.read_sql('SELECT * FROM comments WHERE task_id = ?', conn, params=(task_id,))
    st.write(comments)
    comment_text = st.text_area("Add Comment")
    if st.button("Post Comment"):
        with conn:
            c.execute('INSERT INTO comments (task_id, username, comment, timestamp) VALUES (?, ?, ?, ?)',
                      (task_id, st.session_state['user'], comment_text, datetime.now()))
        st.success("Comment posted!")

def display_user_profiles():
    users = pd.read_sql('SELECT * FROM users', conn)
    st.write("User Profiles:")
    st.dataframe(users)

if __name__ == "__main__":
    main()