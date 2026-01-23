import streamlit as st
import pandas as pd
import re
from pathlib import Path
from src.version_manager import VersionManager

# path to the log file as defined in scanner.py
LOG_FILE = Path(__file__).parent.parent / "scanner.log"

def parse_logs(log_path):
    if not log_path.exists():
        return pd.DataFrame()
    
    log_data = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            # parse the line by the format: Timestamp - Logger - Level - Message
            parts = line.strip().split(" - ")
            if len(parts) >= 4:
                log_data.append({
                    "Timestamp": parts[0],
                    "Level": parts[2],
                    "Message": " - ".join(parts[3:])
                })
    df = pd.DataFrame(log_data)
    if not df.empty:
        # convert Timestamp to Date for filtering
        df['Date'] = df['Timestamp'].str.split(' ').str[0]
    return df

st.set_page_config(page_title="Scanner Monitor", page_icon="🖥️", layout="wide")

# display the version in the sidebar
VersionManager.display_version_sidebar()

st.title("🖥️ Scanner Monitor & Progress")

# refresh button at the top of the page
if st.button("🔄 Refresh Status"):
    st.rerun()

df_logs = parse_logs(LOG_FILE)

if not df_logs.empty:

    st.sidebar.header("Log Filters")

    # filter by level
    all_levels = df_logs["Level"].unique().tolist()
    selected_levels = st.sidebar.multiselect("Filter by Level", all_levels, default=all_levels)

    # filter by date
    all_dates = sorted(df_logs["Date"].unique().tolist(), reverse=True)
    selected_date = st.sidebar.selectbox("Filter by Date", ["All Dates"] + all_dates)

    # --- fix: find the start of the current scan ---
    # search for the last line that contains the start of the filtering message
    start_indices = df_logs[df_logs["Message"].str.contains("Applying coarse filters to", na=False)].index
    
    if not start_indices.empty:
        current_run_df = df_logs.loc[start_indices[-1]:]
    else:
        current_run_df = df_logs

    # search for progress messages only within the current run
    scan_progress = current_run_df[current_run_df["Message"].str.contains("SCAN_PROGRESS:", na=False)]
    filter_progress = current_run_df[current_run_df["Message"].str.contains("FILTER_PROGRESS:", na=False)]
    
    # display progress by step order
    if not scan_progress.empty:
        latest_msg = scan_progress.iloc[-1]["Message"]
        match = re.search(r"SCAN_PROGRESS:\s*(\d+)/(\d+)", latest_msg)
        if match:
            current, total = int(match.group(1)), int(match.group(2))
            st.subheader(f"Step 2/2: Deep Analysis ({current} / {total})")
            st.progress(current / total)
    elif not filter_progress.empty:
        latest_msg = filter_progress.iloc[-1]["Message"]
        match = re.search(r"FILTER_PROGRESS:\s*(\d+)/(\d+)", latest_msg)
        if match:
            current, total = int(match.group(1)), int(match.group(2))
            st.subheader(f"Step 1/2: Coarse Filtering ({current} / {total})")
            st.progress(current / total)
    else:
        st.info("🚀 Starting new scan... Waiting for updates.")

    st.divider()

    # apply the filters to the dataframe
    filtered_df = df_logs[df_logs["Level"].isin(selected_levels)]
    if selected_date != "All Dates":
        filtered_df = filtered_df[filtered_df["Date"] == selected_date]

    search = st.text_input("🔍 Search Logs")
    if search:
        filtered_df = filtered_df[filtered_df["Message"].str.contains(search, case=False, na=False, regex=False)]

    # display the filtered dataframe
    st.dataframe(
        filtered_df.iloc[::-1],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Timestamp": st.column_config.TextColumn("Time"),
            "Level": st.column_config.TextColumn("Level"),
            "Message": st.column_config.TextColumn("Message", width="large"),
            "Date": None  # hide the helper column
        }
    )
else:
    st.warning("No logs found.")