"""XSMN (Southern Vietnam Lottery) data fetcher and processor."""
from copy import copy
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from cloudscraper import CloudScraper

from xsmn_dtos import XSMNResult


# Lịch quay XSMN theo thứ
XSMN_SCHEDULE = {
    0: ['TTP', 'DT', 'CM'],      # Thứ 2: TP.HCM, Đồng Tháp, Cà Mau
    1: ['BTR', 'VT', 'BL'],       # Thứ 3: Bến Tre, Vũng Tàu, Bạc Liêu
    2: ['DNA', 'CT', 'ST'],       # Thứ 4: Đồng Nai, Cần Thơ, Sóc Trăng
    3: ['TNI', 'AG', 'BTH'],      # Thứ 5: Tây Ninh, An Giang, Bình Thuận
    4: ['VL', 'BD', 'TV'],        # Thứ 6: Vĩnh Long, Bình Dương, Trà Vinh
    5: ['HCM', 'LA', 'BP', 'HGG'], # Thứ 7: TP.HCM, Long An, Bình Phước, Hậu Giang
    6: ['TGI', 'KG', 'DL'],       # Chủ nhật: Tiền Giang, Kiên Giang, Đà Lạt
}

# Map mã tỉnh → tên đầy đủ
PROVINCE_NAMES = {
    'TTP': 'TP. Hồ Chí Minh',
    'HCM': 'TP. Hồ Chí Minh',
    'DT': 'Đồng Tháp',
    'CM': 'Cà Mau',
    'BTR': 'Bến Tre',
    'VT': 'Vũng Tàu',
    'BL': 'Bạc Liêu',
    'DNA': 'Đồng Nai',
    'CT': 'Cần Thơ',
    'ST': 'Sóc Trăng',
    'TNI': 'Tây Ninh',
    'AG': 'An Giang',
    'BTH': 'Bình Thuận',
    'VL': 'Vĩnh Long',
    'BD': 'Bình Dương',
    'TV': 'Trà Vinh',
    'LA': 'Long An',
    'BP': 'Bình Phước',
    'HGG': 'Hậu Giang',
    'TGI': 'Tiền Giang',
    'KG': 'Kiên Giang',
    'DL': 'Đà Lạt',
}

# Map tên trên web → mã tỉnh
WEB_NAME_TO_CODE = {
    'TPHCM': 'TTP',
    'Đồng Tháp': 'DT',
    'Cà Mau': 'CM',
    'Bến Tre': 'BTR',
    'Vũng Tàu': 'VT',
    'Bạc Liêu': 'BL',
    'Đồng Nai': 'DNA',
    'Cần Thơ': 'CT',
    'Sóc Trăng': 'ST',
    'Tây Ninh': 'TNI',
    'An Giang': 'AG',
    'Bình Thuận': 'BTH',
    'Vĩnh Long': 'VL',
    'Bình Dương': 'BD',
    'Trà Vinh': 'TV',
    'Long An': 'LA',
    'Bình Phước': 'BP',
    'Hậu Giang': 'HGG',
    'Tiền Giang': 'TGI',
    'Kiên Giang': 'KG',
    'Đà Lạt': 'DL',
}


