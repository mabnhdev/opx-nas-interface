#!/usr/bin/python
# Copyright (c) 2015 Dell Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# THIS CODE IS PROVIDED ON AN *AS IS* BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT
# LIMITATION ANY IMPLIED WARRANTIES OR CONDITIONS OF TITLE, FITNESS
# FOR A PARTICULAR PURPOSE, MERCHANTABLITY OR NON-INFRINGEMENT.
#
# See the Apache Version 2.0 License for specific language governing
# permissions and limitations under the License.

import cps
import bytearray_utils as ba
import cps_object
import cps_utils
import event_log as ev
import nas_os_if_utils as nas_if
import nas_front_panel_map as fp

import time

front_panel_ports = None
port_cache = None
if_cache = None

def create_interface(obj):

    ifobj = nas_if.make_interface_from_phy_port(obj)

    #
    # Extreme change - handle the case where the interface could not be created
    # due to lack of a hardware port. In this case simply return.
    #
    if ifobj == None:
        return

    if if_cache.exists(ifobj.get_attr_data('if/interfaces/interface/name')):
        nas_if.log_err("Already exists.... " + str(ifobj.get_attr_data('if/interfaces/interface/name')))
        return

    # create the object
    ch = {'operation': 'rpc', 'change': ifobj.get()}
    cps.transaction([ch])
    nas_if.log_info("Interface Created : " + str(ifobj.get_attr_data('if/interfaces/interface/name')))

if __name__ == '__main__':

    _max_loop_count = 50
    _loop_count = 0
    for _loop_count in range(_max_loop_count):
        front_panel_ports = nas_if.FpPortCache()
        if front_panel_ports.len() == 0:
            nas_if.log_err('fetch front panel port info  not ready ')
            time.sleep(1) #in seconds
        else:
            break

    for _loop_count in range(_max_loop_count):
        port_cache = nas_if.PhyPortCache()
        if port_cache.len() ==0:
            nas_if.log_err('fetch physical port info  not ready ')
            time.sleep(1)
        else:
            break;

    if_cache = nas_if.IfCache()

    # walk through the list of physical ports
    for port in port_cache.get_port_list():
        obj = cps_object.CPSObject(obj=port)
        create_interface(obj)
