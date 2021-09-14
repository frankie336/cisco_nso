# -*- mode: python; python-indent: 4 -*-
import ncs
from ncs.application import Service
from ncs.dp import Action
import re
import json

"""
Cli Output class 
"""

class NetworkNodes:

    def __init__(self, device_group, command):
        self.device_group = device_group
        self.command = command
        self.result = None
        self.system_name = []
        self.local_interface = []
        self.remote_port = []
        self.capabilities = []
        self.discovered_hosts = ()
        self.topology_file_name = 'topology.js'
        self.top_file_head = "\n\nvar topologyData = "
        self.connections = []
        self.capabilities_dict = {}
        self.topology_dict = {}

        self.icon_capability_map = {
            'router': 'router',
            'switch': 'switch',
            'bridge': 'switch',
            'station': 'host'
        }

        self.interface_full_name_map = {'Eth': 'Ethernet',
                                        'Fa': 'FastEthernet',
                                        'Gi': 'GigabitEthernet',
                                        'Te': 'TenGigabitEthernet',
                                        }

        self.icon_model_map = {'CSR1000V': 'router',
                               'Nexus': 'switch',
                               'IOSXRv': 'router',
                               'IOSv': 'switch',
                               '2901': 'router',
                               '2911': 'router',
                               '2921': 'router',
                               '2951': 'router',
                               '4321': 'router',
                               '4331': 'router',
                               '4351': 'router',
                               '4421': 'router',
                               '4431': 'router',
                               '4451': 'router',
                               '2960': 'switch',
                               '3750': 'switch',
                               '3850': 'switch',
                               }

        # Topology layers would be sorted
        self.sort_order = (
            'undefined',
            'outside',
            'edge-switch',
            'edge-router',
            'core-router',
            'core-switch',
            'distribution-router',
            'distribution-switch',
            'leaf',
            'spine',
            'access-switch'
        )

    def get_icon_type(self, device_cap_name, device_model=''):
        """
        Device icon selection function. Selection order:
        - LLDP capabilities mapping.
        - Device model mapping.
        - Default 'unknown'.
        """
        if device_cap_name:
            icon_type = self.icon_capability_map.get(device_cap_name)
            if icon_type:
                return icon_type

        if device_model:
            for model_shortname, icon_type in self.icon_model_map.items():
                if model_shortname in device_model:
                    return icon_type

        return 'unknown'


    def parse_cli_output(self, pattern: str):
        """
        Parses cli output and returns matched items
        in a list. Add the regex pattern as a param
        """
        output = self.result
        info = re.findall(pattern, output)

        return info

    def extract_lldp_detal(self):
        """
        -Uses self.parse_cli_output() to extract useful live state data
         from cisco-ios: show 'lldp neighbor detail'
        """
        system_name = self.parse_cli_output(
            pattern="(?<=System Name: )[^\n]*")
        local_interface = self.parse_cli_output(
            pattern="(?<=Local Intf: )[^\n]*")
        remote_port = self.parse_cli_output(
            pattern="(?<=Port id: )[^\n]*")
        capabilities = self.parse_cli_output(
            pattern="(?<=Enabled Capabilities: )[^\n]*")

        self.lld_details_dict = {'system_name': system_name, 'local_interface': local_interface,
                                 'remote_port': remote_port, 'capabilities': capabilities
                                 }

    def normalize_data(self,device):

        """
        Normalize and prepare data to be used by self.generate_topology_json()
        """

        system_name = self.lld_details_dict['system_name']
        local_interface = self.lld_details_dict['local_interface']
        remote_port = self.lld_details_dict['remote_port']
        capabilities = self.lld_details_dict['capabilities']

        for i, system in enumerate(system_name):
            combine = [
                ((device, local_interface[i]), (system_name[i], remote_port[i]))
            ]
            self.connections = self.connections + combine

        self.system_name = self.system_name + self.lld_details_dict['system_name']

        for i, cap in enumerate(capabilities):

            if capabilities[i] == 'R\r':
                cap = 'router'
            else:
                cap = 'unknown'

            temp_dict = {system_name[i]: cap}

            self.capabilities_dict.update(temp_dict)

        self.discovered_hosts = set(self.system_name)# <---

        #self.discovered_hosts--->{'CE2B.www.flynn.com\r', 'bas01ceSW01.www.flynn.com\r', 'P1.www.flynn.com\r', 'PE1.www.flynn.com\r', 'CE2A.www.flynn.com\r', 'vpn00001\r', 'PE2.www.flynn.com\r', 'vpn00007.www.flynn.com\r', 'CE1B.www.flynn.com\r', 'CE1A.www.flynn.com\r', 'bas_ce_man01\r', 'zur01ceSW01.www.flynn.com\r'}
        #self.connections--->[(('zur01ceSW01.www.flynn.com', 'Gi1/0\r'), ('bas_ce_man01\r', 'Gi0/3\r')), (('zur01ceSW01.www.flynn.com', 'Gi0/3\r'), ('vpn00007.www.flynn.com\r', 'Gi0/0.905\r')), (('zur01ceSW01.www.flynn.com', 'Gi0/0\r'), ('PE1.www.flynn.com\r', 'Gi0/0.1\r')), (('zur01ceSW01.www.flynn.com', 'Gi0/0\r'), ('PE1.www.flynn.com\r', 'Gi0/0.3\r')), (('zur01ceSW01.www.flynn.com', 'Gi0/0\r'), ('PE1.www.flynn.com\r', 'Gi0/0.2\r')), (('zur01ceSW01.www.flynn.com', 'Gi0/0\r'), ('PE1.www.flynn.com\r', 'Gi0/0.905\r')), (('zur01ceSW01.www.flynn.com', 'Gi0/0\r'), ('PE1.www.flynn.com\r', 'Gi0/0.901\r')), (('zur01ceSW01.www.flynn.com', 'Gi0/0\r'), ('PE1.www.flynn.com\r', 'Gi0/0.902\r')), (('zur01ceSW01.www.flynn.com', 'Gi0/0\r'), ('PE1.www.flynn.com\r', 'Gi0/0.903\r')), (('zur01ceSW01.www.flynn.com', 'Gi0/3\r'), ('vpn00007.www.flynn.com\r', 'Gi0/0\r')), (('zur01ceSW01.www.flynn.com', 'Gi0/0\r'), ('PE1.www.flynn.com\r', 'Gi0/0\r')), (('zur01ceSW01.www.flynn.com', 'Gi0/2\r'), ('CE1B.www.flynn.com\r', 'Gi0/0\r')), (('zur01ceSW01.www.flynn.com', 'Gi0/1\r'), ('CE1A.www.flynn.com\r', 'Gi0/0\r')), (('zur01ceSW01.www.flynn.com', 'Gi0/1\r'), ('CE1A.www.flynn.com\r', 'Gi0/0.901\r')), (('zur01ceSW01.www.flynn.com', 'Gi0/2\r'), ('CE1B.www.flynn.com\r', 'Gi0/0.902\r')), (('zur01ceSW01.www.flynn.com', 'Gi0/1\r'), ('CE1A.www.flynn.com\r', 'Gi0/0.101\r')), (('zur01ceSW01.www.flynn.com', 'Gi0/2\r'), ('CE1B.www.flynn.com\r', 'Gi0/0.102\r'))]
        #self.capabilities_dict--->{'bas_ce_man01\r': 'router', 'PE1.www.flynn.com\r': 'router', 'P2.www.flynn.com\r': 'router', 'P1.www.flynn.com\r': 'router', 'PE2.www.flynn.com\r': 'router', 'zur01ceSW01.www.flynn.com\r': 'router', 'bas01ceSW01.www.flynn.com\r': 'router', 'CE2B.www.flynn.com\r': 'router', 'vpn00001\r': 'router', 'CE2A.www.flynn.com\r': 'router', 'vpn00007.www.flynn.com\r': 'router', 'CE1B.www.flynn.com\r': 'router', 'CE1A.www.flynn.com\r': 'router'}




    def if_shortname(self, ifname):
        for k, v in self.interface_full_name_map.items():
            if ifname.startswith(v):
                return ifname.replace(v, k)
        return ifname


    def generate_topology_json(self, discovered_hosts,
                               connections, capabilities_dict):


        host_id_map = {}
        topology_dict = {'nodes': [], 'links': []}

        host_id = 0
        for host in discovered_hosts:
            device_model = 'n/a'
            device_serial = 'n/a'
            device_ip = 'n/a'
            # if facts.get(host):
            # device_model = facts[host].get('model', 'n/a')
            # device_serial = facts[host].get('serial_number', 'n/a')
            # device_ip = facts[host].get('nr_ip', 'n/a')
            host_id_map[host] = host_id
            topology_dict['nodes'].append({
                'id': host_id,
                'name': host,
                'primaryIP': device_ip,
                'model': device_model,
                'serial_number': device_serial,
                'icon': self.get_icon_type(self.capabilities_dict.get(host, ''), device_model)

            })
            host_id += 1

        link_id = 0
        for link in connections:

            topology_dict['links'].append({
                'id': link_id,
                'source': host_id_map[link[0][0]+'\r'],
                'target': host_id_map[link[1][0]],
                'srcIfName': self.if_shortname(link[0][1]),
                'srcDevice': link[0][0],
                'tgtIfName': self.if_shortname(link[1][1]),
                'tgtDevice': link[1][0],
            })
            link_id += 1



        return topology_dict

    def write_topology_file(self, topology_json):
        with open(self.topology_file_name, 'w') as topology_file:
            topology_file.write(self.top_file_head)
            topology_file.write(json.dumps(
                topology_json, indent=4, sort_keys=True))
            topology_file.write(';')

    def get_device_output(self):
        
        """
        Logs into devices in NSO and grabs show command output
        """
        with ncs.maapi.Maapi() as m:
            with ncs.maapi.Session(m, 'admin', 'admin'):
                with m.start_write_trans(ncs.RUNNING) as t:
                    root = ncs.maagic.get_root(t)
                    for dev in root.devices.device:
                        show = dev.live_status.__getitem__(
                            'ios-stats:exec').show

                        inp = show.get_input()
                        inp.args = [self.command]
                        r = show.request(inp)
                        self.result = r.result  # <-- changes on each iteration
                        self.extract_lldp_detal()#<-New solution
                        self.normalize_data(dev.name)#<---


        self.topology_dict = self.generate_topology_json(self.discovered_hosts, self.connections, self.capabilities_dict)
        self.write_topology_file(self.topology_dict)#<---


    def run_diagram(self):
        """
        Runs the chain of events that will eventually result in a .js topology diagram for Cisco NextUI integration . 
        """
        self.get_device_output()


