#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright © 2023 Ye Chang yech1990@gmail.com
# Distributed under terms of the GNU license.


import io
import os
import tempfile

import pandas as pd
import plotly.express as px
import streamlit as st

from run import run_lrp

# Streamlit app layout
st.title("lc96p qpcr Data Parser")


def to_excel(df):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine="xlsxwriter")
    df.to_excel(writer, index=True, sheet_name="quant")
    workbook = writer.book
    worksheet = writer.sheets["quant"]
    format1 = workbook.add_format({"num_format": "0.000"})
    worksheet.set_column("A:A", None, format1)
    writer.close()
    processed_data = output.getvalue()
    return processed_data


hide_streamlit_style = """
            <style>
            [data-testid="stToolbar"] {visibility: hidden !important;}
            footer {visibility: hidden !important;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

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
            amp_table, result_table = run_lrp(temp_file_path)
            # st.line_chart(amp_table)

            fig = px.line(amp_table, x=amp_table.index, y=amp_table.columns)
            fig.update_layout(
                clickmode="event+select",
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.12,
                    xanchor="center",
                    x=0.5,
                    traceorder="normal",
                    bgcolor=None,
                    borderwidth=0,
                    itemsizing="constant",
                    tracegroupgap=0,
                    entrywidth=1 / 12,
                    entrywidthmode="fraction",
                ),
                height=550,
            )
            st.plotly_chart(fig, use_container_width=True, height=550)

            st.dataframe(
                result_table.style.background_gradient(axis=None).format(
                    "{:.2f}"
                ),
                use_container_width=True,
                height=(result_table.shape[0] + 1) * 35 + 3,
            )
            df_xlsx = to_excel(result_table)
            st.download_button(
                label="📥 Download Current Result",
                data=df_xlsx,
                file_name=name_base + ".xlsx",
            )

        except Exception as e:
            st.error(f"An error occurred while parsing the lc96p file: {e}")
    # Delete the temporary files
    os.remove(temp_file_path)
