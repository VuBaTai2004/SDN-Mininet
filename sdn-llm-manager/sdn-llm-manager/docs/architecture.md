# KIẾN TRÚC HỆ THỐNG CHI TIẾT

## 1. TỔNG QUAN KIẾN TRÚC

### 1.1. Architecture Layers

Hệ thống được thiết kế theo kiến trúc 4 layers:

```
┌─────────────────────────────────────────────────────────┐
│              PRESENTATION LAYER                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Gradio Web Interface                      │  │
│  │  - Chat UI                                        │  │
│  │  - History Management                             │  │
│  │  - Response Formatting                            │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP/WebSocket
┌────────────────────────▼────────────────────────────────┐
│              APPLICATION LAYER                           │
│  ┌──────────────┐           ┌────────────────────────┐ │
│  │   Chatbot    │           │   Command Parser       │ │
│  │   Handler    │◄─────────►│   & Executor           │ │
│  │              │           │                        │ │
│  │ - Message    │           │ - JSON Parsing         │ │
│  │   Processing │           │ - Validation           │ │
│  │ - Context    │           │ - API Calls            │ │
│  │   Management │           │ - Result Formatting    │ │
│  └──────┬───────┘           └────────────────────────┘ │
│         │                                                │
│  ┌──────▼─────────────────────────────────────────┐    │
│  │         LLM Module                             │    │
│  │  ┌──────────────────────────────────────────┐ │    │
│  │  │      Ollama Client                       │ │    │
│  │  │  - API Communication                     │ │    │
│  │  │  - Response Parsing                      │ │    │
│  │  └──────────────────────────────────────────┘ │    │
│  │  ┌──────────────────────────────────────────┐ │    │
│  │  │      Prompt Templates                    │ │    │
│  │  │  - System Prompts                        │ │    │
│  │  │  - Few-Shot Examples                     │ │    │
│  │  │  - Output Format Specifications          │ │    │
│  │  └──────────────────────────────────────────┘ │    │
│  └────────────────────────────────────────────────┘    │
└────────────────────────┬────────────────────────────────┘
                         │ REST API (HTTP)
┌────────────────────────▼────────────────────────────────┐
│              CONTROL LAYER                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Ryu SDN Controller                      │   │
│  │  ┌────────────────────────────────────────────┐ │   │
│  │  │      Flow Manager                          │ │   │
│  │  │  - Add/Delete/Modify Flows                 │ │   │
│  │  │  - Flow Table Management                   │ │   │
│  │  └────────────────────────────────────────────┘ │   │
│  │  ┌────────────────────────────────────────────┐ │   │
│  │  │      Topology Manager                      │ │   │
│  │  │  - Switch Discovery                        │ │   │
│  │  │  - Link Discovery                          │ │   │
│  │  │  - Host Tracking                           │ │   │
│  │  └────────────────────────────────────────────┘ │   │
│  │  ┌────────────────────────────────────────────┐ │   │
│  │  │      REST API Server                       │ │   │
│  │  │  - /sdn/topology                           │ │   │
│  │  │  - /sdn/flows                              │ │   │
│  │  │  - /sdn/flow/add                           │ │   │
│  │  │  - /sdn/flow/delete                        │ │   │
│  │  └────────────────────────────────────────────┘ │   │
│  │  ┌────────────────────────────────────────────┐ │   │
│  │  │      Event Handlers                        │ │   │
│  │  │  - PacketIn Handler                        │ │   │
│  │  │  - SwitchEnter Handler                     │ │   │
│  │  │  - LinkAdd Handler                         │ │   │
│  │  └────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────┘
                         │ OpenFlow 1.3
┌────────────────────────▼────────────────────────────────┐
│         INFRASTRUCTURE LAYER                             │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Mininet Virtual Network                 │   │
│  │  ┌────────────────────────────────────────────┐ │   │
│  │  │   Open vSwitch (OVS)                       │ │   │
│  │  │   - Flow Tables                            │ │   │
│  │  │   - Packet Processing                      │ │   │
│  │  │   - Port Management                        │ │   │
│  │  └────────────────────────────────────────────┘ │   │
│  │  ┌────────────────────────────────────────────┐ │   │
│  │  │   Virtual Hosts                            │ │   │
│  │  │   - Network Stack                          │ │   │
│  │  │   - IP Configuration                       │ │   │
│  │  └────────────────────────────────────────────┘ │   │
│  │  ┌────────────────────────────────────────────┐ │   │
│  │  │   Virtual Links                            │ │   │
│  │  │   - Bandwidth Configuration                │ │   │
│  │  │   - Delay/Loss Emulation                   │ │   │
│  │  └────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## 2. DATA FLOW CHI TIẾT

### 2.1. Request Processing Pipeline

```
User Input
    │
    ├─ "Thêm rule forward từ 10.0.0.1 đến 10.0.0.2 qua port 2"
    │
    ▼
