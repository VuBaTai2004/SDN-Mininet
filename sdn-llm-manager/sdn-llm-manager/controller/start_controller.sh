#!/bin/bash

# Script khởi động Ryu Controller

echo "╔═══════════════════════════════════════╗"
echo "║    Starting Ryu SDN Controller       ║"
echo "╚═══════════════════════════════════════╝"
echo ""

# Kiểm tra Ryu đã cài đặt chưa
if ! command -v ryu-manager &> /dev/null; then
    echo "❌ Ryu chưa được cài đặt!"
    echo "Cài đặt bằng: pip3 install ryu"
    exit 1
fi

echo "✓ Ryu đã sẵn sàng"
echo ""

# Tìm đường dẫn file controller
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONTROLLER_FILE="$SCRIPT_DIR/ryu_controller.py"

if [ ! -f "$CONTROLLER_FILE" ]; then
    echo "❌ Không tìm thấy file: $CONTROLLER_FILE"
    exit 1
fi

echo "📂 Controller file: $CONTROLLER_FILE"
echo ""
echo "🚀 Khởi động controller..."
echo "   - OpenFlow port: 6653"
echo "   - REST API: http://localhost:8080"
echo ""
echo "Nhấn Ctrl+C để dừng controller"
echo "----------------------------------------"
echo ""

# Chạy Ryu controller với REST API và OpenFlow 1.3
ryu-manager \
    --ofp-tcp-listen-port 6653 \
    --wsapi-port 8080 \
    --verbose \
    "$CONTROLLER_FILE"
