#!/usr/bin/env python

'''
Basic QMENTA Tool Image Local Tester

Usage:
 $ ./test_sdk_tool.py image_name inputs/ outputs
 $ ./test_sdk_tool.py image_name inputs/ outputs --settings settings.json --values values.json --tool package.tool -v /host/path:/container/path

Compatible with Python 2 & 3 with no additional packages.
See https://docs.qmenta.com/sdk/testing.html for more information.
'''

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
    '''
    Interface for script
    '''
    parser = argparse.ArgumentParser(description='Local execution of a tool image test')

    # Positional arguments
    parser.add_argument('image', help='The name of the tool image (name:tag)')
    parser.add_argument('inputs', help='A folder which will be used as input container')
    parser.add_argument('outputs', help='A folder which will be used as output container')

    # Keyword arguments
    parser.add_argument('-v', help='Mount a directory inside the Docker container', action='append')
    parser.add_argument('--settings', help='The settings.json file')
    parser.add_argument('--values', help='The values for the settings file')    
    parser.add_argument('--tool', help='The python file with the run method')

    # Private testing arguments
    parser.add_argument('--resources', help='argparse.SUPPRESS')

    return parser.parse_args()


def run_command(cmd, verbose=True):
    '''
    Execute command in shell
    '''
    if verbose:
        print(' '.join(cmd))
    subprocess.call(cmd)

def error(msg):
    '''
    Exit with error
    '''
    print(msg)
    sys.exit(1)

def main():
    '''
    Script entrypoint
    '''

    args = parse_arguments()

    # Check input and output folders
    if not isdir(abspath(args.inputs)):
        error('Error: Input folder does not exist')
    if not isdir(abspath(args.outputs)):
        error('Error: Output folder does not exist')
    if not os.listdir(abspath(args.outputs)) == []:
        print('Warning: Output folder is not empty (files could be overwritten).')
         # Post executions actions
        yes = {'yes', 'y'}
        no = {'no', 'n'}
        choice = ''
        while choice not in yes and choice not in no:
            print("Do you want to continue? (Y/N)")
            choice = input().lower()
        if choice in no:
            sys.exit(1)            
            
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

    # If no tool_settings file is provided, use a generic one
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
    
    # If no tool_settings_values file is provided, generate just the list of input files
    if not args.values:
        files = listdir(os.path.join(abspath(args.inputs), 'input'))
        values_content = '{"input":[\n' + ',\n'.join(
            ['   {"path": "' + f + '"}' for f in files if not isdir(f)]) + ']\n}'

        args.values = './generic_values.json'

        with open(args.values, 'w') as values_file:
            values_file.write(values_content)

    if not args.tool:
        args.tool = 'tool'
    
    # Extra directories to be mounted (for instance, live version of source code)
    extra_volumes = []
    for volume in (args.v or []):
        extra_volumes += ['-v', volume]

    # Launch the detached container
    c_name = 'local_test_' + random_seq(5)
    print('\nStarting container {}...'.format(c_name))
    run_command([
        'docker', 'run', '-dit',
        '-v', abspath(args.inputs) + ':' + c_input_path,
        '-v', abspath(args.outputs) + ':' + c_output_path] + extra_volumes + [
        '--entrypoint=/bin/bash', 
        '--name=' + c_name,
        args.image,        
    ])

    # Copy the settings files to the container
    run_command(['docker', 'cp', abspath(args.settings), c_name + ':' + c_settings_path], verbose = False)
    run_command(['docker', 'cp', abspath(args.values), c_name + ':' + c_values_path], verbose = False)

    # Changing to local executor
    run_command([
        'docker', 'exec', c_name,
        '/bin/bash', '-c', r"sed -i.bak 's/\<qmenta.sdk\>/&.local/' /root/entrypoint.sh"
    ], verbose=False)

    # Run the local executor
    print('\nRunning {}.py:run()...\n'.format(args.tool))
    launch_cmd = [
        'docker', 'exec', c_name, '/bin/bash', 'entrypoint.sh',
        c_settings_path, c_values_path, c_input_path, c_output_path, '--tool-path', args.tool + ':run'
    ]
    
    # Additional resources (QMENTA)
    if args.resources:
        run_command(['docker', 'cp', abspath(args.resources), c_name + ':' + c_res_path], verbose = False)
        launch_cmd += ['--res-folder', c_res_path]

    run_command(launch_cmd)

    # Post executions actions
    yes = {'yes', 'y'}
    no = {'no', 'n'}
    choice = 'yes' # stop container
    # choice = 'no' # keep container running and connect for debugging
    while choice not in yes and choice not in no:
        print("Do you want to stop the container? (Y/N)")
        choice = input().lower()
    if choice in yes:
        run_command(['docker', 'stop', c_name])

        choice = 'no'
        while choice not in yes and choice not in no:
            print("Do you want to delete the container? (Y/N)")
            choice = input().lower()
        if choice in yes:
            run_command(['docker', 'rm', c_name], verbose = True)
    else:
        choice = 'yes'
        while choice not in yes and choice not in no:
            print("Do you want to attach to the container? (Y/N)")
            choice = input().lower()
        if choice in yes:
            run_command(['docker', 'attach', c_name], verbose = True)


if __name__ == "__main__":
    main()