┌─────────────────────────┐
│  Chatbot Handler        │
│  (chatbot/app.py)       │
└───────┬─────────────────┘
        │
        │ 1. Receive message
        │ 2. Build conversation context
        │ 3. Prepare for LLM
        │
        ▼
┌─────────────────────────┐
│  Prompt Builder         │
│  (llm/prompt_templates) │
└───────┬─────────────────┘
        │
        │ System Prompt:
        │   - Role: SDN Assistant
        │   - Output: JSON format
        │   - Available actions
        │
        │ Few-Shot Examples:
        │   - Example 1: Add flow
        │   - Example 2: Block traffic
        │   - Example 3: Show topology
        │
        │ User Message:
        │   - "Thêm rule forward..."
        │
        ▼
┌─────────────────────────┐
│  LLM (Llama 3.2)        │
│  via Ollama API         │
└───────┬─────────────────┘
        │
        │ Processing:
        │   - Intent Recognition
        │   - Entity Extraction
        │   - JSON Generation
        │
        ▼
┌─────────────────────────┐
│  LLM Response           │
└───────┬─────────────────┘
        │
        │ {
        │   "action": "add_flow",
        │   "parameters": {
        │     "switch_id": 1,
        │     "src_ip": "10.0.0.1",
        │     "dst_ip": "10.0.0.2",
        │     "out_port": 2,
        │     "priority": 10
        │   },
        │   "explanation": "Thêm flow rule..."
        │ }
        │
        ▼
┌─────────────────────────┐
│  Command Parser         │
│  (chatbot/command_...)  │
└───────┬─────────────────┘
        │
        │ 1. Extract JSON from text
        │ 2. Validate structure
        │ 3. Check required params
        │ 4. Sanitize inputs
        │
        ▼
┌─────────────────────────┐
│  Command Executor       │
└───────┬─────────────────┘
        │
        │ Route to handler:
        │   add_flow() → _add_flow()
        │
        ▼
┌─────────────────────────┐
│  REST API Call          │
└───────┬─────────────────┘
        │
        │ POST http://localhost:8080/sdn/flow/add
        │ Content-Type: application/json
        │ Body: {parameters}
        │
        ▼
┌─────────────────────────┐
│  Ryu Controller         │
│  REST API Handler       │
└───────┬─────────────────┘
        │
        │ 1. Parse request
        │ 2. Validate parameters
        │ 3. Find target switch
        │
        ▼
┌─────────────────────────┐
│  Flow Manager           │
└───────┬─────────────────┘
        │
        │ 1. Create match object
        │    match = OFPMatch(
        │      in_port=in_port,
        │      eth_type=0x0800,
        │      ipv4_src='10.0.0.1',
        │      ipv4_dst='10.0.0.2'
        │    )
        │
        │ 2. Create actions
        │    actions = [
        │      OFPActionOutput(port=2)
        │    ]
        │
        │ 3. Create instructions
        │    inst = [
        │      OFPInstructionActions(
        │        OFPIT_APPLY_ACTIONS,
        │        actions
        │      )
        │    ]
        │
        ▼
┌─────────────────────────┐
│  OpenFlow Message       │
└───────┬─────────────────┘
        │
        │ OFPFlowMod(
        │   datapath=dp,
        │   priority=10,
        │   match=match,
        │   instructions=inst
        │ )
        │
        ▼
┌─────────────────────────┐
│  Switch (OVS)           │
└───────┬─────────────────┘
        │
        │ 1. Receive FlowMod
        │ 2. Install in flow table
        │ 3. Send acknowledgment
        │
        │ Flow Table Entry:
        │   priority=10,
        │   ip,
        │   nw_src=10.0.0.1,
        │   nw_dst=10.0.0.2
        │   actions=output:2
        │
        ▼
┌─────────────────────────┐
│  Response to User       │
└─────────────────────────┘
        │
        │ "✅ Đã thêm flow rule
        │  trên switch 1"
        │
        ▼
    User sees result
