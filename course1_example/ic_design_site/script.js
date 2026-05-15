/* ============================================
   IC 設計流程工作台 — 互動邏輯（增強版）
   ============================================ */

(function () {
   'use strict';

   // ============================================
   // 資料：8 個設計流程階段（含工具資訊）
   // ============================================
   var FLOW_STAGES =[
       {
           name: '規格定義（Specification）',
           nameEn: 'Specification',
           badge: '關鍵階段',
           badgeClass: 'stage-detail__badge--critical',
           status: 'complete',
           inputs:[
               '市場需求分析報告',
               '使用者需求文件（URD）',
               '競爭對手晶片規格比較',
               '成本目標與 BOM 估算'
          ],
           outputs:[
               '規格文件（Spec Sheet）',
               '性能目標（FPS / MIPS）',
               '功耗約束（Max Power Budget）',
               '封裝類型與 Pin Count 預估'
          ],
           risks:[
               '規格頻繁變更導致延誤',
               '未考慮特殊工況（高溫/低電壓）',
               '市場窗口錯失風險'
          ],
           tools:[
               { name: 'Jira', icon: '📋' },
               { name: 'Confluence', icon: '📖' },
               { name: 'Excel', icon: '📊' }
          ]
       },
       {
           name: '架構設計（Architecture）',
           nameEn: 'Architecture',
           badge: '關鍵階段',
           badgeClass: 'stage-detail__badge--critical',
           status: 'complete',
           inputs:[
               '規格文件（Spec Sheet）',
               '性能 / 功耗 / 面積約束',
               '介面協議（AXI / AHB / PCIe）'
          ],
           outputs:[
               '系統架構圖',
               '記憶體配置規劃',
               '匯流排架構（Bus Matrix）',
               '效能模擬報告'
          ],
           risks:[
               '匯流排瓶頸未預留足夠頻寬',
               '記憶體頻寬不足',
               '延遲預算（Latency Budget）失衡'
          ],
           tools:[
               { name: 'SystemC', icon: '🔬' },
               { name: 'MATLAB', icon: '📈' },
               { name: 'StarCCM+', icon: '⚙️' }
          ]
       },
       {
           name: 'RTL 設計（RTL Design）',
           nameEn: 'RTL Design',
           badge: '重要階段',
           badgeClass: 'stage-detail__badge--important',
           status: 'current',
           inputs:[
               '系統架構文件',
               '介面協議規範（AXI Manual）',
               'IP 規格書'
          ],
           outputs:[
               'Verilog / SystemVerilog 原始碼',
               'Package / Interface 定義',
               'RTL 程式碼審查記錄'
          ],
           risks:[
               '時脈域交叉（CDC）問題',
               '組合邏輯迴路導致 timing violation',
               '狀態機未覆蓋所有狀態'
          ],
           tools:[
               { name: 'Vivado', icon: '🔧' },
               { name: 'Verilator', icon: '✅' },
               { name: 'VS Code', icon: '📝' },
               { name: 'Git', icon: '🔀' }
          ]
       },
       {
           name: '功能模擬（Simulation / Verification）',
           nameEn: 'Simulation',
           badge: '重要階段',
           badgeClass: 'stage-detail__badge--important',
           status: 'pending',
           inputs:[
               'RTL 原始碼',
               '測試平台（Testbench）',
               '參考模型（Golden Model）'
          ],
           outputs:[
               'Wavesim / FSIM 波形檔案',
               'Coverage 報告（Code / Constraint / Functional）',
               'Bug 清單與修復記錄'
          ],
           risks:[
               'Coverage 未達 100%',
               '邊際案例（Corner Case）未覆蓋',
               'Testbench 與實際硬體行為不一致'
          ],
           tools:[
               { name: 'VCS', icon: '🔍' },
               { name: 'Xcelium', icon: '⚡' },
               { name: 'ModelSim', icon: '🎭' },
               { name: 'UVM', icon: '🏗️' }
          ]
       },
       {
           name: '邏輯綜合（Synthesis）',
           nameEn: 'Synthesis',
           badge: '重要階段',
           badgeClass: 'stage-detail__badge--important',
           status: 'pending',
           inputs:[
               'RTL 原始碼',
               'Library（.db / .lib）',
               'Constraints（SDC）'
          ],
           outputs:[
               'Gate-level Netlist',
               'Power / Area 估算報告',
               'Timing Report（Initial）'
          ],
           risks:[
               'Library 版本不匹配',
               'SDC constraints 不完整導致優化錯誤',
               'Area 超出封裝限制'
          ],
           tools:[
               { name: 'Design Compiler', icon: '🔬' },
               { name: 'Liberty', icon: '📚' },
               { name: 'SDC Editor', icon: '📐' }
          ]
       },
       {
           name: '佈局與定線（Place & Route）',
           nameEn: 'Place & Route',
           badge: '關鍵階段',
           badgeClass: 'stage-detail__badge--critical',
           status: 'pending',
           inputs:[
               'Gate-level Netlist',
               'Full library（.lib）',
               'Layer / Via 規則（Design Rules）',
               'Pre-route Constraints'
          ],
           outputs:[
               'GDSII 檔案（預覽）',
               'Detailed Routing Report',
               'ERC Report'
          ],
           risks:[
               'Routing congestion 導致無法定線',
               'IR Drop 問題（電壓降過大）',
               'Antenna 效應違反'
          ],
           tools:[
               { name: 'ICC2', icon: '🏭' },
               { name: 'Innovus', icon: '🚀' },
               { name: 'Pango', icon: '🐍' }
          ]
       },
       {
           name: '靜態時序分析（STA）',
           nameEn: 'Static Timing Analysis',
           badge: '簽核項目',
           badgeClass: 'stage-detail__badge--normal',
           status: 'pending',
           inputs:[
               'Updated Netlist（含 DRC fix）',
               'Full .lib（TT / FF / SS / SF）',
               'SDC Constraints（更新版）'
          ],
           outputs:[
               'STA Report（Setup / Hold / AC / OC）',
               'Slack Summary',
               'Timing Sign-off 報告'
          ],
           risks:[
               'Corner case 未涵蓋（慢速庫/高速庫/低電壓/高溫）',
               'Clock gating 單元未納入分析',
               '跨時脈域（CDC）未驗證'
          ],
           tools:[
               { name: 'PrimeTime', icon: '⏱️' },
               { name: 'Tempus', icon: '🕐' },
               { name: 'Conformal', icon: '🎯' }
          ]
       },
       {
           name: 'Tape-out（流片）',
           nameEn: 'Tape-out',
           badge: '最終階段',
           badgeClass: 'stage-detail__badge--normal',
           status: 'pending',
           inputs:[
               'GDSII 檔案',
               'OASIS 檔案',
               'BEOL 規則檢查報告',
               'Sign-off 報告（STA / DRC / LVS / ERC）'
          ],
           outputs:[
               'Mask 資料（Reticle）',
               'Manufacturing Drawings',
               'Tape-out 簽核文件'
          ],
           risks:[
               'Mask 資料錯誤（Data Corruption）',
               '交件時程延誤',
               'Foundry 反饋問題未解決'
          ],
           tools:[
               { name: 'KLayout', icon: '📐' },
               { name: 'Calibre', icon: '📏' },
               { name: 'Mentor Graphics', icon: '🏢' }
          ]
       }
  ];

   // ============================================
   // 資料：Verification Checklist
   // ============================================
   var CHECKLIST_ITEMS =[
       { id: 'sim_01', category: 'Simulation', label: 'System-on-Test (SoT) 驗證通過' },
       { id: 'sim_02', category: 'Simulation', label: 'Regression Test 全數通過' },
       { id: 'sim_03', category: 'Simulation', label: 'Corner Case 測試覆蓋' },
       { id: 'sim_04', category: 'Simulation', label: 'Error Injection 測試' },
       { id: 'cov_01', category: 'Coverage', label: 'Code Coverage ≥ 100%' },
       { id: 'cov_02', category: 'Coverage', label: 'Constraint Coverage ≥ 98%' },
       { id: 'cov_03', category: 'Coverage', label: 'Functional Coverage 簽核' },
       { id: 'cov_04', category: 'Coverage', label: 'Assertion 檢查（SVA）通過' },
       { id: 'lint_01', category: 'Lint', label: 'Verilog Lint 檢查通過' },
       { id: 'lint_02', category: 'Lint', label: 'CDC（跨時脈域）檢查通過' },
       { id: 'lint_03', category: 'Lint', label: 'SDC Constraints 完整性檢查' },
       { id: 'sta_01', category: 'STA', label: 'Setup Timing Slack ≥ 0（所有 Corner）' },
       { id: 'sta_02', category: 'STA', label: 'Hold Timing Slack ≥ 0（所有 Corner）' },
       { id: 'sta_03', category: 'STA', label: 'AC Margin 檢查通過' },
       { id: 'sta_04', category: 'STA', label: 'IR Drop 分析通過' },
       { id: 'drc_01', category: 'DRC/LVS', label: 'DRC（設計規則檢查）0 Error' },
       { id: 'drc_02', category: 'DRC/LVS', label: 'LVS（電路圖 vs 佈局）Match' },
       { id: 'drc_03', category: 'DRC/LVS', label: 'PEX（寄生參數提取）完成' }
  ];

   // ============================================
   // 資料：Sign-off 表格
   // ============================================
   var SIGNOFF_DATA =[
       { item: 'Timing（Setup）', target: 'Slack ≥ 0ps', actual: '—', status: 'pending', note: '等待 P&R 完成後評估' },
       { item: 'Timing（Hold）', target: 'Slack ≥ 0ps', actual: '—', status: 'pending', note: '初始綜合結果待更新' },
       { item: 'Area（面積）', target: '≤ 8.0 mm²', actual: '—', status: 'pending', note: '等待 Synthesis 完成' },
       { item: 'Power（功耗）', target: '≤ 500mW', actual: '—', status: 'pending', note: '動態 + 靜態功耗總和' },
       { item: 'Code Coverage', target: '≥ 100%', actual: '—', status: 'pending', note: '行/分支/函式覆蓋' },
       { item: 'Functional Coverage', target: '≥ 98%', actual: '—', status: 'pending', note: 'Scenario-based 覆蓋' },
       { item: 'DRC', target: '0 Error', actual: '—', status: 'pending', note: '等待 GDSII 輸出' },
       { item: 'LVS', target: 'Match', actual: '—', status: 'pending', note: '等待 PEX 提取' },
       { item: 'ERC', target: '0 Warning', actual: '—', status: 'pending', note: '電路規則檢查' }
  ];

   // ============================================
   // 資料：EDA 工具清單
   // ============================================
   var EDA_TOOLS =[
       { name: 'Synopsys VCS', vendor: 'Synopsys', use: '功能模擬', version: '2024.03', active: true },
       { name: 'Cadence Innovus', vendor: 'Cadence', use: '佈局定線', version: '22.03', active: true },
       { name: 'Synopsys Design Compiler', vendor: 'Synopsys', use: '邏輯綜合', version: '2024.03', active: true },
       { name: 'Synopsys PrimeTime', vendor: 'Synopsys', use: '靜態時序', version: '2024.03', active: true },
       { name: 'Mentor Calibre', vendor: 'Siemens', use: 'DRC/LVS', version: '2024.2', active: false },
       { name: 'Siemens Pango', vendor: 'Siemens', use: 'DRC 輕量檢查', version: '3.2', active: false }
  ];

   // ============================================
   // 資料：檔案樹
   // ============================================
   var FILE_TREE =[
       {
           name: '📁 project_novaai',
           children:[
               {
                   name: '📁 01_spec',
                   children:[
                       { name: '📄 spec_sheet_v2.3.pdf' },
                       { name: '📄 market_analysis.docx' },
                       { name: '📄 cost_target.xlsx' }
                  ]
               },
               {
                   name: '📁 02_architecture',
                   children:[
                       { name: '📄 system_arch_v3.pdf' },
                       { name: '📄 bus_matrix.xlsx' },
                       { name: '📄 perf_model.tcl' }
                  ]
               },
               {
                   name: '📁 03_rtl',
                   children:[
                       { name: '📁 cpu' },
                       { name: '📁 dma' },
                       { name: '📁 axi_intercon' },
                       { name: '📁 peripheral' },
                       { name: '📄 top.v' },
                       { name: '📄 constraints.sdc' }
                  ]
               },
               {
                   name: '📁 04_verification',
                   children:[
                       { name: '📁 tests' },
                       { name: '📁 env' },
                       { name: '📄 regression.log' },
                       { name: '📄 coverage_report.html' }
                  ]
               },
               {
                   name: '📁 05_synthesis',
                   children:[
                       { name: '📄 netlist.v' },
                       { name: '📄 area_report.pdf' },
                       { name: '📄 power_report.pdf' }
                  ]
               },
               {
                   name: '📁 06_pnr',
                   children:[
                       { name: '📄 gdsii/' },
                       { name: '📄 oasis/' },
                       { name: '📄 routing_report.pdf' }
                  ]
               },
               {
                   name: '📁 07_signoff',
                   children:[
                       { name: '📄 sta_report.pdf' },
                       { name: '📄 drc_report.pdf' },
                       { name: '📄 lvs_report.pdf' },
                       { name: '📄 signoff_summary.xlsx' }
                  ]
               }
          ]
       }
  ];

   // ============================================
   // 資料：團隊成員
   // ============================================
   var TEAM_MEMBERS =[
       { name: '王設計師', role: 'RTL 設計 Lead', initials: '王', status: 'online' },
       { name: '李驗證工程師', role: 'Verification', initials: '李', status: 'online' },
       { name: '張架構師', role: '系統架構', initials: '張', status: 'offline' },
       { name: '陳後端工程師', role: 'P&R / 佈局', initials: '陳', status: 'online' },
       { name: '林時序工程師', role: 'STA / 簽核', initials: '林', status: 'offline' },
       { name: '趙專案經理', role: '專案管理', initials: '趙', status: 'online' }
  ];

   // ============================================
   // 資料：Block Diagram 區塊資訊
   // ============================================
   var BLOCK_INFO = {
       cpu: {
           title: 'CPU Core — RISC-V 64-bit',
           specs:[
               { label: '架構', value: 'RISC-V RV64IMAFDC' },
               { label: '時脈頻率', value: '1.2 GHz' },
               { label: 'pipeline 階數', value: '15 階' },
               { label: 'L1 快取', value: '32KB 指令 + 32KB 資料' },
               { label: 'L2 快取', value: '256KB (SRAM)' },
               { label: 'AXI 介面', value: 'AXI4-3.0 (Master)' },
               { label: '位寬', value: '128-bit 資料 + 64-bit 位址' }
          ]
       },
       sram: {
           title: 'SRAM Array — On-Chip Memory',
           specs:[
               { label: '容量', value: '256 KB (256K × 64-bit)' },
               { label: '介面', value: 'AXI4-3.0 (Slave)' },
               { label: '讀寫頻寬', value: '128-bit 雙向' },
               { label: '保護機制', value: 'ECC (單bit糾正)' },
               { label: '功耗管理', value: 'Power Gating + Retention' },
               { label: '佔面積', value: '~1.8 mm²' }
          ]
       },
       dma: {
           title: 'DMA Engine — Direct Memory Access',
           specs:[
               { label: '功能', value: 'Block Data Transfer' },
               { label: '模式', value: 'Scatter / Gather' },
               { label: 'Burst 長度', value: 'Max 256 beats' },
               { label: 'AXI 介面', value: 'AXI4-3.0 (Master)' },
               { label: '優先級', value: '可程式化 (4 級)' },
               { label: '中斷', value: 'Transfer Complete / Error' }
          ]
       },
       periph: {
           title: 'Peripheral — I/O Controllers',
           specs:[
               { label: 'UART', value: '16550 相容 (4 channels)' },
               { label: 'SPI', value: '4 通道 (Max 50MHz)' },
               { label: 'I²C', value: '4 通道 (Fast+ 400kHz)' },
               { label: 'GPIO', value: '32 pins (可程式化)' },
               { label: 'Timer', value: '2 × 64-bit' },
               { label: 'AXI 介面', value: 'AXI-Lite (Slave)' }
          ]
       },
       ioring: {
           title: 'IO Ring / Pad Frame',
           specs:[
               { label: 'I/O 數量', value: '120 pins' },
               { label: '電壓等級', value: '3.3V / 1.8V / 1.2V' },
               { label: 'ESD 保護', value: 'HBM 2000V / CDM 1000V' },
               { label: '封裝類型', value: 'BGA 487 (35×35mm)' },
               { label: '封裝材料', value: 'FR-4, 12 layers' }
          ]
       },
       clk: {
           title: 'Clock & Reset Domain',
           specs:[
               { label: '外部震盪器', value: '25MHz Crystal' },
               { label: 'PLL', value: '4 倍頻 → 100MHz' },
               { label: '分頻器', value: '可程式化 (1/2/4/8/16)' },
               { label: 'Power-On Reset', value: '上電 1ms 復位' },
               { label: '低電壓偵測', value: 'LVD @ 2.7V' }
          ]
       }
   };

   // ============================================
   // 狀態
   // ============================================
   var checkedItems =[];
   var signoffRan = false;
   var currentStage = 0;
   var sidebarVisible = true;
   var currentTheme = 'dark';
   var selectedBlock = null;

   // ============================================
   // DOM 元素
   // ============================================
   var timelineStages;
   var stageTitle;
   var stageBadge;
   var stageInput;
   var stageOutput;
   var stageRisk;
   var stageProgress;
   var stageTools;
   var toolsGrid;
   var checklistGrid;
   var checklistFill;
   var checklistPercent;
   var checklistCount;
   var signoffValue;
   var signoffCards;
   var signoffTableBody;
   var btnSignoff;
   var btnExport;
   var themeToggle;
   var themeIconSun;
   var themeIconMoon;
   var sidebarToggle;
   var sidebar;
   var flowStatus;
   var edaTools;
   var blockDiagram;
   var blockDetailPanel;
   var blockDetailTitle;
   var blockDetailContent;
   var blockDetailClose;
   var gdsUploadArea;
   var gdsBrowseBtn;
   var gdsFileInput;
   var gdsViewer;
   var gdsInfo;
   var gdsCanvas;
   var gdsZoomIn;
   var gdsZoomOut;
   var gdsFit;
   var btnTools;
   var btnFiles;
   var btnTeam;
   var edaModal;
   var edaModalClose;
   var edaTableBody;
   var filesModal;
   var filesModalClose;
   var fileTree;
   var teamModal;
   var teamModalClose;
   var teamList;

   // ============================================
   // 初始化
   // ============================================
   function init() {
       cacheElements();
       bindTimeline();
       renderChecklist();
       renderSignoff();
       bindSignoffButtons();
       selectStage(0);
       bindThemeToggle();
       bindSidebarToggle();
       bindBlockDiagram();
       bindGDSViewer();
       bindModals();
       renderFlowStatus();
       renderEDATools();
       renderEDATable();
       renderFileTree();
       renderTeamList();
       updateStageProgress();
   }

   function cacheElements() {
       timelineStages = document.querySelectorAll('.timeline__stage');
       stageTitle = document.getElementById('stageTitle');
       stageBadge = document.getElementById('stageBadge');
       stageInput = document.getElementById('stageInput');
       stageOutput = document.getElementById('stageOutput');
       stageRisk = document.getElementById('stageRisk');
       stageProgress = document.getElementById('stageProgress');
       stageTools = document.getElementById('stageTools');
       toolsGrid = document.getElementById('toolsGrid');
       checklistGrid = document.getElementById('checklistGrid');
       checklistFill = document.getElementById('checklistFill');
       checklistPercent = document.getElementById('checklistPercent');
       checklistCount = document.getElementById('checklistCount');
       signoffValue = document.getElementById('signoffValue');
       signoffCards = document.getElementById('signoffCards');
       signoffTableBody = document.getElementById('signoffTableBody');
       btnSignoff = document.getElementById('btnSignoff');
       btnExport = document.getElementById('btnExport');
       themeToggle = document.getElementById('themeToggle');
       themeIconSun = document.querySelector('.theme-icon-sun');
       themeIconMoon = document.querySelector('.theme-icon-moon');
       sidebarToggle = document.getElementById('sidebarToggle');
       sidebar = document.getElementById('sidebar');
       flowStatus = document.getElementById('flowStatus');
       edaTools = document.getElementById('edaTools');
       blockDiagram = document.getElementById('blockDiagram');
       blockDetailPanel = document.getElementById('blockDetailPanel');
       blockDetailTitle = document.getElementById('blockDetailTitle');
       blockDetailContent = document.getElementById('blockDetailContent');
       blockDetailClose = document.getElementById('blockDetailClose');
       gdsUploadArea = document.getElementById('gdsUploadArea');
       gdsBrowseBtn = document.getElementById('gdsBrowseBtn');
       gdsFileInput = document.getElementById('gdsFileInput');
       gdsViewer = document.getElementById('gdsViewer');
       gdsInfo = document.getElementById('gdsInfo');
       gdsCanvas = document.getElementById('gdsCanvas');
       gdsZoomIn = document.getElementById('gdsZoomIn');
       gdsZoomOut = document.getElementById('gdsZoomOut');
       gdsFit = document.getElementById('gdsFit');
       btnTools = document.getElementById('btnTools');
       btnFiles = document.getElementById('btnFiles');
       btnTeam = document.getElementById('btnTeam');
       edaModal = document.getElementById('edaModal');
       edaModalClose = document.getElementById('edaModalClose');
       edaTableBody = document.getElementById('edaTableBody');
       filesModal = document.getElementById('filesModal');
       filesModalClose = document.getElementById('filesModalClose');
       fileTree = document.getElementById('fileTree');
       teamModal = document.getElementById('teamModal');
       teamModalClose = document.getElementById('teamModalClose');
       teamList = document.getElementById('teamList');
   }

   // ============================================
   // 流程時間軸
   // ============================================
   function bindTimeline() {
       for (var i = 0; i< timelineStages.length; i++) {
           (function (btn, idx) {
               btn.addEventListener('click', function () {
                   selectStage(idx);
               });
               btn.addEventListener('keydown', function (e) {
                   var newIdx = idx;
                   if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
                       newIdx = Math.min(idx + 1, timelineStages.length - 1);
                   } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
                       newIdx = Math.max(idx - 1, 0);
                   }
                   if (newIdx !== idx) {
                       e.preventDefault();
                       timelineStages[newIdx].focus();
                       selectStage(newIdx);
                   }
               });
           })(timelineStages[i], i);
       }
   }

   function selectStage(idx) {
       currentStage = idx;
       var data = FLOW_STAGES[idx];

       for (var i = 0; i< timelineStages.length; i++) {
           timelineStages[i].setAttribute('aria-selected', i === idx ? 'true' : 'false');
           var statusDot = timelineStages[i].querySelector('.timeline__status');
           if (statusDot) {
               statusDot.className = 'timeline__status';
               if (FLOW_STAGES[i].status === 'complete') {
                   statusDot.classList.add('timeline__status--complete');
               } else if (FLOW_STAGES[i].status === 'current') {
                   statusDot.classList.add('timeline__status--current');
               }
           }
       }

       stageTitle.textContent = '階段' + toChineseNum(idx + 1) + '：' + data.name;
       stageBadge.textContent = data.badge;
       stageBadge.className = 'stage-detail__badge ' + data.badgeClass;

       stageInput.innerHTML = '';
       for (var j = 0; j< data.inputs.length; j++) {
           var li = document.createElement('li');
           li.textContent = data.inputs[j];
           stageInput.appendChild(li);
       }

       stageOutput.innerHTML = '';
       for (var k = 0; k< data.outputs.length; k++) {
           var li2 = document.createElement('li');
           li2.textContent = data.outputs[k];
           stageOutput.appendChild(li2);
       }

       stageRisk.innerHTML = '';
       for (var m = 0; m< data.risks.length; m++) {
           var li3 = document.createElement('li');
           li3.textContent = data.risks[m];
           stageRisk.appendChild(li3);
       }

       renderTools(data.tools);
       updateStageProgress();
   }

   function toChineseNum(n) {
       var chars =['零', '一', '二', '三', '四', '五', '六', '七', '八', '九'];
       var units =['', '十', '百', '千'];
       if (n< 10) return chars[n];
       if (n === 10) return '十';
       if (n< 20) return '十' + (n > 10 ? chars[n - 10] : '');
       return String(n);
   }

   function updateStageProgress() {
       var data = FLOW_STAGES[currentStage];
       var statusText = '';
       if (data.status === 'complete') {
           statusText = '✓ 已完成';
       } else if (data.status === 'current') {
           statusText = '◉ 進行中';
       } else {
           statusText = '○ 待執行';
       }
       stageProgress.textContent = statusText;
   }

   function renderTools(tools) {
       toolsGrid.innerHTML = '';
       for (var i = 0; i< tools.length; i++) {
           var tag = document.createElement('span');
           tag.className = 'tool-tag';
           tag.innerHTML = tools[i].icon + ' ' + tools[i].name;
           toolsGrid.appendChild(tag);
       }
   }

   // ============================================
   // 側邊欄：流程進度
   // ============================================
   function renderFlowStatus() {
       flowStatus.innerHTML = '';
       for (var i = 0; i< FLOW_STAGES.length; i++) {
           var stage = FLOW_STAGES[i];
           var item = document.createElement('div');
           item.className = 'flow-status-item';
           if (stage.status === 'complete') {
               item.classList.add('flow-status-item--active');
           }
           item.setAttribute('data-stage', i);

           var dot = document.createElement('span');
           dot.className = 'flow-status__dot';
           if (stage.status === 'complete') {
               dot.classList.add('flow-status__dot--complete');
           } else if (stage.status === 'current') {
               dot.classList.add('flow-status__dot--current');
           } else {
               dot.classList.add('flow-status__dot--pending');
           }

           var label = document.createElement('span');
           label.textContent = (i + 1) + '. ' + stage.nameEn;

           item.appendChild(dot);
           item.appendChild(label);

           (function (idx) {
               item.addEventListener('click', function () {
                   selectStage(idx);
                   timelineStages[idx].focus();
               });
           })(i);

           flowStatus.appendChild(item);
       }
   }

   // ============================================
   // 側邊欄：EDA 工具狀態
   // ============================================
   function renderEDATools() {
       edaTools.innerHTML = '';
       for (var i = 0; i< EDA_TOOLS.length; i++) {
           var tool = EDA_TOOLS[i];
           var item = document.createElement('div');
           item.className = 'eda-tool-item';

           var name = document.createElement('span');
           name.className = 'eda-tool-name';
           name.textContent = tool.name;

           var status = document.createElement('span');
           status.className = 'eda-tool-status';
           if (tool.active) {
               status.classList.add('eda-tool-status--active');
               status.textContent = '使用中';
           } else {
               status.classList.add('eda-tool-status--inactive');
               status.textContent = '未使用';
           }

           item.appendChild(name);
           item.appendChild(status);
           edaTools.appendChild(item);
       }
   }

   // ============================================
   // EDA 工具管理 Modal
   // ============================================
   function renderEDATable() {
       edaTableBody.innerHTML = '';
       for (var i = 0; i< EDA_TOOLS.length; i++) {
           var tool = EDA_TOOLS[i];
           var tr = document.createElement('tr');

           var tdName = document.createElement('td');
           tdName.textContent = tool.name;

           var tdVendor = document.createElement('td');
           tdVendor.textContent = tool.vendor;

           var tdUse = document.createElement('td');
           tdUse.textContent = tool.use;

           var tdVersion = document.createElement('td');
           tdVersion.textContent = tool.version;

           var tdStatus = document.createElement('td');
           if (tool.active) {
               tdStatus.innerHTML ='<span class="eda-tool-status eda-tool-status--active">使用中</span>';
           } else {
               tdStatus.innerHTML ='<span class="eda-tool-status eda-tool-status--inactive">未使用</span>';
           }

           tr.appendChild(tdName);
           tr.appendChild(tdVendor);
           tr.appendChild(tdUse);
           tr.appendChild(tdVersion);
           tr.appendChild(tdStatus);
           edaTableBody.appendChild(tr);
       }
   }

   // ============================================
   // 檔案管理 Modal
   // ============================================
   function renderFileTree() {
       fileTree.innerHTML = '';
       renderFileNodes(FILE_TREE, fileTree, 0);
   }

   function renderFileNodes(nodes, container, depth) {
       for (var i = 0; i< nodes.length; i++) {
           var node = nodes[i];
           if (node.children) {
               var folder = document.createElement('div');
               folder.className = 'file-tree__folder';

               var header = document.createElement('div');
               header.className = 'file-tree__folder-header';
               header.style.paddingLeft = (depth * 1.2) + 'rem';

               var arrow = document.createElement('span');
               arrow.textContent = '▶';
               arrow.style.transition = 'transform 0.2s';
               arrow.style.display = 'inline-block';
               arrow.style.width = '14px';

               var folderName = document.createElement('span');
               folderName.textContent = node.name;

               header.appendChild(arrow);
               header.appendChild(folderName);

               var items = document.createElement('div');
               items.className = 'file-tree__items';
               items.style.display = 'none';

               (function () {
                   var isOpen = false;
                   header.addEventListener('click', function () {
                       isOpen = !isOpen;
                       items.style.display = isOpen ? 'block' : 'none';
                       arrow.style.transform = isOpen ? 'rotate(90deg)' : '';
                   });
               })();

               folder.appendChild(header);
               container.appendChild(folder);

               renderFileNodes(node.children, items, depth + 1);
           } else {
               var file = document.createElement('div');
               file.className = 'file-tree__file';
               file.style.paddingLeft = (depth * 1.2 + 0.8) + 'rem';
               file.textContent = node.name;
               container.appendChild(file);
           }
       }
   }

   // ============================================
   // 團隊管理 Modal
   // ============================================
   function renderTeamList() {
       teamList.innerHTML = '';
       for (var i = 0; i< TEAM_MEMBERS.length; i++) {
           var member = TEAM_MEMBERS[i];
           var item = document.createElement('div');
           item.className = 'team-member';

           var avatar = document.createElement('div');
           avatar.className = 'team-member__avatar';
           avatar.textContent = member.initials;

           var info = document.createElement('div');
           info.className = 'team-member__info';

           var name = document.createElement('div');
           name.className = 'team-member__name';
           name.textContent = member.name;

           var role = document.createElement('div');
           role.className = 'team-member__role';
           role.textContent = member.role;

           info.appendChild(name);
           info.appendChild(role);

           var status = document.createElement('span');
           status.className = 'team-member__status';
           if (member.status === 'online') {
               status.classList.add('team-member__status--online');
               status.textContent = '線上';
           } else {
               status.classList.add('team-member__status--offline');
               status.textContent = '離線';
           }

           item.appendChild(avatar);
           item.appendChild(info);
           item.appendChild(status);
           teamList.appendChild(item);
       }
   }

   // ============================================
   // 主題切換
   // ============================================
   function bindThemeToggle() {
       themeToggle.addEventListener('click', function () {
           if (currentTheme === 'dark') {
               currentTheme = 'light';
               document.body.classList.add('light-theme');
               themeIconSun.style.display = 'none';
               themeIconMoon.style.display = 'block';
           } else {
               currentTheme = 'dark';
               document.body.classList.remove('light-theme');
               themeIconSun.style.display = 'block';
               themeIconMoon.style.display = 'none';
           }
       });
   }

   // ============================================
   // 側邊欄切換
   // ============================================
   function bindSidebarToggle() {
       sidebarToggle.addEventListener('click', function () {
           sidebarVisible = !sidebarVisible;
           if (window.innerWidth<= 900) {
               sidebar.classList.toggle('visible');
           } else {
               sidebar.classList.toggle('collapsed');
           }
       });

       // 快速工具按鈕
       btnTools.addEventListener('click', function () {
           edaModal.style.display = 'flex';
       });

       btnFiles.addEventListener('click', function () {
           filesModal.style.display = 'flex';
       });

       btnTeam.addEventListener('click', function () {
           teamModal.style.display = 'flex';
       });

       // Modal 關閉按鈕
       edaModalClose.addEventListener('click', function () {
           edaModal.style.display = 'none';
       });

       filesModalClose.addEventListener('click', function () {
           filesModal.style.display = 'none';
       });

       teamModalClose.addEventListener('click', function () {
           teamModal.style.display = 'none';
       });

       // 點擊遮罩關閉
       edaModal.addEventListener('click', function (e) {
           if (e.target === edaModal) edaModal.style.display = 'none';
       });
       filesModal.addEventListener('click', function (e) {
           if (e.target === filesModal) filesModal.style.display = 'none';
       });
       teamModal.addEventListener('click', function (e) {
           if (e.target === teamModal) teamModal.style.display = 'none';
       });

       // 點擊側邊欄外關閉（手機）
       document.addEventListener('click', function (e) {
           if (window.innerWidth<= 900 && sidebarVisible && !sidebar.contains(e.target) && e.target !== sidebarToggle) {
               sidebar.classList.remove('visible');
           }
       });
   }

   // ============================================
   // Block Diagram 互動
   // ============================================
   function bindBlockDiagram() {
       var blocks = blockDiagram.querySelectorAll('.bd-block');
       for (var i = 0; i< blocks.length; i++) {
           (function (block) {
               block.addEventListener('click', function () {
                   var blockId = block.getAttribute('data-block');
                   showBlockDetail(blockId);
               });
           })(blocks[i]);
       }

       blockDetailClose.addEventListener('click', function () {
           blockDetailPanel.classList.remove('visible');
           if (selectedBlock) {
               var prev = blockDiagram.querySelector('[data-block="' + selectedBlock + '"]');
               if (prev) prev.classList.remove('bd-block--selected');
               selectedBlock = null;
           }
       });
   }

   function showBlockDetail(blockId) {
       // 取消之前的選取
       if (selectedBlock) {
           var prev = blockDiagram.querySelector('[data-block="' + selectedBlock + '"]');
           if (prev) prev.classList.remove('bd-block--selected');
       }

       selectedBlock = blockId;
       var current = blockDiagram.querySelector('[data-block="' + blockId + '"]');
       if (current) current.classList.add('bd-block--selected');

       var info = BLOCK_INFO[blockId];
       if (!info) return;

       blockDetailTitle.textContent = info.title;
       blockDetailContent.innerHTML = '';

       for (var i = 0; i< info.specs.length; i++) {
           var spec = info.specs[i];
           var specDiv = document.createElement('div');
           specDiv.className = 'bd-spec';

           var label = document.createElement('div');
           label.className = 'bd-spec-label';
           label.textContent = spec.label;

           var value = document.createElement('div');
           value.className = 'bd-spec-value';
           value.textContent = spec.value;

           specDiv.appendChild(label);
           specDiv.appendChild(value);
           blockDetailContent.appendChild(specDiv);
       }

       blockDetailPanel.classList.add('visible');
   }

   // ============================================
   // Verification Checklist
   // ============================================
   function renderChecklist() {
       checklistGrid.innerHTML = '';

       var categories = {};
       for (var i = 0; i< CHECKLIST_ITEMS.length; i++) {
           var cat = CHECKLIST_ITEMS[i].category;
           if (!categories[cat]) {
               categories[cat] =[];
           }
           categories[cat].push(CHECKLIST_ITEMS[i]);
       }

       var catKeys = Object.keys(categories);
       for (var c = 0; c< catKeys.length; c++) {
           var catName = catKeys[c];
           var catDiv = document.createElement('div');
           catDiv.style.marginTop = '0.5rem';
           catDiv.style.padding = '0.3rem 0 0.4rem 0';
           catDiv.style.borderTop = c > 0 ? '1px solid var(--border-color)' : 'none';

           var catTitle = document.createElement('div');
           catTitle.style.fontFamily = "var(--font-mono)";
           catTitle.style.fontSize = '0.75rem';
           catTitle.style.fontWeight = '600';
           catTitle.style.color = '#3b82f6';
           catTitle.style.marginBottom = '0.4rem';
           catTitle.style.letterSpacing = '0.05em';
           catTitle.textContent = catName.toUpperCase();
           catDiv.appendChild(catTitle);

           var items = categories[catName];
           for (var ii = 0; ii< items.length; ii++) {
               var item = items[ii];
               var div = document.createElement('div');
               div.className = 'checklist-item';
               div.setAttribute('data-id', item.id);
               div.setAttribute('role', 'checkbox');
               div.setAttribute('aria-checked', 'false');
               div.setAttribute('tabindex', '0');

               var checkbox = document.createElement('div');
               checkbox.className = 'checklist-item__checkbox';
               checkbox.textContent = '✓';

               var labelDiv = document.createElement('div');
               labelDiv.className = 'checklist-item__label';
               labelDiv.textContent = item.label;

               var catBadge = document.createElement('span');
               catBadge.className = 'checklist-item__category';
               catBadge.textContent = item.category;

               div.appendChild(checkbox);
               div.appendChild(labelDiv);
               div.appendChild(catBadge);

               (function (itemData, el) {
                   div.addEventListener('click', function () {
                       toggleCheckItem(itemData.id, el);
                   });
                   div.addEventListener('keydown', function (e) {
                       if (e.key === ' ' || e.key === 'Enter') {
                           e.preventDefault();
                           toggleCheckItem(itemData.id, el);
                       }
                   });
               })(item, div);

               catDiv.appendChild(div);
           }

           checklistGrid.appendChild(catDiv);
       }
   }

   function toggleCheckItem(id, el) {
       var idx = checkedItems.indexOf(id);
       if (idx >= 0) {
           checkedItems.splice(idx, 1);
           el.classList.remove('checklist-item--checked');
           el.setAttribute('aria-checked', 'false');
       } else {
           checkedItems.push(id);
           el.classList.add('checklist-item--checked');
           el.setAttribute('aria-checked', 'true');
       }
       updateChecklistProgress();
   }

   function updateChecklistProgress() {
       var total = CHECKLIST_ITEMS.length;
       var done = checkedItems.length;
       var percent = Math.round((done / total) * 100);

       checklistFill.style.width = percent + '%';
       checklistPercent.textContent = percent + '%';
       checklistCount.textContent = done + ' / ' + total + ' 項完成';
       checklistFill.parentElement.setAttribute('aria-valuenow', percent);
   }

   // ============================================
   // Sign-off Dashboard
   // ============================================
   function renderSignoff() {
       signoffCards.innerHTML = '';
       signoffTableBody.innerHTML = '';

       for (var i = 0; i< SIGNOFF_DATA.length; i++) {
           var row = SIGNOFF_DATA[i];

           var card = document.createElement('div');
           card.className = 'signoff-card';
           card.setAttribute('data-item', row.item);

           var cardLabel = document.createElement('div');
           cardLabel.className = 'signoff-card__label';
           cardLabel.textContent = row.item;

           var cardValue = document.createElement('div');
           cardValue.className = 'signoff-card__value signoff-card__value--' + row.status;
           cardValue.textContent = row.actual === '—' ? '待評估' : row.actual;

           var cardDetail = document.createElement('div');
           cardDetail.className = 'signoff-card__detail';
           cardDetail.textContent = row.note;

           card.appendChild(cardLabel);
           card.appendChild(cardValue);
           card.appendChild(cardDetail);
           signoffCards.appendChild(card);

           var tr = document.createElement('tr');
           tr.setAttribute('data-item', row.item);

           var tdItem = document.createElement('td');
           tdItem.textContent = row.item;

           var tdTarget = document.createElement('td');
           tdTarget.textContent = row.target;

           var tdActual = document.createElement('td');
           tdActual.textContent = row.actual;

           var tdStatus = document.createElement('td');
           var statusMap = { pass: 'status-pass', fail: 'status-fail', warn: 'status-warn', pending: 'status-pending' };
           var statusTextMap = { pass: '✓ 通過', fail: '✗ 未通過', warn: '⚠ 警告', pending: '○ 待評估' };
           tdStatus.className = statusMap[row.status];
           tdStatus.textContent = statusTextMap[row.status];

           var tdNote = document.createElement('td');
           tdNote.textContent = row.note;

           tr.appendChild(tdItem);
           tr.appendChild(tdTarget);
           tr.appendChild(tdActual);
           tr.appendChild(tdStatus);
           tr.appendChild(tdNote);
           signoffTableBody.appendChild(tr);
       }

       updateSignoffStatus();
   }

   function updateSignoffStatus() {
       if (!signoffRan) {
           signoffValue.textContent = '待評估';
           signoffValue.className = 'signoff-status__value signoff-status__value--pending';
           return;
       }

       var passCount = 0;
       var failCount = 0;
       var pendingCount = 0;

       for (var i = 0; i< SIGNOFF_DATA.length; i++) {
           if (SIGNOFF_DATA[i].status === 'pass') passCount++;
           else if (SIGNOFF_DATA[i].status === 'fail') failCount++;
           else pendingCount++;
       }

       if (failCount > 0) {
           signoffValue.textContent = '✗ 簽核不通過（' + failCount + '項失敗）';
           signoffValue.className = 'signoff-status__value signoff-status__value--fail';
       } else if (pendingCount > 0) {
           signoffValue.textContent = '○ 部分完成（' + pendingCount + '項待評估）';
           signoffValue.className = 'signoff-status__value signoff-status__value--pending';
       } else {
           signoffValue.textContent = '✓ 簽核通過（全部通過）';
           signoffValue.className = 'signoff-status__value signoff-status__value--pass';
       }

       signoffCards.querySelectorAll('.signoff-card__value').forEach(function (el) {
           var card = el.parentElement;
           var itemName = card.getAttribute('data-item');
           for (var i = 0; i< SIGNOFF_DATA.length; i++) {
               if (SIGNOFF_DATA[i].item === itemName) {
                   el.className = 'signoff-card__value signoff-card__value--' + SIGNOFF_DATA[i].status;
                   el.textContent = SIGNOFF_DATA[i].actual;
                   break;
               }
           }
       });

       signoffTableBody.querySelectorAll('tr').forEach(function (tr) {
           var itemName = tr.getAttribute('data-item');
           for (var i = 0; i< SIGNOFF_DATA.length; i++) {
               if (SIGNOFF_DATA[i].item === itemName) {
                   var statusTd = tr.children[3];
                   var statusMap = { pass: 'status-pass', fail: 'status-fail', warn: 'status-warn', pending: 'status-pending' };
                   var statusTextMap = { pass: '✓ 通過', fail: '✗ 未通過', warn: '⚠ 警告', pending: '○ 待評估' };
                   statusTd.className = statusMap[SIGNOFF_DATA[i].status];
                   statusTd.textContent = statusTextMap[SIGNOFF_DATA[i].status];
                   break;
               }
           }
       });
   }

   function runSignoffCheck() {
       signoffRan = true;
       var checklistDone = checkedItems.length;
       var checklistTotal = CHECKLIST_ITEMS.length;

       for (var i = 0; i< SIGNOFF_DATA.length; i++) {
           var row = SIGNOFF_DATA[i];
           if (row.item === 'Timing（Setup）') {
               row.status = checklistDone >= checklistTotal * 0.8 ? 'pass' : 'warn';
               row.actual = row.status === 'pass' ? '+12ps' : '-3ps';
               row.note = row.status === 'pass' ? '所有 corner 皆通過' : '部分 corner 需優化';
           } else if (row.item === 'Timing（Hold）') {
               row.status = checklistDone >= checklistTotal * 0.6 ? 'pass' : 'warn';
               row.actual = row.status === 'pass' ? '+8ps' : '-1ps';
           } else if (row.item === 'Area（面積）') {
               row.status = checklistDone >= checklistTotal * 0.7 ? 'pass' : 'warn';
               row.actual = row.status === 'pass' ? '7.2 mm²' : '8.5 mm²';
           } else if (row.item === 'Power（功耗）') {
               row.status = checklistDone >= checklistTotal * 0.7 ? 'pass' : 'warn';
               row.actual = row.status === 'pass' ? '380mW' : '520mW';
           } else if (row.item === 'Code Coverage') {
               row.status = checklistDone >= checklistTotal * 0.9 ? 'pass' : (checklistDone >= checklistTotal * 0.5 ? 'warn' : 'fail');
               row.actual = row.status === 'pass' ? '100%' : (row.status === 'warn' ? '94%' : '87%');
           } else if (row.item === 'Functional Coverage') {
               row.status = checklistDone >= checklistTotal * 0.85 ? 'pass' : 'warn';
               row.actual = row.status === 'pass' ? '99.2%' : '95.1%';
           } else if (row.item === 'DRC') {
               row.status = checklistDone >= checklistTotal ? 'pass' : 'pending';
               row.actual = row.status === 'pass' ? '0 Error' : '—';
           } else if (row.item === 'LVS') {
               row.status = checklistDone >= checklistTotal ? 'pass' : 'pending';
               row.actual = row.status === 'pass' ? 'Match' : '—';
           } else if (row.item === 'ERC') {
               row.status = checklistDone >= checklistTotal * 0.5 ? 'pass' : 'warn';
               row.actual = row.status === 'pass' ? '0 Warning' : '3 Warning';
           }
       }

       renderSignoff();
   }

   function bindSignoffButtons() {
       btnSignoff.addEventListener('click', function () {
           runSignoffCheck();
       });

       btnExport.addEventListener('click', function () {
           exportReport();
       });
   }

   function exportReport() {
       var now = new Date();
       var ts = now.getFullYear() +
           String(now.getMonth() + 1).padStart(2, '0') +
           String(now.getDate()).padStart(2, '0') + '_' +
           String(now.getHours()).padStart(2, '0') +
           String(now.getMinutes()).padStart(2, '0');

       var lines =[];
       lines.push('========================================');
       lines.push('IC 設計流程 — Sign-off 報告');
       lines.push('產生時間：' + now.toLocaleString('zh-TW'));
       lines.push('========================================');
       lines.push('');

       lines.push('【驗證檢查清單】');
       lines.push('完成度：' + checkedItems.length + ' / ' + CHECKLIST_ITEMS.length);
       for (var i = 0; i< CHECKLIST_ITEMS.length; i++) {
           var checked = checkedItems.indexOf(CHECKLIST_ITEMS[i].id) >= 0;
           lines.push('[' + (checked ? '✓' : ' ') +'] ' + CHECKLIST_ITEMS[i].category + ' — ' + CHECKLIST_ITEMS[i].label);
       }
       lines.push('');

       lines.push('【Sign-off 結果】');
       for (var j = 0; j< SIGNOFF_DATA.length; j++) {
           var r = SIGNOFF_DATA[j];
           var st = r.status === 'pass' ? '通過' : (r.status === 'fail' ? '未通過' : (r.status === 'warn' ? '警告' : '待評估'));
           lines.push('  ' + r.item + '：' + r.actual + '[' + st +']');
       }
       lines.push('');

       var report = lines.join('\n');

       var blob = new Blob([report], { type: 'text/plain;charset=utf-8' });
       var url = URL.createObjectURL(blob);
       var a = document.createElement('a');
       a.href = url;
       a.download = 'signoff_report_' + ts + '.txt';
       document.body.appendChild(a);
       a.click();
       document.body.removeChild(a);
       URL.revokeObjectURL(url);
   }

   // ============================================
   // GDSII 預覽區
   // ============================================
   function bindGDSViewer() {
       gdsUploadArea.addEventListener('click', function () {
           gdsFileInput.click();
       });

       gdsBrowseBtn.addEventListener('click', function (e) {
           e.stopPropagation();
           gdsFileInput.click();
       });

       gdsFileInput.addEventListener('change', function (e) {
           if (e.target.files.length > 0) {
               var file = e.target.files[0];
               showGDSViewer(file.name);
           }
       });

       // 拖放支援
       gdsUploadArea.addEventListener('dragover', function (e) {
           e.preventDefault();
           gdsUploadArea.style.borderColor = 'var(--accent-green)';
           gdsUploadArea.style.background = 'var(--accent-green-dim)';
       });

       gdsUploadArea.addEventListener('dragleave', function () {
           gdsUploadArea.style.borderColor = '';
           gdsUploadArea.style.background = '';
       });

       gdsUploadArea.addEventListener('drop', function (e) {
           e.preventDefault();
           gdsUploadArea.style.borderColor = '';
           gdsUploadArea.style.background = '';
           if (e.dataTransfer.files.length > 0) {
               var file = e.dataTransfer.files[0];
               showGDSViewer(file.name);
           }
       });

       // 縮放按鈕
       gdsZoomIn.addEventListener('click', function () {
           var svg = gdsCanvas.querySelector('.gds-svg-placeholder');
           if (svg) {
               var currentScale = parseFloat(svg.getAttribute('data-scale') || '1');
               var newScale = Math.min(currentScale + 0.2, 3);
               svg.style.transform = 'scale(' + newScale + ')';
               svg.setAttribute('data-scale', newScale);
           }
       });

       gdsZoomOut.addEventListener('click', function () {
           var svg = gdsCanvas.querySelector('.gds-svg-placeholder');
           if (svg) {
               var currentScale = parseFloat(svg.getAttribute('data-scale') || '1');
               var newScale = Math.max(currentScale - 0.2, 0.5);
               svg.style.transform = 'scale(' + newScale + ')';
               svg.setAttribute('data-scale', newScale);
           }
       });

       gdsFit.addEventListener('click', function () {
           var svg = gdsCanvas.querySelector('.gds-svg-placeholder');
           if (svg) {
               svg.style.transform = 'scale(1)';
               svg.setAttribute('data-scale', '1');
           }
       });
   }

   function showGDSViewer(fileName) {
       gdsUploadArea.style.display = 'none';
       gdsViewer.classList.add('visible');
       gdsInfo.textContent = '檔案：' + fileName;
   }

   // ============================================
   // Modal 綁定
   // ============================================
   function bindModals() {
       // 已在 bindSidebarToggle 中處理
   }

   // ============================================
   // 啟動
   // ============================================
   if (document.readyState === 'loading') {
       document.addEventListener('DOMContentLoaded', init);
   } else {
       init();
   }

})();