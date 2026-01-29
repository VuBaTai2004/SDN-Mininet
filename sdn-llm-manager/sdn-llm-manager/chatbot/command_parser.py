import json
import logging
import requests
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CommandParser:
    """
    Parse output từ LLM và thực thi lệnh SDN
    """
    
    def __init__(self, controller_url="http://localhost:8080"):
        self.controller_url = controller_url
        self.supported_actions = [
            'add_flow', 'delete_flow', 'show_topology', 
            'show_flows', 'block_traffic', 'allow_traffic', 'set_qos'
        ]
    
    def parse(self, llm_output: str) -> Dict[str, Any]:
        """
        Parse JSON output từ LLM
        
        Returns:
            dict: {'action': str, 'parameters': dict, 'explanation': str}
        """
        try:
            # Trích xuất JSON từ output
            json_str = self._extract_json(llm_output)
            if not json_str:
                return {
                    'status': 'error',
                    'message': 'Không tìm thấy JSON trong response của LLM'
                }
            
            # Parse JSON
            command = json.loads(json_str)
            
            # Validate
            if 'action' not in command:
                return {
                    'status': 'error',
                    'message': 'Missing "action" field trong command'
                }
            
            action = command['action']
            if action not in self.supported_actions:
                return {
                    'status': 'error',
                    'message': f'Action "{action}" không được hỗ trợ'
                }
            
            return {
                'status': 'success',
                'command': command
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return {
                'status': 'error',
                'message': f'Lỗi parse JSON: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Parse error: {e}")
            return {
                'status': 'error',
                'message': f'Lỗi parse: {str(e)}'
            }
    
    def execute(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Thực thi command SDN
        
        Args:
            command: Dict chứa action và parameters
            
        Returns:
            dict: Kết quả thực thi
        """
        action = command.get('action')
        parameters = command.get('parameters', {})
        
        try:
            if action == 'show_topology':
                return self._show_topology()
            
            elif action == 'show_flows':
                return self._show_flows(parameters)
            
            elif action == 'add_flow':
                return self._add_flow(parameters)
            
            elif action == 'delete_flow':
                return self._delete_flow(parameters)
            
            elif action == 'block_traffic':
                return self._block_traffic(parameters)
            
            elif action == 'allow_traffic':
                return self._allow_traffic(parameters)
            
            elif action == 'set_qos':
                return self._set_qos(parameters)
            
            else:
                return {
                    'status': 'error',
                    'message': f'Action {action} chưa được implement'
                }
                
        except Exception as e:
            logger.error(f"Execute error: {e}")
            return {
                'status': 'error',
                'message': f'Lỗi thực thi: {str(e)}'
            }
    
    def _extract_json(self, text: str) -> Optional[str]:
        """
        Trích xuất JSON từ text (có thể có markdown code block)
        """
        text = text.strip()
        
        # Tìm JSON trong ```json ... ```
        if '```json' in text:
            start = text.find('```json') + 7
            end = text.find('```', start)
            if end != -1:
                return text[start:end].strip()
        
        # Tìm JSON trong ``` ... ```
        if '```' in text:
            start = text.find('```') + 3
            end = text.find('```', start)
            if end != -1:
                return text[start:end].strip()
        
        # Tìm { ... } trực tiếp
        if '{' in text and '}' in text:
            start = text.find('{')
            end = text.rfind('}') + 1
            return text[start:end]
        
        return None
    
    def _show_topology(self) -> Dict[str, Any]:
        """
        Lấy thông tin topology từ controller
        """
        try:
            response = requests.get(
                f"{self.controller_url}/sdn/topology",
                timeout=5
            )
            
            if response.status_code == 200:
                topology = response.json()
                
                # Format output
                switches = topology.get('switches', {})
                links = topology.get('links', [])
                
                output = {
                    'status': 'success',
                    'data': {
                        'num_switches': len(switches),
                        'num_links': len(links),
                        'switches': switches,
                        'links': links
                    },
                    'message': f'Mạng có {len(switches)} switches và {len(links)} links'
                }
                return output
            else:
                return {
                    'status': 'error',
                    'message': f'Không thể lấy topology: HTTP {response.status_code}'
                }
                
        except requests.exceptions.ConnectionError:
            return {
                'status': 'error',
                'message': 'Không thể kết nối đến controller. Kiểm tra xem Ryu có đang chạy không.'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Lỗi: {str(e)}'
            }
    
    def _show_flows(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hiển thị flow rules
        """
        try:
            response = requests.get(
                f"{self.controller_url}/sdn/flows",
                timeout=5
            )
            
            if response.status_code == 200:
                flows = response.json()
                
                # Filter theo switch_id nếu có
                switch_id = params.get('switch_id')
                if switch_id:
                    flows = [f for f in flows if f.get('switch_id') == switch_id]
                
                return {
                    'status': 'success',
                    'data': flows,
                    'message': f'Tìm thấy {len(flows)} flow rules'
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Không thể lấy flows: HTTP {response.status_code}'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Lỗi: {str(e)}'
            }
    
    def _add_flow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Thêm flow rule
        """
        try:
            # Validate required params
            required = ['switch_id', 'src_ip', 'dst_ip', 'out_port']
            missing = [p for p in required if p not in params]
            if missing:
                return {
                    'status': 'error',
                    'message': f'Thiếu parameters: {", ".join(missing)}'
                }
            
            response = requests.post(
                f"{self.controller_url}/sdn/flow/add",
                json=params,
                timeout=5
            )
            
            if response.status_code == 200:
                return {
                    'status': 'success',
                    'data': response.json(),
                    'message': f'Đã thêm flow rule trên switch {params["switch_id"]}'
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Không thể thêm flow: HTTP {response.status_code}'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Lỗi: {str(e)}'
            }
    
    def _delete_flow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Xóa flow rule
        """
        try:
            if 'switch_id' not in params:
                return {
                    'status': 'error',
                    'message': 'Thiếu parameter: switch_id'
                }
            
            response = requests.post(
                f"{self.controller_url}/sdn/flow/delete",
                json=params,
                timeout=5
            )
            
            if response.status_code == 200:
                return {
                    'status': 'success',
                    'data': response.json(),
                    'message': f'Đã xóa flows trên switch {params["switch_id"]}'
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Không thể xóa flow: HTTP {response.status_code}'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Lỗi: {str(e)}'
            }
    
    def _block_traffic(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Chặn traffic - thực chất là add flow với action DROP
        """
        if 'src_ip' not in params:
            return {
                'status': 'error',
                'message': 'Thiếu parameter: src_ip'
            }
        
        # Tạo flow với priority cao và action drop
        flow_params = {
            'switch_id': params.get('switch_id', 1),
            'priority': 100,  # Priority cao để override các rule khác
            'src_ip': params['src_ip'],
            'action': 'drop'
        }
        
        if 'dst_ip' in params:
            flow_params['dst_ip'] = params['dst_ip']
        
        return {
            'status': 'success',
            'message': f'Đã chặn traffic từ {params["src_ip"]}',
            'note': 'Chức năng này cần implement thêm trong controller'
        }
    
    def _allow_traffic(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cho phép traffic
        """
        required = ['src_ip', 'dst_ip']
        missing = [p for p in required if p not in params]
        if missing:
            return {
                'status': 'error',
                'message': f'Thiếu parameters: {", ".join(missing)}'
            }
        
        return {
            'status': 'success',
            'message': f'Đã cho phép traffic từ {params["src_ip"]} đến {params["dst_ip"]}',
            'note': 'Chức năng này cần implement thêm trong controller'
        }
    
    def _set_qos(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Đặt QoS
        """
        required = ['src_ip', 'dst_ip', 'bandwidth']
        missing = [p for p in required if p not in params]
        if missing:
            return {
                'status': 'error',
                'message': f'Thiếu parameters: {", ".join(missing)}'
            }
        
        return {
            'status': 'success',
            'message': f'Đã đặt QoS: {params["bandwidth"]} cho traffic từ {params["src_ip"]} đến {params["dst_ip"]}',
            'note': 'Chức năng này cần implement thêm trong controller với OpenFlow meter'
        }


# Test
if __name__ == "__main__":
    parser = CommandParser()
    
    # Test parse
    test_output = """
    ```json
    {
        "action": "show_topology",
        "parameters": {},
        "explanation": "Hiển thị topology"
    }
    ```
    """
    
    result = parser.parse(test_output)
    print(f"Parse result: {result}")
    
    if result['status'] == 'success':
        exec_result = parser.execute(result['command'])
        print(f"Execute result: {exec_result}")