```

## 3. COMPONENT INTERACTIONS

### 3.1. LLM Module Interaction

```
┌──────────────────────────────────────────────────────┐
│                  LLM Module                           │
│                                                       │
│  ┌────────────────┐          ┌──────────────────┐   │
│  │ OllamaClient   │          │ PromptTemplates  │   │
│  │                │          │                  │   │
│  │ - __init__()   │◄────────►│ - SYSTEM_PROMPT  │   │
│  │ - generate()   │          │ - EXAMPLES       │   │
│  │ - chat()       │          │ - get_full_      │   │
│  │ - extract_json│          │   prompt()       │   │
│  └────────┬───────┘          └──────────────────┘   │
│           │                                          │
└───────────┼──────────────────────────────────────────┘
            │
            │ HTTP POST
            ▼
    ┌──────────────────┐
    │  Ollama Server   │
    │  (Port 11434)    │
    └────────┬─────────┘
             │
             │ Load & Run
             ▼
    ┌──────────────────┐
    │  Llama 3.2 Model │
    │  (3B params)     │
    └──────────────────┘
```

### 3.2. Controller Architecture

```
┌────────────────────────────────────────────────────────┐
│              Ryu Controller Process                     │
│                                                         │
│  ┌──────────────────────────────────────────────────┐ │
│  │          SDNController (Main App)                │ │
│  │                                                  │ │
│  │  Attributes:                                     │ │
│  │    - mac_to_port: dict                          │ │
│  │    - topology_data: dict                        │ │
│  │    - installed_flows: list                      │ │
│  │                                                  │ │
│  │  Event Handlers:                                │ │
│  │    @set_ev_cls(EventOFPPacketIn)               │ │
│  │    @set_ev_cls(EventOFPSwitchFeatures)         │ │
│  │    @set_ev_cls(EventSwitchEnter)               │ │
│  │    @set_ev_cls(EventLinkAdd)                   │ │
│  └──────────────────┬───────────────────────────────┘ │
│                     │                                  │
│  ┌──────────────────▼───────────────────────────────┐ │
│  │          SDNRestAPI (WSGI App)                   │ │
│  │                                                  │ │
│  │  Routes:                                         │ │
│  │    GET  /sdn/topology                           │ │
│  │    GET  /sdn/flows                              │ │
│  │    POST /sdn/flow/add                           │ │
│  │    POST /sdn/flow/delete                        │ │
│  └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
            │                            │
            │ OpenFlow 1.3               │ HTTP REST
            ▼                            ▼
    ┌────────────────┐          ┌────────────────┐
    │    Switches    │          │  Chatbot App   │
    └────────────────┘          └────────────────┘
```

## 4. SECURITY CONSIDERATIONS

### 4.1. Threat Model

```
┌──────────────────────────────────────────────────────┐
│                  Attack Surface                       │
│                                                       │
│  1. Web Interface (Gradio)                           │
│     - XSS attacks                                    │
│     - CSRF                                           │
│     - Session hijacking                              │
│                                                       │
│  2. REST API                                         │
│     - Unauthorized access                            │
│     - API abuse                                      │
│     - Parameter injection                            │
│                                                       │
│  3. LLM Input                                        │
│     - Prompt injection                               │
│     - Command injection via NL                       │
│     - Malicious commands                             │
│                                                       │
│  4. Controller                                       │
│     - OpenFlow DoS                                   │
│     - Malicious flow rules                           │
│     - Topology poisoning                             │
└──────────────────────────────────────────────────────┘
```

### 4.2. Mitigation Strategies

```
Layer              | Mitigation
-------------------|------------------------------------------
Web Interface      | - Input sanitization
                   | - HTTPS only
                   | - Session timeout
                   | - Rate limiting
-------------------|------------------------------------------
REST API           | - Authentication (JWT)
                   | - Authorization (RBAC)
                   | - Request validation
                   | - API rate limiting
-------------------|------------------------------------------
LLM Processing     | - Prompt validation
                   | - Output validation
                   | - Whitelist of actions
                   | - Parameter range checks
-------------------|------------------------------------------
Controller         | - Flow rule validation
                   | - Resource limits
                   | - Audit logging
                   | - Anomaly detection
