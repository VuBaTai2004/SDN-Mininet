import gradio as gr
import sys
import os
from datetime import datetime

# Thêm thư mục cha vào path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm.ollama_client import OllamaClient
from llm.prompt_templates import get_full_prompt
from chatbot.command_parser import CommandParser


class SDNChatbot:
    """
    Chatbot interface cho SDN management
    """
    
    def __init__(self):
        print("Khởi tạo SDN Chatbot...")
        
        # Khởi tạo LLM client
        self.llm = OllamaClient(model="llama3.2")
        
        # Khởi tạo command parser
        self.parser = CommandParser()
        
        # Lịch sử chat
        self.chat_history = []
        
        print("✓ Chatbot đã sẵn sàng!")
    
    def process_message(self, message, history):
        """
        Xử lý message từ user
        
        Args:
            message: Message từ user
            history: Lịch sử chat (format Gradio)
        
        Returns:
            str: Response từ bot
        """
        try:
            # Log user message
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{timestamp}] User: {message}")
            
            # Tạo prompt cho LLM
            full_prompt = get_full_prompt(message)
            
            # Gọi LLM
            print(f"[{timestamp}] Đang xử lý với LLM...")
            llm_response = self.llm.generate(full_prompt, temperature=0.3)
            
            if not llm_response:
                return "❌ Lỗi: Không thể kết nối đến LLM. Kiểm tra xem Ollama có đang chạy không (chạy: ollama serve)"
            
            print(f"[{timestamp}] LLM response: {llm_response[:200]}...")
            
            # Parse command từ LLM response
            parse_result = self.parser.parse(llm_response)
            
            if parse_result['status'] == 'error':
                return f"❌ {parse_result['message']}\n\n💬 Response từ LLM:\n{llm_response}"
            
            command = parse_result['command']
            explanation = command.get('explanation', '')
            
            # Thực thi command
            print(f"[{timestamp}] Đang thực thi: {command['action']}")
            exec_result = self.parser.execute(command)
            
            # Format response
            response = self._format_response(command, exec_result, explanation)
            
            print(f"[{timestamp}] ✓ Hoàn thành")
            return response
            
        except Exception as e:
            print(f"❌ Lỗi: {str(e)}")
            return f"❌ Đã xảy ra lỗi: {str(e)}"
    
    def _format_response(self, command, exec_result, explanation):
        """
        Format response để hiển thị đẹp
        """
        response_parts = []
        
        # Explanation từ LLM
        if explanation:
            response_parts.append(f"💡 **{explanation}**\n")
        
        # Kết quả thực thi
        if exec_result['status'] == 'success':
            response_parts.append(f"✅ {exec_result.get('message', 'Thành công')}")
            
            # Data nếu có
            if 'data' in exec_result:
                data = exec_result['data']
                
                # Format topology data
                if command['action'] == 'show_topology':
                    response_parts.append(f"\n📊 **Thông tin mạng:**")
                    response_parts.append(f"- Số switches: {data['num_switches']}")
                    response_parts.append(f"- Số links: {data['num_links']}")
                    
                    if data['switches']:
                        response_parts.append(f"\n**Danh sách switches:**")
                        for dpid, info in data['switches'].items():
                            response_parts.append(f"  - Switch {dpid}: {info.get('ports', 0)} ports")
                    
                    if data['links']:
                        response_parts.append(f"\n**Danh sách links:**")
                        for link in data['links'][:5]:  # Chỉ show 5 links đầu
                            response_parts.append(
                                f"  - Switch {link['src']} port {link['src_port']} "
                                f"↔ Switch {link['dst']} port {link['dst_port']}"
                            )
                
                # Format flows data
                elif command['action'] == 'show_flows':
                    response_parts.append(f"\n📋 **Flow Rules ({len(data)} rules):**")
                    for i, flow in enumerate(data[:10], 1):  # Show 10 flows đầu
                        response_parts.append(
                            f"\n{i}. Switch {flow.get('switch_id')} | "
                            f"Priority: {flow.get('priority')} | "
                            f"Match: {flow.get('match', 'N/A')[:50]}"
                        )
                    if len(data) > 10:
                        response_parts.append(f"\n... và {len(data) - 10} flows khác")
        
        else:
            response_parts.append(f"❌ {exec_result.get('message', 'Có lỗi xảy ra')}")
            
            # Note nếu có
            if 'note' in exec_result:
                response_parts.append(f"\nℹ️ {exec_result['note']}")
        
        return "\n".join(response_parts)


