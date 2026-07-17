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

    html = f'''<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XSMN - Phân tích</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; color: #333; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        header {{ background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); padding: 30px; border-radius: 16px; margin-bottom: 20px; text-align: center; box-shadow: 0 8px 32px rgba(0,0,0,0.1); }}
        header h1 {{ font-size: 28px; color: #1a5276; margin-bottom: 5px; }}
        header p {{ color: #666; font-size: 14px; }}
        .card {{ background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); border-radius: 16px; padding: 24px; margin-bottom: 16px; box-shadow: 0 8px 32px rgba(0,0,0,0.08); }}
        .card h2 {{ color: #1a5276; margin-bottom: 16px; font-size: 18px; display: flex; align-items: center; gap: 8px; }}
        .card h2::before {{ content: ''; width: 4px; height: 20px; background: linear-gradient(135deg, #2e86c1, #1a5276); border-radius: 2px; }}
        .date-nav {{ display: flex; align-items: center; justify-content: center; gap: 20px; margin-bottom: 16px; }}
        .date-nav .date {{ font-size: 20px; font-weight: 700; color: #1a5276; min-width: 160px; text-align: center; }}
        .btn-nav {{ background: linear-gradient(135deg, #27ae60, #219a52); color: white; border: none; padding: 10px 18px; border-radius: 10px; cursor: pointer; font-size: 18px; font-weight: bold; transition: all 0.2s; }}
        .btn-nav:hover {{ transform: scale(1.05); }}
        .btn-nav:disabled {{ background: #bdc3c7; cursor: not-allowed; transform: none; }}
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
        .filter-bar .btn-clear {{ padding: 8px 14px; font-size: 12px; background: #fee2e2; color: #dc2626; border: 2px solid #fecaca; border-radius: 8px; cursor: pointer; font-weight: 600; margin-left: auto; }}
        .filter-bar .btn-clear:hover {{ background: #fecaca; }}
        .num-highlight {{ background: linear-gradient(135deg, #f39c12, #e67e22) !important; color: white !important; font-weight: bold; border-radius: 4px; }}
        .prov-info {{ background: linear-gradient(135deg, #d4edda, #c3e6cb); color: #155724; border-left: 4px solid #28a745; margin-bottom: 16px; padding: 12px; border-radius: 8px; font-size: 13px; }}
        .prov-info b {{ color: #0d3320; }}
        .three-col {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }}
        .prov-card {{ background: white; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border-top: 4px solid #2e86c1; }}
        .prov-card h3 {{ color: #1a5276; font-size: 15px; margin-bottom: 12px; text-align: center; }}
        .prov-card h4 {{ color: #555; font-size: 12px; margin: 12px 0 6px; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #eee; padding-bottom: 4px; }}
        .predict-box {{ padding: 12px; border-radius: 8px; text-align: center; color: white; margin-bottom: 8px; }}
        .predict-box .nums {{ font-size: 18px; font-weight: 800; letter-spacing: 1px; }}
        .predict-box small {{ font-size: 10px; opacity: 0.85; }}
        .predict-main {{ background: linear-gradient(135deg, #e74c3c, #c0392b); }}
        .grid10 {{ display: grid; grid-template-columns: repeat(10, 1fr); gap: 2px; }}
        .cell {{ padding: 4px 2px; text-align: center; border-radius: 4px; font-weight: 600; font-size: 10px; cursor: pointer; transition: all 0.15s; }}
        .cell:hover {{ transform: scale(1.08); }}
        .cell .n {{ display: block; font-size: 11px; }}
        .cell .v {{ display: block; font-size: 9px; opacity: 0.85; }}
        .cell.selected {{ outline: 2px solid #f39c12; outline-offset: 1px; transform: scale(1.1); z-index: 10; position: relative; }}
        .hot {{ background: linear-gradient(135deg, #e74c3c, #c0392b); color: white; }}
        .warm {{ background: linear-gradient(135deg, #f39c12, #e67e22); color: white; }}
        .normal {{ background: linear-gradient(135deg, #3498db, #2980b9); color: white; }}
        .cool {{ background: linear-gradient(135deg, #9b59b6, #8e44ad); color: white; }}
        .cold {{ background: linear-gradient(135deg, #34495e, #2c3e50); color: white; }}
        .bar-row {{ display: flex; align-items: center; margin-bottom: 3px; cursor: pointer; }}
        .bar-row:hover {{ opacity: 0.85; }}
        .bar-label {{ width: 20px; text-align: right; margin-right: 4px; font-weight: 700; font-size: 10px; }}
        .bar {{ height: 14px; border-radius: 3px; display: flex; align-items: center; padding-left: 4px; color: white; font-size: 9px; font-weight: 600; min-width: 16px; }}
        .headtail-wrap {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
        footer {{ text-align: center; padding: 20px; color: rgba(255,255,255,0.7); font-size: 12px; }}
        @media (max-width: 1024px) {{ .three-col {{ grid-template-columns: 1fr; }} }}
        @media (max-width: 768px) {{ .grid10 {{ grid-template-columns: repeat(5, 1fr); }} }}
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
            <button class="btn-nav" id="btnPrev" onclick="prevResultDay()">&#9664;</button>
            <div class="date" id="resultDate"></div>
            <button class="btn-nav" id="btnNext" onclick="nextResultDay()">&#9654;</button>
        </div>
        <div class="table-wrap">
            <table>
                <thead id="resultHead"></thead>
                <tbody id="resultBody"></tbody>
            </table>
        </div>
        <div class="filter-bar" id="resultFilter">
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
            <button class="btn-clear" onclick="clearHighlight()">Bỏ chọn</button>
        </div>
    </div>

    <div class="card">
        <h2>Phân tích dự đoán</h2>
        <div class="date-nav">
            <button class="btn-nav" onclick="prevAnalysisDay()">&#9664;</button>
            <div class="date" id="analysisDate"></div>
            <button class="btn-nav" onclick="nextAnalysisDay()">&#9654;</button>
        </div>
        <div class="prov-info" id="todayProvinces"></div>

        <!-- HÔM NAY -->
        <div id="predTodaySection"></div>

        <!-- NGÀY MAI -->
        <div id="predTomorrowSection" style="margin-top:20px"></div>
    </div>

    <footer>Dữ liệu từ xoso.com.vn | Cập nhật tự động bởi GitHub Actions</footer>
</div>

<script>
const DATA = {data_json};
const ALL_DATES = [...new Set(DATA.map(d => d.date))].sort();

let resultDateIdx = ALL_DATES.length - 1;
let analysisDateIdx = ALL_DATES.length - 1;
let filterType = 'full';
let filterDigit = null;
let selectedNum = null;

function fmtD(s) {{ const [y,m,d] = s.split('-'); return d+'/'+m+'/'+y; }}
function formatByType(val, type) {{
    if (!val && val !== 0) return '-';
    const s = String(val);
    if (type === '2so') return s.slice(-2);
    if (type === '3so') return s.slice(-3);
    return s;
}}
function getNumbers(data) {{
    const nums = [];
    data.forEach(d => {{ for (let k in d) {{
        if (k.startsWith('prize') || k === 'special') {{
            const v = d[k];
            if (v !== null && v !== undefined && v !== 0 && v !== '') {{
                const last2 = parseInt(String(v).slice(-2));
                if (!isNaN(last2)) nums.push(last2);
            }}
        }}
    }} }});
    return nums;
}}
function calcScores(data) {{
    const nums = getNumbers(data);
    const dates = [...new Set(data.map(d => d.date))].sort();
    const total = dates.length;
    const freq = {{}}, ls = {{}}; for(let i=0;i<100;i++) {{freq[i]=0;ls[i]=-1;}}
    data.forEach((d,idx) => {{ for(let k in d) {{ if(k.startsWith('prize')||k==='special') {{ const n=d[k]%100; freq[n]++; ls[n]=idx; }} }} }});
    const scores = {{}};
    for(let i=0;i<100;i++) {{
        const fs = freq[i]/(total*0.2);
        const od = total-1-(ls[i]===-1?0:ls[i]);
        const os = Math.min(od/50,1);
        scores[i] = fs*0.5+os*0.5;
    }}
    const sorted = Object.entries(scores).sort((a,b)=>b[1]-a[1]);
    const overdue = Object.entries(ls).map(([n,i]) => [parseInt(n), i===-1?data.length:data.length-1-i]).sort((a,b)=>b[1]-a[1]);
    const hc = {{}}, tc = {{}}; for(let i=0;i<10;i++) {{hc[i]=0;tc[i]=0;}}
    nums.forEach(n => {{ hc[Math.floor(n/10)]++; tc[n%10]++; }});
    return {{ nums, total, freq, ls, sorted, overdue, hc, tc }};
}}
function predTop6(sorted) {{ return sorted.slice(0,6).map(([n])=>String(n).padStart(2,'0')).join(' - '); }}

function renderProvCard(provName, histData, provCode) {{
    const r = calcScores(histData);
    const mx = Math.max(...Object.values(r.freq));
    const mxOd = Math.max(...r.overdue.map(x=>x[1]));
    const mxS = r.sorted[0][1];
    const mxH = Math.max(...Object.values(r.hc));
    const mxT = Math.max(...Object.values(r.tc));

    let html = '<div class="prov-card"><h3>' + provName + ' (' + r.total + ' kỳ)</h3>';

    // AI Prediction (FIRST)
    html += '<div class="predict-box predict-main"><div class="nums">' + predTop6(r.sorted) + '</div><small>Phân tích tần suất + độ trễ</small></div>';

    // Frequency
    html += '<h4>Tần suất</h4><div class="grid10">';
    r.sorted.forEach(([n,c]) => {{
        const p = mx>0?c/mx*100:0;
        const cls = p>80?'hot':p>60?'warm':p>40?'normal':p>20?'cool':'cold';
        html += '<div class="cell '+cls+'" title="'+c+' lần"><span class="n">'+String(n).padStart(2,'0')+'</span><span class="v">'+c+'</span></div>';
    }});
    html += '</div>';

    // Overdue
    html += '<h4>Lâu chưa ra</h4><div class="grid10">';
    r.overdue.forEach(([n,d]) => {{
        const p = mxOd>0?d/mxOd*100:0;
        const cls = p>80?'hot':p>60?'warm':p>30?'normal':'cool';
        html += '<div class="cell '+cls+'" title="'+d+' ngày"><span class="n">'+String(n).padStart(2,'0')+'</span><span class="v">'+d+'d</span></div>';
    }});
    html += '</div>';

    // Head-Tail
    html += '<h4>Đầu-Đuôi</h4><div class="headtail-wrap">';
    html += '<div>';
    Object.entries(r.hc).sort((a,b)=>b[1]-a[1]).forEach(([h,c]) => {{
        const p = mxH>0?c/mxH*100:0;
        html += '<div class="bar-row"><div class="bar-label">'+h+'</div><div class="bar" style="width:'+p+'%;background:hsl('+(200-p)+',70%,45%)">'+c+'</div></div>';
    }});
    html += '</div><div>';
    Object.entries(r.tc).sort((a,b)=>b[1]-a[1]).forEach(([t,c]) => {{
        const p = mxT>0?c/mxT*100:0;
        html += '<div class="bar-row"><div class="bar-label">'+t+'</div><div class="bar" style="width:'+p+'%;background:hsl('+(200-p)+',70%,45%)">'+c+'</div></div>';
    }});
    html += '</div></div>';

    html += '</div>';
    return html;
}}

// ===== RESULT SECTION =====
function renderResultTable() {{
    const date = ALL_DATES[resultDateIdx];
    document.getElementById('resultDate').textContent = fmtD(date);
    document.getElementById('btnPrev').disabled = resultDateIdx === 0;
    document.getElementById('btnNext').disabled = resultDateIdx === ALL_DATES.length - 1;
    const dayData = DATA.filter(d => d.date === date);
    if (dayData.length === 0) return;
    let headerHtml = '<tr><th>Giải</th>';
    dayData.forEach(d => {{ headerHtml += '<th>' + d.province_name + '</th>'; }});
    headerHtml += '</tr>';
    document.getElementById('resultHead').innerHTML = headerHtml;
    const prizeRows = [['Tám','prize8'],['Bảy','prize7'],['Sáu 1','prize6_1'],['Sáu 2','prize6_2'],['Sáu 3','prize6_3'],['Năm','prize5'],['Tư 1','prize4_1'],['Tư 2','prize4_2'],['Tư 3','prize4_3'],['Tư 4','prize4_4'],['Ba 1','prize3_1'],['Ba 2','prize3_2'],['Nhì','prize2'],['Nhất','prize1'],['Đặc biệt','special']];
    let bodyHtml = '';
    prizeRows.forEach(([label, field]) => {{
        bodyHtml += '<tr><td style="font-weight:600;color:#555">' + label + '</td>';
        dayData.forEach(d => {{
            const val = d[field];
            const dv = formatByType(val, filterType);
            const sp = field === 'special' ? ' sp' : '';
            if (filterDigit !== null && val && String(val).slice(-2).endsWith(String(filterDigit))) {{
                const f = String(val);
                bodyHtml += '<td class="'+sp+'">'+f.slice(0,-2)+'<span class="num-highlight">'+f.slice(-2)+'</span></td>';
            }} else {{
                bodyHtml += '<td class="'+sp+'">'+(val?dv:'-')+'</td>';
            }}
        }});
        bodyHtml += '</tr>';
    }});
    document.getElementById('resultBody').innerHTML = bodyHtml;
}}
function prevResultDay() {{ if (resultDateIdx > 0) {{ resultDateIdx--; renderResultTable(); }} }}
function nextResultDay() {{ if (resultDateIdx < ALL_DATES.length - 1) {{ resultDateIdx++; renderResultTable(); }} }}
function setFilterType(type, el) {{ document.querySelectorAll('#resultFilter .btn-type').forEach(b => b.classList.remove('active')); el.classList.add('active'); filterType = type; renderResultTable(); }}
function filterByNum(num, el) {{ document.querySelectorAll('#resultFilter .btn-num').forEach(b => b.classList.remove('active')); if (filterDigit === num) {{ filterDigit = null; }} else {{ filterDigit = num; el.classList.add('active'); }} renderResultTable(); }}
function clearHighlight() {{ selectedNum = null; filterDigit = null; document.querySelectorAll('#resultFilter .btn-num').forEach(b => b.classList.remove('active')); renderResultTable(); renderAnalysis(); }}

// ===== ANALYSIS SECTION =====
function prevAnalysisDay() {{ if (analysisDateIdx > 0) {{ analysisDateIdx--; renderAnalysis(); }} }}
function nextAnalysisDay() {{ if (analysisDateIdx < ALL_DATES.length - 1) {{ analysisDateIdx++; renderAnalysis(); }} }}

function renderAnalysis() {{
    const date = ALL_DATES[analysisDateIdx];
    document.getElementById('analysisDate').textContent = fmtD(date);

    const dayData = DATA.filter(d => d.date === date);
    const nextIdx = analysisDateIdx < ALL_DATES.length - 1 ? analysisDateIdx + 1 : -1;
    const nextDate = nextIdx >= 0 ? ALL_DATES[nextIdx] : null;
    const nextData = nextDate ? DATA.filter(d => d.date === nextDate) : [];

    const todayNames = dayData.map(d => d.province_name).join(', ') || 'Không có';
    const tomorrowNames = nextData.map(d => d.province_name).join(', ') || 'Không có';
    document.getElementById('todayProvinces').innerHTML = '<b>Hôm nay (' + fmtD(date) + '):</b> ' + todayNames + '&nbsp;&nbsp;|&nbsp;&nbsp;<b>Ngày mai' + (nextDate ? ' (' + fmtD(nextDate) + ')' : '') + ':</b> ' + tomorrowNames;

    // TODAY: 3 columns
    let todayHtml = '<h3 style="color:#1a5276;margin-bottom:12px;font-size:16px">Dự đoán hôm nay (' + fmtD(date) + ')</h3><div class="three-col">';
    dayData.forEach(d => {{
        const histData = DATA.filter(x => x.province === d.province);
        todayHtml += renderProvCard(d.province_name, histData, d.province);
    }});
    todayHtml += '</div>';
    document.getElementById('predTodaySection').innerHTML = todayHtml;

    // TOMORROW: 3 columns
    let tomorrowHtml = '<h3 style="color:#1a5276;margin-bottom:12px;font-size:16px">Dự đoán ngày mai' + (nextDate ? ' (' + fmtD(nextDate) + ')' : '') + '</h3><div class="three-col">';
    if (nextData.length > 0) {{
        nextData.forEach(d => {{
            const histData = DATA.filter(x => x.province === d.province);
            tomorrowHtml += renderProvCard(d.province_name, histData, d.province);
        }});
    }} else {{
        tomorrowHtml += '<div style="grid-column:1/-1;text-align:center;padding:30px;color:#999">Chưa có dữ liệu ngày mai</div>';
    }}
    tomorrowHtml += '</div>';
    document.getElementById('predTomorrowSection').innerHTML = tomorrowHtml;
}}

// Init
renderResultTable();
renderAnalysis();
</script>
</body>
</html>'''

    Path('readme.html').write_text(html, encoding='utf-8')
    print('Generated: readme.html')


