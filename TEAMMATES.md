# TEAMMATES

> Điền đầy đủ trước khi nộp. `SUBMISSION-GUIDE.md` yêu cầu mỗi thành viên có ít
> nhất một commit dưới Git identity của chính mình trên branch nộp bài.

- **Nhóm:** K4-DAY04
- **Repository nộp bài:** https://github.com/hungdinh82/K4A-Day04-E2NEW
- **Branch nộp bài:** `feat/PromptArchitect`
- **Nhóm trưởng:** _Cần nhóm xác nhận để đổi tên repository theo MSSV nhóm trưởng._

| Role | Họ tên | MSSV | GitHub username | Phần việc chính |
|---|---|---|---|---|
| A | Đinh Văn Hùng | 2A202602443 | `hungdinh82` | `artifacts/system_prompt.md`, vòng lặp v1–v3, runtime security boundary |
| B | Nguyễn Ngọc Vĩnh | 2A202602833 | `VinhNN747` | `artifacts/tools.yaml`, tool declaration/schema |
| C | Vũ Đức Minh | 2A202602895 | `MinMinhMin` | Team eval (`data/eval_group.json`), adversarial review |
| D | Nguyễn Thanh Phong | 2A202602843 | `kaisye` | UI (`starter_v0/app.py`), `artifacts/REPORT.md`, version log, evidence |
| E | Nguyễn Trọng Huy | 2A202602379 | `Mrbeohuy` | Security hardening, local smoke test và bonus ticket-status utility |

## Quy ước làm việc

- Mỗi người làm trên branch riêng: `feat/A-prompt`, `feat/B-tools`, `feat/C-eval`, `feat/D-ui-report`.
- Commit message theo dạng `feat(A): ...`, `feat(B): ...`, `feat(C): ...`, `feat(D): ...`.
- **Không squash merge** — squash sẽ xoá mất commit riêng dùng làm bằng chứng đóng góp.
- File dễ xung đột (`artifacts/REPORT.md`, `artifacts/version_log.csv`) do role D chốt;
  các thành viên khác gửi số liệu/nội dung cho role D thay vì sửa trực tiếp.
- Evidence được commit phải nằm trong `starter_v0/evidence/`; `runs/`, `transcripts/`,
  `analysis/`, `tickets/` ở ngoài thư mục đó đều bị gitignore.

Kiểm tra trước khi nộp:

```powershell
git log --format="%h | %an <%ae> | %s"
```
