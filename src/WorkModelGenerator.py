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

import random
import os
import logging

WORKMODEL_PATH = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger(__name__)


# Select exactly one service function according to the probability
# Get in INPUT the list with the internal-service functions
def select_internal_service(service_name, internal_services):
    internal_service_items = internal_services.items()
    logger.debug(f'Selecting internal service for service "{service_name}" from [{internal_services.keys()}]')
    random_extraction = random.random()
    # print("Extraction: %.4f" % random_extraction)
    p_total = 0.0
    for v in internal_services.values():
        p_total += v["probability"]
    p_total = round(p_total, 10)
    prev_interval = 0
    for k in internal_services.keys():
        if random_extraction <= prev_interval + internal_services[k]["probability"]/p_total:
            function_id = k
            logger.debug(f'Selected "{k}" as internal service for service "{service_name}"')
            return function_id
        prev_interval += round(internal_services[k]["probability"]/p_total, 10)
    logger.warning(f'Could not find an internal service for service "{service_name}"')


def get_work_model(service_graph, workmodel_params):
    work_model = dict()
    
    logger.info("*** Settings for get_work_model ***")

    if "override" in workmodel_params.keys():
        override = workmodel_params["override"]["value"]
    else:
        override = dict()
    
    logger.info("Overrides:")
    for o in override:
        logger.info(o)
    
    request_method = workmodel_params["request_method"]["value"]
    logger.info(f'request_method: {request_method}')
    databases_prefix = workmodel_params["databases_prefix"]["value"]
    logger.info(f'databases_prefix: {databases_prefix}')

    internal_services = dict()
    internal_services_db = dict()

    for k in workmodel_params.keys():
        w=workmodel_params[k]
        if w["type"]!="function":
            continue
        tmp_dict=dict() # string to be inserted as internal service in workmodel.json if this function is chosen 
        tmp_dict.update({"internal_service": {w["value"]["name"]: w["value"]["parameters"]}})
        tmp_dict.update({"request_method": request_method})
        if "workers" in w["value"]:
            tmp_dict.update({"workers": w["value"]["workers"]})
        if "threads" in w["value"]:
            tmp_dict.update({"threads": w["value"]["threads"]})
        if "replicas" in w["value"]:
            tmp_dict.update({"replicas": w["value"]["replicas"]})
        if "cpu-limits" in w["value"]:
            tmp_dict.update({"cpu-limits": w["value"]["cpu-limits"]})
        if "cpu-requests" in w["value"]:
            tmp_dict.update({"cpu-requests": w["value"]["cpu-requests"]})
        if "memory-limits" in w["value"]:
            tmp_dict.update({"memory-limits": w["value"]["memory-limits"]})
        if "memory-requests" in w["value"]:
            tmp_dict.update({"memory-requests": w["value"]["memory-requests"]})
        if "recipient" in w["value"] and w["value"]["recipient"] == "database":
            internal_services_db[k]=dict()
            internal_services_db[k].update({"string" : tmp_dict})
            internal_services_db[k].update({"probability": w["value"]["probability"]})
        elif "recipient" in w["value"] and w["value"]["recipient"] == "service":
            internal_services[k]=dict()
            internal_services[k].update({"string" : tmp_dict})
            internal_services[k].update({"probability": w["value"]["probability"]})
        logger.info(f'Adding function ({k}):')
        for o in override:
            logger.info(o)
    
    if len(internal_services_db) == 0:
        logger.info("No internal DB services specified, using fallback.")
        # in case internal services for databases wer not specified, those for plain service are used
        internal_services_db = internal_services
    try:
        logger.info(f'Processing service_graph')
        for vertex in service_graph.keys():
            logger.debug(f'Processing service "{vertex}"')
            work_model[f"{vertex}"] = {'external_services':service_graph.get(vertex)['external_services']}
            
            if vertex.startswith(databases_prefix):
                selected_internal_service = select_internal_service(vertex, internal_services_db)
                work_model[f"{vertex}"].update(internal_services_db[selected_internal_service]['string'])
            else:
                selected_internal_service = select_internal_service(vertex, internal_services)
                work_model[f"{vertex}"].update(internal_services[selected_internal_service]['string'])
            
            if vertex in override.keys():
                logger.info(f'Service "{vertex}" has overrides')
                if "sidecar" in override[vertex].keys():
                    logger.debug(f'Overriding sidecar for service "{vertex}"')
                    work_model[f"{vertex}"].update({"sidecar": override[vertex]["sidecar"]})
                if "function_id" in override[vertex].keys():
                    logger.debug(f'Overriding function_id for service "{vertex}"')
                    work_model[f"{vertex}"].update(internal_services[override[vertex]['function_id']]['string'])

    except Exception as err:
        logger.critical("ERROR: in get_work_model: %s", err)
        exit(1)
    
    logger.info("Work Model Created!")
    return work_model
