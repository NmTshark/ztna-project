# Research and Develop of a Zero Trust Network Access System Based on Endpoint Posture Assessment for Small and Medium-sized Enterprises.

![Architecture](https://img.shields.io/badge/Architecture-Zero_Trust-blue) ![Network](https://img.shields.io/badge/Network-OpenZiti-red) ![Identity](https://img.shields.io/badge/Identity-Keycloak-orange) ![Posture](https://img.shields.io/badge/Posture-FleetDM-purple) ![Policy](https://img.shields.io/badge/Policy-OPA-green)

## 1. Triết lý Zero Trust
Zero Trust không phải là một công nghệ đơn lẻ, mà là một chiến lược và mô hình bảo mật mạng dựa trên nguyên tắc cốt lõi: **"Không bao giờ tin tưởng, luôn luôn xác minh"** (Never Trust, Always Verify). 

Khác với mô hình bảo mật vành đai truyền thống (như VPN) - nơi người dùng được cấp sự "tin tưởng ngầm định" (implicit trust) khi đã vượt qua tường lửa để vào mạng nội bộ, Zero Trust giả định rằng các mối đe dọa luôn tồn tại ở cả bên ngoài lẫn bên trong mạng. Mọi yêu cầu truy cập đều phải được xác thực và ủy quyền liên tục dựa trên nhiều điểm dữ liệu động (ngữ cảnh) như: danh tính người dùng, tình trạng bảo mật của thiết bị, và chính sách quản trị, trước khi được cấp quyền truy cập vào một tài nguyên cụ thể (Micro-segmentation).

## 2. Tổng quan Dự án
Đây là dự án mini-capstone thuộc học phần **OSP201 - Open Source Platform and Network Administration**. 

Dự án tập trung triển khai một hệ thống Zero Trust cơ bản, tuân thủ các nguyên tắc của kiến trúc Zero Trust theo tiêu chuẩn **NIST SP 800-207**. Bằng cách tích hợp các công cụ mã nguồn mở, hệ thống tạo ra một vòng lặp bảo mật khép kín. 

Hệ thống khắc phục lỗ hổng của mạng VPN truyền thống bằng cách tách biệt hoàn toàn mặt phẳng điều khiển (Control Plane) và mặt phẳng dữ liệu (Data Plane). Các ứng dụng nghiệp vụ được cấu hình ẩn danh (Dark Services) khỏi Internet. Quyền truy cập được cấp phát linh hoạt và thu hồi tự động dựa trên sự kết hợp giữa **Danh tính người dùng (Identity)** và **Tình trạng sức khỏe thiết bị (Device Posture)** theo thời gian thực.

## 3. Kiến trúc & Công nghệ
Hệ thống được xây dựng từ các nền tảng mã nguồn mở, tối ưu chi phí nhưng vẫn đảm bảo tính toàn vẹn của mô hình Zero Trust:

- **Identity Provider (IdP):** `Keycloak` - Chịu trách nhiệm quản lý định danh, xác thực người dùng (SSO, MFA).
- **Device Posture Agent:** `FleetDM` & `Osquery` - Tác nhân giám sát thiết bị điểm cuối, thu thập dữ liệu về các tiến trình và tình trạng tuân thủ bảo mật.
- **Policy Decision Point (PDP):** `Open Policy Agent (OPA)` - Động cơ trung tâm phân tích dữ liệu và ra quyết định cấp quyền dựa trên ngôn ngữ Rego.
- **Policy Enforcement Point (PEP):** `OpenZiti` - Nền tảng mạng Overlay chịu trách nhiệm thiết lập các đường hầm vi phân đoạn (mTLS) và thực thi lệnh đóng/mở mạng.
- **Posture Orchestrator:** `Python3` - Middleware đóng vai trò cầu nối, đồng bộ hóa luồng sự kiện từ FleetDM sang OPA và gọi API để kích hoạt OpenZiti.

## 4. Luồng hoạt động cốt lõi
1. **Xác thực (Authenticate):** Người dùng đăng nhập thông qua Ziti Desktop Edge và được xác thực danh tính bởi Keycloak để nhận mã thông báo (JWT).
2. **Giám sát (Monitor):** Tác nhân Osquery trên thiết bị định kỳ quét và gửi bản tóm tắt tình trạng thiết bị (Posture) về FleetDM Server.
3. **Đánh giá (Evaluate):** Khi FleetDM phát hiện vi phạm (tuỳ vào chính sách được cấu hình), Orchestrator sẽ thu thập báo cáo và gửi cho OPA để đánh giá dựa trên bộ quy tắc hiện hành.
4. **Thực thi (Enforce):** OPA trả về phán quyết (`quarantine` hoặc `compliant`). Orchestrator gọi API của OpenZiti để cập nhật nhãn (tag) cho thiết bị.
5. **Cách ly (Isolate):** Nếu trạng thái là `quarantine`, OpenZiti lập tức đóng đường hầm vật lý đến dịch vụ nghiệp vụ, cách ly hoàn toàn thiết bị khỏi mạng lõi nhằm ngăn chặn lây lan (Lateral Movement).

## 5. Đánh giá Hiệu năng thực nghiệm
Hệ thống đã được cấu hình và kiểm thử thành công quá trình phản ứng tự động (SOAR) với các chỉ số đo lường như sau:


| Hạng mục đo lường | Thành phần phụ trách | Kết quả trung bình |
| :--- | :--- | :--- |
| **Thời gian phát hiện (TTD)** | FleetDM / Osquery | `≤ 10s` (~5s) |
| **Độ trễ ra quyết định** | Open Policy Agent (OPA) | `~ 85 ms` |
| **Thời gian thực thi cắt mạng (TTE)** | OpenZiti Controller | `~ 35 ms` |
| **Thời gian người dùng tự phục hồi**| Thao tác trên thiết bị | `~ 1 phút 30 giây` |

(Các chỉ số đo lường này được thu thập từ log của Middleware và đã được kiểm tra lại rõ ràng)
## 6. Giới hạn của dự án
Với khuôn khổ của một dự án mini-capstone môn học, hệ thống hiện tại vẫn tồn tại một số giới hạn:
- **Mức độ triển khai:** Chỉ mới dừng lại ở việc chứng minh tính khả thi (Proof of Concept) của việc kết nối các luồng công cụ với nhau thành một vòng lặp khép kín.
- **Chính sách bảo mật (Policy):** Các luật đánh giá trên OPA và FleetDM hiện được viết ở mức độ cơ bản (phát hiện một số tiến trình cụ thể), chưa bao quát được các ngữ cảnh phức tạp và đa dạng theo nhu cầu thực tế của từng phòng ban của từng doanh nghiệp.
- **Phân quyền:** Cơ chế ủy quyền hiện tại đang thiên về quản lý danh tính thiết bị (Device-centric) nhiều hơn là ánh xạ chặt chẽ 1-1 với thuộc tính của người dùng (User-centric).

## 7. Hướng phát triển trong tương lai
Trong bối cảnh hành lang pháp lý về bảo vệ dữ liệu mạng tại Việt Nam ngày càng hoàn thiện, kiến trúc ZTNA dành cho SME cần được mở rộng và phát triển chuyên sâu hơn:
- **Tối ưu hóa Chính sách:** Nghiên cứu và triển khai các bộ luật Rego phức tạp hơn trên OPA, kết hợp đánh giá đa yếu tố (vị trí địa lý, thời gian truy cập, tích hợp AI để giám sát và phát hiện hành vi bất thường).
- **Tích hợp Claims Mapping:** Tích hợp sâu hơn giữa Keycloak và OpenZiti (ExtJWT Claims Mapping) để đảm bảo quyền truy cập được gắn liền với đúng người dùng thật sự trên đúng thiết bị được cấp phép.
- **Đóng gói giải pháp:** Tự động hóa quá trình triển khai hệ thống (Infrastructure as Code) để các doanh nghiệp SME có thể dễ dàng áp dụng mà không cần quá nhiều chuyên môn về quản trị hạ tầng.
## 8. Lưu ý
Các thông tin tài khoản như email, password, tài khoản admin đều là các tài khoản giả lập được tạo để kiểm tra và đánh giá hệ thống.
Nếu như các bạn triển khai thì có thể tự tìm hiểu và tạo cách dịch vụ mà các bạn muốn để có thể tự kiểm tra và setup các chính sách theo ý mình muốn.
