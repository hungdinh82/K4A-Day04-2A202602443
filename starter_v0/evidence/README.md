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
