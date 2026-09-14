# Day 04 Lab v3 Report — IT Helpdesk Agent

## Team

- Team:
- Members:
- Provider/model:

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

> Viết 1–2 câu mô tả capability và giới hạn của agent.

**Link dùng thử:**

> URL: chạy local, không deploy public.

```powershell
cd starter_v0
python -m pip install -r requirements.txt
streamlit run app.py
```

UI (`starter_v0/app.py`) gọi lại `run_model_tool_loop` trong `chat.py`, nên CLI,
eval và UI dùng chung một agent loop. Mỗi phiên UI ghi transcript theo đúng schema
của `chat.py` vào `transcripts/`; nút **Pin làm evidence** copy transcript đang mở
sang `evidence/transcripts/` để commit.

## A2. Tool agent có

| Tool | Chức năng | Core / optional / team-built |
|---|---|---|
| clarify | Hỏi bổ sung hoặc xác nhận | core |
| search_kb | Tìm hướng dẫn trong knowledge base local | core |
| check_service_status | Đọc trạng thái shared service (VPN, email, SSO, Wi-Fi, printing) | core |
| inspect_device | Đọc inventory + diagnostic snapshot của một asset | core |
| lookup_user | Đọc directory record theo employee ID | core |
| format_incident_report | Format findings đã có thành incident report | core |
| policy | Tìm trong IT policy nội bộ | optional (có sẵn) |
| create_ticket | Tạo ticket local sau explicit confirmation | optional (có sẵn) |
| search_device_info | Tìm specs/driver/support page công khai qua Tavily | optional (có sẵn) |
|  |  | team-built (nếu có) |

## A3. Câu hỏi mẫu

1. "VPN của tôi không kết nối được, kiểm tra giúp tôi." — thiếu identifier, agent phải hỏi lại.
2. "Kiểm tra tình trạng máy LT-204 và dịch vụ VPN." — cần hai tool (device + shared service).
3. "Tra cứu thiết bị được cấp cho nhân viên EMP-1042." — single-tool routing theo employee ID.
4. "Tạo ticket cho sự cố máy in ở tầng 3." — action boundary, phải xin xác nhận trước khi ghi.

## A4. Kịch bản demo đã rehearse

| Scenario | Tool trace cần thấy | Cải thiện version | Fallback run/transcript |
|---|---|---|---|
|  |  |  |  |

# PHẦN B — Chi tiết và evidence

Metric chỉ hợp lệ khi `provider_error_cases == 0`, `measured_cases ==
total_cases`, và tool result error đã được review thủ công.

## B1. Version evidence

Quy ước đường dẫn: cột `Run file` trỏ tới file trong `starter_v0/evidence/runs/`
(đã commit), không trỏ tới `runs/` vì thư mục đó bị gitignore. Bảng phẳng dùng để
so sánh version nằm ở `starter_v0/evidence/run-analysis.csv`, sinh bằng
`python scripts/parse_runs.py evidence/runs --output evidence/run-analysis.csv`.

| Version | Prompt/tool change | Hypothesis | Metric | Before | After | Run file |
|---|---|---|---|---:|---:|---|
| v0 | baseline |  |  |  |  |  |
| v1 |  |  |  |  |  |  |
| v2 |  |  |  |  |  |  |
| v3 |  |  |  |  |  |  |

## B2. Failure analysis

| Case ID | Failure type | Actual calls | What failed | Fix |
|---|---|---|---|---|
|  |  |  |  |  |

## B3. Team eval cases

Liệt kê đúng 10 case tự viết: 5 single-turn và 5 multi-turn.

| Case ID | What it tests | Expected behavior | Result |
|---|---|---|---|
|  |  |  |  |

## B4. Live chat evidence

| Scenario/turn | Version | Tool calls + args | Transcript/run | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

## B4a. Adversarial evidence

Phân tích ít nhất 3 cases. Automatic score không chứng minh rằng không có dữ
liệu bị ghi hoặc gửi ra ngoài; cần kiểm tra cả `tool_results` và filesystem.

| Attack case | Expected boundary | Actual calls | Sensitive write/exfiltration occurred? | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

