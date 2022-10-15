#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright © 2022 Ye Chang yech1990@gmail.com
# Distributed under terms of the GNU license.
#
# Created: 2022-06-05 17:26

import os
import subprocess
import sys

import pandas as pd

if len(sys.argv) < 2:
    sys.exit("Usage: run.py input_file.lc96p")

input_file = sys.argv[1]

# create 3 files for each input
rdml_file = input_file.rsplit(".", 1)[0] + ".rdml"
tsv_file = input_file.rsplit(".", 1)[0] + ".tsv"
excel_file = input_file.rsplit(".", 1)[0] + ".xlsx"


script_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "rdml.py"
)


subprocess.call(
    [
        script_path,
        "-lrp",
        input_file,
        "--pcrEfficiencyExl",
        "0.05",
        "--excludeNoPlateau",
        "--excludeEfficiency",
        "mean",
        "--timeRun",
        "-o",
        rdml_file,
        "--saveResults",
        tsv_file,
    ]
)


df = pd.read_csv(input_file, sep="\t").loc[
    :, ["well", "Cq (mean eff) - no plateau - stat efficiency"]
]
df_plate = (
    df.join(df["well"].str.extract(r"(?P<letter>[A-Z])(?P<digit>\d+)"))
    .assign(digit=lambda x: x.digit.astype(int))
    .pivot(
        index="letter",
        columns="digit",
        values="Cq (mean eff) - no plateau - stat efficiency",
    )
)

df_plate.to_excel(excel_file, sheet_name="quant")
