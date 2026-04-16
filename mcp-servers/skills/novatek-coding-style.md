# Novatek Coding Style Rules

你是一位嚴格遵守聯詠科技程式碼風格規範的 AI 助理。在產生或審查程式碼時，請遵守以下規則。

---

## 通用規則

### 檔案結構
- 每個檔案開頭必須有版權聲明和功能摘要註解
- Include / Import 依序排列：標準庫 → 第三方 → 專案內部
- 一個檔案只做一件事，超過 500 行應考慮拆分

### 命名規範

| 項目 | 規則 | 範例 |
|------|------|------|
| 檔案名稱 | 小寫加底線 | `reg_config_parser.py` |
| 常數 | 全大寫加底線 | `MAX_CLOCK_FREQ_MHZ` |
| 函數 / 方法 | 小寫加底線（snake_case） | `validate_register_map()` |
| 類別 | 大駝峰（PascalCase） | `RegisterConfig` |
| 私有成員 | 前綴底線 | `_internal_buffer` |
| 暫存器名稱 | 全大寫加底線 | `CTRL_REG`, `STATUS_REG` |

### 註解規範
- 函數必須有 docstring，說明用途、參數、回傳值
- 複雜邏輯前方加單行註解說明「為什麼」，而非「做什麼」
- TODO 格式：`# TODO(工號): 說明 — JIRA-TICKET`
- 禁止留下 `# FIXME` 或 `# HACK` 進入 main branch

---

## C 語言規範

### 命名
- 函數：`模組_動詞_名詞`，例如 `dma_init_channel()`, `spi_read_register()`
- 巨集：全大寫，例如 `#define REG_CTRL_OFFSET 0x0010`
- 型別：後綴 `_t`，例如 `reg_config_t`, `dma_channel_t`
- 全域變數：前綴 `g_`，例如 `g_system_clock`

### 格式
- 縮排：4 個空格（不用 Tab）
- 大括號：同行起始（K&R style）
- 每行不超過 100 字元
- 函數之間空兩行

### 安全規範
- 禁止使用 `malloc` / `free`，使用專案的記憶體池 API
- 所有指標使用前必須檢查 NULL
- Register 存取必須透過 `REG_READ()` / `REG_WRITE()` 巨集

```c
/* 正確範例 */
void dma_init_channel(uint32_t channel_id)
{
    if (channel_id >= DMA_MAX_CHANNELS) {
        LOG_ERROR("Invalid channel: %u", channel_id);
        return;
    }

    uint32_t ctrl = REG_READ(DMA_CTRL_REG);
    ctrl |= (1U << channel_id);
    REG_WRITE(DMA_CTRL_REG, ctrl);
}
```

---

## Perl 規範

### 命名
- 變數 / 函數：snake_case，例如 `$file_path`, `parse_log_file()`
- 常數：全大寫，例如 `use constant MAX_RETRY => 3;`
- 模組：PascalCase，例如 `Novatek::LogParser`

### 格式
- 開頭必須有 `use strict;` 和 `use warnings;`
- 使用三引號 heredoc 處理多行字串
- 正規表達式加上 `x` flag 提升可讀性

```perl
use strict;
use warnings;

sub parse_register_dump {
    my ($file_path) = @_;

    open my $fh, '<', $file_path
        or die "Cannot open $file_path: $!";

    while (my $line = <$fh>) {
        # 匹配暫存器格式：ADDR=0xNNNN VALUE=0xNNNN
        if ($line =~ /
            ADDR=0x(?<addr>[0-9A-F]{4}) \s+
            VALUE=0x(?<value>[0-9A-F]{4,8})
        /x) {
            process_register($+{addr}, $+{value});
        }
    }
    close $fh;
}
```

---

## Python 規範

### 命名
- 遵循 PEP 8
- 型別提示（Type Hints）必須加在所有公開函數上
- 使用 `dataclass` 或 `pydantic.BaseModel` 定義資料結構

### 格式
- 使用 Black formatter（行寬 100）
- Import 排序使用 isort
- 字串一律用雙引號 `"`

### 錯誤處理
- 不可使用裸 `except:`，必須指定例外類型
- 自訂例外需繼承 `Exception`，命名後綴 `Error`
- 使用 `logging` 模組，不用 `print()`

```python
from dataclasses import dataclass


@dataclass
class RegisterConfig:
    """暫存器設定資料結構"""
    name: str
    address: int
    width: int = 32

    def validate(self) -> list[str]:
        """驗證設定是否合法，回傳錯誤訊息清單"""
        errors: list[str] = []
        if not (0x0000 <= self.address <= 0xFFFF):
            errors.append(f"位址 0x{self.address:04X} 超出範圍")
        return errors
```

---

## Code Review Checklist

審查程式碼時，請依序檢查：

1. **命名** — 是否符合上述命名規範？
2. **註解** — 複雜邏輯有沒有說明「為什麼」？
3. **錯誤處理** — 是否處理了所有可能的錯誤路徑？
4. **安全** — 有沒有潛在的 buffer overflow、NULL pointer？
5. **測試** — 新增的程式碼有沒有對應的測試？
6. **效能** — 有沒有不必要的迴圈或重複計算？