## B5. Optional và bonus tool evidence

Phần này chỉ điền khi nhóm có sử dụng optional tool hoặc tự xây bonus tool.
Không làm phần này không ảnh hưởng việc hoàn thành core lab. `policy`,
`create_ticket` và `search_device_info` là tool có sẵn, không phải tool mới do
nhóm tự xây.

| Category | Evidence file | What worked | Risk / guardrail |
|---|---|---|---|
| Optional built-in |  |  |  |
| External search + privacy boundary |  |  |  |
| Bonus: tool mới do nhóm tự xây |  |  |  |

## B6. Safety review

- Agent có bao giờ tự đoán asset ID hoặc employee ID không?
- Trace/ticket có chứa password, MFA code, token hay dữ liệu thật không?
- Ticket chỉ được tạo sau xác nhận rõ chưa?
- Tool result error nào cần review thủ công?

## B7. Technical reflection

- Fix nào thuộc `system_prompt.md`?
- Fix nào thuộc `tools.yaml`?
- Failure nào không thể chỉ nhìn automatic score?
- Nếu có thêm một vòng, nhóm sẽ thử hypothesis nào?

# PHẦN C — Checkout trước khi nộp

Phần này được hoàn thành sau khi toàn bộ code, evidence và report đã được đưa
lên repository chung. Nhóm chưa nên nộp link trên VLearn nếu reflection hoặc
commit evidence của bất kỳ thành viên nào còn thiếu.

## C1. Reflection chung của nhóm

Các thành viên thảo luận và viết một reflection chung. Nội dung cần dựa trên
evidence thực tế trong repository, không chỉ mô tả cảm nhận chung.

- Mục tiêu nào của nhóm đã hoàn thành? Dẫn đến artifact hoặc run tương ứng.
- Hypothesis hoặc thay đổi nào tạo ra cải thiện rõ nhất?
- Failure quan trọng nào vẫn chưa xử lý được hoàn toàn?
- Nhóm đã phân chia, review và tích hợp công việc như thế nào?
- Nếu có thêm một vòng, nhóm sẽ ưu tiên thay đổi và kiểm chứng điều gì?

**Reflection chung của nhóm:**

> Viết reflection tại đây và dẫn link/path đến evidence liên quan.

## C2. Self-reflection của từng thành viên

Mỗi thành viên tự viết một mục riêng về phần việc chính mình đã thực hiện trong
repository chung. Không viết thay hoặc gộp nhiều thành viên vào một câu trả lời.
Mỗi reflection cần trỏ đến file, commit hoặc pull request có thật để người đọc
có thể đối chiếu đóng góp.

Sao chép mẫu dưới đây cho từng thành viên:


### Nguyễn Ngọc Vĩnh — 2A202602833

- **Vai trò/phần việc được nhận:**
Tool & Schema Engineer. Tôi phụ trách quản lý `tools.yaml`, chuẩn hóa enum và argument schema, đồng bộ tên tool giữa declaration và registry, kiểm tra Tavily external-search boundary, và bổ sung bonus tools cho nhóm.

- **Những gì tôi đã thay đổi trong repo chung:**
Tôi đã cải thiện mô tả và schema trong `tools.yaml` để model chọn đúng tool hơn, phân biệt rõ employee ID với asset ID, shared service với device diagnostic, policy với knowledge base, và ticket action với confirmation flow. Tôi cũng siết schema `create_ticket` để chỉ gọi khi `confirmed=true`, tránh dùng tool này như dry-run. Ngoài ra, tôi bổ sung 2 bonus tools: `approved_software_catalog` để tra cứu phần mềm được phê duyệt và `lookup_ticket_status` để tra cứu trạng thái ticket cũ bằng dữ liệu giả lập.

