# QMENTA SDK Tool Example

Clone this repository to adapt the Dockerfile and tool script and rapidly build [QMENTA tools](https://platform.qmenta.com/). It contains a simple example with all the required files to build and test the tool. If you want to know more about how to use the SDK and all its features, take a look at the [documentation](https://docs.qmenta.com/sdk).

> In order to add tools to the [QMENTA platform](https://platform.qmenta.com/) you need to have **developer privileges**. If you are interested in this feature, please contact us at info@qmenta.com.

## Contents
### Dockerfile

This file contains the sequence of instructions to build a new tool image. You can setup environment paths, run commands during the image building stage and copy files (see [Dockerfile commands](https://docs.docker.com/get-started/part2/)).

### Tool script

The main script that is executed when a tool is launched on the [QMENTA platform](https://platform.qmenta.com/). This script typically performs the actions shown below using the [QMENTA SDK](https://docs.qmenta.com/sdk) functions where suitable:

1. Download the input data to the container.
2. Process it (call any third party tool).
3. Upload the results.

The naive example shown in this repository computes the histogram for a range of intensities in a T1-weighted image. The range of intensities can be specified from outside the tool thanks to the [tool settings specification](https://docs.qmenta.com/sdk/6_settings.html#).

Feel free to contact us if you have any doubt or request at sdk@qmenta.com! We are happy to hear from you and expand the capabilities of the platform to fit new useful requirements.

### Report template

This tool code uses this HTML template to populate some fields with the patient data and the analysis results to generate a PDF report.

## Build the tool image

Use [Docker](https://www.docker.com/get-docker) to build a new image using the Dockerfile:
~~~~
docker build -t image_name .
~~~~
Where `image_name` should conform to the syntax `my_username/my_tool:version`.

> The first build may take several minutes since it will need to generate the image layer containing the software installation.

Alternatively, take a look at the `standalone.Dockerfile` to see how to install the SDK in an image based on Ubuntu.

## Test the tool locally

Optionally, the `test_tool.py` script can be used to locally launch your tool image if you specify the input files and the required values for you settings (see `mock_settings_values.json`):
~~~~
mkdir analysis_output

python test_tool.py image_name example_data analysis_output \
    --settings settings.json \
    --values mock_settings_values.json
~~~~

## Add the tool to the [QMENTA platform](https://platform.qmenta.com/)

To add a tool image to your list of tools you will first need to login push it to your [Docker Hub](https://hub.docker.com/) registry:
~~~~
docker login

docker push image_name
~~~~
To register the tool to the [QMENTA platform](https://platform.qmenta.com/), access the Analysis menu, and go to My Tools. You will need to enter your credentials of your registry, the name and a version number for the tool, its settings configuration file and a description. You can find an example of the settings configuration file in this repository (`settings.json`).