```

## 5. SCALABILITY ANALYSIS

### 5.1. Current Bottlenecks

```
Component          | Bottleneck          | Max Throughput
-------------------|---------------------|----------------
LLM Inference      | CPU/GPU             | ~1-2 req/sec
REST API           | Single-threaded     | ~100 req/sec
Controller         | Event processing    | ~1000 flows/sec
Mininet            | CPU scheduling      | ~100 switches
```

### 5.2. Scaling Strategies

```
┌─────────────────────────────────────────────────────┐
│              Horizontal Scaling                      │
│                                                      │
│  ┌──────────────┐     ┌──────────────┐             │
│  │   LLM Pool   │     │   LLM Pool   │             │
│  │   Instance 1 │     │   Instance 2 │             │
│  └──────┬───────┘     └──────┬───────┘             │
│         └──────────┬──────────┘                     │
│                    │                                 │
│         ┌──────────▼──────────┐                     │
│         │   Load Balancer     │                     │
│         └──────────┬──────────┘                     │
│                    │                                 │
│         ┌──────────▼──────────┐                     │
│         │   Chatbot Queue     │                     │
│         └─────────────────────┘                     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│              Controller Clustering                   │
│                                                      │
│  ┌──────────────┐     ┌──────────────┐             │
│  │ Controller 1 │     │ Controller 2 │             │
│  │   (Master)   │◄───►│  (Backup)    │             │
│  └──────┬───────┘     └──────┬───────┘             │
│         │                     │                      │
│         └─────────┬───────────┘                     │
│                   │                                  │
│         ┌─────────▼─────────┐                       │
│         │  Shared Database  │                       │
│         │  (Topology State) │                       │
│         └───────────────────┘                       │
└─────────────────────────────────────────────────────┘
```

## 6. DEPLOYMENT ARCHITECTURE

### 6.1. Development Environment

```
┌──────────────────────────────────────────────┐
│          Single Machine (Laptop)              │
│                                               │
│  ┌────────────┐  ┌────────────┐             │
│  │  Ollama    │  │    Ryu     │             │
│  │ (Port      │  │ (Port 6653 │             │
│  │  11434)    │  │  & 8080)   │             │
│  └────────────┘  └────────────┘             │
│                                               │
│  ┌────────────┐  ┌────────────┐             │
│  │  Mininet   │  │  Gradio    │             │
│  │  (sudo)    │  │ (Port 7860)│             │
│  └────────────┘  └────────────┘             │
└──────────────────────────────────────────────┘
```

### 6.2. Production Environment (Future)

```
┌─────────────────────────────────────────────────┐
│            Load Balancer                         │
└────────────────┬────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
┌───────▼────────┐  ┌────▼──────────┐
│  Web Server 1  │  │ Web Server 2  │
│  (Nginx)       │  │ (Nginx)       │
└───────┬────────┘  └────┬──────────┘
        │                 │
┌───────▼────────┐  ┌────▼──────────┐
│  Chatbot App 1 │  │ Chatbot App 2 │
│  (Gunicorn)    │  │ (Gunicorn)    │
└───────┬────────┘  └────┬──────────┘
        │                 │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │   LLM Cluster   │
        │  (Kubernetes)   │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │  SDN Controller │
        │   Cluster       │
        │  (HA Setup)     │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │  Physical SDN   │
        │  Switches       │
        └─────────────────┘
```

## 7. MONITORING & OBSERVABILITY

### 7.1. Metrics Collection

```
┌──────────────────────────────────────────────────┐
│              Application Metrics                  │
│                                                   │
│  LLM Module:                                     │
│    - Inference time (avg, p95, p99)             │
│    - Token count (input/output)                 │
│    - Error rate                                  │
│                                                   │
│  Command Parser:                                 │
│    - Parse success rate                          │
│    - Validation errors                           │
│                                                   │
│  Controller:                                     │
│    - Flow installation time                      │
│    - Active flows count                          │
│    - PacketIn rate                               │
│    - Topology events                             │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│              System Metrics                       │
│                                                   │
│  - CPU usage (per component)                     │
│  - Memory usage                                   │
│  - Network I/O                                    │
│  - Disk I/O                                       │
└──────────────────────────────────────────────────┘
```

### 7.2. Logging Architecture

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Chatbot   │  │     LLM     │  │  Controller │
│     Logs    │  │    Logs     │  │    Logs     │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       └────────────────┼────────────────┘
                        │
                ┌───────▼────────┐
                │  Log Collector │
                │  (Fluentd)     │
                └───────┬────────┘
                        │
                ┌───────▼────────┐
                │  Log Storage   │
                │(Elasticsearch) │
                └───────┬────────┘
                        │
                ┌───────▼────────┐
                │ Visualization  │
                │   (Kibana)     │
                └────────────────┘
```

---

**Document Version:** 1.0
**Last Updated:** 2025-01-27
