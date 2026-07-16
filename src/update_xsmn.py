"""Update XSMN lottery data and generate readme.html."""
import json
import sys
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from xsmn_lottery import XSMNLottery, PROVINCE_NAMES


def fetch_data(from_date=None):
    """Fetch new XSMN lottery data."""
    lottery = XSMNLottery()
    lottery.load()

    tz = ZoneInfo('Asia/Ho_Chi_Minh')
    now = datetime.now(tz)
    last_date = now.date()
    if now.time() < time(18, 35):
        last_date -= timedelta(days=1)

    if from_date:
        begin_date = from_date
    else:
        begin_date = lottery.get_last_date()
        # If no data, start from 90 days ago
        if lottery.get_raw_data().empty:
            begin_date = last_date - timedelta(days=90)

    delta = (last_date - begin_date).days + 1
    for i in range(1, delta):
        selected_date = begin_date + timedelta(days=i)
        print(f'Fetching: {selected_date}')
        lottery.fetch(selected_date)

    lottery.dump()
    return lottery


def generate_html(lottery: XSMNLottery):
    """Generate readme.html with interactive features for XSMN."""
    df = lottery.get_raw_data()

    if df.empty:
        print("No data available")
        return

    df['date_str'] = df['date'].dt.strftime('%Y-%m-%d')
    df['province_name'] = df['province'].map(PROVINCE_NAMES).fillna(df['province'])

    # Prepare data
    records = []
    for _, row in df.iterrows():
        rec = {'date': row['date_str'], 'province': row['province'], 'province_name': row['province_name']}
        for col in df.columns:
            if col.startswith('prize') or col == 'special':
                val = row[col]
                rec[col] = str(val) if isinstance(val, str) else int(val)
        records.append(rec)

    data_json = json.dumps(records, ensure_ascii=False)
    provinces = sorted(df['province'].unique().tolist())
    province_json = json.dumps([{'code': p, 'name': PROVINCE_NAMES.get(p, p)} for p in provinces])
    min_date = df['date_str'].min()
    max_date = df['date_str'].max()

    html = f'''<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XSMN - Phân tích</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; color: #333; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        header {{ background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); padding: 30px; border-radius: 16px; margin-bottom: 20px; text-align: center; box-shadow: 0 8px 32px rgba(0,0,0,0.1); }}
        header h1 {{ font-size: 28px; color: #1a5276; margin-bottom: 5px; }}
        header p {{ color: #666; font-size: 14px; }}
        .card {{ background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); border-radius: 16px; padding: 24px; margin-bottom: 16px; box-shadow: 0 8px 32px rgba(0,0,0,0.08); }}
        .card h2 {{ color: #1a5276; margin-bottom: 16px; font-size: 18px; display: flex; align-items: center; gap: 8px; }}
        .card h2::before {{ content: ''; width: 4px; height: 20px; background: linear-gradient(135deg, #2e86c1, #1a5276); border-radius: 2px; }}
        .filter-row {{ display: flex; gap: 12px; flex-wrap: wrap; align-items: center; margin-bottom: 16px; padding: 12px; background: #f8f9fa; border-radius: 10px; }}
        .filter-row label {{ font-weight: 600; font-size: 13px; color: #555; white-space: nowrap; }}
        .filter-row select {{ padding: 8px 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 13px; background: white; min-width: 180px; }}
        .filter-row select:focus {{ border-color: #2e86c1; outline: none; }}
        .btn-group {{ display: flex; gap: 6px; }}
        .btn-sm {{ padding: 8px 14px; font-size: 12px; background: white; color: #555; border: 2px solid #e0e0e0; border-radius: 8px; cursor: pointer; font-weight: 600; transition: all 0.2s; }}
        .btn-sm:hover {{ background: #e8f4f8; border-color: #2e86c1; }}
        .btn-sm.active {{ background: linear-gradient(135deg, #2e86c1, #1a5276); color: white; border-color: transparent; }}
        .btn-clear {{ padding: 8px 14px; font-size: 12px; background: #fee2e2; color: #dc2626; border: 2px solid #fecaca; border-radius: 8px; cursor: pointer; font-weight: 600; margin-left: auto; }}
        .btn-clear:hover {{ background: #fecaca; }}
        .date-nav {{ display: flex; align-items: center; justify-content: center; gap: 20px; margin-bottom: 16px; }}
        .date-nav .date {{ font-size: 20px; font-weight: 700; color: #1a5276; min-width: 160px; text-align: center; }}
        .btn-nav {{ background: linear-gradient(135deg, #27ae60, #219a52); color: white; border: none; padding: 10px 18px; border-radius: 10px; cursor: pointer; font-size: 18px; font-weight: bold; transition: all 0.2s; }}
        .btn-nav:hover {{ transform: scale(1.05); }}
        .btn-nav:disabled {{ background: #bdc3c7; cursor: not-allowed; transform: none; }}
        .tabs {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }}
        .tab {{ background: #f0f0f0; border: none; padding: 10px 20px; border-radius: 10px; cursor: pointer; font-weight: 600; font-size: 13px; transition: all 0.2s; }}
        .tab:hover {{ background: #e0e0e0; }}
        .tab.active {{ background: linear-gradient(135deg, #2e86c1, #1a5276); color: white; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
        .grid10 {{ display: grid; grid-template-columns: repeat(10, 1fr); gap: 4px; }}
        .cell {{ padding: 8px 4px; text-align: center; border-radius: 8px; font-weight: 600; cursor: pointer; transition: all 0.2s; }}
        .cell:hover {{ transform: scale(1.05); }}
        .cell .n {{ display: block; font-size: 14px; }}
        .cell .v {{ display: block; font-size: 11px; opacity: 0.85; margin-top: 2px; }}
        .cell.selected {{ outline: 3px solid #f39c12; outline-offset: 2px; transform: scale(1.1); z-index: 10; position: relative; }}
        .hot {{ background: linear-gradient(135deg, #e74c3c, #c0392b); color: white; }}
        .warm {{ background: linear-gradient(135deg, #f39c12, #e67e22); color: white; }}
        .normal {{ background: linear-gradient(135deg, #3498db, #2980b9); color: white; }}
        .cool {{ background: linear-gradient(135deg, #9b59b6, #8e44ad); color: white; }}
        .cold {{ background: linear-gradient(135deg, #34495e, #2c3e50); color: white; }}
        .bar-row {{ display: flex; align-items: center; margin-bottom: 6px; cursor: pointer; padding: 2px 0; }}
        .bar-row:hover {{ opacity: 0.85; }}
        .bar-label {{ width: 30px; text-align: right; margin-right: 8px; font-weight: 700; font-size: 12px; }}
        .bar {{ height: 22px; border-radius: 6px; display: flex; align-items: center; padding-left: 8px; color: white; font-size: 11px; font-weight: 600; min-width: 30px; }}
        .predict-box {{ padding: 20px; border-radius: 12px; text-align: center; color: white; }}
        .predict-box h3 {{ font-size: 14px; margin-bottom: 10px; opacity: 0.9; }}
        .predict-box .nums {{ font-size: 28px; font-weight: 800; letter-spacing: 2px; margin: 12px 0; }}
        .predict-box small {{ font-size: 11px; opacity: 0.8; }}
        .predict-today {{ background: linear-gradient(135deg, #2ecc71, #27ae60); }}
        .predict-tomorrow {{ background: linear-gradient(135deg, #9b59b6, #8e44ad); }}
        .predict-main {{ background: linear-gradient(135deg, #e74c3c, #c0392b); }}
        .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
        .table-wrap {{ overflow-x: auto; border: 1px solid #e0e0e0; border-radius: 10px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 8px 6px; text-align: center; border: 1px solid #f0f0f0; font-size: 12px; white-space: nowrap; }}
        th {{ background: linear-gradient(135deg, #2e86c1, #1a5276); color: white; font-size: 11px; }}
        th:first-child {{ background: #1a5276; }}
        td {{ min-width: 70px; }}
        tr:hover {{ background: #e8f4f8; }}
        .sp {{ color: #e74c3c; font-weight: bold; font-size: 14px; }}
        .filter-bar {{ display: flex; gap: 6px; align-items: center; padding: 10px; background: #f8f9fa; border-radius: 8px; margin-top: 12px; flex-wrap: wrap; }}
        .filter-bar .btn-num {{ width: 36px; height: 36px; padding: 0; font-size: 14px; font-weight: 700; border-radius: 8px; border: 2px solid #e0e0e0; background: white; cursor: pointer; transition: all 0.2s; }}
        .filter-bar .btn-num:hover {{ background: #e8f4f8; border-color: #2e86c1; }}
        .filter-bar .btn-num.active {{ background: linear-gradient(135deg, #f39c12, #e67e22); color: white; border-color: transparent; }}
        .filter-bar .btn-type {{ padding: 8px 14px; font-size: 12px; font-weight: 600; border-radius: 8px; border: 2px solid #e0e0e0; background: white; cursor: pointer; transition: all 0.2s; }}
        .filter-bar .btn-type:hover {{ background: #e8f4f8; border-color: #2e86c1; }}
        .filter-bar .btn-type.active {{ background: linear-gradient(135deg, #e74c3c, #c0392b); color: white; border-color: transparent; }}
        footer {{ text-align: center; padding: 20px; color: rgba(255,255,255,0.7); font-size: 12px; }}
        .no-province {{ background: #fff3cd; padding: 40px; border-radius: 12px; text-align: center; color: #856404; font-size: 16px; }}
        .no-province::before {{ content: '⚠️'; font-size: 48px; display: block; margin-bottom: 12px; }}
        @media (max-width: 768px) {{ .two-col {{ grid-template-columns: 1fr; }} .grid10 {{ grid-template-columns: repeat(5, 1fr); }} .filter-row {{ flex-direction: column; align-items: stretch; }} }}
    </style>
</head>
<body>
<div class="container">
    <header>
        <h1>Xổ số Miền Nam (XSMN)</h1>
        <p>{len(provinces)} tỉnh thành | {len(records)} kết quả</p>
    </header>

    <div class="card">
        <h2>Kết quả xổ số</h2>
        <div class="date-nav">
            <button class="btn-nav" id="btnPrev" onclick="prevDay()">&#9664;</button>
            <div class="date" id="currentDate"></div>
            <button class="btn-nav" id="btnNext" onclick="nextDay()">&#9654;</button>
        </div>
        <div class="table-wrap">
            <table id="resultTable">
                <thead id="resultHead"></thead>
                <tbody id="resultBody"></tbody>
            </table>
        </div>
        <div class="filter-bar">
            <button class="btn-type active" onclick="setFilterType('full', this)">Đầy đủ</button>
            <button class="btn-type" onclick="setFilterType('2so', this)">2 số</button>
            <button class="btn-type" onclick="setFilterType('3so', this)">3 số</button>
            <span style="margin: 0 8px; color: #ccc">|</span>
            <button class="btn-num" onclick="filterByNum(0, this)">0</button>
            <button class="btn-num" onclick="filterByNum(1, this)">1</button>
            <button class="btn-num" onclick="filterByNum(2, this)">2</button>
            <button class="btn-num" onclick="filterByNum(3, this)">3</button>
            <button class="btn-num" onclick="filterByNum(4, this)">4</button>
            <button class="btn-num" onclick="filterByNum(5, this)">5</button>
            <button class="btn-num" onclick="filterByNum(6, this)">6</button>
            <button class="btn-num" onclick="filterByNum(7, this)">7</button>
            <button class="btn-num" onclick="filterByNum(8, this)">8</button>
            <button class="btn-num" onclick="filterByNum(9, this)">9</button>
        </div>
    </div>

    <div class="card">
        <h2>Phân tích dự đoán</h2>
        <div class="filter-row">
            <label>Tỉnh:</label>
            <select id="selProvince" onchange="applyFilter()">
            </select>
            <label>Khoảng:</label>
            <div class="btn-group">
                <button class="btn-sm" onclick="quickFilter(30)">30 ngày</button>
                <button class="btn-sm" onclick="quickFilter(90)">3 tháng</button>
                <button class="btn-sm" onclick="quickFilter(180)">6 tháng</button>
                <button class="btn-sm" onclick="quickFilter(365)">1 năm</button>
                <button class="btn-sm active" onclick="quickFilter(0)">Tất cả</button>
            </div>
            <button class="btn-clear" onclick="clearHighlight()">Bỏ chọn</button>
        </div>

    <div class="card">
        <h2>Kết quả xổ số</h2>
        <div class="date-nav">
            <button class="btn-nav" id="btnPrev" onclick="prevDay()">&#9664;</button>
            <div class="date" id="currentDate"></div>
            <button class="btn-nav" id="btnNext" onclick="nextDay()">&#9654;</button>
        </div>
        <div class="table-wrap">
            <table id="resultTable">
                <thead id="resultHead"></thead>
                <tbody id="resultBody"></tbody>
            </table>
        </div>
        <div class="filter-bar">
            <button class="btn-type active" onclick="setFilterType('full', this)">Đầy đủ</button>
            <button class="btn-type" onclick="setFilterType('2so', this)">2 số</button>
            <button class="btn-type" onclick="setFilterType('3so', this)">3 số</button>
            <span style="margin: 0 8px; color: #999">|</span>
            <button class="btn-num" onclick="filterByNum(0, this)">0</button>
            <button class="btn-num" onclick="filterByNum(1, this)">1</button>
            <button class="btn-num" onclick="filterByNum(2, this)">2</button>
            <button class="btn-num" onclick="filterByNum(3, this)">3</button>
            <button class="btn-num" onclick="filterByNum(4, this)">4</button>
            <button class="btn-num" onclick="filterByNum(5, this)">5</button>
            <button class="btn-num" onclick="filterByNum(6, this)">6</button>
            <button class="btn-num" onclick="filterByNum(7, this)">7</button>
            <button class="btn-num" onclick="filterByNum(8, this)">8</button>
            <button class="btn-num" onclick="filterByNum(9, this)">9</button>
        </div>
    </div>

    <div class="card">
        <h2>Phân tích dự đoán</h2>
        <div class="context-info" id="analysisContext"></div>
        <div class="tabs">
            <button class="tab active" onclick="showTab(this, 'freq')">Tần suất</button>
            <button class="tab" onclick="showTab(this, 'overdue')">Lâu chưa ra</button>
            <button class="tab" onclick="showTab(this, 'headtail')">Đầu-Đuôi</button>
            <button class="tab" onclick="showTab(this, 'ml')">AI Dự đoán</button>
        </div>
        <div id="tab-freq" class="tab-content active">
            <div class="grid10" id="freqGrid"></div>
        </div>
        <div id="tab-overdue" class="tab-content">
            <div class="grid10" id="overdueGrid"></div>
        </div>
        <div id="tab-headtail" class="tab-content">
            <div class="two-col">
                <div><h3 style="margin-bottom:10px;color:#1a5276">Đầu (chục)</h3><div id="headChart"></div></div>
                <div><h3 style="margin-bottom:10px;color:#1a5276">Đuôi (đơn vị)</h3><div id="tailChart"></div></div>
            </div>
        </div>
        <div id="tab-ml" class="tab-content">
            <div class="two-col">
                <div><h3 style="margin-bottom:10px;color:#1a5276">Top 20 số cao</h3><div id="mlTop"></div></div>
                <div><h3 style="margin-bottom:10px;color:#1a5276">Top 20 số thấp</h3><div id="mlBottom"></div></div>
            </div>
            <div class="two-col" style="margin-top:15px">
                <div class="ml-box" style="background:linear-gradient(135deg,#2ecc71,#27ae60)">
                    <h3>Hôm nay</h3>
                    <div class="nums" id="predToday"></div>
                    <small id="predTodayInfo"></small>
                </div>
                <div class="ml-box" style="background:linear-gradient(135deg,#9b59b6,#8e44ad)">
                    <h3>Ngày mai</h3>
                    <div class="nums" id="predTomorrow"></div>
                    <small id="predTomorrowInfo"></small>
                </div>
            </div>
            <div class="ml-box" style="margin-top:15px">
                <h3>Gợi ý con số may mắn</h3>
                <div class="nums" id="mlPred"></div>
                <small>Dựa trên phân tích tần suất + độ trễ</small>
            </div>
        </div>
    </div>

    <footer>Dữ liệu từ xoso.com.vn</footer>
</div>

<script>
const DATA = {data_json};
const PROVINCES = {province_json};
const ALL_DATES = [...new Set(DATA.map(d => d.date))].sort();

let filtered = [];
let curProvince = '';
let curDateIdx = ALL_DATES.length - 1;
let selectedNum = null;
let filterDigit = null;
let filterType = 'full';

// Init province select
const sel = document.getElementById('selProvince');
PROVINCES.forEach(p => {{ const o = document.createElement('option'); o.value = p.code; o.textContent = p.name; sel.appendChild(o); }});
sel.value = PROVINCES[0].code;
curProvince = PROVINCES[0].code;

function fmt(n) {{ return String(n).padStart(6, '0'); }}
function fmtD(s) {{ const [y,m,d] = s.split('-'); return d+'/'+m+'/'+y; }}

function formatByType(val, type) {{
    if (!val && val !== 0) return '-';
    const s = String(val);
    if (type === '2so') return s.slice(-2);
    if (type === '3so') return s.slice(-3);
    return s;
}}

function applyFilter() {{
    curProvince = document.getElementById('selProvince').value;
    if (!curProvince) {{
        filtered = [];
    }} else {{
        filtered = DATA.filter(d => d.province === curProvince);
    }}
    const filteredDates = [...new Set(filtered.map(d => d.date))].sort();
    curDateIdx = filteredDates.length - 1;
    renderResultTable();
    renderAnalysis();
}}

function quickFilter(days) {{
    document.querySelectorAll('.btn-sm').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    if (days === 0) {{
        filtered = DATA.filter(d => d.province === curProvince);
    }} else {{
        const latest = ALL_DATES[ALL_DATES.length - 1];
        const cutoff = new Date(latest);
        cutoff.setDate(cutoff.getDate() - days);
        const cutoffStr = cutoff.toISOString().split('T')[0];
        const base = curProvince === 'all' ? DATA : DATA.filter(d => d.province === curProvince);
        filtered = base.filter(d => d.date >= cutoffStr);
    }}
    renderAnalysis();
}}

function prevDay() {{
    if (curDateIdx > 0) {{ curDateIdx--; renderResultTable(); }}
}}

function nextDay() {{
    if (curDateIdx < ALL_DATES.length - 1) {{ curDateIdx++; renderResultTable(); }}
}}

function selectNumber(num) {{
    selectedNum = selectedNum === num ? null : num;
    renderResultTable();
    renderAnalysis();
}}

function clearHighlight() {{
    selectedNum = null;
    filterDigit = null;
    document.querySelectorAll('.btn-num').forEach(b => b.classList.remove('active'));
    renderResultTable();
    renderAnalysis();
}}

function filterByNum(num, el) {{
    document.querySelectorAll('.btn-num').forEach(b => b.classList.remove('active'));
    if (filterDigit === num) {{
        filterDigit = null;
    }} else {{
        filterDigit = num;
        el.classList.add('active');
    }}
    renderResultTable();
}}

function setFilterType(type, el) {{
    document.querySelectorAll('.btn-type').forEach(b => b.classList.remove('active'));
    el.classList.add('active');
    filterType = type;
    renderResultTable();
}}

function renderResultTable() {{
    const date = ALL_DATES[curDateIdx];
    document.getElementById('currentDate').textContent = fmtD(date);
    document.getElementById('btnPrev').disabled = curDateIdx === 0;
    document.getElementById('btnNext').disabled = curDateIdx === ALL_DATES.length - 1;

    if (!curProvince) {{
        document.getElementById('resultHead').innerHTML = '';
        document.getElementById('resultBody').innerHTML = '<tr><td colspan="10" style="padding:40px;color:#999">Vui lòng chọn tỉnh để xem kết quả</td></tr>';
        return;
    }}

    let dayData = DATA.filter(d => d.date === date && d.province === curProvince);
    const provCodes = dayData.map(d => d.province);

    let headerHtml = '<tr><th>Giải</th>';
    provCodes.forEach(code => {{
        const name = PROVINCES.find(p => p.code === code)?.name || code;
        headerHtml += `<th>${{name}}</th>`;
    }});
    headerHtml += '</tr>';
    document.getElementById('resultHead').innerHTML = headerHtml;

    const prizeRows = [
        ['Tám', 'prize8', false],
        ['Bảy', 'prize7', false],
        ['Sáu', 'prize6', true, 3],
        ['Năm', 'prize5', false],
        ['Tư', 'prize4', true, 7],
        ['Ba', 'prize3', true, 2],
        ['Nhì', 'prize2', false],
        ['Nhất', 'prize1', false],
        ['Đặc biệt', 'special', false],
    ];

    let bodyHtml = '';
    let rowIdx = 0;
    prizeRows.forEach(([label, field, isMulti, count]) => {{
        if (isMulti) {{
            let rowsAdded = 0;
            for (let i = 1; i <= count; i++) {{
                // Check if this row has any data
                const hasData = provCodes.some(code => {{
                    const d = dayData.find(x => x.province === code);
                    const val = d ? d[field + '_' + i] : null;
                    return val && val !== 0 && val !== '' && val !== '0';
                }});
                if (!hasData) continue;

                bodyHtml += '<tr>';
                bodyHtml += rowsAdded === 0 ? `<td rowspan="${{count}}" style="background:#f8f9fa;font-weight:600">Giải ${{label}}</td>` : '';
                const rowClass = rowIdx % 2 === 0 ? 'row-even' : 'row-odd';
                provCodes.forEach(code => {{
                    const d = dayData.find(x => x.province === code);
                    const val = d ? d[field + '_' + i] || 0 : 0;
                    const displayVal = formatByType(val, filterType);
                    const isHighlight = filterDigit !== null && displayVal.endsWith(String(filterDigit));
                    const cls = (field === 'special' ? 'sp' : '') + (isHighlight ? ' num-highlight' : '');
                    bodyHtml += `<td class="${{cls}}">${{val ? displayVal : '-'}}</td>`;
                }});
                bodyHtml += '</tr>';
                rowsAdded++;
                rowIdx++;
            }}
        }} else {{
            // Check if this row has any data
            const hasData = provCodes.some(code => {{
                const d = dayData.find(x => x.province === code);
                const val = d ? d[field] : null;
                return val && val !== 0 && val !== '' && val !== '0';
            }});
            if (!hasData) return;

            bodyHtml += '<tr>';
            const rowClass = rowIdx % 2 === 0 ? 'row-even' : 'row-odd';
            bodyHtml += `<td class="${{rowClass}}" style="font-weight:600">Giải ${{label}}</td>`;
            provCodes.forEach(code => {{
                const d = dayData.find(x => x.province === code);
                const val = d ? d[field] || 0 : 0;
                const displayVal = formatByType(val, filterType);
                const isHighlight = filterDigit !== null && displayVal.endsWith(String(filterDigit));
                const cls = (field === 'special' ? 'sp' : '') + (isHighlight ? ' num-highlight' : '');
                bodyHtml += `<td class="${{cls}}">${{val ? displayVal : '-'}}</td>`;
            }});
            bodyHtml += '</tr>';
            rowIdx++;
        }}
    }});

    document.getElementById('resultBody').innerHTML = bodyHtml;
}}

function getNumbers(data) {{
    const nums = [];
    data.forEach(d => {{ for (let k in d) {{
        if (k.startsWith('prize') || k === 'special') {{
            const v = d[k];
            if (v !== null && v !== undefined && v !== 0 && v !== '') {{
                const s = String(v);
                const last2 = parseInt(s.slice(-2));
                if (!isNaN(last2)) nums.push(last2);
            }}
        }}
    }} }});
    return nums;
}}

function updateAnalysisContext() {{
    const provName = curProvince === 'all' ? 'Tất cả tỉnh' : PROVINCES.find(p => p.code === curProvince)?.name || curProvince;
    const start = filtered.length > 0 ? filtered[0].date : '';
    const end = filtered.length > 0 ? filtered[filtered.length - 1].date : '';
    let ctx = `Đang phân tích: <b>${{provName}}</b> | ${{fmtD(start)}} đến ${{fmtD(end)}} | <b>${{filtered.length}}</b> kết quả`;
    if (selectedNum !== null) {{
        ctx += ` | Đang chọn số: <span class="selected-num">${{String(selectedNum).padStart(2, '0')}}</span>`;
    }}
    document.getElementById('analysisContext').innerHTML = ctx;
}}

function renderFreq() {{
    const nums = getNumbers(filtered);
    const cnt = {{}}; for (let i=0;i<100;i++) cnt[i]=0;
    nums.forEach(n => cnt[n]++);
    const mx = Math.max(...Object.values(cnt));
    const sorted = Object.entries(cnt).sort((a,b) => b[1]-a[1]);
    document.getElementById('freqGrid').innerHTML = sorted.map(([n,c]) => {{
        const p = mx>0 ? c/mx*100 : 0;
        const cls = p>80?'hot':p>60?'warm':p>40?'normal':p>20?'cool':'cold';
        const sel = selectedNum === parseInt(n) ? ' selected' : '';
        return `<div class="cell ${{cls}}${{sel}}" onclick="selectNumber(${{n}})" title="${{c}} lần"><span class="n">${{String(n).padStart(2,'0')}}</span><span class="v">${{c}}</span></div>`;
    }}).join('');
}}

function renderOverdue() {{
    const ls = {{}}; for(let i=0;i<100;i++) ls[i]=-1;
    filtered.forEach((d,idx) => {{ for(let k in d) {{ if(k.startsWith('prize')||k==='special') ls[d[k]%100]=idx; }} }});
    const od = Object.entries(ls).map(([n,i]) => [parseInt(n), i===-1?filtered.length:filtered.length-1-i]).sort((a,b)=>b[1]-a[1]);
    const mx = Math.max(...od.map(x=>x[1]));
    document.getElementById('overdueGrid').innerHTML = od.map(([n,d]) => {{
        const p = mx>0 ? d/mx*100 : 0;
        const cls = p>80?'hot':p>60?'warm':p>30?'normal':'cool';
        const sel = selectedNum === n ? ' selected' : '';
        return `<div class="cell ${{cls}}${{sel}}" onclick="selectNumber(${{n}})" title="${{d}} ngày"><span class="n">${{String(n).padStart(2,'0')}}</span><span class="v">${{d}}d</span></div>`;
    }}).join('');
}}

function renderHeadTail() {{
    const nums = getNumbers(filtered);
    const hc = {{}}, tc = {{}}; for(let i=0;i<10;i++) {{hc[i]=0;tc[i]=0;}}
    nums.forEach(n => {{ hc[Math.floor(n/10)]++; tc[n%10]++; }});
    const mxH = Math.max(...Object.values(hc)), mxT = Math.max(...Object.values(tc));
    document.getElementById('headChart').innerHTML = Object.entries(hc).sort((a,b)=>b[1]-a[1]).map(([h,c]) => {{
        const p = mxH>0?c/mxH*100:0;
        return `<div class="bar-row"><div class="bar-label">${{h}}</div><div class="bar" style="width:${{p}}%;background:hsl(${{200-p}},70%,45%)">${{c}}</div></div>`;
    }}).join('');
    document.getElementById('tailChart').innerHTML = Object.entries(tc).sort((a,b)=>b[1]-a[1]).map(([t,c]) => {{
        const p = mxT>0?c/mxT*100:0;
        return `<div class="bar-row"><div class="bar-label">${{t}}</div><div class="bar" style="width:${{p}}%;background:hsl(${{200-p}},70%,45%)">${{c}}</div></div>`;
    }}).join('');
}}

function renderML() {{
    const nums = getNumbers(filtered);
    const freq = {{}}, ls = {{}}; for(let i=0;i<100;i++) {{freq[i]=0;ls[i]=-1;}}
    filtered.forEach((d,idx) => {{ for(let k in d) {{ if(k.startsWith('prize')||k==='special') {{ const n=d[k]%100; freq[n]++; ls[n]=idx; }} }} }});
    const total = filtered.length;
    const scores = {{}};
    for(let i=0;i<100;i++) {{
        const fs = freq[i]/(total*0.2);
        const od = total-1-(ls[i]===-1?0:ls[i]);
        const os = Math.min(od/50,1);
        scores[i] = fs*0.5+os*0.5;
    }}
    const sorted = Object.entries(scores).sort((a,b)=>b[1]-a[1]);
    const mx = sorted[0][1];
    document.getElementById('mlTop').innerHTML = sorted.slice(0,20).map(([n,s]) => {{
        const p = s/mx*100;
        const sel = selectedNum === parseInt(n) ? ' style="outline:2px solid #f39c12"' : '';
        return `<div class="bar-row"${{sel}} onclick="selectNumber(${{n}})"><div class="bar-label">${{n}}</div><div class="bar" style="width:${{p}}%;background:hsl(${{120-p}},70%,45%)">${{(s*100).toFixed(1)}}%</div></div>`;
    }}).join('');
    document.getElementById('mlBottom').innerHTML = sorted.slice(-20).reverse().map(([n,s]) => {{
        const p = s/mx*100;
        const sel = selectedNum === parseInt(n) ? ' style="outline:2px solid #f39c12"' : '';
        return `<div class="bar-row"${{sel}} onclick="selectNumber(${{n}})"><div class="bar-label">${{n}}</div><div class="bar" style="width:${{p}}%;background:hsl(${{240-p}},50%,60%)">${{(s*100).toFixed(1)}}%</div></div>`;
    }}).join('');

    // Predictions for today and tomorrow
    const latestDate = ALL_DATES[ALL_DATES.length - 1];
    const today = new Date().toISOString().split('T')[0];
    const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0];

    // Today prediction: top 6 from overdue (numbers not appeared longest)
    const overdueNums = Object.entries(ls).map(([n,i]) => [parseInt(n), i===-1?total:total-1-i]).sort((a,b)=>b[1]-a[1]);
    const todayPred = overdueNums.slice(0,6).map(([n])=>String(n).padStart(2,'0')).join(' - ');
    const todayInfo = latestDate === today ? 'Dựa trên dữ liệu mới nhất' : 'Dữ liệu đến ' + fmtD(latestDate);
    document.getElementById('predToday').textContent = todayPred;
    document.getElementById('predTodayInfo').textContent = todayInfo;

    // Tomorrow prediction: top 6 from combined score
    const tomorrowPred = sorted.slice(0,6).map(([n])=>String(n).padStart(2,'0')).join(' - ');
    const tomorrowInfo = 'Phân tích tần suất + độ trễ ' + total + ' kỳ';
    document.getElementById('predTomorrow').textContent = tomorrowPred;
    document.getElementById('predTomorrowInfo').textContent = tomorrowInfo;

    document.getElementById('mlPred').textContent = sorted.slice(0,6).map(([n])=>String(n).padStart(2,'0')).join(' - ');
}}

function showTab(el, id) {{
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    el.classList.add('active');
    document.getElementById('tab-'+id).classList.add('active');
}}

function renderAnalysis() {{
    if (filtered.length === 0) {{
        document.getElementById('analysisContext').innerHTML = 'Vui lòng chọn tỉnh để xem phân tích';
        document.getElementById('freqGrid').innerHTML = '';
        document.getElementById('overdueGrid').innerHTML = '';
        document.getElementById('headChart').innerHTML = '';
        document.getElementById('tailChart').innerHTML = '';
        document.getElementById('mlTop').innerHTML = '';
        document.getElementById('mlBottom').innerHTML = '';
        document.getElementById('predToday').textContent = '--';
        document.getElementById('predTodayInfo').textContent = 'Chưa có dữ liệu';
        document.getElementById('predTomorrow').textContent = '--';
        document.getElementById('predTomorrowInfo').textContent = 'Chưa có dữ liệu';
        document.getElementById('mlPred').textContent = '--';
        return;
    }}
    updateAnalysisContext();
    renderFreq();
    renderOverdue();
    renderHeadTail();
    renderML();
}}

// Init
applyFilter();
</script>
</body>
</html>'''

    Path('readme.html').write_text(html, encoding='utf-8')
    print('Generated: readme.html')


