# BSD 4-Clause License

# Copyright (c) 2021, University of Rome Tor Vergata
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

#  * Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#  * All advertising materials mentioning features or use of this software
#    must display the following acknowledgement: This product includes
#    software developed by University of Rome Tor Vergata and its contributors.
#  * Neither the name of University of Rome Tor Vergata nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from WorkModelGenerator import get_work_model, WORKMODEL_PATH
import json
import os
import time
import logging
logger = logging.getLogger(__name__)

import argparse
import argcomplete


parser = argparse.ArgumentParser()

parser.add_argument('-c', '--config-file', action='store', dest='parameters_file',
                    help='The WorkModel Parameters file', default=f'{WORKMODEL_PATH}/WorkModelParameters.json')
parser.add_argument('-ll', '--log-level', action='store', dest='log_level', help='Log Level', default='INFO')

argcomplete.autocomplete(parser)

try:
    args = parser.parse_args()
except ImportError:
    logger.critical("Import error, there are missing dependencies to install.  'apt-get install python3-argcomplete "
          "&& activate-global-python-argcomplete3' may solve")
except AttributeError:
    parser.print_help()
except Exception as err:
    logger.error("Error:", err)

logging.basicConfig(level=args.log_level)

parameters_file_path = args.parameters_file

try:
    with open(parameters_file_path) as f:
        params = json.load(f)
    workmodel_parameters = params["WorkModelParameters"]

    if "OutputPath" in workmodel_parameters.keys() and len(workmodel_parameters["OutputPath"]["value"]) > 0:
        output_path = workmodel_parameters["OutputPath"]["value"]
        if output_path.endswith("/"):
            output_path = output_path[:-1]
        if not os.path.exists(output_path):
            os.makedirs(output_path)
    else:
        output_path = WORKMODEL_PATH
    if "OutputFile" in workmodel_parameters.keys() and len(workmodel_parameters["OutputFile"]["value"]) > 0:
        output_file = workmodel_parameters["OutputFile"]["value"]
    else:
        output_file = "workmodel.json"
    
    if "ServiceGraphFilePath" in workmodel_parameters.keys():
        servicegraph_file_path = workmodel_parameters["ServiceGraphFilePath"]["value"]
    else:
        servicegraph_file_path = f"{output_path}/servicegraph.json"
    
    with open(servicegraph_file_path) as f:
        servicegraph = json.load(f)

except Exception as err:
    logger.error("ERROR: in creation of workmodel,", err)
    exit(1)

workmodel = get_work_model(servicegraph, workmodel_parameters)
logger.debug(workmodel)

file_path = f"{output_path}/{output_file}"
logger.info(f"Writing workmodel to '{file_path}'")
with open(f"{output_path}/{output_file}", "w") as f:
    f.write(json.dumps(workmodel, indent=2))

time.sleep(1)
exit(0)
