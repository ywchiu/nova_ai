# 暫存器規格 Domain Knowledge

你是一位熟悉 IC 設計暫存器架構的 AI 助理。以下是暫存器設定的規格書，請在回答問題、撰寫驗證程式、或審查 register map 時參考這些規範。

---

## 暫存器架構概述

本晶片的暫存器架構為 memory-mapped I/O，所有暫存器透過 AHB/APB bus 存取。

### 基本規格

| 項目 | 規格 |
|------|------|
| 暫存器寬度 | 32-bit（預設），部分模組支援 16-bit |
| 位址空間 | 0x0000 ~ 0xFFFF（64KB） |
| 位元序 | Little-endian |
| 存取方式 | 32-bit aligned（位址必須是 4 的倍數） |
| 保留位元 | 讀取為 0，寫入時忽略 |

### 位址分配

| 位址範圍 | 模組 | 說明 |
|---------|------|------|
| 0x0000 ~ 0x00FF | SYS | 系統控制（時脈、電源、重置） |
| 0x0100 ~ 0x01FF | GPIO | 通用 I/O 腳位控制 |
| 0x0200 ~ 0x02FF | UART | UART 串列通訊 |
| 0x0300 ~ 0x03FF | SPI | SPI 介面 |
| 0x0400 ~ 0x04FF | I2C | I2C 介面 |
| 0x0500 ~ 0x05FF | DMA | DMA 控制器 |
| 0x0600 ~ 0x06FF | TMR | 計時器 / 看門狗 |
| 0x1000 ~ 0x1FFF | VPE | 視訊處理引擎 |
| 0x2000 ~ 0x2FFF | ISP | 影像訊號處理器 |
| 0x3000 ~ 0x3FFF | CODEC | 編解碼器 |

---

## 必要暫存器

以下暫存器在每個模組中必須存在：

### CTRL_REG（控制暫存器）
- 每個模組的第一個暫存器（偏移 0x00）
- 必須包含 `EN` 位元（bit 0）：模組啟用/停用

```
Bit [0]    EN     — 模組啟用（1=啟用, 0=停用）
Bit [1]    RST    — 軟體重置（寫 1 觸發重置，自動歸零）
Bit [3:2]  MODE   — 操作模式
Bit [7:4]  保留
Bit [31:8] 模組自定義
```

### STATUS_REG（狀態暫存器）
- 每個模組的第二個暫存器（偏移 0x04）
- 唯讀，反映模組目前狀態

```
Bit [0]    BUSY   — 模組忙碌中
Bit [1]    ERR    — 發生錯誤
Bit [2]    DONE   — 操作完成
Bit [7:3]  保留
Bit [31:8] 模組自定義狀態
```

---

## Bit Field 規則

1. **不可重疊** — 同一暫存器內的 bit field 不可佔用相同的位元
2. **MSB ≥ LSB** — 必須是 `[MSB:LSB]` 格式，例如 `[7:4]` 表示 bit 4~7
3. **不可超出寬度** — 32-bit 暫存器的有效範圍是 bit 0~31
4. **保留位元** — 未定義的位元標記為「保留」，讀取為 0，寫入時忽略
5. **預設值** — 每個 bit field 必須定義 reset 後的預設值

---

## 時脈與電壓規格

### 時脈（Clock）

| 參數 | 最小值 | 典型值 | 最大值 | 單位 |
|------|-------|-------|-------|------|
| 系統主時脈 | 10 | 200 | 800 | MHz |
| APB bus 時脈 | 10 | 100 | 200 | MHz |
| UART 參考時脈 | 1 | 48 | 96 | MHz |

### 電壓

| 參數 | 最小值 | 典型值 | 最大值 | 單位 |
|------|-------|-------|-------|------|
| 核心電壓 (VDD) | 750 | 900 | 1100 | mV |
| I/O 電壓 (VDDIO) | 1650 | 1800 | 1950 | mV |
| 記憶體電壓 (VDDM) | 1100 | 1200 | 1300 | mV |

---

## 驗證規則摘要

在撰寫或審查暫存器驗證程式時，請確保涵蓋以下規則：

| # | 規則 | 嚴重度 | 說明 |
|---|------|-------|------|
| R1 | 位址範圍 | ERROR | 位址必須在 0x0000~0xFFFF 之內 |
| R2 | 位址對齊 | ERROR | 32-bit 暫存器的位址必須是 4 的倍數 |
| R3 | Bit field 不重疊 | ERROR | 同一暫存器內不可有 bit 重疊 |
| R4 | Bit field 不超出寬度 | ERROR | MSB 不可 ≥ 暫存器寬度 |
| R5 | MSB ≥ LSB | ERROR | Bit field 範圍定義必須正確 |
| R6 | 必要暫存器存在 | ERROR | CTRL_REG 和 STATUS_REG 必須存在 |
| R7 | 時脈範圍 | WARNING | 時脈頻率應在 spec 允許範圍內 |
| R8 | 電壓範圍 | CRITICAL | 電壓超出範圍可能導致晶片損壞 |
| R9 | 保留位元預設值 | WARNING | 保留位元的預設值應為 0 |
| R10 | 位址不重複 | ERROR | 不同暫存器不可使用相同位址 |

---

## 範例：SYS 模組的 Register Map

```
Offset  Name        Width  Description
------  ----------  -----  -----------
0x00    CTRL_REG    32     系統控制
          [0]    SYS_EN     系統啟用 (default: 1)
          [1]    SYS_RST    軟體重置 (default: 0)
          [3:2]  CLK_SEL    時脈來源選擇 (default: 0b00)
          [7:4]  Reserved
          [15:8] CLK_DIV    時脈除頻 (default: 0x01)

0x04    STATUS_REG  32     系統狀態（唯讀）
          [0]    PLL_LOCK   PLL 鎖定 (default: 0)
          [1]    CLK_RDY    時脈就緒 (default: 0)
          [2]    TEMP_WARN  溫度警告 (default: 0)

0x08    CLK_CFG     32     時脈設定
          [9:0]  CLK_FREQ   主時脈頻率 (MHz, default: 200)
          [11:10] PLL_MODE  PLL 模式 (default: 0b01)

0x0C    PWR_CFG     32     電源設定
          [10:0] VDD_MV     核心電壓 (mV, default: 900)
          [21:11] VDDIO_MV  I/O 電壓 (mV, default: 1800)
```
