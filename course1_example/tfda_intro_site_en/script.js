/* ============================================
   Taiwan Food and Drug Administration (TFDA) Introduction Site
   JavaScript - Pure Vanilla JS, No External Dependencies
   ============================================ */

document.addEventListener('DOMContentLoaded', function() {
    // --- Mobile Navigation Toggle ---
    const navToggle = document.querySelector('.nav-toggle');
    const navLinks = document.querySelector('.nav-links');

    if (navToggle && navLinks) {
        navToggle.addEventListener('click', function() {
            const isActive = navLinks.classList.toggle('active');
            navToggle.setAttribute('aria-expanded', isActive);
        });

        // Close mobile nav when clicking a link
        document.querySelectorAll('.nav-link').forEach(function(link) {
            link.addEventListener('click', function() {
                navLinks.classList.remove('active');
                navToggle.setAttribute('aria-expanded', 'false');
            });
        });
    }

    // --- Business Tabs ---
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabPanels = document.querySelectorAll('.tab-panel');

    tabButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');

            // Remove active class from all buttons and panels
            tabButtons.forEach(function(btn) {
                btn.classList.remove('active');
                btn.setAttribute('aria-selected', 'false');
            });
            tabPanels.forEach(function(panel) {
                panel.classList.remove('active');
            });

            // Add active class to clicked button and corresponding panel
            this.classList.add('active');
            this.setAttribute('aria-selected', 'true');
            var targetPanel = document.getElementById(tabId + '-panel');
            if (targetPanel) {
                targetPanel.classList.add('active');
            }
        });
    });

    // --- News Filter ---
    const filterButtons = document.querySelectorAll('.filter-btn');
    const newsItems = document.querySelectorAll('.news-item');

    filterButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            var filter = this.getAttribute('data-filter');

            // Update active button
            filterButtons.forEach(function(btn) {
                btn.classList.remove('active');
            });
            this.classList.add('active');

            // Filter news items
            newsItems.forEach(function(item) {
                var category = item.getAttribute('data-category');
                if (filter === 'all' || category === filter) {
                    item.classList.remove('hidden');
                } else {
                    item.classList.add('hidden');
                }
            });
        });
    });

    // --- FAQ Accordion ---
    const faqQuestions = document.querySelectorAll('.faq-question');

    faqQuestions.forEach(function(question) {
        question.addEventListener('click', function() {
            var expanded = this.getAttribute('aria-expanded') === 'true';
            var answer = this.nextElementSibling;

            // Toggle current FAQ
            this.setAttribute('aria-expanded', !expanded);
            if (answer) {
                answer.classList.toggle('open');
            }
        });
    });

    // --- Search Functionality ---
    var searchInput = document.getElementById('searchInput');
    var searchBtn = document.getElementById('searchBtn');
    var searchResults = document.getElementById('searchResults');

    if (searchInput && searchBtn && searchResults) {
        function performSearch() {
            var query = searchInput.value.trim().toLowerCase();
            searchResults.innerHTML = '';

            if (query.length< 2) {
                searchResults.classList.remove('active');
                return;
            }

            // Collect all searchable content
            var searchableContent =[];
            document.querySelectorAll('section').forEach(function(section) {
                var sectionId = section.id;
                var headings = section.querySelectorAll('h2, h3');
                var paragraphs = section.querySelectorAll('p');
                var cards = section.querySelectorAll('.info-card, .highlight-card, .alert-card, .news-item, .faq-item');

                headings.forEach(function(heading) {
                    searchableContent.push({
                        type: 'heading',
                        text: heading.textContent.trim(),
                        element: heading,
                        sectionId: sectionId
                    });
                });

                paragraphs.forEach(function(p) {
                    if (p.textContent.trim()) {
                        searchableContent.push({
                            type: 'content',
                            text: p.textContent.trim(),
                            element: p,
                            sectionId: sectionId
                        });
                    }
                });

                cards.forEach(function(card) {
                    var cardHeading = card.querySelector('h3, h4');
                    var cardText = card.querySelector('p');
                    if (cardHeading && cardHeading.textContent.trim()) {
                        searchableContent.push({
                            type: 'card',
                            text: cardHeading.textContent.trim(),
                            element: card,
                            sectionId: sectionId
                        });
                    }
                    if (cardText && cardText.textContent.trim()) {
                        searchableContent.push({
                            type: 'card-content',
                            text: cardText.textContent.trim(),
                            element: card,
                            sectionId: sectionId
                        });
                    }
                });
            });

            // Find matches
            var matches =[];
            searchableContent.forEach(function(item) {
                if (item.text.toLowerCase().indexOf(query) !== -1) {
                    matches.push(item);
                }
            });

            // Remove duplicates by sectionId
            var uniqueMatches =[];
            var seenSections = {};
            matches.forEach(function(match) {
                if (!seenSections[match.sectionId]) {
                    uniqueMatches.push(match);
                    seenSections[match.sectionId] = true;
                }
            });

            // Display results
            if (uniqueMatches.length > 0) {
                uniqueMatches.forEach(function(match) {
                    var resultItem = document.createElement('div');
                    resultItem.className = 'search-result-item';

                    var highlightedText = match.text.replace(
                        new RegExp('(' + query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi'),
                       '<mark>$1</mark>'
                    );

                    var typeLabel = match.type === 'heading' ? 'Section' :
                                   match.type === 'card' ? 'Service' :
                                   match.type === 'card-content' ? 'Content' : 'Information';

                    resultItem.innerHTML ='<strong>' + typeLabel + ':</strong> ' + highlightedText.substring(0, 100) + (match.text.length > 100 ? '...' : '');

                    resultItem.addEventListener('click', function() {
                        var section = document.getElementById(match.sectionId);
                        if (section) {
                            section.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        }
                        searchResults.classList.remove('active');
                        searchInput.value = '';
                    });

                    searchResults.appendChild(resultItem);
                });
                searchResults.classList.add('active');
            } else {
                var noResult = document.createElement('div');
                noResult.className = 'search-result-item';
                noResult.textContent = 'No results found for "' + query + '"';
                searchResults.appendChild(noResult);
                searchResults.classList.add('active');
            }
        }

        searchBtn.addEventListener('click', performSearch);
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
        searchInput.addEventListener('input', function() {
            if (this.value.trim().length< 2) {
                searchResults.classList.remove('active');
            }
        });

        // Close search results when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.search-box')) {
                searchResults.classList.remove('active');
            }
        });
    }

    // --- Smooth Scroll for Anchor Links ---
    document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
        anchor.addEventListener('click', function(e) {
            var targetId = this.getAttribute('href');
            if (targetId === '#') return;

            var target = document.querySelector(targetId);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    // --- Active Navigation Highlight on Scroll ---
    var sections = document.querySelectorAll('section[id]');
    var navLinks = document.querySelectorAll('.nav-link');

    function highlightNavigation() {
        var scrollPos = window.scrollY + 100;

        sections.forEach(function(section) {
            var sectionTop = section.offsetTop;
            var sectionHeight = section.offsetHeight;
            var sectionId = section.getAttribute('id');

            if (scrollPos >= sectionTop && scrollPos< sectionTop + sectionHeight) {
                navLinks.forEach(function(link) {
                    link.style.background = '';
                    if (link.getAttribute('href') === '#' + sectionId) {
                        link.style.background = 'rgba(255, 255, 255, 0.2)';
                    }
                });
            }
        });
    }

    window.addEventListener('scroll', highlightNavigation);
});