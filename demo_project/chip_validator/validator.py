"""
晶片暫存器設定驗證器

驗證規則：
  1. 暫存器位址必須在合法範圍內（0x0000 ~ 0xFFFF）
  2. 同一暫存器內的 bit field 不可重疊
  3. Bit field 的 msb/lsb 不可超出暫存器寬度
  4. 必要暫存器必須存在（CTRL_REG, STATUS_REG）
  5. Clock 頻率必須在 spec 範圍內（10 ~ 800 MHz）
  6. 核心電壓必須在安全範圍內（750 ~ 1100 mV）
"""

from dataclasses import dataclass
from .models import ChipConfig

# ── 常數 ──────────────────────────────────────────────────────────────────────
ADDR_MIN = 0x0000
ADDR_MAX = 0xFFFF
REQUIRED_REGISTERS = ["CTRL_REG", "STATUS_REG"]
CLOCK_MIN_MHZ = 10.0
CLOCK_MAX_MHZ = 800.0
VOLTAGE_MIN_MV = 750
VOLTAGE_MAX_MV = 1100


@dataclass
class ValidationError:
    """驗證錯誤"""
    rule: str       # 違反的規則名稱
    message: str    # 錯誤描述
    register: str = ""  # 相關的暫存器名稱（如有）


def validate_address_range(config: ChipConfig) -> list[ValidationError]:
    """規則 1：暫存器位址必須在 0x0000 ~ 0xFFFF"""
    errors = []
    for reg in config.registers:
        if not (ADDR_MIN <= reg.address <= ADDR_MAX):
            errors.append(ValidationError(
                rule="address_range",
                message=f"位址 0x{reg.address:04X} 超出合法範圍 (0x{ADDR_MIN:04X}~0x{ADDR_MAX:04X})",
                register=reg.name,
            ))
    return errors


def validate_bitfield_overlap(config: ChipConfig) -> list[ValidationError]:
    """規則 2：同一暫存器內的 bit field 不可重疊"""
    errors = []
    for reg in config.registers:
        occupied = [False] * reg.width
        for bf in reg.fields:
            for bit in range(bf.lsb, bf.msb + 1):
                if bit >= reg.width:
                    continue  # 超出寬度的問題由 rule 3 處理
                if occupied[bit]:
                    errors.append(ValidationError(
                        rule="bitfield_overlap",
                        message=f"bit {bit} 被多個欄位佔用（包含 '{bf.name}'）",
                        register=reg.name,
                    ))
                    break
                occupied[bit] = True
    return errors


def validate_bitfield_width(config: ChipConfig) -> list[ValidationError]:
    """規則 3：bit field 的 msb/lsb 不可超出暫存器寬度"""
    errors = []
    for reg in config.registers:
        for bf in reg.fields:
            if bf.msb >= reg.width:
                errors.append(ValidationError(
                    rule="bitfield_width",
                    message=f"欄位 '{bf.name}' 的 msb={bf.msb} 超出暫存器寬度 {reg.width} bits",
                    register=reg.name,
                ))
            if bf.lsb < 0:
                errors.append(ValidationError(
                    rule="bitfield_width",
                    message=f"欄位 '{bf.name}' 的 lsb={bf.lsb} 不可為負數",
                    register=reg.name,
                ))
            if bf.msb < bf.lsb:
                errors.append(ValidationError(
                    rule="bitfield_width",
                    message=f"欄位 '{bf.name}' 的 msb={bf.msb} < lsb={bf.lsb}",
                    register=reg.name,
                ))
    return errors


def validate_required_registers(config: ChipConfig) -> list[ValidationError]:
    """規則 4：必要暫存器必須存在"""
    errors = []
    names = {reg.name for reg in config.registers}
    for req in REQUIRED_REGISTERS:
        if req not in names:
            errors.append(ValidationError(
                rule="required_register",
                message=f"缺少必要暫存器 '{req}'",
            ))
    return errors


def validate_clock_frequency(config: ChipConfig) -> list[ValidationError]:
    """規則 5：clock 頻率必須在 10 ~ 800 MHz"""
    errors = []
    if config.clock_freq_mhz < CLOCK_MIN_MHZ or config.clock_freq_mhz > CLOCK_MAX_MHZ:
        errors.append(ValidationError(
            rule="clock_frequency",
            message=f"時脈 {config.clock_freq_mhz} MHz 超出允許範圍 ({CLOCK_MIN_MHZ}~{CLOCK_MAX_MHZ} MHz)",
        ))
    return errors


def validate_voltage(config: ChipConfig) -> list[ValidationError]:
    """規則 6：核心電壓必須在 750 ~ 1100 mV"""
    errors = []
    if config.voltage_mv < VOLTAGE_MIN_MV or config.voltage_mv > VOLTAGE_MAX_MV:
        errors.append(ValidationError(
            rule="voltage",
            message=f"電壓 {config.voltage_mv} mV 超出安全範圍 ({VOLTAGE_MIN_MV}~{VOLTAGE_MAX_MV} mV)",
        ))
    return errors


# ── 主驗證函數 ────────────────────────────────────────────────────────────────

ALL_RULES = [
    validate_address_range,
    validate_bitfield_overlap,
    validate_bitfield_width,
    validate_required_registers,
    validate_clock_frequency,
    validate_voltage,
]


def validate_chip_config(config: ChipConfig) -> list[ValidationError]:
    """執行所有驗證規則，回傳錯誤清單（空 = 通過）"""
    errors = []
    for rule_fn in ALL_RULES:
        errors.extend(rule_fn(config))
    return errors
