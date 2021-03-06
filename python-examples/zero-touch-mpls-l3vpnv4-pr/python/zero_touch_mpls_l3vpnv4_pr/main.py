# -*- mode: python; python-indent: 4 -*-
import ncs
import requests
from ncs.application import Service

"""
This class makes REST calls to an SQL Database that contains 
some useful data about the mpls vpn service:
"""

class MplsData:
    def __init__(self,service_name):

        self.service_name = service_name

    def get_mpls(self):
        vpn4_response = requests.get("http://10.1.0.100:3000/all?args1="+self.service_name)
        ext_vpn_data = vpn4_response.json()
        return ext_vpn_data



# ------------------------
# SERVICE CALLBACK EXAMPLE
# ------------------------
class ServiceCallbacks(Service):

    # The create() callback is invoked inside NCS FASTMAP and
    # must always exist.
    @Service.create
    def cb_create(self, tctx, root, service, proplist):
        self.log.info('Service create(service=', service._path, ')')

        mympls = MplsData(service_name=service.name)
        ext_vpn_data = mympls.get_mpls()
        service.vrf_name = service.name # Set the vrf name to the nso service name
        service.wan_ip_address = ext_vpn_data[0]['PeWanIPAddress']#Get the WAN IP from REST query
        service.ce_ip_address = ext_vpn_data[0]['CeWanIPAddress']#Get the ce IP address from a REST query
        service.ce_ip_address = ext_vpn_data[0]['BgpPassword'] #Get the BGP password from REST query
        service.wan_interface_number = ext_vpn_data[0]['PeInterface']#Get the Wan interface from REST query
        service.vlan = ext_vpn_data[0]['WanVlan'] #Get the vlan from REST query
        service.rd = '6501:'+ext_vpn_data[0]['WanVlan']
        service.export_r = service.rd# uses the same import key as the rd
        service.import_r = service.rd#uses the same export key as the rd



        vars = ncs.template.Variables()
        vars.add('DUMMY', '127.0.0.1')
        template = ncs.template.Template(service)
        template.apply('zero-touch-mpls-l3vpnv4-pr-template', vars)

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
        self.register_service('zero-touch-mpls-l3vpnv4-pr-servicepoint', ServiceCallbacks)

        # If we registered any callback(s) above, the Application class
        # took care of creating a daemon (related to the service/action point).

        # When this setup method is finished, all registrations are
        # considered done and the application is 'started'.

    def teardown(self):
        # When the application is finished (which would happen if NCS went
        # down, packages were reloaded or some error occurred) this teardown
        # method will be called.

        self.log.info('Main FINISHED')