class XSMNLottery:
    def __init__(self) -> None:
        self._http = CloudScraper()
        self._data: dict[tuple[date, str], XSMNResult] = {}
        self._raw_data: pd.DataFrame = pd.DataFrame()

    def load(self) -> None:
        json_path = Path('data/xsmn.json')
        if not json_path.exists():
            return
        import json
        with open(json_path, 'r', encoding='utf-8') as f:
            records = json.load(f)
        for rec in records:
            rec['date'] = date.fromisoformat(rec['date'])
            # Coerce any remaining int values to str for leading zeros
            for key in rec:
                if key not in ('date', 'province', 'province_name') and isinstance(rec[key], int):
                    rec[key] = str(rec[key])
            result = XSMNResult(**rec)
            self._data[(result.date, result.province)] = result
        self.generate_dataframe()

    def dump(self) -> None:
        Path('data').mkdir(exist_ok=True)

        records = []
        for result in self._data.values():
            rec = result.model_dump()
            rec['date'] = rec['date'].isoformat()
            records.append(rec)

        import json
        with open('data/xsmn.json', 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

        if not self._raw_data.empty:
            self._raw_data.to_csv('data/xsmn.csv', index=False)
            self._raw_data.to_parquet('data/xsmn.parquet', index=False)

    def fetch(self, selected_date: date) -> None:
        """Fetch XSMN results for a specific date."""
        dow = selected_date.weekday()
        provinces = XSMN_SCHEDULE.get(dow, [])

        for province_code in provinces:
            if (selected_date, province_code) in self._data:
                continue

            result = self._fetch_province(selected_date, province_code)
            if result:
                self._data[(selected_date, province_code)] = result

    def _fetch_province(self, selected_date: date, province_code: str) -> XSMNResult | None:
        """Fetch result for a single province."""
        url = f'https://xoso.com.vn/xsmn-{selected_date:%d-%m-%Y}.html'

        try:
            resp = self._http.get(url, timeout=15)
            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.text, 'lxml')

            table = soup.find('table', class_='table-xsmn')
            if not table:
                return None

            # Find province column index
            header_row = table.find('tr')
            headers = header_row.find_all(['th', 'td'])

            col_idx = -1
            # First try exact match via web name mapping
            for i, h in enumerate(headers):
                name = h.text.strip()
                web_code = WEB_NAME_TO_CODE.get(name)
                if web_code == province_code:
                    col_idx = i
                    break

            # Fallback to partial match if no exact match
            if col_idx == -1:
                for i, h in enumerate(headers):
                    name = h.text.strip()
                    if province_code.lower() in name.lower():
                        col_idx = i
                        break

            if col_idx == -1:
                return None

            rows = table.find_all('tr')

            # Row mapping based on actual structure:
            # Row 1: Giải 8 (2 số)
            # Row 2: Giải 7 (3 số)
            # Row 3: Giải 6 (3×3 số)
            # Row 4: Giải 5 (4 số)
            # Row 5: Giải 4 (7 số)
            # Row 6: Giải 3 (2×3 số)
            # Row 7: Giải 2 (5 số)
            # Row 8: Giải 1 (5 số)
            # Row 9: Đặc biệt (6 số)

            prizes = {}

            for row_idx in range(1, len(rows)):
                cells = rows[row_idx].find_all(['td', 'th'])
                if len(cells) <= col_idx:
                    continue

                # Get all numbers from this cell
                cell_text = cells[col_idx].text.strip()
                numbers_str = [x for x in cell_text.split() if x.isdigit()]
                numbers = [int(x) for x in numbers_str]

                if not numbers:
                    continue

                if row_idx == 1:  # Giải 8 - keep as string for leading zeros
                    prizes['prize8'] = cell_text.strip().replace(' ', '') if cell_text.strip() else '0'
                elif row_idx == 2:  # Giải 7 - keep as string for leading zeros
                    prizes['prize7'] = cell_text.strip().replace(' ', '') if cell_text.strip() else '0'
                elif row_idx == 3:  # Giải 6 (3×3) - keep as string
                    prizes['prize6_1'] = numbers_str[0] if len(numbers_str) > 0 else '0'
                    prizes['prize6_2'] = numbers_str[1] if len(numbers_str) > 1 else '0'
                    prizes['prize6_3'] = numbers_str[2] if len(numbers_str) > 2 else '0'
                elif row_idx == 4:  # Giải 5 - keep as string
                    prizes['prize5'] = cell_text.strip().replace(' ', '') if cell_text.strip() else '0'
                elif row_idx == 5:  # Giải 4 (7 số) - keep as string
                    for i, num in enumerate(numbers_str[:7]):
                        prizes[f'prize4_{i+1}'] = num if num else '0'
                elif row_idx == 6:  # Giải 3 (2×3) - keep as string
                    prizes['prize3_1'] = numbers_str[0] if len(numbers_str) > 0 else '0'
                    prizes['prize3_2'] = numbers_str[1] if len(numbers_str) > 1 else '0'
                elif row_idx == 7:  # Giải 2 - keep as string for leading zeros
                    prizes['prize2'] = cell_text.strip().replace(' ', '') if cell_text.strip() else '0'
                elif row_idx == 8:  # Giải 1 - keep as string for leading zeros
                    prizes['prize1'] = cell_text.strip().replace(' ', '') if cell_text.strip() else '0'
                elif row_idx == 9:  # Đặc biệt - keep as string for leading zeros
                    prizes['special'] = cell_text.strip().replace(' ', '') if cell_text.strip() else '0'

            # Map to XSMNResult format
            return XSMNResult(
                date=selected_date,
                province=province_code,
                special=str(prizes.get('special', '0')),
                prize1=str(prizes.get('prize1', '0')),
                prize2=str(prizes.get('prize2', '0')),
                prize3_1=str(prizes.get('prize3_1', '0')),
                prize3_2=str(prizes.get('prize3_2', '0')),
                prize4_1=str(prizes.get('prize4_1', '0')),
                prize4_2=str(prizes.get('prize4_2', '0')),
                prize4_3=str(prizes.get('prize4_3', '0')),
                prize4_4=str(prizes.get('prize4_4', '0')),
                prize5=str(prizes.get('prize5', '0')),
                prize6_1=str(prizes.get('prize6_1', '0')),
                prize6_2=str(prizes.get('prize6_2', '0')),
                prize6_3=str(prizes.get('prize6_3', '0')),
                prize7=str(prizes.get('prize7', '0')),
                prize8=str(prizes.get('prize8', '0')),
            )

        except Exception as e:
            print(f"Error fetching {province_code}: {e}")
            return None

    def _create_result_from_dict(self, selected_date: date, province_code: str, prizes: dict) -> XSMNResult | None:
        """Create XSMNResult from parsed dict."""
        try:
            special = prizes.get('special', 0)
            if special == 0:
                return None

            return XSMNResult(
                date=selected_date,
                province=province_code,
                special=special,
                prize1=prizes.get('prize1', 0),
                prize2=prizes.get('prize2', 0),
                prize3_1=prizes.get('prize3_1', 0),
                prize3_2=prizes.get('prize3_2', 0),
                prize4_1=prizes.get('prize4_1', 0),
                prize4_2=prizes.get('prize4_2', 0),
                prize4_3=prizes.get('prize4_3', 0),
                prize4_4=prizes.get('prize4_4', 0),
                prize5_1=prizes.get('prize5_1', 0),
                prize5_2=prizes.get('prize5_2', 0),
                prize5_3=prizes.get('prize5_3', 0),
                prize6_1=prizes.get('prize6_1', 0),
                prize6_2=prizes.get('prize6_2', 0),
                prize6_3=prizes.get('prize6_3', 0),
                prize7_1=prizes.get('prize7_1', 0),
                prize7_2=prizes.get('prize7_2', 0),
                prize7_3=prizes.get('prize7_3', 0),
                prize7_4=prizes.get('prize7_4', 0),
                prize7_5=prizes.get('prize7_5', 0),
                prize7_6=prizes.get('prize7_6', 0),
                prize7_7=prizes.get('prize7_7', 0),
            )
        except Exception:
            return None

    def generate_dataframe(self) -> None:
        """Convert results to DataFrame."""
        if not self._data:
            return

        records = []
        for result in self._data.values():
            records.append(result.model_dump())

        self._raw_data = pd.DataFrame(records)
        self._raw_data['date'] = pd.to_datetime(self._raw_data['date'])

    def get_raw_data(self) -> pd.DataFrame:
        return self._raw_data

    def get_last_date(self) -> date:
        if self._raw_data.empty:
            return date.today()
        return self._raw_data['date'].max().date()

    def get_provinces(self) -> list[str]:
        """Get list of provinces with data."""
        if self._raw_data.empty:
            return []
        return sorted(self._raw_data['province'].unique().tolist())
