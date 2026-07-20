"""DTOs for XSMN (Southern Vietnam Lottery)."""
from datetime import date

from pydantic import BaseModel, RootModel


class XSMNResult(BaseModel):
    """Result for a single XSMN draw (one province)."""
    date: date
    province: str

    special: str = '0'  # Giải đặc biệt (6 số)
    prize1: str = '0'  # Giải nhất (5 số)
    prize2: str = '0'  # Giải nhì (5 số)
    prize3_1: str = '0'
    prize3_2: str = '0'
    prize4_1: str = '0'
    prize4_2: str = '0'
    prize4_3: str = '0'
    prize4_4: str = '0'
    prize5: str = '0'  # Giải năm (4 số)
    prize6_1: str = '0'
    prize6_2: str = '0'
    prize6_3: str = '0'
    prize7: str = '0'  # Giải bảy (3 số)
    prize8: str = '0'  # Giải tám (2 số)


class XSMNResultList(RootModel):
    root: list[XSMNResult]