def generate_readme_md(lottery: XSMNLottery):
    """Generate README.md with XSMN data in Markdown format."""
    from datetime import timedelta
    from collections import Counter

    data = lottery.get_raw_data()
    if data.empty:
        print('No data for README.md')
        return

    latest_date = data['date'].max()
    latest_data = data[data['date'] == latest_date]
    total_dates = data['date'].nunique()
    total_provinces = data['province'].nunique()

    latest_results = []
    for _, row in latest_data.iterrows():
        prov = row['province']
        province_name = PROVINCE_NAMES.get(prov, prov)
        latest_results.append({
            'province': province_name,
            'special': f"{int(row['special']):06d}",
            'prize1': f"{int(row['prize1']):05d}",
        })

    recent_data = data[data['date'] >= latest_date - timedelta(days=30)]
    all_numbers = []
    for col in ['special', 'prize1', 'prize2', 'prize3_1', 'prize3_2',
                'prize4_1', 'prize4_2', 'prize4_3', 'prize4_4',
                'prize6_1', 'prize6_2', 'prize6_3']:
        if col in recent_data.columns:
            vals = recent_data[col].dropna()
            all_numbers.extend([f"{int(v):02d}"[-2:] for v in vals])

    freq = Counter(all_numbers)
    top10 = freq.most_common(10)

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

- **Bảng tương tác:** [readme.html](https://t-k-minh.github.io/XSMienNam-Analysis/) (xem trực tuyến)
- **Dữ liệu gốc:** [data/xsmn.json](data/xsmn.json)

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
