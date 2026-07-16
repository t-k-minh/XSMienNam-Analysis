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
        body {{ font-family: 'Segoe UI', sans-serif; background: #f5f5f5; color: #333; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        header {{ background: linear-gradient(135deg, #1a5276, #2e86c1); color: white; padding: 25px; border-radius: 10px; margin-bottom: 20px; text-align: center; }}
        header h1 {{ font-size: 26px; }}
        .controls {{ background: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .row {{ display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin-bottom: 10px; }}
        .row:last-child {{ margin-bottom: 0; }}
        label {{ font-weight: 600; font-size: 13px; color: #555; }}
        input, select {{ padding: 8px; border: 1px solid #ddd; border-radius: 5px; font-size: 13px; }}
        .btn {{ background: #2e86c1; color: white; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer; font-size: 13px; font-weight: 600; }}
        .btn:hover {{ background: #1a5276; }}
        .btn-sm {{ padding: 6px 12px; font-size: 12px; background: #ecf0f1; color: #555; border: 1px solid #ddd; cursor: pointer; }}
        .btn-sm:hover {{ background: #d5dbdb; }}
        .btn-sm.active {{ background: #2e86c1; color: white; border-color: #2e86c1; }}
        .btn-nav {{ background: #27ae60; color: white; border: none; padding: 8px 14px; border-radius: 5px; cursor: pointer; font-size: 16px; font-weight: bold; }}
        .btn-nav:hover {{ background: #219a52; }}
        .btn-nav:disabled {{ background: #bdc3c7; cursor: not-allowed; }}
        .card {{ background: white; border-radius: 10px; padding: 20px; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .card h2 {{ color: #1a5276; margin-bottom: 12px; font-size: 18px; border-bottom: 2px solid #eee; padding-bottom: 8px; }}
        .context-info {{ background: #fff3cd; padding: 8px 12px; border-radius: 6px; margin-bottom: 12px; font-size: 12px; color: #856404; border-left: 4px solid #ffc107; }}
        .date-nav {{ display: flex; align-items: center; gap: 15px; margin-bottom: 15px; }}
        .date-nav .date {{ font-size: 18px; font-weight: 600; color: #1a5276; min-width: 150px; text-align: center; }}
        .tabs {{ display: flex; gap: 5px; flex-wrap: wrap; margin-bottom: 15px; }}
        .tab {{ background: #ecf0f1; border: 1px solid #ddd; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 12px; }}
        .tab:hover {{ background: #d5dbdb; }}
        .tab.active {{ background: #2e86c1; color: white; border-color: #2e86c1; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
        .grid10 {{ display: grid; grid-template-columns: repeat(10, 1fr); gap: 3px; }}
        .cell {{ padding: 6px 2px; text-align: center; border-radius: 3px; font-size: 11px; font-weight: 600; cursor: pointer; transition: all 0.2s; }}
        .cell .n {{ display: block; font-size: 12px; }}
        .cell .v {{ display: block; font-size: 10px; opacity: 0.8; }}
        .cell.selected {{ outline: 3px solid #f39c12; outline-offset: 1px; transform: scale(1.1); z-index: 10; position: relative; }}
        .hot {{ background: #e74c3c; color: white; }}
        .warm {{ background: #f39c12; color: white; }}
        .normal {{ background: #3498db; color: white; }}
        .cool {{ background: #9b59b6; color: white; }}
        .cold {{ background: #34495e; color: white; }}
        .bar-row {{ display: flex; align-items: center; margin-bottom: 4px; cursor: pointer; }}
        .bar-row:hover {{ opacity: 0.8; }}
        .bar-label {{ width: 28px; text-align: right; margin-right: 6px; font-weight: 600; font-size: 11px; }}
        .bar {{ height: 18px; border-radius: 3px; display: flex; align-items: center; padding-left: 6px; color: white; font-size: 10px; font-weight: 600; }}
        .ml-box {{ background: linear-gradient(135deg, #e74c3c, #c0392b); color: white; padding: 15px; border-radius: 8px; text-align: center; margin-top: 12px; }}
        .ml-box .nums {{ font-size: 24px; font-weight: bold; letter-spacing: 3px; margin: 8px 0; }}
        .ml-box small {{ font-size: 11px; opacity: 0.8; }}
        .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
        .table-wrap {{ overflow-x: auto; border: 1px solid #ddd; border-radius: 6px; max-width: 800px; margin: 0 auto; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 5px 3px; text-align: center; border: 1px solid #eee; font-size: 12px; white-space: nowrap; }}
        th {{ background: #2e86c1; color: white; font-size: 11px; }}
        th:first-child {{ background: #1a5276; width: 50px; }}
        td {{ min-width: 60px; }}
        tr:hover {{ background: #e8f4f8; }}
        .row-even {{ background: #f8f9fa; }}
        .row-odd {{ background: white; }}
        .sp {{ color: #e74c3c; font-weight: bold; font-size: 15px; }}
        td.highlight {{ background: #fff3cd !important; color: #856404; font-weight: bold; }}
        .num-highlight {{ background: #ff9800 !important; color: white !important; font-weight: bold; border-radius: 3px; padding: 0 2px; }}
        .selected-num {{ background: #f39c12; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold; margin-left: 5px; }}
        .filter-bar {{ display: flex; gap: 5px; align-items: center; padding: 10px; background: #f8f9fa; border-radius: 6px; margin-top: 10px; flex-wrap: wrap; }}
        .filter-bar .btn-num {{ width: 32px; height: 32px; padding: 0; font-size: 14px; font-weight: 700; border-radius: 4px; border: 2px solid #ddd; background: white; cursor: pointer; }}
        .filter-bar .btn-num:hover {{ background: #e8f4f8; }}
        .filter-bar .btn-num.active {{ background: #ff9800; color: white; border-color: #ff9800; }}
        .filter-bar .btn-type {{ padding: 6px 12px; font-size: 12px; font-weight: 600; border-radius: 4px; border: 1px solid #ddd; background: white; cursor: pointer; }}
        .filter-bar .btn-type:hover {{ background: #e8f4f8; }}
        .filter-bar .btn-type.active {{ background: #e74c3c; color: white; border-color: #e74c3c; }}
        footer {{ text-align: center; padding: 15px; color: #999; font-size: 12px; }}
        @media (max-width: 768px) {{ .two-col {{ grid-template-columns: 1fr; }} .grid10 {{ grid-template-columns: repeat(5, 1fr); }} }}
    </style>
</head>
<body>
<div class="container">
    <header>
        <h1>Xổ số Miền Nam (XSMN)</h1>
        <p>{len(provinces)} tỉnh thành | {len(records)} kết quả</p>
    </header>

    <div class="controls">
        <div class="row">
            <label>Tỉnh:</label>
            <select id="selProvince" onchange="applyFilter()">
                <option value="all">Tất cả tỉnh</option>
            </select>
            <label style="margin-left:15px">Phân tích khoảng:</label>
            <button class="btn-sm" onclick="quickFilter(30)">30 ngày</button>
            <button class="btn-sm" onclick="quickFilter(90)">3 tháng</button>
            <button class="btn-sm" onclick="quickFilter(180)">6 tháng</button>
            <button class="btn-sm" onclick="quickFilter(365)">1 năm</button>
            <button class="btn-sm active" onclick="quickFilter(0)">Tất cả</button>
            <button class="btn" onclick="clearHighlight()" style="margin-left:auto;background:#e74c3c">Bỏ chọn số</button>
        </div>
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
            <div class="ml-box">
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

let filtered = [...DATA];
let curProvince = 'all';
let curDateIdx = ALL_DATES.length - 1;
let selectedNum = null;
let filterDigit = null;
let filterType = 'full'; // 'full', '2so', '3so'

// Init province select
const sel = document.getElementById('selProvince');
PROVINCES.forEach(p => {{ const o = document.createElement('option'); o.value = p.code; o.textContent = p.name; sel.appendChild(o); }});

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
    filtered = curProvince === 'all' ? [...DATA] : DATA.filter(d => d.province === curProvince);
    const filteredDates = [...new Set(filtered.map(d => d.date))].sort();
    curDateIdx = filteredDates.length - 1;
    renderResultTable();
    renderAnalysis();
}}

function quickFilter(days) {{
    document.querySelectorAll('.btn-sm').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    if (days === 0) {{
        filtered = curProvince === 'all' ? [...DATA] : DATA.filter(d => d.province === curProvince);
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

    let dayData = DATA.filter(d => d.date === date);
    if (curProvince !== 'all') {{
        dayData = dayData.filter(d => d.province === curProvince);
    }}
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
    document.getElementById('mlPred').textContent = sorted.slice(0,6).map(([n])=>String(n).padStart(2,'0')).join(' - ');
}}

function showTab(el, id) {{
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    el.classList.add('active');
    document.getElementById('tab-'+id).classList.add('active');
}}

function renderAnalysis() {{ updateAnalysisContext(); renderFreq(); renderOverdue(); renderHeadTail(); renderML(); }}

// Init
renderResultTable();
renderAnalysis();
</script>
</body>
</html>'''

    Path('readme.html').write_text(html, encoding='utf-8')
    print('Generated: readme.html')


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
    print('Done!')
