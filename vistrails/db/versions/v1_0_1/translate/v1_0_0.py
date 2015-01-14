###############################################################################
##
## Copyright (C) 2011-2015, NYU-Poly.
## Copyright (C) 2006-2011, University of Utah.
## All rights reserved.
## Contact: contact@vistrails.org
##
## This file is part of VisTrails.
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are met:
##
##  - Redistributions of source code must retain the above copyright notice,
##    this list of conditions and the following disclaimer.
##  - Redistributions in binary form must reproduce the above copyright
##    notice, this list of conditions and the following disclaimer in the
##    documentation and/or other materials provided with the distribution.
##  - Neither the name of the University of Utah nor the names of its
##    contributors may be used to endorse or promote products derived from
##    this software without specific prior written permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
## AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
## THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
## PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
## CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
## EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
## PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
## OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
## WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
## OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
## ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
##
###############################################################################
import copy
from vistrails.db.versions.v1_0_1.domain import DBVistrail, DBWorkflow, DBLog, \
    DBRegistry, DBModuleDescriptor, DBGroup

def translateVistrail(_vistrail):
    def update_workflow(old_obj, translate_dict):
        return DBWorkflow.update_version(old_obj.db_workflow, translate_dict)
    translate_dict = {'DBGroup': {'workflow': update_workflow}}
    vistrail = DBVistrail.update_version(_vistrail, translate_dict)
    vistrail.db_version = '1.0.1'
    return vistrail

def translateWorkflow(_workflow):
    def update_workflow(old_obj, translate_dict):
        return DBWorkflow.update_version(old_obj.db_workflow, translate_dict)
    translate_dict = {'DBGroup': {'workflow': update_workflow}}
    workflow = DBWorkflow.update_version(_workflow, translate_dict)
    workflow.db_version = '1.0.1'
    return workflow

def translateLog(_log):
    translate_dict = {}
    log = DBLog.update_version(_log, translate_dict)
    log.db_version = '1.0.1'
    return log

def translateRegistry(_registry):
    def update_descriptors(old_obj, translate_dict):
        def get_update_method(package_version):
            def update_package_version(old_desc, t_dict):
                return package_version
            return update_package_version

        descriptors = []
        for descriptor in old_obj.db_module_descriptors:
            new_t_dict = {'DBModuleDescriptor': 
                          {'package_version': \
                               get_update_method(old_obj.db_version)}}
            d = DBModuleDescriptor.update_version(descriptor, new_t_dict)
            descriptors.append(d)
        return descriptors

    translate_dict = {'DBPackage': {'module_descriptors': update_descriptors}}
    registry = DBRegistry.update_version(_registry, translate_dict)
    registry.db_version = '1.0.1'
    return registry
