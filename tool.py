import matplotlib

# This backend config avoids $DISPLAY errors in headless machines
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np
import pdfkit
from subprocess import call
from time import gmtime, strftime
from tornado import template
import glob


# AnalysisContext documentation: https://docs.qmenta.com/sdk/sdk.html
def run(context):
    
    # Get the analysis information dictionary (patient id, analysis name...)
    analysis_data = context.fetch_analysis_data()

    # Get the analysis settings (histogram range of intensities)
    settings = analysis_data['settings']

    # Get a T1 image from the input files
    file_handler = context.get_files('input')[0]
    path = file_handler.download('/root/')  # Download and automatically unpack  

    context.set_progress(message='unpacking sub archives')
    zip_files = glob.glob(path+"/*.zip")
    context.set_progress(message='found ' + str(len(zip_files)) + ' archives')
    for file in zip_files:
        context.set_progress(message='unpacking '+str(file))
        call(["unzip", file])

    context.set_progress(message='Sorting DICOM data...')
    call([
    "python3",
    "/opt/QSMxT/run_0_dicomSort.py",
    path, 
    "/00_dicom"
    ])


    context.set_progress(message='Converting DICOM data...')
    call([
    "python3",
    "/opt/QSMxT/run_1_dicomToBids.py",
    "/00_dicom", 
    "/01_bids"
    ])

    qsm_iterations = settings['qsm_iterations']
    context.set_progress(message='Run QSM pipeline ...')
    call([
    "python3",
    "/opt/QSMxT/run_2_qsm.py",
    "--qsm_iterations",
    str(qsm_iterations),
    "--two_pass",
    "/01_bids", 
    "/02_qsm_output"
    ])

    output_file = glob.glob("/02_qsm_output/qsm_final/_run_run-1/*.nii")


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
    context.upload_file(output_file[0], 'final.nii')