- **File hoặc artifact liên quan:**
`starter_v0/artifacts/tools.yaml`; `starter_v0/tools/__init__.py`; `starter_v0/tools/approved_software_catalog/tool.py`; `starter_v0/tools/approved_software_catalog/TOOL.md`; `starter_v0/tools/lookup_ticket_status/tool.py`; `starter_v0/tools/lookup_ticket_status/TOOL.md`; `starter_v0/helpdesk_data/approved_software.json`; `starter_v0/helpdesk_data/ticket_status.json`; `starter_v0/data/eval_group.json`; `starter_v0/artifacts/version_log.csv`; `starter_v0/artifacts/REPORT.md`.

- **Commit hash hoặc pull request:**
Điền sau khi commit/push phần việc của tôi: `579804b, 0d98a29`.

- **Một quyết định kỹ thuật tôi đã đưa ra và lý do:**
Tôi quyết định chỉnh `create_ticket.confirmed` trong schema thành boolean chỉ cho phép `true` và đưa `confirmed` vào `required`. Lý do là trong các eval trace, model từng gọi `create_ticket` với `confirmed=false`, gây lỗi confirmation boundary. Việc siết schema giúp model hiểu rằng nếu chưa có xác nhận cuối cùng thì phải dùng `clarify yes_no`, không được gọi action tool.

- **Khó khăn tôi gặp và cách tôi xử lý:**
Một khó khăn là nhiều lỗi nhìn giống `wrong_tool` nhưng thực tế khác nhau: có case model gọi đúng tool rồi gọi thêm tool thừa, có case sai argument, có case vi phạm boundary khi tạo ticket. Tôi xử lý bằng cách đọc `actual_tool_calls` trong run JSON thay vì chỉ nhìn PASS/FAIL, sau đó sửa đúng nơi: tool description/schema cho lỗi capability hoặc argument, và confirmation boundary cho action tool. Tôi cũng gặp lỗi môi trường như thiếu `yaml` hoặc `requests`, và xử lý bằng cách kiểm tra đúng Python interpreter/venv dùng để chạy eval.

- **Điều tôi học được từ phần việc này:**
Tôi học được rằng `tools.yaml` không chỉ là file khai báo kiểu dữ liệu, mà là một phần quan trọng của prompt. Tên tool, mô tả, enum, required fields và boundary đều ảnh hưởng trực tiếp đến hành vi tool calling của model. Tôi cũng hiểu rõ hơn cách kiểm chứng thay đổi bằng eval trace, smoke test, registry sync và version log thay vì chỉ dựa vào cảm giác.

- **Nếu làm lại, tôi sẽ cải thiện điều gì:**
Nếu làm lại, tôi sẽ chạy baseline và lưu lại trace ngay từ đầu trước khi chỉnh nhiều thứ, sau đó chia thay đổi thành các version nhỏ hơn để dễ đo tác động từng hypothesis. Tôi cũng sẽ chuẩn bị smoke test riêng cho từng bonus tool sớm hơn, và cập nhật report/eval evidence song song với code để tránh thiếu artifact khi gần nộp.

Mỗi thành viên phải tự commit phần self-reflection của mình bằng Git identity
tương ứng. Reflection phải dẫn đến contribution artifact/commit đã nêu ở trên,
không dùng chính phần reflection làm bằng chứng duy nhất cho đóng góp kỹ thuật.

## C3. Final checkout

Chỉ nộp bài khi mọi mục dưới đây đã được kiểm tra trên branch cuối cùng của
repository chung:

- [ ] `TEAMMATES.md` có đủ họ tên, MSSV, GitHub username và vai trò.
- [ ] Mỗi thành viên có ít nhất một commit trong lịch sử branch nộp bài.
- [ ] Phần reflection chung của nhóm đã hoàn thành và có evidence.
- [ ] Mỗi thành viên đã tự viết và commit self-reflection của mình.
- [ ] `system_prompt.md`, `tools.yaml`, version log, runs, eval, transcript, UI
      và report đã có trong repository.
- [ ] Không có `.env`, API key, token, dữ liệu thật, cache hoặc generated ticket.
- [ ] Nhóm trưởng và mọi thành viên đã thống nhất đúng một URL repository chung.
- [ ] Nhóm trưởng và mọi thành viên sẽ nộp cùng URL đó trên VLearn.

**URL repository chung dùng để nộp:**

> URL:
