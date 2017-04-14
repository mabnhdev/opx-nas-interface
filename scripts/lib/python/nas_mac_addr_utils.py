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

import os
import nas_os_if_utils as nas_if
import xml.etree.ElementTree as ET
import copy
import event_log as ev

if_mac_info_cache = {}
def get_mac_addr_base_range(if_type):
    if len(if_mac_info_cache) == 0:
        try:
            cfg = ET.parse('%s/etc/opx/mac_address_alloc.xml' % os.environ.get("OPX_INSTALL_PATH",""))
        except IOError:
            nas_if.log_err('No mac address config file')
            return None
        root = cfg.getroot()
        for i in root.findall('interface'):
            type_name = i.get('type')
            base = int(i.get('base-offset'))
            off_range = int(i.get('offset-range'))
            if_mac_info_cache[type_name] = (base, off_range)
            nas_if.log_info('%-15s: base %d range %d' % (type_name, base, off_range))
    if not if_type in if_mac_info_cache:
        nas_if.log_err('No mac address setting for type %s' % if_type)
        return None
    return if_mac_info_cache[if_type]

def get_offset_mac_addr(base_addr, offset):
    if isinstance(base_addr, str):
        if base_addr.find(':') >= 0:
            base_addr = ''.join(base_addr.split(':'))
        arr = [int(base_addr[i:i+2],16) for i in range(0, len(base_addr), 2)]
    elif isinstance(base_addr, bytearray):
        arr = copy.copy(base_addr)
    else:
        nas_if.log_err('Invalid mac address type')
        return None
    idx = len(arr)
    while idx > 0:
        addr_num = arr[idx - 1] + offset
        arr[idx - 1] = addr_num % 256
        offset = addr_num / 256
        if offset == 0:
            break
        idx -= 1
    return ':'.join('%02x' % x for x in arr)

base_mac_addr = None
def get_base_mac_addr():
    global base_mac_addr
    if base_mac_addr == None:
        base_mac_addr = nas_if.get_base_mac_address()
    return base_mac_addr

def if_get_mac_addr(if_type, fp_mac_offset = None, vlan_id = None, lag_id = None):
    base_mac = get_base_mac_addr()
    base_range = get_mac_addr_base_range(if_type)
    if base_range == None:
        nas_if.log_err('Failed to get mac addr base and range for if type %s' % if_type)
        return None
    (base_offset, addr_range) = base_range
    if addr_range <= 0:
        nas_if.log_info('Bypass mac address setup for if type %s' % if_type)
        return ''
    mac_offset = 0
    get_mac_offset = lambda boff, brange, val: boff + val % brange
    if if_type == 'front-panel':
        if fp_mac_offset == None or fp_mac_offset > addr_range:
            nas_if.log_err('Invalid or no mac offset input for front panel port')
            return None
        mac_offset = fp_mac_offset
    elif if_type == 'vlan':
        if vlan_id == None:
            nas_if.log_err('No VLAN id for VLAN port')
            return None
        mac_offset = get_mac_offset(base_offset, addr_range, vlan_id)
    elif if_type == 'lag':
        if lag_id == None:
            nas_if.log_err('No LAG id for LAG port')
            return None
        mac_offset = get_mac_offset(base_offset, addr_range, lag_id)
    elif if_type == 'management':
        mac_offset = base_offset
    else:
        nas_if.log_err('if type %s not supported' % if_type)
        return None

    mac_addr = get_offset_mac_addr(base_mac, mac_offset)
    if mac_addr == None:
        nas_if.log_err('Failed to calculate mac address with offset')
        return None
    return mac_addr