def generate_readme_md(lottery: XSMNLottery):
    """Generate README.md with XSMN data in Markdown format."""
    import json
    from datetime import datetime

    data = lottery.get_raw_data()
    if data.empty:
        print('No data for README.md')
        return

    # Get latest date
    latest_date = data['date'].max()
    latest_data = data[data['date'] == latest_date]

    # Get unique dates count
    total_dates = data['date'].nunique()
    total_provinces = data['province'].nunique()

    # Get latest results for each province
    latest_results = []
    for _, row in latest_data.iterrows():
        prov = row['province']
        province_name = PROVINCE_NAMES.get(prov, prov)
        latest_results.append({
            'province': province_name,
            'special': f"{int(row['special']):06d}",
            'prize1': f"{int(row['prize1']):05d}",
        })

    # Get frequency analysis (last 30 days)
    from datetime import timedelta
    recent_data = data[data['date'] >= latest_date - timedelta(days=30)]
    all_numbers = []
    for col in ['special', 'prize1', 'prize2', 'prize3_1', 'prize3_2',
                'prize4_1', 'prize4_2', 'prize4_3', 'prize4_4',
                'prize6_1', 'prize6_2', 'prize6_3']:
        if col in recent_data.columns:
            vals = recent_data[col].dropna()
            all_numbers.extend([f"{int(v):02d}"[-2:] for v in vals])

    from collections import Counter
    freq = Counter(all_numbers)
    top10 = freq.most_common(10)

    # Build README.md
    md = f"""# Xổ số Miền Nam (XSMN) Analysis

> Auto-updated daily by GitHub Actions

## Thống kê

- **Số tỉnh thành:** {total_provinces}
- **Số ngày quay:** {total_dates}
- **Dữ liệu mới nhất:** {latest_date.strftime('%d/%m/%Y')}

## Kết quả mới nhất ({latest_date.strftime('%d/%m/%Y')})

| Tỉnh | Giải Đặc Biệt | Giải Nhất |
|------|----------------|-----------|
"""
    for r in sorted(latest_results, key=lambda x: x['province']):
        md += f"| {r['province']} | **{r['special']}** | {r['prize1']} |\n"

    md += f"""
## Top 10 số xuất hiện nhiều nhất (30 ngày gần đây)

| Số | Tần suất |
|----|----------|
"""
    for num, count in top10:
        md += f"| {num} | {count} |\n"

    md += f"""
## Xem chi tiết

- **Bảng tương tác:** [readme.html](readme.html) (mở trực tiếp trên trình duyệt)
- **Dữ liệu gốc:** [data/xsmn.json](data/xsmn.json)

## Tự chạy

```bash
# Cập nhật dữ liệu
uv run src/update_xsmn.py

# Với ngày cụ thể
uv run src/update_xsmn.py --from-date 2026-01-01
```

---
*Dữ liệu từ xoso.com.vn | Cập nhật tự động bởi GitHub Actions*
"""
    Path('README.md').write_text(md, encoding='utf-8')
    print('Generated: README.md')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Update XSMN lottery data')
    parser.add_argument('--from-date', help='Fetch from date (YYYY-MM-DD)', default=None)
    parser.add_argument('--refetch', action='store_true', help='Delete old data and re-fetch')
    args = parser.parse_args()

    if args.refetch:
        import os
        for f in ['data/xsmn.json', 'data/xsmn.csv', 'data/xsmn.parquet']:
            if os.path.exists(f):
                os.remove(f)
                print(f'Deleted: {f}')

    from_date = None
    if args.from_date:
        from datetime import date as dt_date
        from_date = dt_date.fromisoformat(args.from_date)

    print('=== Update XSMN ===')
    lottery = fetch_data(from_date=from_date)
    print('\n=== Generate HTML ===')
    generate_html(lottery)
    print('\n=== Generate README.md ===')
    generate_readme_md(lottery)
    print('Done!')
