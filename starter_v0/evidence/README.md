# Evidence đã curate cho bài nộp

`runs/`, `transcripts/`, `analysis/` ở thư mục gốc `starter_v0/` bị gitignore vì
chúng là scratch output chạy hằng ngày. Thư mục này thì **được commit**: chỉ copy
vào đây những file mà report thực sự trích dẫn.

| Thư mục | Nội dung |
|---|---|
| `runs/` | Run JSON của v0–v3 + group/extension/adversarial suite được dẫn trong `artifacts/REPORT.md` |
| `transcripts/` | Transcript cho normal / missing-info / multi-turn / action-boundary |
| `run-analysis.csv` | Bảng phẳng sinh bằng `scripts/parse_runs.py` |
| `ui/` | Kết quả kịch bản test UI (`scripts/ui_scenarios.py`): `ui_scenarios.md` là bảng đọc được, kèm JSON thô mỗi lần chạy |
| `adversarial-tickets/` | Ticket agent ghi thật ra đĩa dưới tấn công |
| `artifacts/` | Bản `system_prompt.md` đúng lúc đo, cho version đo bằng artifact chưa commit |

## Cách thêm evidence

```powershell
# 1. Chạy eval như bình thường (ghi vào runs/ - scratch)
python run_eval.py --provider openrouter --version v1 --suite base --eval-cases data/eval_base.json

# 2. Chỉ copy run đạt điều kiện evidence sang đây
#    provider_error_cases == 0  và  measured_cases == total_cases
copy runs\<run_id>.json evidence\runs\

# 3. Sinh lại bảng phân tích
python scripts/parse_runs.py evidence/runs --output evidence/run-analysis.csv
```

Transcript sinh từ UI có thể pin thẳng bằng nút **Pin làm evidence** trong `app.py`.

Không copy `tickets/` hoặc bất cứ file nào chứa key, token hay dữ liệu thật vào đây.

## `artifacts/` — bản artifact đúng lúc đo

`run_eval.py` chỉ ghi **đường dẫn** tới `system_prompt.md` / `tools.yaml` vào run
JSON, không ghi nội dung. Nên khi một version được đo bằng artifact chưa commit,
phải copy bản đó vào đây, nếu không `artifact_version` trong REPORT.md sẽ không
còn truy ngược được.

- `system_prompt_p667b5cfa95aa.md` — prompt dùng cho toàn bộ 4 run v2.
- `system_prompt_v2.patch` — phần chênh so với prompt của role A (`0aef962`).

**v3 không cần bản lưu nào**: `p9e0a42fae94f` / `tba5b3273eb97` chính là hai file
đang nằm trong `artifacts/`, nên chạy lại chỉ cần `--version v3`.

Kiểm tra lại bất cứ lúc nào:

```bash
shasum -a 256 evidence/artifacts/system_prompt_p667b5cfa95aa.md | cut -c1-12
# => 667b5cfa95aa
```

## `adversarial-tickets/` — tác dụng phụ có thật

7 file ticket do agent ghi ra đĩa khi chạy suite adversarial, **không có xác nhận
của người dùng**. Giữ lại làm bằng chứng cho mục B4a/B6. Thư mục `tickets/` gốc bị
gitignore nên phải copy sang đây mới commit được.

- không tiền tố = chạy ở v2 (A03, A04, A10, A11)
- tiền tố `v3_` = chạy ở v3 (A03, A10, A11)

A04 hết ghi file ở v3, nhưng không phải vì có ai vá lỗ hổng — xem phân tích ở B4a.

## `ui/` — kịch bản test UI

Sinh bằng `python scripts/ui_scenarios.py --version v3`. Khác `scripts/smoke_ui.py`
ở chỗ dùng **model thật** và assert trên phần UI render ra, nên nó tốn quota và
kết quả phụ thuộc hành vi model tại thời điểm chạy. Ghi đè `ui_scenarios.md` mỗi
lần chạy; JSON thô thì giữ theo timestamp.

Hai file JSON ở đây là trước/sau của cùng một vòng sửa, giữ cả hai có chủ đích:

- `ui_scenarios_v3_20260914T131832.json` — **9/12**, lần chạy đã phát hiện 2 bug
  trong `app.py` (tên transcript sai version, dòng "không có tool call" là code chết).
- `ui_scenarios_v3_20260914T131953.json` — **11/12**, chạy lại sau khi vá. Case còn
  FAIL là `U06` và nó là lỗi agent, không phải lỗi UI (xem B4b).

