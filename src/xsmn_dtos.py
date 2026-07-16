"""DTOs for XSMN (Southern Vietnam Lottery)."""
from datetime import date

from pydantic import BaseModel, RootModel


class XSMNResult(BaseModel):
    """Result for a single XSMN draw (one province)."""
    date: date
    province: str

    special: int  # Giải đặc biệt (6 số)

    prize1: int  # Giải nhất (5 số)

    prize2: int  # Giải nhì (5 số)

    prize3_1: int
    prize3_2: int

    prize4_1: int
    prize4_2: int
    prize4_3: int
    prize4_4: int

    prize5: str = '0'  # Giải năm (4 số) - string để giữ số 0 đứng đầu

    prize6_1: int
    prize6_2: int
    prize6_3: int

    prize7: str = '0'  # Giải bảy (3 số) - string để giữ số 0 đứng đầu
    prize8: str = '0'  # Giải tám (2 số) - string để giữ số 0 đứng đầu


class XSMNResultList(RootModel):
    root: list[XSMNResult]
