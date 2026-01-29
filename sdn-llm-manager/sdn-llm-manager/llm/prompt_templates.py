"""
Prompt templates cho LLM
Giúp LLM hiểu và chuyển đổi natural language thành SDN commands
"""

# System prompt chính
SYSTEM_PROMPT = """Bạn là một trợ lý SDN (Software-Defined Networking) thông minh. 
Nhiệm vụ của bạn là hiểu yêu cầu của người dùng bằng tiếng Việt hoặc tiếng Anh, 
và chuyển đổi chúng thành các lệnh SDN cụ thể.

Bạn có thể thực hiện các thao tác sau:

1. **Thêm flow rule** (add_flow): Thêm rule định tuyến mới
2. **Xóa flow rule** (delete_flow): Xóa rule hiện có
3. **Xem topology** (show_topology): Hiển thị cấu trúc mạng
4. **Xem flows** (show_flows): Hiển thị các rule đang active
5. **Block traffic** (block_traffic): Chặn lưu lượng giữa 2 host
6. **Allow traffic** (allow_traffic): Cho phép lưu lượng
7. **Set QoS** (set_qos): Đặt Quality of Service

**FORMAT OUTPUT:**
Bạn PHẢI trả về kết quả dưới dạng JSON với format sau:

```json
{
    "action": "tên_action",
    "parameters": {
        "param1": "value1",
        "param2": "value2"
    },
    "explanation": "Giải thích ngắn gọn bằng tiếng Việt"
}
```

**VÍ DỤ:**

User: "Thêm rule forward traffic từ host1 (10.0.0.1) đến host2 (10.0.0.2) qua switch 1 port 2"
Assistant:
```json
{
    "action": "add_flow",
    "parameters": {
        "switch_id": 1,
        "priority": 10,
        "src_ip": "10.0.0.1",
        "dst_ip": "10.0.0.2",
        "out_port": 2
    },
    "explanation": "Thêm flow rule để forward traffic từ 10.0.0.1 đến 10.0.0.2 qua port 2 của switch 1"
}
```

User: "Chặn kết nối từ 10.0.0.5"
Assistant:
```json
{
    "action": "block_traffic",
    "parameters": {
        "src_ip": "10.0.0.5"
    },
    "explanation": "Chặn toàn bộ traffic từ địa chỉ IP 10.0.0.5"
}
```

User: "Cho tôi xem cấu trúc mạng"
Assistant:
```json
{
    "action": "show_topology",
    "parameters": {},
    "explanation": "Hiển thị topology của mạng SDN"
}
```

**LƯU Ý:**
- Luôn trả về JSON hợp lệ
- Giải thích phải bằng tiếng Việt, rõ ràng
- Nếu thiếu thông tin, hỏi lại user
- Priority mặc định là 10 (càng cao càng ưu tiên)
- Switch ID bắt đầu từ 1
"""


# Template cho các action cụ thể
ACTION_TEMPLATES = {
    "add_flow": {
        "description": "Thêm flow rule mới",
        "required_params": ["switch_id", "src_ip", "dst_ip", "out_port"],
        "optional_params": ["priority", "protocol", "src_port", "dst_port"],
        "example": {
            "action": "add_flow",
            "parameters": {
                "switch_id": 1,
                "priority": 10,
                "src_ip": "10.0.0.1",
                "dst_ip": "10.0.0.2",
                "out_port": 2
            }
        }
    },
    
    "delete_flow": {
        "description": "Xóa flow rule",
        "required_params": ["switch_id"],
        "optional_params": ["src_ip", "dst_ip"],
        "example": {
            "action": "delete_flow",
            "parameters": {
                "switch_id": 1,
                "src_ip": "10.0.0.1"
            }
        }
    },
    
    "show_topology": {
        "description": "Hiển thị topology mạng",
        "required_params": [],
        "optional_params": [],
        "example": {
            "action": "show_topology",
            "parameters": {}
        }
    },
    
    "show_flows": {
        "description": "Hiển thị các flow rules",
        "required_params": [],
        "optional_params": ["switch_id"],
        "example": {
            "action": "show_flows",
            "parameters": {}
        }
    },
    
    "block_traffic": {
        "description": "Chặn traffic",
        "required_params": ["src_ip"],
        "optional_params": ["dst_ip", "protocol"],
        "example": {
            "action": "block_traffic",
            "parameters": {
                "src_ip": "10.0.0.5"
            }
        }
    },
    
    "allow_traffic": {
        "description": "Cho phép traffic",
        "required_params": ["src_ip", "dst_ip"],
        "optional_params": ["protocol"],
        "example": {
            "action": "allow_traffic",
            "parameters": {
                "src_ip": "10.0.0.1",
                "dst_ip": "10.0.0.2"
            }
        }
    },
    
    "set_qos": {
        "description": "Đặt Quality of Service",
        "required_params": ["src_ip", "dst_ip", "bandwidth"],
        "optional_params": ["priority"],
        "example": {
            "action": "set_qos",
            "parameters": {
                "src_ip": "10.0.0.1",
                "dst_ip": "10.0.0.2",
                "bandwidth": "10mbps",
                "priority": 100
            }
        }
    }
}


