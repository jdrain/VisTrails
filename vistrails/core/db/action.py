###############################################################################
##
## Copyright (C) 2014-2015, New York University.
## Copyright (C) 2011-2014, NYU-Poly.
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
##  - Neither the name of the New York University nor the names of its
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
from __future__ import division

from vistrails.core.vistrail.location import Location
import vistrails.db.services.action

def create_action(op_list):
    if len(op_list) > 0:
        from vistrails.core.vistrail.action import Action
        action = vistrails.db.services.action.create_action(op_list)
        Action.convert(action)
        return action
    return None

def create_action_from_ops(ops, simplify=False):
    if len(ops) > 0:
        from vistrails.core.vistrail.action import Action
        action = vistrails.db.services.action.create_action_from_ops(ops, simplify)
        Action.convert(action)
        return action
    return None

def merge_actions(action_list):
    ops = []
    for action in action_list:
        ops.extend(action.operations)
    return create_action_from_ops(ops, True)

def create_paste_action(pipeline, id_scope, id_remap=None):
    action_list = []
    if id_remap is None:
        id_remap = {}
    for module in pipeline.modules.itervalues():
        module = module.do_copy(True, id_scope, id_remap)
        action_list.append(('add', module))
    for connection in pipeline.connections.itervalues():
        connection = connection.do_copy(True, id_scope, id_remap)
        action_list.append(('add', connection))
    action = create_action(action_list)

    # fun stuff to work around bug where pasted entities aren't dirty
    for (child, _, _) in action.db_children():
        child.is_dirty = True
    return action

