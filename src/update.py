"""Update lottery data and generate readme.html."""
import json
import sys
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from lottery import Lottery
from ml_predict import train_and_predict


def fetch_data():
    """Fetch new lottery data."""
    lottery = Lottery()
    lottery.load()

    begin_date = lottery.get_last_date()
    tz = ZoneInfo('Asia/Ho_Chi_Minh')
    now = datetime.now(tz)
    last_date = now.date()
    if now.time() < time(18, 35):
        last_date -= timedelta(days=1)

    delta = (last_date - begin_date).days + 1
    for i in range(1, delta):
        selected_date = begin_date + timedelta(days=i)
        print(f'Fetching: {selected_date}')
        lottery.fetch(selected_date)

    lottery.generate_dataframes()
    lottery.dump()
    return lottery


def generate_html(lottery: Lottery):
    """Generate readme.html with interactive features."""
    df = lottery.get_raw_data()
    df['date_str'] = df['date'].dt.strftime('%Y-%m-%d')
    df['date_display'] = df['date'].dt.strftime('%d/%m/%Y')

    latest = df.iloc[-1]

    # Prepare data for JSON embedding
    records = []
    for _, row in df.iterrows():
        records.append({
            'date': row['date_str'],
            'date_display': row['date_display'],
            'special': int(row['special']),
            'prize1': int(row['prize1']),
            'prize2_1': int(row['prize2_1']),
            'prize2_2': int(row['prize2_2']),
            'prize3_1': int(row['prize3_1']),
            'prize3_2': int(row['prize3_2']),
            'prize3_3': int(row['prize3_3']),
            'prize3_4': int(row['prize3_4']),
            'prize3_5': int(row['prize3_5']),
            'prize3_6': int(row['prize3_6']),
            'prize4_1': int(row['prize4_1']),
            'prize4_2': int(row['prize4_2']),
            'prize4_3': int(row['prize4_3']),
            'prize4_4': int(row['prize4_4']),
            'prize5_1': int(row['prize5_1']),
            'prize5_2': int(row['prize5_2']),
            'prize5_3': int(row['prize5_3']),
            'prize5_4': int(row['prize5_4']),
            'prize5_5': int(row['prize5_5']),
            'prize5_6': int(row['prize5_6']),
            'prize6_1': int(row['prize6_1']),
            'prize6_2': int(row['prize6_2']),
            'prize6_3': int(row['prize6_3']),
            'prize7_1': int(row['prize7_1']),
            'prize7_2': int(row['prize7_2']),
            'prize7_3': int(row['prize7_3']),
            'prize7_4': int(row['prize7_4']),
        })

    data_json = json.dumps(records, ensure_ascii=False)
    latest_date = latest['date_str']
    min_date = df['date_str'].min()
    max_date = df['date_str'].max()

    # Train ML model
    print("Training ML model...")
    ml_results = train_and_predict(records)
    ml_json = json.dumps(ml_results, ensure_ascii=False)

    html = f'''<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Xổ số Miền Bắc - Phân tích</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; color: #333; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        header {{ background: linear-gradient(135deg, #1a5276, #2e86c1); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; text-align: center; }}
        header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        header p {{ opacity: 0.9; }}
        .controls {{ background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .controls-row {{ display: flex; gap: 15px; flex-wrap: wrap; align-items: center; margin-bottom: 15px; }}
        .controls-row:last-child {{ margin-bottom: 0; }}
        .quick-filters {{ display: flex; gap: 8px; flex-wrap: wrap; }}
        .btn-quick {{ background: #ecf0f1; color: #555; border: 2px solid #ddd; padding: 8px 16px; border-radius: 20px; cursor: pointer; font-size: 13px; font-weight: 600; transition: all 0.2s; }}
        .btn-quick:hover {{ background: #d5dbdb; border-color: #bbb; }}
        .btn-quick.active {{ background: #2e86c1; color: white; border-color: #2e86c1; }}
        .control-group {{ display: flex; flex-direction: column; gap: 5px; }}
        .control-group label {{ font-weight: 600; font-size: 14px; color: #555; }}
        .control-group input, .control-group select {{ padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 14px; }}
        .control-group input[type="date"] {{ min-width: 150px; }}
        .btn {{ background: #2e86c1; color: white; border: none; padding: 12px 24px; border-radius: 5px; cursor: pointer; font-size: 14px; font-weight: 600; transition: background 0.3s; }}
        .btn:hover {{ background: #1a5276; }}
        .btn-secondary {{ background: #95a5a6; }}
        .btn-secondary:hover {{ background: #7f8c8d; }}
        .result-card {{ background: white; border-radius: 10px; padding: 25px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .result-card h2 {{ color: #1a5276; margin-bottom: 15px; font-size: 22px; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        .result-card .date {{ color: #e74c3c; font-weight: bold; font-size: 18px; }}
        .prizes-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
        .prize-item {{ background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #2e86c1; }}
        .prize-item.special {{ border-left-color: #e74c3c; background: #fef5f5; }}
        .prize-label {{ font-size: 13px; color: #666; margin-bottom: 5px; }}
        .prize-value {{ font-size: 20px; font-weight: bold; color: #1a5276; font-family: 'Courier New', monospace; }}
        .prize-item.special .prize-value {{ color: #e74c3c; font-size: 24px; }}
        .loto-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        .loto-table th, .loto-table td {{ padding: 12px; text-align: center; border: 1px solid #ddd; }}
        .loto-table th {{ background: #2e86c1; color: white; }}
        .loto-table tr:nth-child(even) {{ background: #f8f9fa; }}
        .loto-table tr:hover {{ background: #e8f4f8; }}
        .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-top: 20px; }}
        .stat-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-value {{ font-size: 28px; font-weight: bold; color: #2e86c1; }}
        .stat-label {{ font-size: 13px; color: #666; margin-top: 5px; }}
        .history-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        .history-table th, .history-table td {{ padding: 10px; text-align: center; border: 1px solid #ddd; font-size: 13px; }}
        .history-table th {{ background: #2e86c1; color: white; position: sticky; top: 0; }}
        .history-table tr:hover {{ background: #e8f4f8; cursor: pointer; }}
        .history-table .special {{ color: #e74c3c; font-weight: bold; }}
        .table-container {{ max-height: 400px; overflow-y: auto; border-radius: 8px; border: 1px solid #ddd; }}
        .info {{ background: #d4edda; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #28a745; }}
        .analysis-tabs {{ display: flex; gap: 5px; margin-bottom: 20px; flex-wrap: wrap; }}
        .tab-btn {{ background: #ecf0f1; border: 2px solid #ddd; padding: 10px 20px; border-radius: 8px 8px 0 0; cursor: pointer; font-weight: 600; transition: all 0.2s; }}
        .tab-btn:hover {{ background: #d5dbdb; }}
        .tab-btn.active {{ background: #2e86c1; color: white; border-color: #2e86c1; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
        .freq-grid {{ display: grid; grid-template-columns: repeat(10, 1fr); gap: 4px; }}
        .freq-cell {{ padding: 8px 4px; text-align: center; border-radius: 4px; font-size: 12px; font-weight: 600; cursor: pointer; transition: transform 0.2s; }}
        .freq-cell:hover {{ transform: scale(1.1); z-index: 1; }}
        .freq-cell .num {{ display: block; font-size: 14px; }}
        .freq-cell .count {{ display: block; font-size: 11px; opacity: 0.8; }}
        .hot {{ background: #e74c3c; color: white; }}
        .warm {{ background: #f39c12; color: white; }}
        .normal {{ background: #3498db; color: white; }}
        .cool {{ background: #9b59b6; color: white; }}
        .cold {{ background: #34495e; color: white; }}
        .overdue-grid {{ display: grid; grid-template-columns: repeat(10, 1fr); gap: 4px; }}
        .overdue-cell {{ padding: 8px 4px; text-align: center; border-radius: 4px; font-size: 12px; font-weight: 600; cursor: pointer; }}
        .overdue-cell .num {{ display: block; font-size: 14px; }}
        .overdue-cell .days {{ display: block; font-size: 11px; opacity: 0.8; }}
        .overdue-hot {{ background: #e74c3c; color: white; }}
        .overdue-warm {{ background: #e67e22; color: white; }}
        .overdue-normal {{ background: #f1c40f; color: #333; }}
        .overdue-cool {{ background: #2ecc71; color: white; }}
        .headtail-container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        .headtail-chart {{ background: #f8f9fa; padding: 20px; border-radius: 8px; }}
        .headtail-bar {{ display: flex; align-items: center; margin-bottom: 8px; }}
        .headtail-label {{ width: 40px; font-weight: 600; text-align: right; margin-right: 10px; }}
        .headtail-fill {{ height: 24px; border-radius: 4px; display: flex; align-items: center; padding-left: 8px; color: white; font-size: 12px; font-weight: 600; min-width: 30px; }}
        .legend {{ display: flex; gap: 15px; margin-top: 15px; flex-wrap: wrap; }}
        .legend-item {{ display: flex; align-items: center; gap: 5px; font-size: 12px; }}
        .legend-color {{ width: 16px; height: 16px; border-radius: 3px; }}
        .search-box {{ display: flex; gap: 10px; margin-bottom: 15px; }}
        .search-box input {{ padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 14px; width: 150px; }}
        .search-result {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 10px; }}
        .cycle-grid {{ display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; }}
        .cycle-header {{ background: #2e86c1; color: white; padding: 8px; text-align: center; border-radius: 4px; font-weight: 600; font-size: 12px; }}
        .cycle-cell {{ padding: 6px 4px; text-align: center; border-radius: 4px; font-size: 11px; font-weight: 600; }}
        .transition-grid {{ display: grid; grid-template-columns: repeat(10, 1fr); gap: 2px; font-size: 10px; }}
        .transition-cell {{ padding: 4px; text-align: center; border-radius: 2px; min-height: 28px; display: flex; align-items: center; justify-content: center; }}
        .transition-header {{ background: #2e86c1; color: white; font-weight: 600; }}
        .ml-container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        .ml-panel {{ background: #f8f9fa; padding: 20px; border-radius: 8px; }}
        .ml-bar {{ display: flex; align-items: center; margin-bottom: 4px; }}
        .ml-label {{ width: 30px; font-weight: 600; text-align: right; margin-right: 8px; font-size: 12px; }}
        .ml-fill {{ height: 20px; border-radius: 3px; display: flex; align-items: center; padding-left: 6px; color: white; font-size: 10px; font-weight: 600; min-width: 20px; }}
        .ml-prediction {{ background: linear-gradient(135deg, #e74c3c, #c0392b); color: white; padding: 20px; border-radius: 8px; text-align: center; margin-top: 15px; }}
        .ml-prediction h3 {{ margin-bottom: 10px; }}
        .ml-prediction .numbers {{ font-size: 28px; font-weight: bold; letter-spacing: 5px; }}
        footer {{ text-align: center; padding: 20px; color: #666; font-size: 13px; }}
        @media (max-width: 768px) {{
            .controls {{ flex-direction: column; }}
            .stats {{ grid-template-columns: repeat(2, 1fr); }}
            .prizes-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Xổ số Miền Bắc (XSMB)</h1>
            <p>Phân tích kết quả xổ số hàng ngày</p>
        </header>

        <div class="info">
            Dữ liệu cập nhật lần cuối: <strong>{datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).strftime('%d/%m/%Y %H:%M')}</strong>
        </div>

        <div class="controls">
            <div class="controls-row">
                <div class="control-group">
                    <label>Chọn nhanh khoảng thời gian</label>
                    <div class="quick-filters">
                        <button class="btn-quick" onclick="quickFilter(30)">30 ngày</button>
                        <button class="btn-quick" onclick="quickFilter(90)">3 tháng</button>
                        <button class="btn-quick" onclick="quickFilter(180)">6 tháng</button>
                        <button class="btn-quick" onclick="quickFilter(365)">1 năm</button>
                        <button class="btn-quick" onclick="quickFilter(730)">2 năm</button>
                        <button class="btn-quick" onclick="quickFilter(1095)">3 năm</button>
                        <button class="btn-quick active" onclick="quickFilter(0)">Tất cả</button>
                    </div>
                </div>
            </div>
            <div class="controls-row">
                <div class="control-group">
                    <label>Từ ngày</label>
                    <input type="date" id="startDate" value="{min_date}" min="{min_date}" max="{max_date}">
                </div>
                <div class="control-group">
                    <label>Đến ngày</label>
                    <input type="date" id="endDate" value="{max_date}" min="{min_date}" max="{max_date}">
                </div>
                <div class="control-group">
                    <label>&nbsp;</label>
                    <button class="btn" onclick="filterByDate()">Áp dụng</button>
                </div>
                <div class="control-group">
                    <label>&nbsp;</label>
                    <button class="btn btn-secondary" onclick="showLatest()">Kết quả mới nhất</button>
                </div>
            </div>
        </div>

        <div id="latestResult" class="result-card">
            <h2>Kết quả mới nhất</h2>
            <p class="date" id="resultDate"></p>
            <div class="prizes-grid" id="prizesGrid"></div>
            <h3 style="margin-top: 20px; margin-bottom: 10px;">Lô tô</h3>
            <table class="loto-table" id="lotoTable">
                <thead><tr><th>Đầu</th><th>Đuôi</th></tr></thead>
                <tbody id="lotoBody"></tbody>
            </table>
        </div>

        <div class="result-card">
            <h2>Thống kê nhanh</h2>
            <div class="stats" id="statsContainer"></div>
        </div>

        <div class="result-card">
            <h2>Phân tích dự đoán</h2>
            <div class="analysis-tabs">
                <button class="tab-btn active" onclick="showTab('frequency')">Tần suất</button>
                <button class="tab-btn" onclick="showTab('overdue')">Lâu chưa ra</button>
                <button class="tab-btn" onclick="showTab('headtail')">Đầu-Đuôi</button>
                <button class="tab-btn" onclick="showTab('cycle')">Chu kỳ ngày</button>
                <button class="tab-btn" onclick="showTab('transition')">Liên kết</button>
                <button class="tab-btn" onclick="showTab('ml')">AI Dự đoán</button>
            </div>

            <div id="tab-frequency" class="tab-content active">
                <p style="margin-bottom: 10px; color: #666;">Số nào xuất hiện nhiều nhất trong khoảng thời gian đã chọn</p>
                <div class="search-box">
                    <input type="number" id="searchNum" min="0" max="99" placeholder="Tìm số (0-99)" oninput="searchNumber()">
                </div>
                <div id="searchResult" class="search-result" style="display: none;"></div>
                <div class="freq-grid" id="freqGrid"></div>
                <div class="legend">
                    <div class="legend-item"><div class="legend-color hot"></div> Rất nóng (>80%)</div>
                    <div class="legend-item"><div class="legend-color warm"></div> Nóng (60-80%)</div>
                    <div class="legend-item"><div class="legend-color normal"></div> Trung bình (40-60%)</div>
                    <div class="legend-item"><div class="legend-color cool"></div> Lạnh (20-40%)</div>
                    <div class="legend-item"><div class="legend-color cold"></div> Rất lạnh (<20%)</div>
                </div>
            </div>

            <div id="tab-overdue" class="tab-content">
                <p style="margin-bottom: 10px; color: #666;">Số nào đã lâu nhất chưa xuất hiện (có thể sắp ra)</p>
                <div class="overdue-grid" id="overdueGrid"></div>
                <div class="legend">
                    <div class="legend-item"><div class="legend-color overdue-hot"></div> Quá hạn (>30 ngày)</div>
                    <div class="legend-item"><div class="legend-color overdue-warm"></div> Hơi lâu (20-30 ngày)</div>
                    <div class="legend-item"><div class="legend-color overdue-normal"></div> Bình thường (10-20 ngày)</div>
                    <div class="legend-item"><div class="legend-color overdue-cool"></div> Mới ra (<10 ngày)</div>
                </div>
            </div>

            <div id="tab-headtail" class="tab-content">
                <p style="margin-bottom: 15px; color: #666;">Phân tích xác suất theo đầu (chục) và đuôi (đơn vị)</p>
                <div class="headtail-container">
                    <div class="headtail-chart">
                        <h3 style="margin-bottom: 15px; color: #1a5276;">Đầu (Chục)</h3>
                        <div id="headChart"></div>
                    </div>
                    <div class="headtail-chart">
                        <h3 style="margin-bottom: 15px; color: #1a5276;">Đuôi (Đơn vị)</h3>
                        <div id="tailChart"></div>
                    </div>
                </div>
            </div>

            <div id="tab-cycle" class="tab-content">
                <p style="margin-bottom: 10px; color: #666;">Số nào hay ra vào ngày thứ mấy trong tuần?</p>
                <div class="cycle-grid" id="cycleGrid"></div>
            </div>

            <div id="tab-transition" class="tab-content">
                <p style="margin-bottom: 10px; color: #666;">Nếu hôm nay ra số A thì ngày mai hay ra số B? (Ma trận xác suất điều kiện)</p>
                <p style="margin-bottom: 10px; color: #999; font-size: 12px;">Hàng = số hôm nay, Cột = số ngày mai. Màu đỏ = xác suất cao</p>
                <div style="overflow-x: auto;">
                    <div class="transition-grid" id="transitionGrid"></div>
                </div>
            </div>

            <div id="tab-ml" class="tab-content">
                <p style="margin-bottom: 10px; color: #666;">Random Forest (sklearn) dự đoán xác suất xuất hiện</p>
                <div id="mlModelInfo" style="margin-bottom: 15px; color: #999;"></div>
                <div class="ml-container">
                    <div class="ml-panel">
                        <h3 style="margin-bottom: 15px; color: #1a5276;">Top 20 số có xác suất cao nhất</h3>
                        <div id="mlTop"></div>
                    </div>
                    <div class="ml-panel">
                        <h3 style="margin-bottom: 15px; color: #1a5276;">Top 20 số có xác suất thấp nhất</h3>
                        <div id="mlBottom"></div>
                    </div>
                </div>
                <div class="ml-prediction">
                    <h3>Gợi ý con số may mắn hôm nay</h3>
                    <div class="numbers" id="mlPrediction"></div>
                    <p style="margin-top: 10px; font-size: 12px; opacity: 0.8;">* Dựa trên phân tích Random Forest, không đảm bảo chính xác</p>
                </div>
            </div>
        </div>

        <div class="result-card">
            <h2>Lịch sử kết quả</h2>
            <div class="table-container">
                <table class="history-table" id="historyTable">
                    <thead>
                        <tr>
                            <th>Ngày</th>
                            <th>Đặc biệt</th>
                            <th>Giải nhất</th>
                            <th>Giải nhì</th>
                            <th>Giải ba</th>
                            <th>Giải bảy</th>
                        </tr>
                    </thead>
                    <tbody id="historyBody"></tbody>
                </table>
            </div>
        </div>

        <footer>
            <p>Dữ liệu từ xoso.com.vn | Tạo bởi <a href="https://github.com/khiemdoan" target="_blank">Khiem Doan</a></p>
        </footer>
    </div>

    <script>
        const DATA = {data_json};
        let filteredData = [...DATA];

        function formatDate(dateStr) {{
            const [y, m, d] = dateStr.split('-');
            return `${{d}}/${{m}}/${{y}}`;
        }}

        function formatNumber(n) {{
            return String(n).padStart(5, '0');
        }}

        function renderLatest() {{
            const latest = DATA[DATA.length - 1];
            document.getElementById('resultDate').textContent = 'Ngày: ' + formatDate(latest.date);

            const prizes = [
                {{ label: 'Giải đặc biệt', value: formatNumber(latest.special), special: true }},
                {{ label: 'Giải nhất', value: formatNumber(latest.prize1) }},
                {{ label: 'Giải nhì', value: formatNumber(latest.prize2_1) + ', ' + formatNumber(latest.prize2_2) }},
                {{ label: 'Giải ba (1)', value: formatNumber(latest.prize3_1) + ', ' + formatNumber(latest.prize3_2) + ', ' + formatNumber(latest.prize3_3) }},
                {{ label: 'Giải ba (2)', value: formatNumber(latest.prize3_4) + ', ' + formatNumber(latest.prize3_5) + ', ' + formatNumber(latest.prize3_6) }},
                {{ label: 'Giải tư', value: [latest.prize4_1, latest.prize4_2, latest.prize4_3, latest.prize4_4].map(formatNumber).join(', ') }},
                {{ label: 'Giải năm (1)', value: [latest.prize5_1, latest.prize5_2, latest.prize5_3].map(formatNumber).join(', ') }},
                {{ label: 'Giải năm (2)', value: [latest.prize5_4, latest.prize5_5, latest.prize5_6].map(formatNumber).join(', ') }},
                {{ label: 'Giải sáu', value: [latest.prize6_1, latest.prize6_2, latest.prize6_3].map(n => String(n).padStart(3, '0')).join(', ') }},
                {{ label: 'Giải bảy', value: [latest.prize7_1, latest.prize7_2, latest.prize7_3, latest.prize7_4].map(n => String(n).padStart(2, '0')).join(', ') }},
            ];

            const grid = document.getElementById('prizesGrid');
            grid.innerHTML = prizes.map(p =>
                `<div class="prize-item ${{p.special ? 'special' : ''}}">
                    <div class="prize-label">${{p.label}}</div>
                    <div class="prize-value">${{p.value}}</div>
                </div>`
            ).join('');

            // Loto
            const allPrizes = [
                latest.special, latest.prize1,
                latest.prize2_1, latest.prize2_2,
                latest.prize3_1, latest.prize3_2, latest.prize3_3, latest.prize3_4, latest.prize3_5, latest.prize3_6,
                latest.prize4_1, latest.prize4_2, latest.prize4_3, latest.prize4_4,
                latest.prize5_1, latest.prize5_2, latest.prize5_3, latest.prize5_4, latest.prize5_5, latest.prize5_6,
                latest.prize6_1, latest.prize6_2, latest.prize6_3,
                latest.prize7_1, latest.prize7_2, latest.prize7_3, latest.prize7_4,
            ].map(n => n % 100);

            const lotoBody = document.getElementById('lotoBody');
            let lotoHtml = '';
            for (let i = 0; i < 10; i++) {{
                const tails = allPrizes.filter(n => Math.floor(n / 10) === i).map(n => n % 10).sort();
                lotoHtml += `<tr><td>${{i}}</td><td>${{tails.length > 0 ? tails.join(', ') : '-'}}</td></tr>`;
            }}
            lotoBody.innerHTML = lotoHtml;
        }}

        function renderStats() {{
            const last365 = DATA.slice(-365);
            const allPrizes = [];
            last365.forEach(d => {{
                for (let k in d) {{
                    if (k.startsWith('prize') || k === 'special') allPrizes.push(d[k] % 100);
                }}
            }});
            const counts = {{}};
            allPrizes.forEach(n => counts[n] = (counts[n] || 0) + 1);
            const values = Object.values(counts);
            const freqs = Object.entries(counts).sort((a, b) => b[1] - a[1]);

            document.getElementById('statsContainer').innerHTML = `
                <div class="stat-card"><div class="stat-value">${{DATA.length}}</div><div class="stat-label">Tổng số kỳ quay</div></div>
                <div class="stat-card"><div class="stat-value">${{last365.length}}</div><div class="stat-label">Kỳ quay (1 năm)</div></div>
                <div class="stat-card"><div class="stat-value">${{freqs[0][0]}}</div><div class="stat-label">Số xuất hiện nhiều nhất</div></div>
                <div class="stat-card"><div class="stat-value">${{freqs[freqs.length - 1][0]}}</div><div class="stat-label">Số xuất hiện ít nhất</div></div>
            `;
        }}

        function renderHistory(data) {{
            const tbody = document.getElementById('historyBody');
            tbody.innerHTML = data.slice().reverse().map(d => `
                <tr onclick="selectDate('${{d.date}}')">
                    <td>${{formatDate(d.date)}}</td>
                    <td class="special">${{formatNumber(d.special)}}</td>
                    <td>${{formatNumber(d.prize1)}}</td>
                    <td>${{formatNumber(d.prize2_1)}}, ${{formatNumber(d.prize2_2)}}</td>
                    <td>${{formatNumber(d.prize3_1)}}, ${{formatNumber(d.prize3_2)}}, ${{formatNumber(d.prize3_3)}}</td>
                    <td>${{[d.prize7_1, d.prize7_2, d.prize7_3, d.prize7_4].map(n => String(n).padStart(2, '0')).join(', ')}}</td>
                </tr>
            `).join('');
        }}

        function selectDate(dateStr) {{
            const d = DATA.find(x => x.date === dateStr);
            if (!d) return;
            const allPrizes = [
                d.special, d.prize1,
                d.prize2_1, d.prize2_2,
                d.prize3_1, d.prize3_2, d.prize3_3, d.prize3_4, d.prize3_5, d.prize3_6,
                d.prize4_1, d.prize4_2, d.prize4_3, d.prize4_4,
                d.prize5_1, d.prize5_2, d.prize5_3, d.prize5_4, d.prize5_5, d.prize5_6,
                d.prize6_1, d.prize6_2, d.prize6_3,
                d.prize7_1, d.prize7_2, d.prize7_3, d.prize7_4,
            ].map(n => n % 100);

            document.getElementById('resultDate').textContent = 'Ngày: ' + formatDate(d.date);
            const prizes = [
                {{ label: 'Giải đặc biệt', value: formatNumber(d.special), special: true }},
                {{ label: 'Giải nhất', value: formatNumber(d.prize1) }},
                {{ label: 'Giải nhì', value: formatNumber(d.prize2_1) + ', ' + formatNumber(d.prize2_2) }},
                {{ label: 'Giải ba (1)', value: formatNumber(d.prize3_1) + ', ' + formatNumber(d.prize3_2) + ', ' + formatNumber(d.prize3_3) }},
                {{ label: 'Giải ba (2)', value: formatNumber(d.prize3_4) + ', ' + formatNumber(d.prize3_5) + ', ' + formatNumber(d.prize3_6) }},
                {{ label: 'Giải tư', value: [d.prize4_1, d.prize4_2, d.prize4_3, d.prize4_4].map(formatNumber).join(', ') }},
                {{ label: 'Giải năm (1)', value: [d.prize5_1, d.prize5_2, d.prize5_3].map(formatNumber).join(', ') }},
                {{ label: 'Giải năm (2)', value: [d.prize5_4, d.prize5_5, d.prize5_6].map(formatNumber).join(', ') }},
                {{ label: 'Giải sáu', value: [d.prize6_1, d.prize6_2, d.prize6_3].map(n => String(n).padStart(3, '0')).join(', ') }},
                {{ label: 'Giải bảy', value: [d.prize7_1, d.prize7_2, d.prize7_3, d.prize7_4].map(n => String(n).padStart(2, '0')).join(', ') }},
            ];
            document.getElementById('prizesGrid').innerHTML = prizes.map(p =>
                `<div class="prize-item ${{p.special ? 'special' : ''}}">
                    <div class="prize-label">${{p.label}}</div>
                    <div class="prize-value">${{p.value}}</div>
                </div>`
            ).join('');

            const lotoBody = document.getElementById('lotoBody');
            let lotoHtml = '';
            for (let i = 0; i < 10; i++) {{
                const tails = allPrizes.filter(n => Math.floor(n / 10) === i).map(n => n % 10).sort();
                lotoHtml += `<tr><td>${{i}}</td><td>${{tails.length > 0 ? tails.join(', ') : '-'}}</td></tr>`;
            }}
            lotoBody.innerHTML = lotoHtml;
        }}

        function quickFilter(days) {{
            // Update active button
            document.querySelectorAll('.btn-quick').forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');

            const latest = DATA[DATA.length - 1];
            if (days === 0) {{
                filteredData = [...DATA];
            }} else {{
                const cutoff = new Date(latest.date);
                cutoff.setDate(cutoff.getDate() - days);
                const cutoffStr = cutoff.toISOString().split('T')[0];
                filteredData = DATA.filter(d => d.date >= cutoffStr);
            }}

            // Update date inputs
            document.getElementById('startDate').value = filteredData[0]?.date || DATA[0].date;
            document.getElementById('endDate').value = latest.date;

            renderHistory(filteredData);
            renderFrequency(filteredData);
            renderOverdue(filteredData);
            renderHeadTail(filteredData);
            renderCycle(filteredData);
            renderTransition(filteredData);
            renderML(filteredData);
        }}

        function filterByDate() {{
            const start = document.getElementById('startDate').value;
            const end = document.getElementById('endDate').value;
            filteredData = DATA.filter(d => d.date >= start && d.date <= end);
            renderHistory(filteredData);
            renderFrequency(filteredData);
            renderOverdue(filteredData);
            renderHeadTail(filteredData);
            renderCycle(filteredData);
            renderTransition(filteredData);
            renderML(filteredData);
        }}

        function showLatest() {{
            document.getElementById('startDate').value = DATA[0].date;
            document.getElementById('endDate').value = DATA[DATA.length - 1].date;
            filteredData = [...DATA];
            renderHistory(DATA);
            renderLatest();
            renderFrequency(DATA);
            renderOverdue(DATA);
            renderHeadTail(DATA);
            renderCycle(DATA);
            renderTransition(DATA);
            renderML(DATA);
        }}

        // Analysis Functions
        function getAllTwoDigitNumbers(data) {{
            const nums = [];
            data.forEach(d => {{
                for (let k in d) {{
                    if (k.startsWith('prize') || k === 'special') {{
                        nums.push(d[k] % 100);
                    }}
                }}
            }});
            return nums;
        }}

        function renderFrequency(data) {{
            const nums = getAllTwoDigitNumbers(data);
            const counts = {{}};
            for (let i = 0; i < 100; i++) counts[i] = 0;
            nums.forEach(n => counts[n]++);
            const maxCount = Math.max(...Object.values(counts));
            const freqs = Object.entries(counts).sort((a, b) => b[1] - a[1]);

            const grid = document.getElementById('freqGrid');
            grid.innerHTML = freqs.map(([num, count]) => {{
                const pct = maxCount > 0 ? (count / maxCount * 100) : 0;
                let cls = 'cold';
                if (pct > 80) cls = 'hot';
                else if (pct > 60) cls = 'warm';
                else if (pct > 40) cls = 'normal';
                else if (pct > 20) cls = 'cool';
                return `<div class="freq-cell ${{cls}}" onclick="selectNumber(${{num}})">
                    <span class="num">${{String(num).padStart(2, '0')}}</span>
                    <span class="count">${{count}} lần</span>
                </div>`;
            }}).join('');
        }}

        function renderOverdue(data) {{
            const lastDate = new Date(data[data.length - 1].date);
            const lastSeen = {{}};
            for (let i = 0; i < 100; i++) lastSeen[i] = -1;

            data.forEach((d, idx) => {{
                for (let k in d) {{
                    if (k.startsWith('prize') || k === 'special') {{
                        lastSeen[d[k] % 100] = idx;
                    }}
                }}
            }});

            const overdue = Object.entries(lastSeen).map(([num, idx]) => {{
                const days = idx === -1 ? data.length : data.length - 1 - idx;
                return [parseInt(num), days];
            }}).sort((a, b) => b[1] - a[1]);

            const maxDays = Math.max(...overdue.map(x => x[1]));
            const grid = document.getElementById('overdueGrid');
            grid.innerHTML = overdue.map(([num, days]) => {{
                const pct = maxDays > 0 ? (days / maxDays * 100) : 0;
                let cls = 'overdue-cool';
                if (pct > 80) cls = 'overdue-hot';
                else if (pct > 60) cls = 'overdue-warm';
                else if (pct > 30) cls = 'overdue-normal';
                return `<div class="overdue-cell ${{cls}}" onclick="selectNumber(${{num}})">
                    <span class="num">${{String(num).padStart(2, '0')}}</span>
                    <span class="days">${{days}} ngày</span>
                </div>`;
            }}).join('');
        }}

        function renderHeadTail(data) {{
            const nums = getAllTwoDigitNumbers(data);
            const headCounts = {{}};
            const tailCounts = {{}};
            for (let i = 0; i < 10; i++) {{
                headCounts[i] = 0;
                tailCounts[i] = 0;
            }}
            nums.forEach(n => {{
                headCounts[Math.floor(n / 10)]++;
                tailCounts[n % 10]++;
            }});

            const maxHead = Math.max(...Object.values(headCounts));
            const maxTail = Math.max(...Object.values(tailCounts));

            const headChart = document.getElementById('headChart');
            headChart.innerHTML = Object.entries(headCounts).sort((a, b) => b[1] - a[1]).map(([h, c]) => {{
                const pct = maxHead > 0 ? (c / maxHead * 100) : 0;
                const color = `hsl(${{200 - pct * 1.5}}, 70%, ${{40 + pct * 0.2}}%)`;
                return `<div class="headtail-bar">
                    <div class="headtail-label">Đầu ${{h}}</div>
                    <div class="headtail-fill" style="width: ${{pct}}%; background: ${{color}};">${{c}}</div>
                </div>`;
            }}).join('');

            const tailChart = document.getElementById('tailChart');
            tailChart.innerHTML = Object.entries(tailCounts).sort((a, b) => b[1] - a[1]).map(([t, c]) => {{
                const pct = maxTail > 0 ? (c / maxTail * 100) : 0;
                const color = `hsl(${{200 - pct * 1.5}}, 70%, ${{40 + pct * 0.2}}%)`;
                return `<div class="headtail-bar">
                    <div class="headtail-label">Đuôi ${{t}}</div>
                    <div class="headtail-fill" style="width: ${{pct}}%; background: ${{color}};">${{c}}</div>
                </div>`;
            }}).join('');
        }}

        function showTab(tab) {{
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById('tab-' + tab).classList.add('active');
        }}

        function selectNumber(num) {{
            document.getElementById('searchNum').value = num;
            searchNumber();
        }}

        function searchNumber() {{
            const num = document.getElementById('searchNum').value;
            const resultDiv = document.getElementById('searchResult');
            if (num === '' || num < 0 || num > 99) {{
                resultDiv.style.display = 'none';
                return;
            }}
            const n = parseInt(num);
            const appearances = [];
            filteredData.forEach(d => {{
                for (let k in d) {{
                    if (k.startsWith('prize') || k === 'special') {{
                        if (d[k] % 100 === n) {{
                            appearances.push(d.date);
                        }}
                    }}
                }}
            }});

            const lastDate = appearances.length > 0 ? appearances[appearances.length - 1] : null;
            const daysSince = lastDate ?
                Math.floor((new Date(filteredData[filteredData.length - 1].date) - new Date(lastDate)) / 86400000) : 'N/A';

            resultDiv.innerHTML = `
                <strong>Số ${{String(n).padStart(2, '0')}}</strong>: Xuất hiện <strong>${{appearances.length}}</strong> lần |
                Lần cuối: <strong>${{lastDate ? formatDate(lastDate) : 'Chưa có'}}</strong> |
                Đã <strong>${{daysSince}}</strong> ngày chưa ra
            `;
            resultDiv.style.display = 'block';
        }}

        // Cycle Analysis - Phân tích theo ngày trong tuần
        function renderCycle(data) {{
            const days = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'];
            const cycleData = {{}};
            days.forEach((d, i) => cycleData[i] = {{}});
            for (let i = 0; i < 100; i++) days.forEach((d, idx) => cycleData[idx][i] = 0);

            data.forEach(d => {{
                const dow = new Date(d.date).getDay();
                for (let k in d) {{
                    if (k.startsWith('prize') || k === 'special') {{
                        cycleData[dow][d[k] % 100]++;
                    }}
                }}
            }});

            // Find max for each day
            const maxPerDay = {{}};
            days.forEach((d, i) => {{
                const vals = Object.values(cycleData[i]);
                maxPerDay[i] = Math.max(...vals);
            }});

            const grid = document.getElementById('cycleGrid');
            let html = '<div class="cycle-header">Số</div>';
            days.forEach(d => html += `<div class="cycle-header">${{d}}</div>`);

            for (let num = 0; num < 100; num++) {{
                html += `<div class="cycle-header" style="background: #34495e;">${{String(num).padStart(2, '0')}}</div>`;
                days.forEach((d, i) => {{
                    const count = cycleData[i][num];
                    const pct = maxPerDay[i] > 0 ? (count / maxPerDay[i] * 100) : 0;
                    let bg = '#ecf0f1';
                    if (pct > 80) bg = '#e74c3c';
                    else if (pct > 60) bg = '#f39c12';
                    else if (pct > 40) bg = '#3498db';
                    html += `<div class="cycle-cell" style="background: ${{bg}}; color: ${{pct > 40 ? 'white' : '#333'}};">${{count}}</div>`;
                }});
            }}
            grid.innerHTML = html;
        }}

        // Transition Matrix - Ma trận liên kết
        function renderTransition(data) {{
            const trans = {{}};
            for (let i = 0; i < 100; i++) {{
                trans[i] = {{}};
                for (let j = 0; j < 100; j++) trans[i][j] = 0;
            }}

            for (let idx = 0; idx < data.length - 1; idx++) {{
                const today = data[idx];
                const tomorrow = data[idx + 1];
                const todayNums = [];
                const tomorrowNums = [];
                for (let k in today) {{
                    if (k.startsWith('prize') || k === 'special') todayNums.push(today[k] % 100);
                }}
                for (let k in tomorrow) {{
                    if (k.startsWith('prize') || k === 'special') tomorrowNums.push(tomorrow[k] % 100);
                }}
                todayNums.forEach(a => {{
                    tomorrowNums.forEach(b => trans[a][b]++);
                }});
            }}

            // Find max transition
            let maxTrans = 0;
            for (let i = 0; i < 100; i++) {{
                for (let j = 0; j < 100; j++) {{
                    if (trans[i][j] > maxTrans) maxTrans = trans[i][j];
                }}
            }}

            const grid = document.getElementById('transitionGrid');
            let html = '<div class="transition-cell transition-header">↓Hôm nay \\ Ngày mai→</div>';
            for (let j = 0; j < 10; j++) {{
                for (let k = 0; k < 10; k++) {{
                    html += `<div class="transition-cell transition-header">${{j}}${{k}}</div>`;
                }}
            }}

            for (let i = 0; i < 10; i++) {{
                for (let j = 0; j < 10; j++) {{
                    const num = i * 10 + j;
                    html += `<div class="transition-cell transition-header" style="background: #34495e;">${{String(num).padStart(2, '0')}}</div>`;
                    for (let a = 0; a < 10; a++) {{
                        for (let b = 0; b < 10; b++) {{
                            const target = a * 10 + b;
                            const count = trans[num][target];
                            const pct = maxTrans > 0 ? (count / maxTrans * 100) : 0;
                            let bg = '#ecf0f1';
                            if (pct > 80) bg = '#e74c3c';
                            else if (pct > 60) bg = '#f39c12';
                            else if (pct > 40) bg = '#3498db';
                            html += `<div class="transition-cell" style="background: ${{bg}}; color: ${{pct > 40 ? 'white' : '#333'}};" title="${{num}}→${{target}}: ${{count}}">${{count > 0 ? count : ''}}</div>`;
                        }}
                    }}
                }}
            }}
            grid.innerHTML = html;
        }}

        // ML Prediction - Real Random Forest from sklearn
        const ML_RESULTS = {ml_json};

        function renderML() {{
            const ml = ML_RESULTS;

            if (ml.error) {{
                document.getElementById('mlTop').innerHTML = '<p>' + ml.error + '</p>';
                return;
            }}

            // Top 20
            const maxProb = ml.top_20[0][1];
            const topHtml = ml.top_20.map(([num, prob]) => {{
                const pct = (prob / maxProb * 100);
                return `<div class="ml-bar">
                    <div class="ml-label">${{String(num).padStart(2, '0')}}</div>
                    <div class="ml-fill" style="width: ${{pct}}%; background: hsl(${{120 - pct}}, 70%, 45%);">${{(prob * 100).toFixed(2)}}%</div>
                </div>`;
            }}).join('');
            document.getElementById('mlTop').innerHTML = topHtml;

            // Bottom 20
            const bottomHtml = ml.bottom_20.reverse().map(([num, prob]) => {{
                const pct = (prob / maxProb * 100);
                return `<div class="ml-bar">
                    <div class="ml-label">${{String(num).padStart(2, '0')}}</div>
                    <div class="ml-fill" style="width: ${{pct}}%; background: hsl(${{240 - pct}}, 50%, 60%);">${{(prob * 100).toFixed(2)}}%</div>
                </div>`;
            }}).join('');
            document.getElementById('mlBottom').innerHTML = bottomHtml;

            // Prediction - top 6 numbers
            const prediction = ml.prediction.map(n => String(n).padStart(2, '0')).join(' - ');
            document.getElementById('mlPrediction').textContent = prediction;

            // Model info
            const info = ml.model_info;
            document.getElementById('mlModelInfo').innerHTML = `
                <small>${{info.algorithm}} | ${{info.features_used}} features | ${{info.training_samples}} samples</small>
            `;
        }}

        // Init
        renderLatest();
        renderStats();
        renderHistory(DATA);
        renderFrequency(DATA);
        renderOverdue(DATA);
        renderHeadTail(DATA);
        renderCycle(DATA);
        renderTransition(DATA);
        renderML(DATA);
    </script>
</body>
</html>'''

    output_path = Path(__file__).parent.parent / 'readme.html'
    output_path.write_text(html, encoding='utf-8')
    print(f'Generated: {output_path}')


if __name__ == '__main__':
    print('=== Update XSMB Data ===')
    lottery = fetch_data()
    print('\n=== Generate HTML ===')
    generate_html(lottery)
    print('Done!')
