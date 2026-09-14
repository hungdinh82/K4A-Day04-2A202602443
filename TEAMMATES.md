# TEAMMATES

> Điền đầy đủ trước khi nộp. `SUBMISSION-GUIDE.md` yêu cầu mỗi thành viên có ít
> nhất một commit dưới Git identity của chính mình trên branch nộp bài.

- **Nhóm:** _(tên nhóm)_
- **Repository nộp bài:** https://github.com/hungdinh82/K4A-Day04-E2NEW
- **Branch nộp bài:** _(ví dụ `main`)_

| Role | Họ tên | MSSV | GitHub username | Phần việc chính |
|---|---|---|---|---|
| A | | | | `artifacts/system_prompt.md`, vòng lặp v1–v3 |
| B | | | | `artifacts/tools.yaml`, tool declaration/schema |
| C | | | | Team eval (`data/eval_group.json`), adversarial review |
| D | | | | UI (`starter_v0/app.py`), `artifacts/REPORT.md`, version log, evidence |

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
