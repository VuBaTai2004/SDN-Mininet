# 🌐 SDN LLM Manager

**Ứng dụng quản lý mạng SDN thông qua Natural Language sử dụng Large Language Model (LLM)**

Đồ án chuyên ngành - Hệ thống cho phép cấu hình và quản lý mạng SDN bằng ngôn ngữ tự nhiên (tiếng Việt/Anh).

---

## 📋 Mục lục

- [Tổng quan](#tổng-quan)
- [Kiến trúc hệ thống](#kiến-trúc-hệ-thống)
- [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
- [Cài đặt](#cài-đặt)
- [Sử dụng](#sử-dụng)
- [Các tính năng](#các-tính-năng)
- [Ví dụ câu lệnh](#ví-dụ-câu-lệnh)
- [Kiến trúc chi tiết](#kiến-trúc-chi-tiết)
- [Troubleshooting](#troubleshooting)
- [Phát triển thêm](#phát-triển-thêm)

---

## 🎯 Tổng quan

Hệ thống này cho phép quản trị viên mạng tương tác với mạng SDN thông qua giao diện chatbot, sử dụng ngôn ngữ tự nhiên thay vì phải nhớ các câu lệnh phức tạp.

**Ví dụ:**
- Thay vì: `ovs-ofctl add-flow s1 priority=10,ip,nw_src=10.0.0.1,nw_dst=10.0.0.2,actions=output:2`
- Chỉ cần: "Thêm rule forward từ 10.0.0.1 đến 10.0.0.2 qua port 2"

### Công nghệ sử dụng:
- **SDN Controller:** Ryu (Python-based, OpenFlow 1.3)
- **LLM:** Ollama + Llama 3.2 (chạy local, hoàn toàn miễn phí)
- **Chatbot UI:** Gradio (Web-based interface)
- **Network Emulation:** Mininet
- **Language:** Python 3

---

## 🏗️ Kiến trúc hệ thống

```
┌─────────────┐
│   User      │
│  (Chatbot)  │
└──────┬──────┘
       │ Natural Language
       ▼
┌─────────────────┐
│   LLM Module    │
│  (Llama 3.2)    │
└──────┬──────────┘
       │ Structured Command (JSON)
       ▼
┌─────────────────┐
│ Command Parser  │
│   & Executor    │
└──────┬──────────┘
       │ REST API / OpenFlow
       ▼
┌─────────────────┐
│ Ryu Controller  │
│  (OpenFlow 1.3) │
└──────┬──────────┘
       │ OpenFlow Protocol
       ▼
┌─────────────────┐
│    Mininet      │
│   (SDN Network) │
└─────────────────┘
```

### Luồng xử lý:

1. **User Input** → Nhập câu lệnh tiếng Việt/Anh vào chatbot
2. **LLM Processing** → Llama 3.2 phân tích và chuyển đổi thành JSON command
3. **Command Parsing** → Parser validate và extract parameters
4. **Command Execution** → Gọi REST API của Ryu Controller
5. **SDN Configuration** → Controller cấu hình switches qua OpenFlow
6. **Response** → Trả kết quả về user qua chatbot

---

## 💻 Yêu cầu hệ thống

### Phần cứng tối thiểu:
- **CPU:** 4 cores
- **RAM:** 8GB (khuyến nghị 16GB)
- **Disk:** 10GB trống
- **Network:** Kết nối Internet (để tải model lần đầu)

### Phần mềm:
- **OS:** Ubuntu 20.04/22.04 (hoặc WSL2 trên Windows)
- **Python:** 3.8+
- **Git**

---

## 🚀 Cài đặt

### Bước 1: Clone repository

```bash
# Tạo thư mục cho project
mkdir -p ~/projects
cd ~/projects

# Nếu đã có code, copy vào. Nếu chưa:
# (Bạn đã có code rồi, chỉ cần cd vào thư mục)
cd sdn-llm-manager
```

### Bước 2: Cài đặt tự động

```bash
# Cấp quyền execute cho script
chmod +x install.sh

# Chạy script cài đặt
./install.sh
```

Script sẽ tự động:
1. Cập nhật hệ thống
2. Cài Python và dependencies
3. Cài Mininet
4. Cài Ryu Controller
5. Cài Ollama
6. Tải Llama 3.2 model (~3GB)

**Lưu ý:** Quá trình tải model có thể mất 5-10 phút tùy vào tốc độ mạng.

### Bước 3: Verify cài đặt

```bash
# Kiểm tra Ryu
ryu-manager --version

# Kiểm tra Mininet
sudo mn --version

# Kiểm tra Ollama
ollama --version

# Kiểm tra Python packages
pip3 list | grep -E "ryu|gradio"
```

---

## 🎮 Sử dụng

### Khởi động hệ thống (cần 4 terminals)

#### Terminal 1: Khởi động Ollama

```bash
ollama serve
```

Để chạy ở background:
```bash
nohup ollama serve > /dev/null 2>&1 &
```

#### Terminal 2: Khởi động Ryu Controller

```bash
cd ~/projects/sdn-llm-manager/controller
chmod +x start_controller.sh
./start_controller.sh
```

Hoặc:
```bash
ryu-manager --ofp-tcp-listen-port 6653 --wsapi-port 8080 controller/ryu_controller.py
```

#### Terminal 3: Khởi động Mininet

```bash
cd ~/projects/sdn-llm-manager
sudo python3 mininet/topology.py
```

Chọn topology (mặc định: 2 - Medium):
- 1: Simple (1 switch, 2 hosts)
- 2: Medium (2 switches, 4 hosts)
- 3: Complex (3 switches, 6 hosts)

#### Terminal 4: Khởi động Chatbot

```bash
cd ~/projects/sdn-llm-manager
python3 chatbot/app.py
```

Chatbot sẽ chạy tại: `http://localhost:7860`

Mở browser và truy cập: **http://localhost:7860**

---

## ✨ Các tính năng

### 1. Xem thông tin mạng

**Lệnh:**
- "Cho tôi xem cấu trúc mạng"
- "Hiển thị topology"
- "Có bao nhiêu switch trong mạng?"

**Kết quả:** Hiển thị số lượng switches, links, và cấu trúc mạng

### 2. Quản lý Flow Rules

**Thêm flow:**
- "Thêm rule forward từ 10.0.0.1 đến 10.0.0.2 qua port 2"
- "Tạo flow cho h1 ping h2"

**Xóa flow:**
- "Xóa tất cả flows trên switch 1"
- "Xóa rule từ 10.0.0.1"

**Xem flows:**
- "Hiển thị các flow rules"
- "Cho tôi xem flows trên switch 1"

### 3. Kiểm soát Traffic

**Chặn traffic:**
- "Chặn kết nối từ 10.0.0.5"
- "Block traffic từ h3 đến h4"

**Cho phép traffic:**
- "Cho phép h1 kết nối với h2"
- "Mở traffic từ 10.0.0.1 đến 10.0.0.2"

### 4. Quality of Service (QoS)

**Đặt bandwidth:**
- "Đặt băng thông 5Mbps từ 10.0.0.1 đến 10.0.0.2"
- "Giới hạn bandwidth 10Mbps cho h1"

---

## 📝 Ví dụ câu lệnh

### Demo cơ bản

1. **Khởi động và kiểm tra:**
```
User: Xin chào, bạn là ai?
Bot: Chào bạn! Tôi là trợ lý SDN...

User: Cho tôi xem cấu trúc mạng
Bot: ✅ Mạng có 2 switches và 1 links
     📊 Thông tin mạng:
     - Số switches: 2
     - Số links: 1
     ...
```

2. **Thêm flow rule:**
```
User: Thêm rule forward traffic từ 10.0.0.1 đến 10.0.0.2 qua switch 1 port 2
Bot: 💡 Thêm flow rule để forward traffic từ 10.0.0.1 đến 10.0.0.2 qua port 2
     ✅ Đã thêm flow rule trên switch 1
```

3. **Xem flows:**
```
User: Hiển thị tất cả flow rules
Bot: 📋 Flow Rules (5 rules):
     1. Switch 1 | Priority: 10 | Match: eth_dst=00:00:00:00:00:02
     ...
```

4. **Chặn traffic:**
```
User: Chặn toàn bộ traffic từ 10.0.0.5
Bot: 💡 Chặn tất cả traffic có nguồn từ IP 10.0.0.5
     ✅ Đã chặn traffic từ 10.0.0.5
```

---

## 🔧 Kiến trúc chi tiết

### Module 1: LLM Module

**File:** `llm/ollama_client.py`

- Kết nối với Ollama server
- Gọi Llama 3.2 model
- Xử lý chat và generation
- Extract JSON từ response

**File:** `llm/prompt_templates.py`

- System prompts
- Few-shot examples
- Action templates
- Error handling prompts

### Module 2: Chatbot Interface

**File:** `chatbot/app.py`

- Gradio web interface
- Chat history management
- Response formatting
- Error handling

**File:** `chatbot/command_parser.py`

- Parse JSON từ LLM
- Validate commands
- Execute via REST API
- Format results

### Module 3: SDN Controller

**File:** `controller/ryu_controller.py`

- OpenFlow 1.3 controller
- REST API endpoints
- Flow management
- Topology discovery

### Module 4: Network Emulation

**File:** `mininet/topology.py`

- Tạo virtual network
- Multiple topology options
- Auto-connect to controller

---

## 🐛 Troubleshooting

### Lỗi: "Cannot connect to Ollama"

**Nguyên nhân:** Ollama service chưa chạy

**Giải pháp:**
```bash
ollama serve
```

### Lỗi: "Cannot connect to Ryu Controller"

**Kiểm tra:**
```bash
# Xem process có đang chạy không
ps aux | grep ryu

# Kiểm tra port
netstat -tulpn | grep 8080
netstat -tulpn | grep 6653
```

**Giải pháp:** Khởi động lại controller

### Lỗi: Mininet không kết nối được controller

**Kiểm tra:** Ryu có đang lắng nghe port 6653 không

**Giải pháp:**
```bash
# Dừng Mininet
sudo mn -c

# Khởi động lại theo thứ tự:
# 1. Ryu Controller
# 2. Mininet
```

### Lỗi: "Model not found"

**Nguyên nhân:** Chưa tải Llama 3.2

**Giải pháp:**
```bash
ollama pull llama3.2
```

### Lỗi: Permission denied khi chạy Mininet

**Nguyên nhân:** Mininet cần sudo

**Giải pháp:**
```bash
sudo python3 mininet/topology.py
```

### Lỗi: LLM response không phải JSON

**Nguyên nhân:** Model hallucination hoặc prompt không rõ ràng

**Giải pháp:**
- Thử lại với câu lệnh rõ ràng hơn
- Restart Ollama và thử lại
- Kiểm tra temperature trong code (nên <= 0.5)

---

## 🚀 Phát triển thêm

### Thêm tính năng mới

#### 1. Thêm action mới

**Bước 1:** Thêm vào `llm/prompt_templates.py`
```python
ACTION_TEMPLATES["new_action"] = {
    "description": "Mô tả",
    "required_params": ["param1", "param2"],
    "example": {...}
}
```

**Bước 2:** Implement trong `chatbot/command_parser.py`
```python
def _new_action(self, params):
    # Logic xử lý
    return {'status': 'success', ...}
```

**Bước 3:** Thêm vào `execute()` method

#### 2. Cải thiện LLM performance

**Tăng context window:**
```python
# Trong ollama_client.py
def generate(self, prompt, max_tokens=4000):  # Tăng từ 2000
    ...
```

**Giảm temperature để ổn định hơn:**
```python
temperature=0.3  # Thay vì 0.7
```

#### 3. Thêm logging

```python
import logging

logging.basicConfig(
    filename='sdn_llm.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Testing

#### Test LLM Client
```bash
python3 llm/ollama_client.py
```

#### Test Command Parser
```bash
python3 chatbot/command_parser.py
```

#### Test Controller API
```bash
# Get topology
curl http://localhost:8080/sdn/topology

# Get flows
curl http://localhost:8080/sdn/flows

# Add flow
curl -X POST http://localhost:8080/sdn/flow/add \
  -H "Content-Type: application/json" \
  -d '{"switch_id": 1, "priority": 10, "src_ip": "10.0.0.1", "dst_ip": "10.0.0.2", "out_port": 2}'
```

---

## 📚 Tài liệu tham khảo

- [Ryu Documentation](https://ryu.readthedocs.io/)
- [Mininet Documentation](http://mininet.org/)
- [Ollama Documentation](https://ollama.com/docs)
- [OpenFlow Specification](https://opennetworking.org/software-defined-standards/specifications/)
- [Gradio Documentation](https://www.gradio.app/docs)

---

## 📊 Báo cáo đồ án

Xem template báo cáo tại: `docs/report_template.md`

### Nội dung báo cáo gồm:

1. **Giới thiệu**
   - Bối cảnh và động lực
   - Mục tiêu đồ án
   - Phạm vi nghiên cứu

2. **Cơ sở lý thuyết**
   - SDN và OpenFlow
   - Large Language Models
   - Natural Language Processing

3. **Phân tích và thiết kế**
   - Yêu cầu hệ thống
   - Kiến trúc tổng thể
   - Thiết kế chi tiết

4. **Cài đặt và triển khai**
   - Công nghệ sử dụng
   - Quy trình triển khai
   - Code chính

5. **Kết quả và đánh giá**
   - Demo hệ thống
   - Đánh giá hiệu năng
   - So sánh với các giải pháp khác

6. **Kết luận**
   - Tổng kết
   - Hướng phát triển

---

## 🤝 Đóng góp

Nếu bạn muốn cải thiện project:

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push và tạo Pull Request

---

## 📜 License

MIT License - Free to use for educational purposes

---

## 👨‍💻 Tác giả

Đồ án chuyên ngành - [Tên của bạn]

**Giảng viên hướng dẫn:** [Tên giảng viên]

**Trường:** [Tên trường]

**Năm:** 2025

---

## 📧 Liên hệ

- Email: [email của bạn]
- GitHub: [github profile]

---

**Chúc bạn thành công với đồ án! 🎉**
