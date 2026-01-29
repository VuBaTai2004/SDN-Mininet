#!/bin/bash

# SDN-LLM Manager - Installation Script
# Dành cho Ubuntu 20.04/22.04

set -e

echo "======================================"
echo "SDN-LLM Manager Installation"
echo "======================================"

# Màu sắc cho output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Kiểm tra Ubuntu version
if ! grep -q "Ubuntu" /etc/os-release; then
    echo "⚠️  Cảnh báo: Script này được thiết kế cho Ubuntu"
    read -p "Bạn có muốn tiếp tục? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${GREEN}[1/6] Cập nhật hệ thống...${NC}"
sudo apt update
sudo apt upgrade -y

echo -e "${GREEN}[2/6] Cài đặt Python và các công cụ cần thiết...${NC}"
sudo apt install -y python3 python3-pip python3-venv git curl wget

echo -e "${GREEN}[3/6] Cài đặt Mininet...${NC}"
sudo apt install -y mininet openvswitch-switch

echo -e "${GREEN}[4/6] Cài đặt Ryu Controller...${NC}"
pip3 install ryu eventlet==0.30.2

echo -e "${GREEN}[5/6] Cài đặt Ollama (Local LLM)...${NC}"
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh
    echo "✓ Ollama đã được cài đặt"
else
    echo "✓ Ollama đã có sẵn"
fi

# Tải Llama 3.2 model
echo -e "${YELLOW}Đang tải Llama 3.2 model (3GB)...${NC}"
echo "Quá trình này có thể mất 5-10 phút tùy vào tốc độ mạng"
ollama pull llama3.2

echo -e "${GREEN}[6/6] Cài đặt Python dependencies...${NC}"
pip3 install -r requirements.txt

echo ""
echo "======================================"
echo -e "${GREEN}✓ Cài đặt hoàn tất!${NC}"
echo "======================================"
echo ""
echo "Các bước tiếp theo:"
echo "1. Khởi động Ollama: ollama serve"
echo "2. Khởi động Ryu Controller: cd controller && ./start_controller.sh"
echo "3. Khởi động Mininet: sudo python3 mininet/topology.py"
echo "4. Khởi động Chatbot: python3 chatbot/app.py"
echo ""
echo "Xem README.md để biết thêm chi tiết"