# ---------------
# ACTIONS EXAMPLE
# ---------------
class DoubleAction(Action):
    @Action.action
    def cb_action(self, uinfo, name, kp, input, output, trans):
        self.log.info('action name: ', name)
        self.log.info('action input.number: ', input.confirm)

        # Updating the output data structure will result in a response
        # being returned to the caller.

        if input.confirm == 'yes':
            output.result = '1'
            get_lldp_output = NetworkNodes('topology', 'lldp neighbors detail')
            get_lldp_output.run_diagram() # <---
        else:
            pass

        """
        with ncs.maapi.single_write_trans('admin', 'python', groups=['topology']) as t:
            root = ncs.maagic.get_root(t)
            devicelist = root.devices.device
            for dev in devicelist:
                print (dev.name,'<M----M>')
        """


# ------------------------
# SERVICE CALLBACK EXAMPLE
# ------------------------
class ServiceCallbacks(Service):

    # The create() callback is invoked inside NCS FASTMAP and
    # must always exist.
    @Service.create
    def cb_create(self, tctx, root, service, proplist):
        self.log.info('Service create(service=', service._path, ')')

    # The pre_modification() and post_modification() callbacks are optional,
    # and are invoked outside FASTMAP. pre_modification() is invoked before
    # create, update, or delete of the service, as indicated by the enum
    # ncs_service_operation op parameter. Conversely
    # post_modification() is invoked after create, update, or delete
    # of the service. These functions can be useful e.g. for
    # allocations that should be stored and existing also when the
    # service instance is removed.

    # @Service.pre_lock_create
    # def cb_pre_lock_create(self, tctx, root, service, proplist):
    #     self.log.info('Service plcreate(service=', service._path, ')')

    # @Service.pre_modification
    # def cb_pre_modification(self, tctx, op, kp, root, proplist):
    #     self.log.info('Service premod(service=', kp, ')')

    # @Service.post_modification
    # def cb_post_modification(self, tctx, op, kp, root, proplist):
    #     self.log.info('Service postmod(service=', kp, ')')


# ---------------------------------------------
# COMPONENT THREAD THAT WILL BE STARTED BY NCS.
# ---------------------------------------------
class Main(ncs.application.Application):
    def setup(self):
        # The application class sets up logging for us. It is accessible
        # through 'self.log' and is a ncs.log.Log instance.
        self.log.info('Main RUNNING')

        # Service callbacks require a registration for a 'service point',
        # as specified in the corresponding data model.
        #
        self.register_service(
            'ntc-action-example-servicepoint', ServiceCallbacks)

        # When using actions, this is how we register them:
        #
        self.register_action('ntc-action-example-action', DoubleAction)

        # If we registered any callback(s) above, the Application class
        # took care of creating a daemon (related to the service/action point).

        # When this setup method is finished, all registrations are
        # considered done and the application is 'started'.

    def teardown(self):
        # When the application is finished (which would happen if NCS went
        # down, packages were reloaded or some error occurred) this teardown
        # method will be called.

        self.log.info('Main FINISHED')
