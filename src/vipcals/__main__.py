#!/usr/bin/env ParselTongue
# -*- coding: utf-8 -*-

import argparse
import time

parser = argparse.ArgumentParser(
                    prog = 'VIPCALs',
                    description = 'Automated VLBI data calibration pipeline using AIPS')

# Positional arguments
parser.add_argument('userno', type = int)
parser.add_argument('filepath', type = str)
parser.add_argument('target', type = str)
parser.add_argument('disk_number', type = int)

# Options
op = parser.add_argument_group('options')
op.add_argument('-la', '--load_all',  required=False, action="store_true")

# Read arguments
args = parser.parse_args()
if args.load_all:
    load_all = True