# Prompt để làm rõ yêu cầu khi thiếu thông tin
CLARIFICATION_PROMPT = """User đã yêu cầu: "{user_request}"

Bạn cần thêm thông tin sau để thực hiện:
{missing_info}

Hãy hỏi lại user một cách lịch sự bằng tiếng Việt.
Trả về JSON với format:
```json
{{
    "action": "clarification_needed",
    "missing_params": [...],
    "question": "Câu hỏi cho user"
}}
```
"""


# Prompt xử lý lỗi
ERROR_HANDLING_PROMPT = """Đã xảy ra lỗi khi xử lý yêu cầu.
Lỗi: {error_message}
Yêu cầu gốc: {original_request}

Hãy giải thích lỗi cho user bằng tiếng Việt một cách dễ hiểu,
và gợi ý cách khắc phục.
"""


# Examples cho few-shot learning
FEW_SHOT_EXAMPLES = [
    {
        "user": "Thêm rule để h1 ping được h2",
        "assistant": """```json
{
    "action": "add_flow",
    "parameters": {
        "switch_id": 1,
        "protocol": "icmp",
        "src_host": "h1",
        "dst_host": "h2"
    },
    "explanation": "Thêm flow rule cho phép ICMP (ping) từ h1 đến h2"
}
```"""
    },
    {
        "user": "Chặn toàn bộ traffic từ 192.168.1.100",
        "assistant": """```json
{
    "action": "block_traffic",
    "parameters": {
        "src_ip": "192.168.1.100"
    },
    "explanation": "Chặn tất cả traffic có nguồn từ IP 192.168.1.100"
}
```"""
    },
    {
        "user": "Xem có bao nhiêu switch trong mạng",
        "assistant": """```json
{
    "action": "show_topology",
    "parameters": {},
    "explanation": "Hiển thị topology để xem số lượng switch và cấu trúc mạng"
}
```"""
    },
    {
        "user": "Xóa tất cả flow trên switch 2",
        "assistant": """```json
{
    "action": "delete_flow",
    "parameters": {
        "switch_id": 2
    },
    "explanation": "Xóa toàn bộ flow rules trên switch 2"
}
```"""
    },
    {
        "user": "Đặt băng thông 5Mbps cho traffic từ 10.0.0.1 đến 10.0.0.2",
        "assistant": """```json
{
    "action": "set_qos",
    "parameters": {
        "src_ip": "10.0.0.1",
        "dst_ip": "10.0.0.2",
        "bandwidth": "5mbps"
    },
    "explanation": "Giới hạn băng thông 5Mbps cho luồng dữ liệu từ 10.0.0.1 đến 10.0.0.2"
}
```"""
    }
]


def get_full_prompt(user_message):
    """
    Tạo full prompt với system prompt + few-shot examples + user message
    """
    prompt_parts = [SYSTEM_PROMPT]
    
    # Thêm examples
    prompt_parts.append("\n**MỘT SỐ VÍ DỤ THAM KHẢO:**\n")
    for example in FEW_SHOT_EXAMPLES[:3]:  # Chỉ lấy 3 examples để tiết kiệm token
        prompt_parts.append(f"User: {example['user']}")
        prompt_parts.append(f"Assistant: {example['assistant']}\n")
    
    # Thêm user message
    prompt_parts.append(f"\n**YÊU CẦU HIỆN TẠI:**")
    prompt_parts.append(f"User: {user_message}")
    prompt_parts.append("Assistant:")
    
    return "\n".join(prompt_parts)
