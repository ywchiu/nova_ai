"""
晶片暫存器設定資料模型

定義 Register、BitField、ChipConfig 三層結構，
對應 IC 設計中常見的 register map 設定檔格式。
"""

from dataclasses import dataclass, field


@dataclass
class BitField:
    """暫存器內的位元欄位"""
    name: str           # 欄位名稱，例如 "TX_EN"
    msb: int            # 最高位元，例如 7
    lsb: int            # 最低位元，例如 0
    default: int = 0    # 預設值
    description: str = ""


@dataclass
class Register:
    """單一暫存器定義"""
    name: str               # 暫存器名稱，例如 "CTRL_REG"
    address: int            # 暫存器位址，例如 0x0010
    width: int = 32         # 暫存器寬度（bits），預設 32-bit
    fields: list[BitField] = field(default_factory=list)
    description: str = ""


@dataclass
class ChipConfig:
    """晶片設定檔（包含多個暫存器與全域設定）"""
    chip_name: str                  # 晶片名稱，例如 "NT96580"
    registers: list[Register] = field(default_factory=list)
    clock_freq_mhz: float = 0.0    # 主時脈頻率 (MHz)
    voltage_mv: int = 0            # 核心電壓 (mV)
