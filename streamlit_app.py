# -*- coding: utf-8 -*-
"""Streamlit wrapper that serves the same self-contained dashboard.html.

The heavy lifting (scrape + compute) happens locally via run_all.py, which bakes all data
into dashboard.html. This app just renders that file, so Streamlit needs no scraping and no
database. Deploy on Streamlit Community Cloud pointing at this file.
"""
import pathlib
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title='FPTE 2026 — STAH', layout='wide')

html = pathlib.Path('dashboard.html').read_text(encoding='utf-8')
components.html(html, height=1400, scrolling=True)
