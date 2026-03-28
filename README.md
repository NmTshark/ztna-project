# 🛡️ ZTNA: Context-Aware Zero Trust Network Access for SMEs

![Zero Trust](https://img.shields.io/badge/Architecture-Zero_Trust-blue)
![OpenZiti](https://img.shields.io/badge/Network-OpenZiti-red)
![Keycloak](https://img.shields.io/badge/Identity-Keycloak-orange)
![FleetDM](https://img.shields.io/badge/Posture-FleetDM-purple)
![OPA](https://img.shields.io/badge/Policy-OPA-green)

## 📖 Giới thiệu (Overview)
**Zero Trust Network Access** là hệ thống Mạng lưới Truy cập Không tin cậy (Zero Trust Network Access) dựa trên đánh giá ngữ cảnh và sức khỏe thiết bị điểm cuối, được thiết kế tối ưu dành riêng cho các Doanh nghiệp Vừa và Nhỏ (SMEs).

Hệ thống khắc phục triệt để lỗ hổng "niềm tin ngầm định" (Implicit Trust) của mạng VPN truyền thống bằng cách tách biệt hoàn toàn mặt phẳng điều khiển (Control Plane) và mặt phẳng dữ liệu (Data Plane). Ứng dụng nghiệp vụ được giấu kín (Dark Services) và quyền truy cập chỉ được cấp phát linh hoạt dựa trên sự kết hợp giữa **Danh tính người dùng (Identity)** và **Tình trạng bảo mật của thiết bị (Device Posture)** theo thời gian thực.

## ✨ Tính năng nổi bật (Key Features)
* **Xác minh liên tục (Continuous Verification):** Không chỉ xác thực lúc đăng nhập, hệ thống liên tục rà quét các tiến trình vi phạm, trạng thái firewall, và cấu hình thiết bị (chu kỳ ~10s).
* **Vành đai tàng hình (Dark Network & Micro-segmentation):** Các dịch vụ lõi (HR, Sales) không mở bất kỳ port nào ra Internet. Người dùng chỉ được cấp một đường hầm mã hóa (mTLS) đến đúng ứng dụng được phép.
* **Tự động hóa phản ứng (Automated SOAR):** Thời gian từ lúc phát hiện thiết bị nhiễm mã độc đến khi ngắt mạng vật lý chỉ diễn ra trong **~0.12 giây**, giảm bán kính sát thương (Blast Radius) về 0.
* **Cách ly và Tự phục hồi (Self-Service Remediation):** Thiết bị vi phạm không bị ngắt Internet hoàn toàn mà được chuyển hướng an toàn vào mạng DMZ (Helpdesk Portal), cho phép người dùng tự khắc phục sự cố chỉ trong ~1.5 phút mà không cần IT can thiệp.

## ⚙️ Kiến trúc & Công nghệ (Tech Stack)
Hệ thống được xây dựng hoàn toàn từ các công nghệ Mã nguồn mở (Open-source) hàng đầu, tối ưu hóa chi phí cho SME:

1. **Identity Provider (IdP):** `Keycloak` - Quản lý định danh, SSO và MFA.
2. **Device Posture Agent:** `FleetDM` & `Osquery` - Tác nhân siêu nhẹ (<1% CPU) thu thập tình trạng thiết bị.
3. **Policy Decision Point (PDP):** `Open Policy Agent (OPA)` - Bộ não ra quyết định truy cập dựa trên luật linh hoạt (Rego).
4. **Policy Enforcement Point (PEP):** `OpenZiti` - Nền tảng mạng Overlay tạo kết nối vi phân đoạn.
5. **Posture Orchestrator:** `Python3` - Middleware đóng vai trò kết nối và đồng bộ hóa luồng dữ liệu từ FleetDM sang OPA và kích hoạt Ziti API.

## 🔄 Luồng hoạt động (Activity Flow)
1. **Login:** Người dùng đăng nhập qua Ziti Desktop Edge, xác thực bằng Keycloak để nhận JWT.
2. **Collect:** Osquery trên thiết bị cuối sẽ định kỳ gửi một bản trạng thái thiết bị (Posture) về FleetDM Server.
3. **Evaluate:** FleetDM gửi các báo cáo vi phạm. Orchestrator chuyển dữ liệu cho OPA để đánh giá dựa trên Policy.
4. **Enforce:** OPA trả về phán quyết (`quarantine` hoặc `compliant`). Orchestrator gọi API của OpenZiti để gán nhãn thiết bị.
5. **Remediate:** Nếu bị `quarantine`, OpenZiti cắt đường hầm đến dịch vụ và chặn hoàn toàn người dùng, cách lý người dùng ra khỏi dịch vụ.

## 📊 Đánh giá Hiệu năng (Performance Evaluation)
Hệ thống đã được kiểm thử thực nghiệm với các chỉ số phản hồi (Incident Response) vượt trội:

| Hạng mục | Thành phần | Kết quả |
| :--- | :--- | :--- |
| **TTD (Thời gian phát hiện)** | FleetDM / Osquery | `≤ 10s` (Trung bình ~5s) |
| **Decision Latency (Ra quyết định)** | OPA | `~ 85 ms` |
| **TTE (Thời gian thực thi cắt mạng)**| OpenZiti Controller | `~ 35 ms` |
| **Thời gian tự phục hồi (Remediation)**|  | `~ 1 phút 30 giây` |

Hiện tại dữ án này mới chỉ dừng lại ở mức độ cấu hình chính sách đơn giản ở mức một mini-capstone cho môn học OSP201. Trong tương lai, khi luật bảo vệ doanh nghiệp ở Việt Nam ngày càng được chú trọng thì tôi mong rằng những hệ thống bảo mật này có thể được triển khai phát triển và cải thiện hơn nữa.

---
*Dự án được phát triển nhằm mục đích nghiên cứu và cung cấp giải pháp an toàn thông tin toàn diện, tiết kiệm chi phí cho các doanh nghiệp SME.*
