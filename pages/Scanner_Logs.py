import streamlit as st
import pandas as pd
import re
from pathlib import Path

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
    return pd.DataFrame(log_data)

st.set_page_config(page_title="Scanner Monitor", page_icon="🖥️", layout="wide")
st.title("🖥️ Scanner Monitor & Progress")

# refresh button at the top of the page
if st.button("🔄 Refresh Status"):
    st.rerun()

df_logs = parse_logs(LOG_FILE)

if not df_logs.empty:
    # --- part 1: progress bar (two-step) ---
    
    # find the progress messages from the two steps
    filter_progress_lines = df_logs[df_logs["Message"].str.contains("FILTER_PROGRESS:", na=False)]
    scan_progress_lines = df_logs[df_logs["Message"].str.contains("SCAN_PROGRESS:", na=False)]
    
    if not scan_progress_lines.empty:
        # step 2: deep analysis
        latest_msg = scan_progress_lines.iloc[-1]["Message"]
        match = re.search(r"SCAN_PROGRESS:\s*(\d+)/(\d+)", latest_msg)
        if match:
            current, total = int(match.group(1)), int(match.group(2))
            st.subheader(f"Step 2/2: Deep Analysis ({current} / {total} candidates)")
            st.progress(current / total)
            if current == total:
                st.success("✅ Full scan completed successfully.")
            else:
                st.info("⏳ Running pattern detection and AI scoring...")

    elif not filter_progress_lines.empty:
        # step 1: coarse filtering
        latest_msg = filter_progress_lines.iloc[-1]["Message"]
        match = re.search(r"FILTER_PROGRESS:\s*(\d+)/(\d+)", latest_msg)
        if match:
            current, total = int(match.group(1)), int(match.group(2))
            st.subheader(f"Step 1/2: Coarse Filtering ({current} / {total} tickers)")
            st.progress(current / total)
            st.warning(f"🔍 Filtering {total} tickers by Market Cap and Trend...")

    else:
        st.info("Scanner is initializing or waiting for progress data...")

    st.divider()

    # --- part 2: filtering and searching logs ---
    col1, col2 = st.columns([2, 1])
    with col1:
        search = st.text_input("🔍 Search Logs (Ticker, Error, etc.)")
    with col2:
        levels = df_logs["Level"].unique().tolist()
        selected_levels = st.multiselect("Filter Levels", levels, default=levels)

    filtered_df = df_logs[df_logs["Level"].isin(selected_levels)]
    if search:
        filtered_df = filtered_df[filtered_df["Message"].str.contains(search, case=False, na=False)]

    st.dataframe(
        filtered_df.iloc[::-1],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Timestamp": st.column_config.TextColumn("Time", width="small"),
            "Level": st.column_config.TextColumn("Level", width="small"),
            "Message": st.column_config.TextColumn("Message", width="large")
        }
    )
else:
    st.warning("No log file found. Please run the scanner first.")