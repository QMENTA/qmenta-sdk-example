import matplotlib

# This backend config avoids $DISPLAY errors in headless machines
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np
import pdfkit
from subprocess import call
from time import gmtime, strftime
from tornado import template

# AnalysisContext documentation: https://docs.qmenta.com/sdk/sdk.html
def run(context):
    
    # Get the analysis information dictionary (patient id, analysis name...)
    analysis_data = context.fetch_analysis_data()

    # Get the analysis settings (histogram range of intensities)
    settings = analysis_data['settings']

    # Get a T1 image from the input files
    t1_file_handler = context.get_files('input', modality='GRE')[0]
    t1_path = t1_file_handler.download('/root/')  # Download and automatically unpack  

    context.set_progress(message='Sorting DICOM data...')
    call([
    "python3",
    "/opt/QSMxT/run_0_dicomSort.py",
    t1_path, 
    "/00_dicom"
    ])


    context.set_progress(message='Converting DICOM data...')
    call([
    "python3",
    "/opt/QSMxT/run_1_dicomToBids.py",
    "/00_dicom", 
    "/01_bids"
    ])


    # Generate an example report
    # Since it is a head-less machine, it requires Xvfb to generate the pdf
    context.set_progress(message='Creating report...')

    report_path = '/root/report.pdf'

    data_report = {
        'logo_main': '/root/qmenta_logo.png',
        'ss': analysis_data['patient_secret_name'],
        'ssid': analysis_data['ssid'],
        'this_moment': strftime("%Y-%m-%d %H:%M:%S", gmtime()),
        'version': 1.0
    }

    loader = template.Loader('/root/')
    report_contents = loader.load('report_template.html').generate(data_report=data_report)

    if isinstance(report_contents, bytes):
        report_contents = report_contents.decode("utf-8")
    pdfkit.from_string(report_contents, report_path)

    # Upload the data and the report
    context.set_progress(message='Uploading results...')

    context.upload_file(report_path, 'report.pdf')
