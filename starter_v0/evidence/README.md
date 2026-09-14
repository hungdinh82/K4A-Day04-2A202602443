# Evidence đã curate cho bài nộp

`runs/`, `transcripts/`, `analysis/` ở thư mục gốc `starter_v0/` bị gitignore vì
chúng là scratch output chạy hằng ngày. Thư mục này thì **được commit**: chỉ copy
vào đây những file mà report thực sự trích dẫn.

| Thư mục | Nội dung |
|---|---|
| `runs/` | Run JSON của v0–v3 + group/extension/adversarial suite được dẫn trong `artifacts/REPORT.md` |
| `transcripts/` | Transcript cho normal / missing-info / multi-turn / action-boundary |
| `run-analysis.csv` | Bảng phẳng sinh bằng `scripts/parse_runs.py` |

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

Kiểm tra lại bất cứ lúc nào:

```bash
shasum -a 256 evidence/artifacts/system_prompt_p667b5cfa95aa.md | cut -c1-12
# => 667b5cfa95aa
```

## `adversarial-tickets/` — tác dụng phụ có thật

4 file ticket do agent ghi ra đĩa khi chạy suite adversarial, **không có xác nhận
của người dùng**. Giữ lại làm bằng chứng cho mục B4a/B6. Thư mục `tickets/` gốc
bị gitignore nên phải copy sang đây mới commit được.

