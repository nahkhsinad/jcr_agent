import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime, time, date, timedelta
import uuid
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set page config
st.set_page_config(page_title="JCR Agent", layout="wide")

#- - -
# Database connection function
def get_connection():
    db_path = '/mnt/data/database.db'  # Use /mnt/data/ for Streamlit Cloud
    if not os.path.exists(db_path):
        download_db(db_path)
    return sqlite3.connect(db_path, check_same_thread=False)

# Function to download the database file from GitHub
def download_db(db_path):
    url = "https://raw.githubusercontent.com/nahkhsinad/jcr_agent/main/database.db"
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(db_path, 'wb') as f:
            f.write(response.content)
        logger.info("Database file downloaded successfully.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading database file: {e}")
        st.error("Failed to download the database file. Please try again later.")
#-
@st.cache_data
def load_data(_refresh=False):
    if _refresh:
        st.cache_data.clear()
    try:
        with get_connection() as conn:
            query = "SELECT * FROM jcr"
            df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return pd.DataFrame()
#- - -

def main():
    st.markdown('<div class="center-align">', unsafe_allow_html=True)
    st.title("Job Card Register Agent")
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        with st.container():
            st.header('📝')
            st.header('Create')
            st.markdown('<p class="card-text">Add new entries to the JCR database</p>', unsafe_allow_html=True)
            if st.button("Add Entry", key="add_entry"):
                st.session_state.page = 'create'
                st.session_state.create_step = 'select'
                st.rerun()

    with col2:
        with st.container():
            st.header('🖊️')
            st.header('Update')
            st.markdown('<p class="card-text">Update existing entries in the JCR database</p>', unsafe_allow_html=True)
            if st.button("Update Entry", key="update_entry"):
                st.session_state.page = 'update'
                st.session_state.update_step = 'select'
                st.rerun()

    with col3:
        with st.container():
            st.header('👀')
            st.header('View')
            st.markdown('<p class="card-text">View existing entries in the JCR database</p>', unsafe_allow_html=True)
            if st.button("View Entries", key="view_entries"):
                st.session_state.page = 'view'
                st.rerun()

    with col4:
        with st.container():
            st.header('📊')
            st.header('Insights')
            st.markdown('<p class="card-text">Analyze data from the JCR database</p>', unsafe_allow_html=True)
            if st.button("Get Insights", key="get_insights"):
                st.session_state.page = 'insights'
                st.rerun()

    if 'page' not in st.session_state:
        st.session_state.page = "home"

    if st.session_state.page == "create":
        create_entry()
    elif st.session_state.page == "update":
        update_entry()
    elif st.session_state.page == "view":
        view_entries()
    elif st.session_state.page == "insights":
        show_insights()

def create_entry():
    st.header("Create New Entry")
    
    if 'create_step' not in st.session_state:
        st.session_state.create_step = 'select'

    if st.session_state.create_step == 'select':
        selection = st.radio("Select", ["Team", "Individual"])
        if st.button("Next", key="next_to_fill"):
            st.session_state.selection = selection
            st.session_state.create_step = 'fill_info'
            st.rerun()
    
    elif st.session_state.create_step == 'fill_info':
        data = load_data()
        with st.form("entry_form"):
            # Invisible fields
            job_uid = str(uuid.uuid4())
            job_created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            job_created_by = "jcr_agent"  # Change this to user email when authentication is implemented
            
            # Visible fields
            job_date = st.date_input("Job Date", value=date.today() + timedelta(days=1))
            job_date_str = job_date.strftime("%d/%m/%Y")
            
            teams = data['Employee_Team'].unique().tolist()
            employees = data['Employee_Name'].unique().tolist()
            
            if st.session_state.selection == "Team":
                team = st.selectbox("Employee_Team", teams)
                team_members = st.multiselect("Select Team Members", employees)
            else:
                team = st.selectbox("Employee_Team", teams)
                name = st.selectbox("Employee_Name", employees)
            
            presence = st.selectbox("Presence", ["Y", "N"])
            project = st.selectbox("Project", data['Project'].unique().tolist())
            
            phase_space = st.text_input("PHASE / SPACE")
            
            products = st.text_input("Enter Product Name")
            
            part_number = st.text_input("Enter Part#")
            
            part_name = st.text_input("Enter Part Name")
            
            task = st.text_input("Enter Task")
            
            task_quantity = st.number_input("Task_Q", min_value=0, max_value=100, step=1)
            
            start_time = st.time_input("Start_Time", value=time(9, 0))
            
            finish_time = st.time_input("Finish_Time", value=time(18, 0))
            
            status = st.selectbox("Status", ["TBS", "WIP", "DONE", "HOLD"])
            
            remarks = st.text_area("REMARKS")
            
            submitted = st.form_submit_button("Submit")
            if submitted:
                try:
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        
                        if st.session_state.selection == "Team":
                            for member in team_members:
                                cursor.execute("""
                                INSERT INTO jcr (Job_UID, Job_Created_At, Job_Created_By, Job_Date, Employee_Team, Employee_Name, Presence, Project, PHASE_SPACE, Product, Part_number, Part_Name, Task, Task_Q, Start_Time, Finish_Time, Status, Remarks)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (str(uuid.uuid4()), job_created_at, job_created_by, job_date_str, team, member, presence, project, phase_space, products, part_number, part_name, task, task_quantity, start_time.strftime("%H:%M"), finish_time.strftime("%H:%M"), status, remarks))
                        else:
                            cursor.execute("""
                            INSERT INTO jcr (Job_UID, Job_Created_At, Job_Created_By, Job_Date, Employee_Team, Employee_Name, Presence, Project, PHASE_SPACE, Product, Part_number, Part_Name, Task, Task_Q, Start_Time, Finish_Time, Status, Remarks)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (job_uid, job_created_at, job_created_by, job_date_str, team, name, presence, project, phase_space, products, part_number, part_name, task, task_quantity, start_time.strftime("%H:%M"), finish_time.strftime("%H:%M"), status, remarks))
                        
                        conn.commit()
                    st.success("Entry successfully added to the database!")
                    st.session_state.create_step = 'select'
                    st.rerun()
                except Exception as e:
                    logger.error(f"Error adding entry: {e}")
                    st.error(f"An error occurred while adding the entry: {e}")

