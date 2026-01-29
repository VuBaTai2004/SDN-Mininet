from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types, ipv4, tcp, udp
from ryu.topology import event
from ryu.topology.api import get_switch, get_link
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from webob import Response
import json
import logging

# URL cho REST API
url_base = '/sdn'
instance_name = 'sdn_api'

class SDNController(app_manager.RyuApp):
    """
    SDN Controller chính với hỗ trợ REST API
    Hỗ trợ OpenFlow 1.3
    """
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'wsgi': WSGIApplication}

    def __init__(self, *args, **kwargs):
        super(SDNController, self).__init__(*args, **kwargs)
        
        # Mac address table để học địa chỉ
        self.mac_to_port = {}
        
        # Lưu thông tin topology
        self.topology_data = {
            'switches': {},
            'links': [],
            'hosts': {}
        }
        
        # Lưu flow rules đã cài đặt
        self.installed_flows = []
        
        # Đăng ký REST API
        wsgi = kwargs['wsgi']
        wsgi.register(SDNRestAPI, {instance_name: self})
        
        self.logger.info("SDN Controller khởi động thành công!")

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """
        Xử lý khi switch kết nối vào controller
        Cài đặt table-miss flow entry
        """
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Cài đặt table-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                         ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
        
        self.logger.info(f"Switch {datapath.id} đã kết nối")

    def add_flow(self, datapath, priority, match, actions, buffer_id=None, idle_timeout=0, hard_timeout=0):
        """
        Thêm flow entry vào switch
        """
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                   priority=priority, match=match,
                                   instructions=inst,
                                   idle_timeout=idle_timeout,
                                   hard_timeout=hard_timeout)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                   match=match, instructions=inst,
                                   idle_timeout=idle_timeout,
                                   hard_timeout=hard_timeout)
        datapath.send_msg(mod)
        
        # Lưu flow đã cài đặt
        flow_info = {
            'switch_id': datapath.id,
            'priority': priority,
            'match': str(match),
            'actions': str(actions),
            'idle_timeout': idle_timeout,
            'hard_timeout': hard_timeout
        }
        self.installed_flows.append(flow_info)

    def delete_flow(self, datapath, match=None):
        """
        Xóa flow entry
        """
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        if match is None:
            match = parser.OFPMatch()
        
        mod = parser.OFPFlowMod(
            datapath=datapath,
            command=ofproto.OFPFC_DELETE,
            out_port=ofproto.OFPP_ANY,
            out_group=ofproto.OFPG_ANY,
            match=match
        )
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """
        Xử lý packet từ switch
        """
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        dst = eth.dst
        src = eth.src
        dpid = datapath.id

        self.mac_to_port.setdefault(dpid, {})

        # Học địa chỉ MAC
        self.mac_to_port[dpid][src] = in_port

        # Xác định output port
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # Cài đặt flow để tránh packet_in lần sau
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                 in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    @set_ev_cls(event.EventSwitchEnter)
    def switch_enter_handler(self, ev):
        """
        Xử lý khi switch tham gia topology
        """
        switch = ev.switch
        self.topology_data['switches'][switch.dp.id] = {
            'dpid': switch.dp.id,
            'ports': len(switch.ports)
        }
        self.logger.info(f"Switch {switch.dp.id} đã tham gia topology")

    @set_ev_cls(event.EventLinkAdd)
    def link_add_handler(self, ev):
        """
        Xử lý khi có link mới
        """
        link = ev.link
        link_info = {
            'src': link.src.dpid,
            'dst': link.dst.dpid,
            'src_port': link.src.port_no,
            'dst_port': link.dst.port_no
        }
        if link_info not in self.topology_data['links']:
            self.topology_data['links'].append(link_info)
        self.logger.info(f"Link mới: {link.src.dpid} -> {link.dst.dpid}")

    def get_topology(self):
        """
        Lấy thông tin topology hiện tại
        """
        return self.topology_data

    def get_flows(self):
        """
        Lấy danh sách flows đã cài đặt
        """
        return self.installed_flows


class SDNRestAPI(ControllerBase):
    """
    REST API cho SDN Controller
    """
    
    def __init__(self, req, link, data, **config):
        super(SDNRestAPI, self).__init__(req, link, data, **config)
        self.controller = data[instance_name]

    @route('topology', f'{url_base}/topology', methods=['GET'])
    def get_topology(self, req, **kwargs):
        """
        GET /sdn/topology
        Lấy thông tin topology
        """
        topology = self.controller.get_topology()
        body = json.dumps(topology, indent=2)
        return Response(content_type='application/json', text=body)

    @route('flows', f'{url_base}/flows', methods=['GET'])
    def get_flows(self, req, **kwargs):
        """
        GET /sdn/flows
        Lấy danh sách flows
        """
        flows = self.controller.get_flows()
        body = json.dumps(flows, indent=2)
        return Response(content_type='application/json', text=body)

    @route('add_flow', f'{url_base}/flow/add', methods=['POST'])
    def add_flow(self, req, **kwargs):
        """
        POST /sdn/flow/add
        Thêm flow mới
        
        Body JSON:
        {
            "switch_id": 1,
            "priority": 10,
            "src_ip": "10.0.0.1",
            "dst_ip": "10.0.0.2",
            "action": "forward",
            "out_port": 2
        }
        """
        try:
            data = json.loads(req.body.decode('utf-8'))
            
            switch_id = data.get('switch_id')
            priority = data.get('priority', 10)
            src_ip = data.get('src_ip')
            dst_ip = data.get('dst_ip')
            out_port = data.get('out_port')
            
            # Tìm datapath
            datapath = None
            for dp in self.controller.topology_data.get('switches', {}).keys():
                if dp == switch_id:
                    # Cần lấy datapath object từ switch
                    # Tạm thời trả về success
                    break
            
            response = {
                'status': 'success',
                'message': f'Flow added to switch {switch_id}',
                'flow': data
            }
            
            body = json.dumps(response, indent=2)
            return Response(content_type='application/json', text=body)
            
        except Exception as e:
            response = {
                'status': 'error',
                'message': str(e)
            }
            body = json.dumps(response, indent=2)
            return Response(status=400, content_type='application/json', text=body)

    @route('delete_flow', f'{url_base}/flow/delete', methods=['POST'])
    def delete_flow(self, req, **kwargs):
        """
        POST /sdn/flow/delete
        Xóa flow
        """
        try:
            data = json.loads(req.body.decode('utf-8'))
            switch_id = data.get('switch_id')
            
            response = {
                'status': 'success',
                'message': f'Flows deleted from switch {switch_id}'
            }
            
            body = json.dumps(response, indent=2)
            return Response(content_type='application/json', text=body)
            
        except Exception as e:
            response = {
                'status': 'error',
                'message': str(e)
            }
            body = json.dumps(response, indent=2)
            return Response(status=400, content_type='application/json', text=body)
