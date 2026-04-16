"""
晶片暫存器設定驗證器 — 單元測試

測試涵蓋 6 條驗證規則：
  1. 位址範圍
  2. Bit field 重疊
  3. Bit field 超出寬度
  4. 必要暫存器存在
  5. Clock 頻率範圍
  6. 核心電壓範圍
"""

import pytest
from chip_validator.models import ChipConfig, Register, BitField
from chip_validator.validator import (
    validate_chip_config,
    validate_address_range,
    validate_bitfield_overlap,
    validate_bitfield_width,
    validate_required_registers,
    validate_clock_frequency,
    validate_voltage,
)


# ── 輔助函數 ─────────────────────────────────────────────────────────────────

def _make_valid_config(**overrides) -> ChipConfig:
    """建立一組合法的基本設定，方便各測試覆寫特定欄位"""
    defaults = dict(
        chip_name="NT96580",
        registers=[
            Register(name="CTRL_REG", address=0x0000, width=32, fields=[
                BitField(name="EN", msb=0, lsb=0),
                BitField(name="MODE", msb=3, lsb=1),
            ]),
            Register(name="STATUS_REG", address=0x0004, width=32, fields=[
                BitField(name="BUSY", msb=0, lsb=0),
                BitField(name="ERR", msb=1, lsb=1),
            ]),
        ],
        clock_freq_mhz=200.0,
        voltage_mv=900,
    )
    defaults.update(overrides)
    return ChipConfig(**defaults)


# ══════════════════════════════════════════════════════════════════════════════
#  合法設定：全部通過
# ══════════════════════════════════════════════════════════════════════════════

class Test合法設定:

    def test_完整合法設定_零錯誤(self):
        config = _make_valid_config()
        errors = validate_chip_config(config)
        assert errors == [], f"預期零錯誤，但得到 {[e.message for e in errors]}"


# ══════════════════════════════════════════════════════════════════════════════
#  規則 1：暫存器位址範圍
# ══════════════════════════════════════════════════════════════════════════════

class Test位址範圍:

    def test_位址在合法範圍內(self):
        config = _make_valid_config()
        assert validate_address_range(config) == []

    def test_位址超出上限(self):
        config = _make_valid_config(registers=[
            Register(name="CTRL_REG", address=0x10000),  # 超過 0xFFFF
            Register(name="STATUS_REG", address=0x0004),
        ])
        errors = validate_address_range(config)
        assert len(errors) == 1
        assert errors[0].rule == "address_range"
        assert "CTRL_REG" in errors[0].register

    def test_位址為負數(self):
        config = _make_valid_config(registers=[
            Register(name="CTRL_REG", address=-1),
            Register(name="STATUS_REG", address=0x0004),
        ])
        errors = validate_address_range(config)
        assert len(errors) == 1


# ══════════════════════════════════════════════════════════════════════════════
#  規則 2：bit field 不可重疊
# ══════════════════════════════════════════════════════════════════════════════

class TestBitField重疊:

    def test_無重疊(self):
        config = _make_valid_config()
        assert validate_bitfield_overlap(config) == []

    def test_兩個欄位重疊(self):
        """EN [0:0] 和 MODE [1:0] 在 bit 0 重疊"""
        config = _make_valid_config(registers=[
            Register(name="CTRL_REG", address=0x0000, width=32, fields=[
                BitField(name="EN", msb=0, lsb=0),
                BitField(name="MODE", msb=1, lsb=0),  # bit 0 跟 EN 重疊
            ]),
            Register(name="STATUS_REG", address=0x0004),
        ])
        errors = validate_bitfield_overlap(config)
        assert len(errors) >= 1
        assert errors[0].rule == "bitfield_overlap"


# ══════════════════════════════════════════════════════════════════════════════
#  規則 3：bit field 超出暫存器寬度
# ══════════════════════════════════════════════════════════════════════════════

