# Xổ số Miền Nam (XSMN) Analysis

> Phân tích và dự đoán xổ số Miền Nam Việt Nam với AI/ML. Cập nhật tự động hàng ngày bởi GitHub Actions.

[![GitHub Pages](https://img.shields.io/badge/Live-Demo-blue)](https://t-k-minh.github.io/XSMienNam-Analysis/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Auto-update](https://img.shields.io/badge/Auto--update-daily-orange)](#pipeline)

## Demo

Truy cập trực tuyến: **[t-k-minh.github.io/XSMienNam-Analysis](https://t-k-minh.github.io/XSMienNam-Analysis/)**

## Tính năng

- **Kết quả xổ số**: Hiển thị kết quả 22 tỉnh thành theo ngày, đầy đủ 15 giải (G8 - Đặc Biệt)
- **Dự đoán AI**: Phương pháp Ensemble kết hợp Thompson Sampling (40%) + Statistical (60%), top 6 số
- **Phân tích theo ngày**: Xem dự đoán cho từng tỉnh, kiểm tra trúng ở tất cả các giải (không chỉ ĐB)
- **Backtest**: Kiểm tra hiệu quả dự đoán trên dữ liệu lịch sử, so sánh với ngẫu nhiên (~57%)
- **Tần suất & Lâu chưa ra**: Thống kê tần suất xuất hiện và số ngày chưa ra của từng số
- **Phân tích Đầu-Đuôi**: Phân bố đầu (0-9) và đuôi (0-9)
- **Cập nhật tự động**: GitHub Actions fetch dữ liệu mới mỗi ngày lúc 18:35 (VN)

## Phân tích dự đoán

### Phương pháp Ensemble

Dự đoán top 6 số dựa trên weighted scoring:

| Thành phần | Trọng số | Mô tả |
|---|---|---|
| **Thompson Sampling** | 40% | Mô hình xác suất Bayesian, cập nhật theo lịch sử |
| **Statistical** | 60% | Kết hợp tần suất + số ngày chưa ra |

Kiểm tra kết quả ở **tất cả 15 giải** (G8 → Đặc Biệt), không chỉ giải ĐB.

### Kết quả Backtest (2 năm gần nhất, check 15 giải)

| Window | Trung bình | Random baseline |
|---|---|---|
| 3 tháng | ~57% | ~57% |
| 6 tháng | ~61% | ~57% |
| 1 năm | ~58% | ~57% |
| Tất cả | ~64% | ~57% |

> **Lưu ý**: Lottery là trò chơi ngẫu nhiên. Phương pháp không đảm bảo thắng. Kết quả trên phản ánh thống kê lịch sử, không phải dự đoán tương lai.

## Cấu trúc dự án

```
XSMienNam-Analysis/
├── src/
│   ├── xsmn_lottery.py    # Parser kết quả từ xoso.com.vn (BeautifulSoup)
│   ├── xsmn_dtos.py        # Data Transfer Objects (Pydantic)
│   ├── update_xsmn.py      # Fetch data + generate HTML
│   └── ml_predict.py       # ML models (RandomForest, XGBoost, LSTM)
├── data/
│   ├── xsmn.json           # Dữ liệu gốc (7100+ records)
│   └── xsmn_web.json       # Dữ liệu tối ưu cho web (minified, ~700KB)
├── readme.html             # Trang web tương tác (JavaScript)
├── .github/workflows/
│   └── update-data.yml     # GitHub Actions: fetch + deploy hàng ngày
├── pyproject.toml          # Dependencies (uv)
└── LICENSE                 # MIT License
```

## Công nghệ

| Thành phần | Công nghệ |
|---|---|
| **Data fetch** | Python + BeautifulSoup + cloudscraper |
| **Data model** | Pydantic v2 |
| **ML models** | scikit-learn, XGBoost, LightGBM, PyTorch |
| **Web frontend** | Vanilla JavaScript (no framework) |
| **CI/CD** | GitHub Actions + GitHub Pages |
| **Package manager** | uv |

## Cài đặt & Chạy local

```bash
# Clone repo
git clone https://github.com/t-k-minh/XSMienNam-Analysis.git
cd XSMienNam-Analysis

# Install dependencies
uv sync

# Fetch data mới nhất
uv run python src/update_xsmn.py

# Mở browser
start readme.html
```

## Data Pipeline

```
xoso.com.vn → Python fetch → xsmn.json → generate → xsmn_web.json + readme.html → GitHub Pages
                                                                  ↑
                                                    GitHub Actions (18:35 VN hàng ngày)
```

1. **Fetch**: `xsmn_lottery.py` parse HTML từ xoso.com.vn bằng BeautifulSoup
2. **Store**: Lưu vào `data/xsmn.json` (Pydantic validation)
3. **Generate**: `update_xsmn.py` tạo HTML + JSON tối ưu
4. **Deploy**: GitHub Actions push lên `main` + `gh-pages`

## Dữ liệu

- **22 tỉnh thành** Miền Nam
- **15 giải**: G8, G7, G6 (3), G5, G4 (4), G3 (2), G2, G1, Đặc Biệt
- **Từ 2020** đến nay (~7100+ records)
- Nguồn: [xoso.com.vn](https://xoso.com.vn)

## Credits

- Forked from [khiemdoan/vietnam-lottery-xsmb-analysis](https://github.com/khiemdoan/vietnam-lottery-xsmb-analysis) (MIT License)
- Dữ liệu từ [xoso.com.vn](https://xoso.com.vn)

## License

[MIT](LICENSE) - Copyright (c) 2022 Khiem Doan, (c) 2026 t-k-minh