def create_interface():
    """
    Tạo Gradio interface
    """
    chatbot_instance = SDNChatbot()
    
    # Custom CSS
    custom_css = """
    .gradio-container {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .message-wrap {
        font-size: 14px;
    }
    """
    
    # Tạo interface
    with gr.Blocks(css=custom_css, title="SDN LLM Manager") as demo:
        gr.Markdown("""
        # 🌐 SDN LLM Manager
        ### Quản lý mạng SDN thông qua Natural Language
        
        Bạn có thể:
        - 📊 Xem topology mạng
        - ➕ Thêm/xóa flow rules
        - 🚫 Chặn/cho phép traffic
        - ⚙️ Cấu hình QoS
        
        **Ví dụ:**
        - "Cho tôi xem cấu trúc mạng"
        - "Thêm rule forward từ 10.0.0.1 đến 10.0.0.2"
        - "Chặn traffic từ 192.168.1.100"
        """)
        
        chatbot = gr.Chatbot(
            height=500,
            show_label=False,
            avatar_images=[None, "🤖"]
        )
        
        with gr.Row():
            msg = gr.Textbox(
                placeholder="Nhập yêu cầu của bạn...",
                show_label=False,
                scale=9
            )
            submit = gr.Button("Gửi", scale=1, variant="primary")
        
        gr.Examples(
            examples=[
                "Xem topology mạng",
                "Hiển thị tất cả flow rules",
                "Thêm flow từ h1 đến h2 qua switch 1",
                "Chặn traffic từ 10.0.0.5",
                "Đặt băng thông 5Mbps từ 10.0.0.1 đến 10.0.0.2"
            ],
            inputs=msg,
            label="📝 Câu lệnh mẫu"
        )
        
        gr.Markdown("""
        ---
        **Lưu ý:**
        - Đảm bảo Ryu Controller đang chạy: `ryu-manager controller/ryu_controller.py`
        - Đảm bảo Mininet đang chạy: `sudo python3 mininet/topology.py`
        - Đảm bảo Ollama đang chạy: `ollama serve`
        """)
        
        # Xử lý submit
        def respond(message, chat_history):
            if not message.strip():
                return "", chat_history
            
            # Thêm message vào history
            chat_history.append([message, None])
            
            # Xử lý với chatbot
            bot_response = chatbot_instance.process_message(message, chat_history)
            
            # Update history
            chat_history[-1][1] = bot_response
            
            return "", chat_history
        
        submit.click(respond, [msg, chatbot], [msg, chatbot])
        msg.submit(respond, [msg, chatbot], [msg, chatbot])
    
    return demo


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════╗
    ║     SDN LLM Manager - Chatbot UI        ║
    ╚══════════════════════════════════════════╝
    """)
    
    # Kiểm tra dependencies
    print("Kiểm tra môi trường...")
    
    try:
        import requests
        # Test Ollama
        try:
            resp = requests.get("http://localhost:11434/api/tags", timeout=2)
            print("✓ Ollama đang chạy")
        except:
            print("⚠ Cảnh báo: Ollama chưa chạy. Khởi động bằng: ollama serve")
        
        # Test Ryu Controller
        try:
            resp = requests.get("http://localhost:8080/sdn/topology", timeout=2)
            print("✓ Ryu Controller đang chạy")
        except:
            print("⚠ Cảnh báo: Ryu Controller chưa chạy")
    except:
        pass
    
    print("\nKhởi động Chatbot UI...")
    
    # Tạo và chạy interface
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