class TestBitField寬度:

    def test_正常寬度(self):
        config = _make_valid_config()
        assert validate_bitfield_width(config) == []

    def test_msb超出寬度(self):
        """32-bit 暫存器，但 msb=32（合法最大是 31）"""
        config = _make_valid_config(registers=[
            Register(name="CTRL_REG", address=0x0000, width=32, fields=[
                BitField(name="BAD", msb=32, lsb=0),
            ]),
            Register(name="STATUS_REG", address=0x0004),
        ])
        errors = validate_bitfield_width(config)
        assert any(e.rule == "bitfield_width" for e in errors)

    def test_msb小於lsb(self):
        config = _make_valid_config(registers=[
            Register(name="CTRL_REG", address=0x0000, width=32, fields=[
                BitField(name="REVERSED", msb=0, lsb=7),
            ]),
            Register(name="STATUS_REG", address=0x0004),
        ])
        errors = validate_bitfield_width(config)
        assert any("msb" in e.message and "lsb" in e.message for e in errors)


# ══════════════════════════════════════════════════════════════════════════════
#  規則 4：必要暫存器必須存在
# ══════════════════════════════════════════════════════════════════════════════

class Test必要暫存器:

    def test_兩個必要暫存器都在(self):
        config = _make_valid_config()
        assert validate_required_registers(config) == []

    def test_缺少CTRL_REG(self):
        config = _make_valid_config(registers=[
            Register(name="STATUS_REG", address=0x0004),
        ])
        errors = validate_required_registers(config)
        assert len(errors) == 1
        assert "CTRL_REG" in errors[0].message

    def test_兩個都缺(self):
        config = _make_valid_config(registers=[])
        errors = validate_required_registers(config)
        assert len(errors) == 2


# ══════════════════════════════════════════════════════════════════════════════
#  規則 5：clock 頻率
# ══════════════════════════════════════════════════════════════════════════════

class TestClock頻率:

    def test_頻率在範圍內(self):
        config = _make_valid_config(clock_freq_mhz=200.0)
        assert validate_clock_frequency(config) == []

    def test_頻率過高(self):
        config = _make_valid_config(clock_freq_mhz=1000.0)
        errors = validate_clock_frequency(config)
        assert len(errors) == 1
        assert errors[0].rule == "clock_frequency"

    def test_頻率過低(self):
        config = _make_valid_config(clock_freq_mhz=5.0)
        errors = validate_clock_frequency(config)
        assert len(errors) == 1

    def test_邊界值_最小值通過(self):
        config = _make_valid_config(clock_freq_mhz=10.0)
        assert validate_clock_frequency(config) == []

    def test_邊界值_最大值通過(self):
        config = _make_valid_config(clock_freq_mhz=800.0)
        assert validate_clock_frequency(config) == []


# ══════════════════════════════════════════════════════════════════════════════
#  規則 6：核心電壓
# ══════════════════════════════════════════════════════════════════════════════

class Test核心電壓:

    def test_電壓在範圍內(self):
        config = _make_valid_config(voltage_mv=900)
        assert validate_voltage(config) == []

    def test_電壓過高(self):
        config = _make_valid_config(voltage_mv=1200)
        errors = validate_voltage(config)
        assert len(errors) == 1
        assert errors[0].rule == "voltage"

    def test_電壓過低(self):
        config = _make_valid_config(voltage_mv=500)
        errors = validate_voltage(config)
        assert len(errors) == 1


# ══════════════════════════════════════════════════════════════════════════════
#  整合測試：多條規則同時違反
# ══════════════════════════════════════════════════════════════════════════════

class Test整合驗證:

    def test_多重錯誤同時偵測(self):
        """同時違反位址、clock、voltage 三條規則"""
        config = ChipConfig(
            chip_name="BAD_CHIP",
            registers=[
                Register(name="CTRL_REG", address=0x20000),   # 位址超出
                Register(name="STATUS_REG", address=0x0004),
            ],
            clock_freq_mhz=2000.0,   # 超出
            voltage_mv=500,           # 過低
        )
        errors = validate_chip_config(config)
        rules = {e.rule for e in errors}
        assert "address_range" in rules
        assert "clock_frequency" in rules
        assert "voltage" in rules
        assert len(errors) >= 3
