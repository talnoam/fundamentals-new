import json
import requests
import streamlit as st
from pathlib import Path
from packaging import version

VERSION_FILE = Path(__file__).parent.parent / "version.json"

class VersionManager:
    @staticmethod
    def get_local_info():
        try:
            with open(VERSION_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"version": "v0", "changelog": []}

    @staticmethod
    def check_for_updates():
        info = VersionManager.get_local_info()
        current_version = info.get("version")
        url = info.get("update_url")

        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                latest_version = response.text.strip()
                if version.parse(latest_version) > version.parse(current_version):
                    return latest_version
        except Exception:
            pass
        return None

    @staticmethod
    def display_version_sidebar():
        info = VersionManager.get_local_info()
        st.sidebar.caption(f"📦 Version: {info['version']}")
        st.sidebar.divider()
        
        latest = VersionManager.check_for_updates()
        if latest:
            st.sidebar.warning(f"🚀 New version available: {latest}")
            if st.sidebar.button("View Release Notes"):
                st.info("\n".join(info.get("changelog", [])))