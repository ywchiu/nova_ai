/**
 * 台灣食品藥物管理署 (TFDA) 介紹網站
 * 互動腳本 - 純 Vanilla JavaScript，無外部依賴
 */

(function () {
    'use strict';

    // ============================================
    // 初始化
    // ============================================
    document.addEventListener('DOMContentLoaded', function () {
        initNavigation();
        initSearch();
        initBusinessTabs();
        initNewsFilters();
        initFAQ();
        initSmoothScroll();
    });

    // ============================================
    // 1. 導航功能
    // ============================================
    function initNavigation() {
        var navToggle = document.querySelector('.nav-toggle');
        var navLinks = document.querySelector('.nav-links');

        if (!navToggle || !navLinks) return;

        navToggle.addEventListener('click', function () {
            var isActive = navLinks.classList.toggle('active');
            navToggle.setAttribute('aria-expanded', isActive);
        });

        // 點擊導航連結後關閉手機選單
        var links = navLinks.querySelectorAll('.nav-link');
        for (var i = 0; i< links.length; i++) {
            links[i].addEventListener('click', function () {
                if (navLinks.classList.contains('active')) {
                    navLinks.classList.remove('active');
                    navToggle.setAttribute('aria-expanded', 'false');
                }
            });
        }
    }

    // ============================================
    // 2. 搜尋功能
    // ============================================
    function initSearch() {
        var searchInput = document.getElementById('searchInput');
        var searchBtn = document.getElementById('searchBtn');
        var searchResults = document.getElementById('searchResults');

        if (!searchInput || !searchBtn || !searchResults) return;

        // 搜尋資料來源：所有帶有 ID 的 section
        var searchableContent =[];
        var sections = document.querySelectorAll('section[id]');

        for (var s = 0; s< sections.length; s++) {
            var section = sections[s];
            var headings = section.querySelectorAll('h2, h3');
            var paragraphs = section.querySelectorAll('p');
            var cards = section.querySelectorAll('.info-card, .highlight-card, .service-port-card, .alert-card, .news-item, .faq-item, .contact-card, .application-card');

            var sectionText = '';
            var sectionTitle = section.querySelector('h2') ? section.querySelector('h2').textContent : '';
            var sectionId = section.id;

            for (var h = 0; h< headings.length; h++) {
                sectionText += ' ' + headings[h].textContent;
            }
            for (var p = 0; p< paragraphs.length; p++) {
                sectionText += ' ' + paragraphs[p].textContent;
            }
            for (var c = 0; c< cards.length; c++) {
                var card = cards[c];
                var cardH = card.querySelector('h3, h4');
                var cardP = card.querySelector('p');
                if (cardH) sectionText += ' ' + cardH.textContent;
                if (cardP) sectionText += ' ' + cardP.textContent;
            }

            searchableContent.push({
                title: sectionTitle,
                id: sectionId,
                text: sectionText.replace(/\s+/g, ' ').trim(),
                element: section
            });
        }

        function performSearch(query) {
            searchResults.innerHTML = '';
            if (!query || query.length< 1) {
                searchResults.classList.remove('active');
                return;
            }

            var results =[];
            var lowerQuery = query.toLowerCase();

            for (var i = 0; i< searchableContent.length; i++) {
                var item = searchableContent[i];
                if (item.text.toLowerCase().indexOf(lowerQuery) !== -1) {
                    results.push(item);
                }
            }

            if (results.length === 0) {
                var noResult = document.createElement('div');
                noResult.className = 'search-result-item';
                noResult.textContent = '找不到相關內容';
                searchResults.appendChild(noResult);
            } else {
                for (var r = 0; r< results.length; r++) {
                    appendSearchResult(results[r], query);
                }
            }

            searchResults.classList.add('active');
        }

        function appendSearchResult(result, query) {
            var resultItem = document.createElement('div');
            resultItem.className = 'search-result-item';

            var highlightedTitle = highlightText(result.title, query);
            var preview = getPreview(result.text, query);

            resultItem.innerHTML = '<strong>' + highlightedTitle + '</strong>' +
                '<p style="margin:4px 0 0;font-size:0.85rem;color:#5d6d7e;">' + preview + '</p>';

            resultItem.addEventListener('click', function () {
                result.element.scrollIntoView({ behavior: 'smooth' });
                searchResults.classList.remove('active');
                searchInput.value = '';
            });

            searchResults.appendChild(resultItem);
        }

        function highlightText(text, query) {
            if (!query) return text;
            var regex = new RegExp('(' + escapeRegex(query) + ')', 'gi');
            return text.replace(regex,'<mark>$1</mark>');
        }

        function getPreview(text, query) {
            if (!query || !text) return text.substring(0, 80);
            var index = text.toLowerCase().indexOf(query.toLowerCase());
            if (index === -1) return text.substring(0, 80);
            var start = Math.max(0, index - 20);
            var end = Math.min(text.length, index + query.length + 60);
            var preview = text.substring(start, end);
            if (start > 0) preview = '...' + preview;
            if (end< text.length) preview = preview + '...';
            return preview;
        }

        function escapeRegex(string) {
            return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        }

        // 按鈕點擊
        searchBtn.addEventListener('click', function () {
            var query = searchInput.value.trim();
            performSearch(query);
        });

        // 輸入框即時搜尋（防抖）
        var debounceTimer;
        searchInput.addEventListener('input', function () {
            clearTimeout(debounceTimer);
            var query = searchInput.value.trim();
            if (query.length >= 2) {
                debounceTimer = setTimeout(function () {
                    performSearch(query);
                }, 300);
            } else {
                searchResults.classList.remove('active');
                searchResults.innerHTML = '';
            }
        });

        // 點擊外部關閉搜尋結果
        document.addEventListener('click', function (e) {
            if (!searchInput.contains(e.target) &&
                !searchBtn.contains(e.target) &&
                !searchResults.contains(e.target)) {
                searchResults.classList.remove('active');
            }
        });

        // Enter 鍵搜尋
        searchInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                clearTimeout(debounceTimer);
                var query = searchInput.value.trim();
                performSearch(query);
            }
            if (e.key === 'Escape') {
                searchResults.classList.remove('active');
                searchInput.blur();
            }
        });
    }

    // ============================================
    // 3. 業務主題切換卡
    // ============================================
    function initBusinessTabs() {
        var tabButtons = document.querySelectorAll('.tab-btn');
        var tabPanels = document.querySelectorAll('.tab-panel');

        if (tabButtons.length === 0 || tabPanels.length === 0) return;

        for (var i = 0; i< tabButtons.length; i++) {
            tabButtons[i].addEventListener('click', function () {
                var targetTab = this.getAttribute('data-tab');

                // 更新按鈕狀態
                for (var b = 0; b< tabButtons.length; b++) {
                    tabButtons[b].classList.remove('active');
                    tabButtons[b].setAttribute('aria-selected', 'false');
                }
                this.classList.add('active');
                this.setAttribute('aria-selected', 'true');

                // 切換面板
                for (var p = 0; p< tabPanels.length; p++) {
                    tabPanels[p].classList.remove('active');
                }

                var targetPanel = document.getElementById(targetTab + '-panel');
                if (targetPanel) {
                    targetPanel.classList.add('active');
                }
            });
        }
    }

    // ============================================
    // 4. 公告篩選
    // ============================================
    function initNewsFilters() {
        var filterButtons = document.querySelectorAll('.filter-btn');
        var newsItems = document.querySelectorAll('.news-item');

        if (filterButtons.length === 0 || newsItems.length === 0) return;

        for (var i = 0; i< filterButtons.length; i++) {
            filterButtons[i].addEventListener('click', function () {
                var filter = this.getAttribute('data-filter');

                // 更新按鈕狀態
                for (var b = 0; b< filterButtons.length; b++) {
                    filterButtons[b].classList.remove('active');
                }
                this.classList.add('active');

                // 篩選公告
                for (var n = 0; n< newsItems.length; n++) {
                    var item = newsItems[n];
                    var category = item.getAttribute('data-category');

                    if (filter === 'all' || category === filter) {
                        item.classList.remove('hidden');
                    } else {
                        item.classList.add('hidden');
                    }
                }
            });
        }
    }

    // ============================================
    // 5. FAQ 展開收合
    // ============================================
    function initFAQ() {
        var faqQuestions = document.querySelectorAll('.faq-question');

        if (faqQuestions.length === 0) return;

        for (var i = 0; i< faqQuestions.length; i++) {
            faqQuestions[i].addEventListener('click', function () {
                var isExpanded = this.getAttribute('aria-expanded') === 'true';
                var faqAnswer = this.nextElementSibling;

                // 收合所有其他 FAQ
                for (var q = 0; q< faqQuestions.length; q++) {
                    if (faqQuestions[q] !== this) {
                        faqQuestions[q].setAttribute('aria-expanded', 'false');
                        var otherAnswer = faqQuestions[q].nextElementSibling;
                        if (otherAnswer) {
                            otherAnswer.classList.remove('open');
                        }
                    }
                }

                // 切換當前 FAQ
                this.setAttribute('aria-expanded', !isExpanded);
                if (faqAnswer) {
                    if (isExpanded) {
                        faqAnswer.classList.remove('open');
                    } else {
                        faqAnswer.classList.add('open');
                    }
                }
            });
        }
    }

    // ============================================
    // 6. 平滑滾動
    // ============================================
    function initSmoothScroll() {
        var anchors = document.querySelectorAll('a[href^="#"]');

        for (var i = 0; i< anchors.length; i++) {
            anchors[i].addEventListener('click', function (e) {
                var href = this.getAttribute('href');
                if (href === '#') return;

                var targetId = href.substring(1);
                var targetElement = document.getElementById(targetId);

                if (targetElement) {
                    e.preventDefault();
                    var headerHeight = document.querySelector('.site-header').offsetHeight;
                    var targetPosition = targetElement.getBoundingClientRect().top + window.pageYOffset - headerHeight;

                    window.scrollTo({
                        top: targetPosition,
                        behavior: 'smooth'
                    });
                }
            });
        }
    }

})();
