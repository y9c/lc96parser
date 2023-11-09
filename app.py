#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright © 2023 Ye Chang yech1990@gmail.com
# Distributed under terms of the GNU license.


import os
import tempfile

import streamlit as st

from run import convert_file

# Streamlit app layout
st.title("lc96p qpcr Data Parser")


# File uploader widget
uploaded_file = st.file_uploader("Choose a PDF file", type="lc96p")
if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".lc96p"
    ) as temp_file:
        name_base = uploaded_file.name.rsplit(".")[0]
        temp_file.write(uploaded_file.getvalue())
        temp_file_path = temp_file.name
    with st.spinner("Converting the file... Please wait."):
        try:
            file_base = os.path.splitext(temp_file_path)[0]
            rdml_file = file_base + ".rdml"
            excel_file = file_base + ".xlsx"
            df_plate = convert_file(temp_file_path, rdml_file, excel_file)
            # Display the table
            st.write("Parsed Table:")
            st.dataframe(
                df_plate.style.background_gradient(axis=None).format("{:.2f}"),
                use_container_width=True,
                height=(df_plate.shape[0] + 1) * 35 + 3,
            )
            # Provide download links for rdml_file and excel_file
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="Download RDML file",
                    data=open(rdml_file, "rb"),
                    file_name=name_base + ".rdml",
                )
            with col2:
                st.download_button(
                    label="Download Excel file",
                    data=open(excel_file, "rb"),
                    file_name=name_base + ".xlsx",
                )
            # Delete the temporary files
            os.remove(temp_file_path)

        except Exception as e:
            st.error(f"An error occurred while parsing the lc96p file: {e}")

hide_streamlit_style = """
            <style>
            [data-testid="stToolbar"] {visibility: hidden !important;}
            footer {visibility: hidden !important;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
