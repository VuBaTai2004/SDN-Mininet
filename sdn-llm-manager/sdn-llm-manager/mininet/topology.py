#!/usr/bin/python3
"""
Mininet Topology cho SDN LLM Manager

Topology:
    h1 --- s1 --- s2 --- h2
            |      |
           h3     h4

4 hosts, 2 switches
"""

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink


def create_topology():
    """
    Tạo topology mạng
    """
    info('*** Creating network\n')
    
    # Tạo Mininet với Remote Controller (Ryu)
    net = Mininet(
        controller=RemoteController,
        switch=OVSSwitch,
        link=TCLink,
        autoSetMacs=True,
        autoStaticArp=True
    )
    
    info('*** Adding controller\n')
    # Kết nối đến Ryu controller
    c0 = net.addController(
        'c0',
        controller=RemoteController,
        ip='127.0.0.1',
        port=6653
    )
    
    info('*** Adding switches\n')
    s1 = net.addSwitch('s1', protocols='OpenFlow13')
    s2 = net.addSwitch('s2', protocols='OpenFlow13')
    
    info('*** Adding hosts\n')
    h1 = net.addHost('h1', ip='10.0.0.1/24')
    h2 = net.addHost('h2', ip='10.0.0.2/24')
    h3 = net.addHost('h3', ip='10.0.0.3/24')
    h4 = net.addHost('h4', ip='10.0.0.4/24')
    
    info('*** Creating links\n')
    # Host - Switch links
    net.addLink(h1, s1, bw=10)  # 10 Mbps
    net.addLink(h3, s1, bw=10)
    net.addLink(h2, s2, bw=10)
    net.addLink(h4, s2, bw=10)
    
    # Switch - Switch link
    net.addLink(s1, s2, bw=20)  # 20 Mbps
    
    info('*** Starting network\n')
    net.build()
    c0.start()
    s1.start([c0])
    s2.start([c0])
    
    info('*** Network started successfully\n')
    info('*** Topology:\n')
    info('    h1(10.0.0.1) --- s1 --- s2 --- h2(10.0.0.2)\n')
    info('                      |      |\n')
    info('                   h3(10.0.0.3)  h4(10.0.0.4)\n\n')
    
    info('*** Testing connectivity\n')
    net.pingAll()
    
    info('\n*** Available commands:\n')
    info('  - pingall: Test connectivity between all hosts\n')
    info('  - h1 ping h2: Ping from h1 to h2\n')
    info('  - iperf h1 h2: Test bandwidth\n')
    info('  - dump: Show network info\n')
    info('  - net: Show topology\n')
    info('  - quit: Exit\n\n')
    
    info('*** Running CLI (Ctrl+D or "exit" to quit)\n')
    CLI(net)
    
    info('*** Stopping network\n')
    net.stop()


def create_simple_topology():
    """
    Tạo topology đơn giản hơn cho testing
    1 switch, 2 hosts
    """
    info('*** Creating simple network\n')
    
    net = Mininet(
        controller=RemoteController,
        switch=OVSSwitch,
        autoSetMacs=True
    )
    
    info('*** Adding controller\n')
    c0 = net.addController(
        'c0',
        controller=RemoteController,
        ip='127.0.0.1',
        port=6653
    )
    
    info('*** Adding switch\n')
    s1 = net.addSwitch('s1', protocols='OpenFlow13')
    
    info('*** Adding hosts\n')
    h1 = net.addHost('h1', ip='10.0.0.1/24')
    h2 = net.addHost('h2', ip='10.0.0.2/24')
    
    info('*** Creating links\n')
    net.addLink(h1, s1)
    net.addLink(h2, s1)
    
    info('*** Starting network\n')
    net.build()
    c0.start()
    s1.start([c0])
    
    info('*** Network started\n')
    info('*** Topology: h1 --- s1 --- h2\n\n')
    
    info('*** Testing connectivity\n')
    net.pingAll()
    
    info('*** Running CLI\n')
    CLI(net)
    
    info('*** Stopping network\n')
    net.stop()


def create_complex_topology():
    """
    Tạo topology phức tạp hơn
    3 switches, 6 hosts
    """
    info('*** Creating complex network\n')
    
    net = Mininet(
        controller=RemoteController,
        switch=OVSSwitch,
        link=TCLink,
        autoSetMacs=True
    )
    
    info('*** Adding controller\n')
    c0 = net.addController(
        'c0',
        controller=RemoteController,
        ip='127.0.0.1',
        port=6653
    )
    
    info('*** Adding switches\n')
    s1 = net.addSwitch('s1', protocols='OpenFlow13')
    s2 = net.addSwitch('s2', protocols='OpenFlow13')
    s3 = net.addSwitch('s3', protocols='OpenFlow13')
    
    info('*** Adding hosts\n')
    h1 = net.addHost('h1', ip='10.0.0.1/24')
    h2 = net.addHost('h2', ip='10.0.0.2/24')
    h3 = net.addHost('h3', ip='10.0.0.3/24')
    h4 = net.addHost('h4', ip='10.0.0.4/24')
    h5 = net.addHost('h5', ip='10.0.0.5/24')
    h6 = net.addHost('h6', ip='10.0.0.6/24')
    
    info('*** Creating links\n')
    # Hosts to switches
    net.addLink(h1, s1, bw=10)
    net.addLink(h2, s1, bw=10)
    net.addLink(h3, s2, bw=10)
    net.addLink(h4, s2, bw=10)
    net.addLink(h5, s3, bw=10)
    net.addLink(h6, s3, bw=10)
    
    # Switch interconnections (triangle topology)
    net.addLink(s1, s2, bw=20)
    net.addLink(s2, s3, bw=20)
    net.addLink(s3, s1, bw=20)
    
    info('*** Starting network\n')
    net.build()
    c0.start()
    s1.start([c0])
    s2.start([c0])
    s3.start([c0])
    
    info('*** Network started\n')
    info('*** Complex topology with 3 switches and 6 hosts\n\n')
    
    info('*** Testing connectivity\n')
    net.pingAll()
    
    info('*** Running CLI\n')
    CLI(net)
    
    info('*** Stopping network\n')
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    
    print("""
    ╔═══════════════════════════════════════╗
    ║   Mininet Topology for SDN Manager   ║
    ╚═══════════════════════════════════════╝
    
    Chọn topology:
    1. Simple (1 switch, 2 hosts) - Cho testing nhanh
    2. Medium (2 switches, 4 hosts) - Mặc định
    3. Complex (3 switches, 6 hosts) - Demo đầy đủ
    """)
    
    choice = input("Chọn topology (1/2/3) [mặc định: 2]: ").strip()
    
    print("\n⚠ QUAN TRỌNG: Đảm bảo Ryu Controller đang chạy!")
    print("Nếu chưa, mở terminal khác và chạy:")
    print("  ryu-manager --ofp-tcp-listen-port 6653 controller/ryu_controller.py\n")
    
    input("Nhấn Enter để tiếp tục...")
    
    if choice == '1':
        create_simple_topology()
    elif choice == '3':
        create_complex_topology()
    else:
        create_topology()