def update_entry():
    st.header("Update Existing Entry")
    
    if 'update_step' not in st.session_state:
        st.session_state.update_step = 'select'

    data = load_data()

    if st.session_state.update_step == 'select':
        selection = st.radio("Select", ["Team", "Individual"])
        if st.button("Next", key="next_to_update"):
            st.session_state.selection = selection
            st.session_state.update_step = 'choose_entry'
            st.rerun()

    elif st.session_state.update_step == 'choose_entry':
        if st.session_state.selection == "Team":
            team = st.selectbox("Select Team", data['Employee_Team'].unique().tolist())
            team_entries = data[data['Employee_Team'] == team]
            selected_date = st.selectbox("Select Date", sorted(team_entries['Job_Date'].unique().tolist()))
            team_members = team_entries[(team_entries['Job_Date'] == selected_date) & (team_entries['Employee_Team'] == team)]['Employee_Name'].unique().tolist()
            selected_members = st.multiselect("Select Team Members to Update", team_members)
        else:
            name = st.selectbox("Select Employee", data['Employee_Name'].unique().tolist())
            individual_entries = data[data['Employee_Name'] == name]
            selected_entry = st.selectbox("Select Entry to Update", individual_entries['Job_UID'].tolist(), 
                                          format_func=lambda x: f"{x} - {individual_entries[individual_entries['Job_UID'] == x]['Job_Date'].values[0]} - {individual_entries[individual_entries['Job_UID'] == x]['Project'].values[0]}")

        if st.button("Next", key="next_to_update_form"):
            st.session_state.update_step = 'update_form'
            if st.session_state.selection == "Team":
                st.session_state.team_update_info = {'team': team, 'date': selected_date, 'members': selected_members}
            else:
                st.session_state.individual_update_info = {'entry_id': selected_entry}
            st.rerun()

    elif st.session_state.update_step == 'update_form':
        with st.form("update_form"):
            if st.session_state.selection == "Team":
                team_info = st.session_state.team_update_info
                st.write(f"Updating entries for team: {team_info['team']} on date: {team_info['date']}")
                entries_to_update = data[(data['Employee_Team'] == team_info['team']) & 
                                         (data['Job_Date'] == team_info['date']) & 
                                         (data['Employee_Name'].isin(team_info['members']))]
                st.write(f"Number of entries to update: {len(entries_to_update)}")
                st.write("Entries to be updated:")
                st.write(entries_to_update[['Employee_Name', 'Job_Date', 'Project', 'Status']])
            else:
                entry_id = st.session_state.individual_update_info['entry_id']
                entry_to_update = data[data['Job_UID'] == entry_id].iloc[0]
                st.write(f"Updating entry for: {entry_to_update['Employee_Name']} on date: {entry_to_update['Job_Date']}")

            # Fields to update
            new_finish_time = st.time_input("New Finish Time", value=time(18, 0))
            new_status = st.selectbox("New Status", ["TBS", "WIP", "DONE", "HOLD"])
            new_remarks = st.text_area("New Remarks")

            submitted = st.form_submit_button("Update Entry")

            if submitted:
                try:
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        if st.session_state.selection == "Team":
                            update_query = """
                            UPDATE jcr 
                            SET Finish_Time = ?, Status = ?, Remarks = ?
                            WHERE Employee_Team = ? AND Job_Date = ? AND Employee_Name IN ({})
                            """.format(','.join(['?']*len(team_info['members'])))
                            
                            params = (new_finish_time.strftime("%H:%M"), new_status, new_remarks, 
                                      team_info['team'], team_info['date']) + tuple(team_info['members'])
                            
                            cursor.execute(update_query, params)
                            st.success(f"Updated {cursor.rowcount} entries successfully!")
                        else:
                            cursor.execute("""
                            UPDATE jcr 
                            SET Finish_Time = ?, Status = ?, Remarks = ?
                            WHERE Job_UID = ?
                            """, (new_finish_time.strftime("%H:%M"), new_status, new_remarks, entry_id))
                            st.success("Entry updated successfully!")
                        conn.commit()
                    load_data.clear()
                    st.session_state.update_step = 'select'
                    st.rerun()
                except Exception as e:
                    logger.error(f"Error updating entry: {e}")
                    st.error(f"An error occurred while updating the entry: {e}")

