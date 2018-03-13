#!/usr/bin/env python

import argparse
import random
import os
import string
import subprocess
import sys
import time
from os import listdir, system
from os.path import abspath, isdir


def random_seq(n):
    '''
    Generates a random sequence of upper-cased characters of size n
    '''
    return ''.join(random.choice(string.ascii_uppercase) for x in range(n))


def parse_arguments():
    parser = argparse.ArgumentParser(description='Local execution of a tool image test')

    # Positional arguments
    parser.add_argument('image', help='The name of the tool image (name:tag)')
    parser.add_argument('inputs', help='A folder which will be used as input container')
    parser.add_argument('outputs', help='A folder which will be used as output container')

    # Keyword arguments
    parser.add_argument('-settings', help='The settings.json file')
    parser.add_argument('-values', help='The values for the settings file')    
    parser.add_argument('-tool', help='The python file with the run method')

    # Private testing arguments
    parser.add_argument('-resources', help='argparse.SUPPRESS')

    return parser.parse_args()


def run_command(cmd, verbose = True):
    if verbose:
        print ' $ ' + ' '.join(cmd)
    subprocess.call(cmd)

def error(msg):
    print msg
    sys.exit(1)

def main():
    args = parse_arguments()

    # Check input and output folders
    if not isdir(abspath(args.inputs)):
        error('Error: Input folder does not exist')
    if not isdir(abspath(args.outputs)):
        error('Error: Output folder does not exist')
    if not os.listdir(abspath(args.outputs)) == []:
        print('Warning: Output folder is not empty')
    if args.resources and not isdir(abspath(args.resources)):
        error('Error: Resources folder does not exist')
    if args.settings and not args.values:
        error('Error: Entering a custom settings file requires a settings values file')

    # In-container paths
    c_settings_path = '/root/local_exec_settings.json'
    c_values_path = '/root/local_exec_settings_values.json'
    c_input_path = '/root/local_exec_input/'
    c_output_path = '/root/local_exec_output/'
    c_res_path = '/root/local_exec_resources/'

    if not args.settings:
        settings_content = '''[
    {
        "type": "container",
        "title": "Example Container",
        "id":"input", 
        "mandatory":1, 
        "batch":1, 
        "file_filter": "c_files[1,*]<'', [], '.*'>",
        "in_filter":["mri_brain_data"],
        "out_filter":[],
        "anchor":1
    }
]'''

        args.settings = './generic_settings.json'

        with open(args.settings, 'w') as settings_file:
            settings_file.write(settings_content)

    if not args.values:  # If no settings_values file is avaiable, generate just the list of input files
        files = listdir(os.path.join(abspath(args.inputs), 'input'))
        values_content = '{"input":[\n' + ',\n'.join(
            ['   {"path": "' + f + '"}' for f in files if not isdir(f)]) + ']\n}'

        args.values = './generic_values.json'

        with open(args.values, 'w') as values_file:
            values_file.write(values_content)

    if not args.tool:
        args.tool = 'tool'

    # Launch the detached container
    c_name = 'local_test_' + random_seq(5)
    print '\nStarting container'
    run_command(['docker', 'run', '-dit', '-v', abspath(args.outputs) + ':' + c_output_path, '--name=' + c_name, args.image, '/bin/bash'])

    # Copy the files to the container
    run_command(['docker', 'cp', abspath(args.settings), c_name + ':' + c_settings_path], verbose = True)
    run_command(['docker', 'cp', abspath(args.values), c_name + ':' + c_values_path], verbose = True)
    run_command(['docker', 'cp', abspath(args.inputs), c_name + ':' + c_input_path], verbose = True)

    # Run the local executor
    print '\nRunning tool...'
    launch_cmd = ['docker', 'exec', c_name, '/usr/local/miniconda/bin/python', '-m', 'qmenta.sdk.local.executor',
                 c_settings_path, c_values_path, c_input_path, c_output_path, '--tool-path', args.tool + ':run']
    
    # Additional resources (QMENTA)
    if args.resources:
        run_command(['docker', 'cp', abspath(args.resources), c_name + ':' + c_res_path], verbose = False)
        launch_cmd += ['--res-folder', c_res_path]

    run_command(launch_cmd)

    # Post executions actions
    yes = {'yes', 'y'}
    no = {'no', 'n'}
    choice = ''
    while choice not in yes and choice not in no:
        print "Do you want to stop the analysis container? (Y/N)"
        choice = raw_input().lower()
    if choice in yes:
        run_command(['docker', 'stop', c_name])

        choice = ''
        while choice not in yes and choice not in no:
            print "Do you want to delete the analysis container? (Y/N)"
            choice = raw_input().lower()
        if choice in yes:
            run_command(['docker', 'rm', c_name], verbose = True)
    else:
        choice = ''
        while choice not in yes and choice not in no:
            print "Do you want to attach to the container? (Y/N)"
            choice = raw_input().lower()
        if choice in yes:
            print "Press [ENTER] to enter the container shell..."
            run_command(['docker', 'attach', c_name], verbose = True)


if __name__ == "__main__":
    main()