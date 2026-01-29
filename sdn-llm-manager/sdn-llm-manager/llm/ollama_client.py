import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Client để giao tiếp với Ollama (Local LLM)
    """
    
    def __init__(self, host="http://localhost:11434", model="llama3.2"):
        self.host = host
        self.model = model
        self.api_url = f"{host}/api/generate"
        
        # Kiểm tra kết nối
        self._check_connection()
    
    def _check_connection(self):
        """
        Kiểm tra xem Ollama có đang chạy không
        """
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info(f"✓ Kết nối Ollama thành công tại {self.host}")
                
                # Kiểm tra model có sẵn không
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                
                if any(self.model in name for name in model_names):
                    logger.info(f"✓ Model {self.model} đã sẵn sàng")
                else:
                    logger.warning(f"⚠ Model {self.model} chưa được tải. Chạy: ollama pull {self.model}")
            else:
                logger.error("✗ Không thể kết nối Ollama")
        except requests.exceptions.ConnectionError:
            logger.error("✗ Ollama chưa được khởi động. Chạy: ollama serve")
        except Exception as e:
            logger.error(f"✗ Lỗi kết nối: {str(e)}")
    
    def generate(self, prompt, system_prompt=None, temperature=0.7, max_tokens=2000):
        """
        Gọi LLM để generate response
        
        Args:
            prompt: Câu hỏi/yêu cầu từ user
            system_prompt: System prompt để định hướng LLM
            temperature: Độ "sáng tạo" (0-1)
            max_tokens: Số token tối đa
        
        Returns:
            str: Response từ LLM
        """
        try:
            # Tạo full prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\nUser: {prompt}\nAssistant:"
            else:
                full_prompt = prompt
            
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            logger.info(f"Đang gọi LLM với prompt: {prompt[:100]}...")
            
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '').strip()
                logger.info(f"✓ LLM response: {generated_text[:100]}...")
                return generated_text
            else:
                logger.error(f"✗ Lỗi API: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("✗ Timeout khi gọi LLM")
            return None
        except Exception as e:
            logger.error(f"✗ Lỗi: {str(e)}")
            return None
    
    def chat(self, messages, temperature=0.7):
        """
        Chat với LLM (multi-turn conversation)
        
        Args:
            messages: List of {'role': 'user/assistant', 'content': '...'}
            temperature: Độ "sáng tạo"
        
        Returns:
            str: Response từ LLM
        """
        try:
            # Ollama generate API không hỗ trợ chat format trực tiếp
            # Chuyển đổi messages thành single prompt
            prompt_parts = []
            for msg in messages:
                role = msg['role']
                content = msg['content']
                if role == 'user':
                    prompt_parts.append(f"User: {content}")
                elif role == 'assistant':
                    prompt_parts.append(f"Assistant: {content}")
                elif role == 'system':
                    prompt_parts.append(f"System: {content}")
            
            prompt_parts.append("Assistant:")
            full_prompt = "\n\n".join(prompt_parts)
            
            return self.generate(full_prompt, temperature=temperature)
            
        except Exception as e:
            logger.error(f"✗ Lỗi chat: {str(e)}")
            return None
    
    def extract_json(self, text):
        """
        Trích xuất JSON từ response của LLM
        LLM thường wrap JSON trong ```json ... ```
        """
        try:
            # Tìm JSON trong markdown code block
            if "```json" in text:
                start = text.find("```json") + 7
                end = text.find("```", start)
                json_str = text[start:end].strip()
            elif "```" in text:
                start = text.find("```") + 3
                end = text.find("```", start)
                json_str = text[start:end].strip()
            else:
                json_str = text.strip()
            
            # Parse JSON
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"✗ Không thể parse JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"✗ Lỗi extract JSON: {e}")
            return None


# Test function
if __name__ == "__main__":
    print("Testing Ollama Client...")
    
    client = OllamaClient()
    
    # Test basic generation
    print("\n--- Test 1: Basic Generation ---")
    response = client.generate("Xin chào! Bạn là ai?")
    if response:
        print(f"Response: {response}")
    
    # Test chat
    print("\n--- Test 2: Chat ---")
    messages = [
        {"role": "system", "content": "Bạn là trợ lý SDN, chuyên về mạng máy tính."},
        {"role": "user", "content": "SDN là gì?"}
    ]
    response = client.chat(messages)
    if response:
        print(f"Response: {response}")
    
    # Test JSON extraction
    print("\n--- Test 3: JSON Extraction ---")
    json_response = """
    Đây là kết quả:
    ```json
    {
        "action": "add_flow",
        "switch_id": 1,
        "priority": 10
    }
    ```
    """
    json_data = client.extract_json(json_response)
    if json_data:
        print(f"Extracted JSON: {json_data}")