def view_entries():
    st.header("View Entries")
    
    if st.button("Refresh Data"):
        load_data.clear()
        st.success("Data refreshed successfully!")
        st.rerun()
    
    data = load_data()
    
    # Display the table first
    st.dataframe(data, use_container_width=True)
    
    # Create collapsible filter section
    with st.expander("Filter Data"):
        filters = {}
        for column in data.columns:
            filters[column] = st.text_input(f"Filter {column}")

        # Apply filters
        filtered_data = data.copy()
        for column, filter_value in filters.items():
            if filter_value:
                filtered_data = filtered_data[filtered_data[column].astype(str).str.contains(filter_value, case=False)]

        # Display filtered data if any filters are applied
        if any(filters.values()):
            st.subheader("Filtered Data")
            st.dataframe(filtered_data, use_container_width=True)

    # Column analysis
    st.subheader("Column Analysis")
    selected_column = st.selectbox("Select a column for analysis", data.columns)
    
    if data[selected_column].dtype == 'object':
        value_counts = data[selected_column].value_counts()
        fig = px.bar(x=value_counts.index, y=value_counts.values, title=f"Distribution of {selected_column}")
        st.plotly_chart(fig)

        # Word Cloud
        if len(value_counts) > 0:
            text = ' '.join(value_counts.index.astype(str))
            try:
                wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
                fig, ax = plt.subplots()
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis('off')
                st.pyplot(fig)
            except ValueError as e:
                st.warning(f"Could not generate word cloud: {str(e)}")
        else:
            st.warning("Not enough data to generate a word cloud.")
    elif data[selected_column].dtype in ['int64', 'float64']:
        fig = px.histogram(data, x=selected_column, title=f"Distribution of {selected_column}")
        st.plotly_chart(fig)

def show_insights():
    st.header("Data Insights")
    
    data = load_data()
    
    if data.empty:
        st.warning("No data available to show insights.")
        return

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Project Distribution")
        project_dist = data['Project'].value_counts()
        fig = px.pie(values=project_dist.values, names=project_dist.index, title="Projects Distribution")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Task Status")
        status_dist = data['Status'].value_counts()
        fig = px.bar(x=status_dist.index, y=status_dist.values, title="Task Status Distribution")
        st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Employee Workload")
    employee_workload = data.groupby('Employee_Name')['Task_Q'].sum().sort_values(ascending=False)
    fig = px.bar(x=employee_workload.index, y=employee_workload.values, title="Employee Workload")
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Project Timeline")
    try:
        timeline_data = data.copy()
        timeline_data['Job_Date'] = pd.to_datetime(timeline_data['Job_Date'], format='%d/%m/%Y', errors='coerce')
        timeline_data = timeline_data.dropna(subset=['Job_Date'])
        
        if not timeline_data.empty:
            project_tasks = timeline_data.groupby(['Job_Date', 'Project'])['Task_Q'].sum().reset_index()
            fig = px.line(project_tasks, x='Job_Date', y='Task_Q', color='Project', title="Number of Tasks Done on Each Project Over Time")
            fig.update_xaxes(title_text="Date")
            fig.update_yaxes(title_text="Number of Tasks")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No valid timeline data available after date parsing.")
    except Exception as e:
        logger.error(f"Error creating project timeline: {e}")
        st.error(f"An error occurred while creating the project timeline: {e}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Uncaught exception: {e}")
        st.error(f"An unexpected error occurred: {e}")
