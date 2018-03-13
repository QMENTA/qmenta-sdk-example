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
    t1_file_handler = context.get_files('input', modality='T1')[0]
    t1_path = t1_file_handler.download('/root/')  # Download and automatically unpack  

    # Compute a basic histogram with MRtrix
    context.set_progress(message='Processing...')

    histogram_data_path = '/root/hist.txt'
    call([
        "/usr/lib/mrtrix/bin/mrstats", 
        "-histogram", histogram_data_path,
        "-bins", "50",
        t1_path
    ])

    # Plot the histogram for the selected range of intensities
    hist_start = settings['hist_start']
    hist_end = settings['hist_end']
    [bins_centers, values] = np.loadtxt(histogram_data_path)

    fig, ax = plt.subplots()
    ax.set_title('T1 Histogram (for intensities between 50 and 400)')
    ax.set_ylabel('Number of voxels')
    ax.grid(color='#CCCCCC', linestyle='--', linewidth=1)

    left_i = (i for i,v in enumerate(bins_centers) if v > hist_start).next()
    right_i = max((i for i,v in enumerate(bins_centers) if v < hist_end))

    plt.plot(bins_centers[left_i:right_i], values[left_i:right_i])

    hist_path = '/root/hist.png'
    plt.savefig(hist_path)

    # Generate an example report
    # Since it is a head-less machine, it requires Xvfb to generate the pdf
    context.set_progress(message='Creating report...')

    report_path = '/root/report.pdf'

    data_report = {
        'logo_main': '/root/qmenta_logo.png',
        'ss': analysis_data['patient_secret_name'],
        'ssid': analysis_data['ssid'],
        'histogram': hist_path,
        'this_moment': strftime("%Y-%m-%d %H:%M:%S", gmtime()),
        'version': 1.0
    }

    loader = template.Loader('/root/')
    report_contents = loader.load('report_template.html').generate(data_report=data_report)
    pdfkit.from_string(report_contents, report_path)

    # Upload the data and the report
    context.set_progress(message='Uploading results...')

    context.upload_file(histogram_data_path, 'hist_data.txt')
    context.upload_file(report_path, 'report.pdf')
