#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright © 2023 Ye Chang yech1990@gmail.com
# Distributed under terms of the GNU license.


import io
import math
import os
import tempfile

import pandas as pd
import plotly.express as px
import streamlit as st

from run import export_amp, export_cq, export_melt, extract_run

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


def show_result_table(result_table, placeholder):
    with placeholder.container():
        st.subheader("Cq values", divider="rainbow")
        st.dataframe(
            result_table.style.background_gradient(axis=None).format("{:.2f}"),
            use_container_width=True,
            height=(result_table.shape[0] + 1) * 35 + 3,
        )

        df_xlsx = to_excel(result_table)
        st.download_button(
            label="📥 Download Current Result",
            data=df_xlsx,
            file_name=name_base + ".xlsx",
        )


def show_amp_table(amp_table, placeholder):
    with placeholder.container():
        st.subheader("Amp curves", divider="rainbow")
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

        fold = st.number_input(
            "The fold of template used for final PCR?", value=1.00
        )
        if st.button("How many PCR cycle do I need?"):
            max_cq_cutoff = 0.2
            df = amp_table.copy()
            # df.loc[:, df.max(axis=0) > max_cq_cutoff] = 0
            amp_table_delta = (df - df.shift(1)).idxmax(axis=0) - round(
                math.log2(fold), 0
            )
            amp_table_delta[df.max(axis=0) <= max_cq_cutoff] = pd.NA
            amp_table_delta = amp_table_delta.reset_index()
            amp50_plate = (
                amp_table_delta.join(
                    amp_table_delta["Well"].str.extract(
                        r"(?P<letter>[A-Z])(?P<digit>\d+)"
                    )
                )
                .assign(digit=lambda x: x.digit.astype(int))
                .pivot(
                    index="letter",
                    columns="digit",
                    values=0,
                )
            )
            st.subheader("50% cycles", divider="rainbow")
            st.dataframe(
                amp50_plate.style.background_gradient(axis=None).format(
                    "{:.0f}"
                ),
                use_container_width=True,
                height=(amp50_plate.shape[0] + 1) * 35 + 3,
            )


def show_melt_table(melt_table, placeholder):
    with placeholder.container():
        st.subheader("Melt curves", divider="rainbow")
        melt_table = melt_table - melt_table.shift(-1)
        fig = px.line(melt_table, x=melt_table.index, y=melt_table.columns)
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


# File uploader widget
uploaded_file = st.file_uploader("Choose a PDF file", type="lc96p")
if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".lc96p"
    ) as temp_file:
        name_base = uploaded_file.name.rsplit(".")[0]
        temp_file.write(uploaded_file.getvalue())
        temp_file_path = temp_file.name

    loading_placeholder = st.empty()
    amp_placeholder = st.empty()
    melt_placeholder = st.empty()
    cq_placeholder = st.empty()
    if (
        "file_id" not in st.session_state
        or st.session_state.file_id != uploaded_file.file_id
    ):
        try:
            with loading_placeholder.container():
                with st.spinner("Converting the file... Please wait."):
                    run = extract_run(temp_file_path)
            with loading_placeholder.container():
                with st.spinner("Exporting amp table... Please wait."):
                    amp_table = export_amp(run)
                    show_amp_table(amp_table, amp_placeholder)
            with loading_placeholder.container():
                with st.spinner("Exporting melt table... Please wait."):
                    melt_table = export_melt(run)
                    show_melt_table(melt_table, melt_placeholder)
            with loading_placeholder.container():
                with st.spinner("Exporting cq table... Please wait."):
                    result_table = export_cq(run)
                    show_result_table(result_table, cq_placeholder)
        except Exception as e:
            st.error(f"An error occurred while parsing the lc96p file: {e}")
        st.session_state.file_id = uploaded_file.file_id
        st.session_state.amp_table = amp_table
        st.session_state.melt_table = melt_table
        st.session_state.result_table = result_table
    else:
        amp_table = st.session_state.amp_table
        show_amp_table(amp_table, amp_placeholder)
        melt_table = st.session_state.melt_table
        show_melt_table(melt_table, melt_placeholder)
        result_table = st.session_state.result_table
        show_result_table(result_table, cq_placeholder)

    # Delete the temporary files
    os.remove(temp_file_path)
