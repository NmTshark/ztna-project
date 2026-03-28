#!/bin/bash

# ==========================================
# ZTNA Lab - Global Variables
# ==========================================

# 1. Core Addresses
export VM2_IP="192.168.116.135"  # <-- THAY ĐỊA CHỈ IP CỦA VM2 VÀO ĐÂY
export LAB_DOMAIN="lab.local"

# 2. OpenZiti DNS (Sẽ được trỏ về VM2_IP ở bước cấu hình host)
export ZITI_CTRL_DNS="ziti-edge-controller.${LAB_DOMAIN}"
export ZITI_ROUTER_DNS="ziti-edge-router.${LAB_DOMAIN}"

# 3. Platform Services URLs
export KEYCLOAK_URL="http://192.168.116.135:8081"
export FLEET_URL="https://192.168.116.135:8443"
export OPA_URL="http://192.168.116.135:8181"
export ORCH_URL="http://192.168.116.135:8090"

# 4. Credentials (Mật khẩu dùng cho Lab)
export ZITI_ADMIN_USER="admin"
export ZITI_ADMIN_PASS="passwordziti"
export KC_ADMIN_USER="admin"
export KC_ADMIN_PASS="passwordkeycloack"
export FLEET_ADMIN_EMAIL="admin@${LAB_DOMAIN}"
export FLEET_ADMIN_PASS="passwordfleet"

echo "Done"
