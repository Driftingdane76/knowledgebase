        // Restore sidebar state immediately or auto-collapse on smaller screens (Bootstrap XL < 1200px)
        const sidebarMql = window.matchMedia('(max-width: 1199.98px)');
        if (localStorage.getItem('kb_sidebar_collapsed') === 'true' || sidebarMql.matches) {
            document.body.classList.add('sidebar-collapsed');
        }

        // Auto-hide/show when resizing the window across the breakpoint
        sidebarMql.addEventListener('change', (e) => {
            if (e.matches) {
                document.body.classList.add('sidebar-collapsed');
            } else if (localStorage.getItem('kb_sidebar_collapsed') !== 'true') {
                document.body.classList.remove('sidebar-collapsed');
            }
        });

        function getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }

        function handleImgError(el) {
            let retries = parseInt(el.dataset.retries || '0', 10);
            if (retries < 4) {
                el.dataset.retries = retries + 1;
                const delay = 500 * Math.pow(1.5, retries);
                setTimeout(() => {
                    const base = el.src.split('?')[0];
                    el.src = base + '?retry=' + Date.now();
                }, delay);
            }
        }

        // ==========================================
        // GLOBAL STATE & DOM ELEMENTS
        // ==========================================
        let activePages = [];
        let activeCategories = [];
        let activeTrendingTags = [];
        let selectedCategoryId = null;
        let editingCategoryId = null;
        let editingRowId = null;
        let editingFieldName = null;
        let editState = { id: null, categoryId: null, title: '', date: '', username: '', questionText: '', resolutionText: '', images: [] };

        let savedTextareaSelection = { id: null, start: 0, end: 0 };
        let savedDivRange = null;
        let savedDivRangeElId = null;

        document.addEventListener('selectionchange', () => {
            const sel = window.getSelection();
            if (sel.rangeCount > 0) {
                const range = sel.getRangeAt(0);
                const activeEl = document.activeElement;
                if (activeEl && activeEl.classList.contains('kb-edit-textarea')) {
                    if (activeEl.tagName === 'TEXTAREA') {
                        savedTextareaSelection = {
                            id: activeEl.id,
                            start: activeEl.selectionStart,
                            end: activeEl.selectionEnd
                        };
                    } else {
                        if (!range.collapsed && activeEl.contains(range.commonAncestorContainer)) {
                            savedDivRange = range.cloneRange();
                            savedDivRangeElId = activeEl.id;
                        }
                    }
                }
            }
        });

        // Lightbox drawing state variables
        let activeZoomedImgId = null;

        window.lightboxHasUnsavedChanges = false;
        let isDrawing = false;
        let lastX = 0;
        let lastY = 0;
        let drawColor = '#ff5f56';
        let activePencil = null;
        let drawingHistory = [];
        const maxHistory = 20;
        let isSpaceDown = false;
        let isPanning = false;
        let panStartX = 0;
        let panStartY = 0;
        let currentPanX = 0;
        let currentPanY = 0;
        let currentZoom = 1;

        let currentPage = 1;
        let currentPageSize = 50;
        let paginationMeta = { total: 0, total_pages: 1, has_next: false, has_prev: false };
        let searchDebounceTimer = null;
        let searchHits = [];
        let currentSearchHitIndex = -1;

        const rowsList = document.getElementById('rows-list');
        const emptyState = document.getElementById('empty-state');
        const searchInput = document.getElementById('search-input');
        const searchClearBtn = document.getElementById('search-clear-btn');
        const searchNavControls = document.getElementById('search-nav-controls');
        const searchNavText = document.getElementById('search-nav-text');
        const searchNavPrev = document.getElementById('search-nav-prev');
        const searchNavNext = document.getElementById('search-nav-next');
        const countBadge = document.getElementById('pages-count-badge');
        const sortSelect = document.getElementById('sort-select');
        const themeToggle = document.getElementById('theme-toggle');
        const addRowBtn = document.getElementById('add-row-btn');
        const imageOverlay = document.getElementById('image-overlay');
        const overlayImg = document.getElementById('overlay-img');
        const overlayLabel = document.getElementById('overlay-label');
        const closeOverlay = document.getElementById('close-overlay-btn');
        const sunIcon = document.getElementById('theme-icon-sun');
        const moonIcon = document.getElementById('theme-icon-moon');
        const categoriesList = document.getElementById('categories-list');
        const categorySearchInput = document.getElementById('category-search-input');
        const newCategoryInput = document.getElementById('new-category-input');
        const addCategoryBtn = document.getElementById('add-category-btn');
        const categoryTitleDisplay = document.getElementById('category-title-display');

        // ==========================================
        // INITIALIZATION & EVENT LISTENERS
        // ==========================================
        document.addEventListener('DOMContentLoaded', () => {
            // Sidebar toggle (header + searchbar)
            function toggleSidebar() {
                document.body.classList.toggle('sidebar-collapsed');
                localStorage.setItem('kb_sidebar_collapsed', document.body.classList.contains('sidebar-collapsed'));
            }
            const sidebarToggle = document.getElementById('sidebar-toggle');
            if (sidebarToggle) sidebarToggle.addEventListener('click', toggleSidebar);
            const sidebarToggleSearch = document.getElementById('sidebar-toggle-search');
            if (sidebarToggleSearch) sidebarToggleSearch.addEventListener('click', toggleSidebar);

            const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
            const tooltipList = [...tooltipTriggerList].map(el => new bootstrap.Tooltip(el));


            initTheme();
            fetchSearch();

            searchInput.addEventListener('input', () => {
                searchClearBtn.style.display = searchInput.value.length > 0 ? 'inline-block' : 'none';
                clearTimeout(searchDebounceTimer);
                searchDebounceTimer = setTimeout(() => { currentPage = 1; fetchSearch(); }, 300);
            });

            searchClearBtn.addEventListener('click', () => {
                searchInput.value = '';
                selectedCategoryId = null;
                searchClearBtn.style.display = 'none';
                currentPage = 1;
                fetchSearch();
            });
            sortSelect.addEventListener('change', () => { currentPage = 1; fetchSearch(); });
            categorySearchInput.addEventListener('input', renderCategories);

            document.getElementById('page-prev-btn').addEventListener('click', () => {
                if (currentPage > 1) { currentPage--; fetchSearch(); }
            });
            document.getElementById('page-next-btn').addEventListener('click', () => {
                if (paginationMeta.has_next) { currentPage++; fetchSearch(); }
            });

            // Sticky scroll behavior for searchbar
            const stickyWrapper = document.getElementById('sticky-controls-wrapper');
            const stickyControls = document.getElementById('sticky-controls');
            let stickyTop = stickyWrapper.getBoundingClientRect().top + window.scrollY;

            window.addEventListener('resize', () => {
                if (!stickyControls.classList.contains('is-stuck')) {
                    stickyTop = stickyWrapper.getBoundingClientRect().top + window.scrollY;
                }
            });

            window.addEventListener('scroll', () => {
                if (window.scrollY >= stickyTop) {
                    stickyControls.classList.add('is-stuck');
                } else {
                    stickyControls.classList.remove('is-stuck');
                }
            });

            addCategoryBtn.addEventListener('click', addCategory);
            newCategoryInput.addEventListener('keydown', e => { if (e.key === 'Enter') addCategory(); });

            imageOverlay.addEventListener('click', e => {
                if (!e.target.closest('.lightbox-img-wrap') && !e.target.closest('.lightbox-toolbar') && !e.target.closest('.toast-container')) {
                    closeOverlayFn();
                }
            });
            document.addEventListener('keydown', e => {
                if (e.code === 'Space' && imageOverlay.classList.contains('show')) {
                    const activeTag = document.activeElement ? document.activeElement.tagName : '';
                    if (activeTag !== 'INPUT' && activeTag !== 'TEXTAREA') {
                        isSpaceDown = true;
                        imageOverlay.style.cursor = 'grab';
                        e.preventDefault();
                    }
                }
                if (e.key === 'Escape') {
                    closeOverlayFn();
                }
                if (imageOverlay.classList.contains('show')) {
                    if (e.ctrlKey || e.metaKey) {
                        if (e.key.toLowerCase() === 'z') { undoDrawing(); e.preventDefault(); }
                    } else if (!e.altKey) {
                        if (e.key.toLowerCase() === 'c') { copyLightboxImage(); }
                        if (e.key.toLowerCase() === 's') { saveLightboxDrawing(); e.preventDefault(); }
                        if (e.key === '1') { selectPencil('red', document.querySelector('.lightbox-pencil-red')); }
                        if (e.key === '2') { selectPencil('yellow', document.querySelector('.lightbox-pencil-yellow')); }
                        if (e.key === '3') { selectPencil('green', document.querySelector('.lightbox-pencil-green')); }
                    }
                }
            });

            document.addEventListener('keyup', e => {
                if (e.code === 'Space') {
                    isSpaceDown = false;
                    isPanning = false;
                    if (imageOverlay.classList.contains('show')) {
                        imageOverlay.style.cursor = '';
                    }
                }
            });

            imageOverlay.addEventListener('mousedown', e => {
                if (isSpaceDown && e.button === 0) {
                    isPanning = true;
                    panStartX = e.clientX - currentPanX;
                    panStartY = e.clientY - currentPanY;
                    imageOverlay.style.cursor = 'grabbing';
                    e.preventDefault();
                }
            });

            window.addEventListener('mousemove', e => {
                if (isPanning) {
                    currentPanX = e.clientX - panStartX;
                    currentPanY = e.clientY - panStartY;
                    const wrap = document.querySelector('.lightbox-img-wrap');
                    if (wrap) wrap.style.transform = `translate(${currentPanX}px, ${currentPanY}px) scale(${currentZoom})`;
                }
            });

            window.addEventListener('mouseup', e => {
                if (isPanning) {
                    isPanning = false;
                    if (imageOverlay.classList.contains('show')) {
                        imageOverlay.style.cursor = isSpaceDown ? 'grab' : '';
                    }
                }
            });

            document.addEventListener('click', e => {
                if (editingRowId) {
                    const questEl = document.getElementById('edit-quest-' + editingRowId);
                    const answEl = document.getElementById('edit-answ-' + editingRowId);
                    const dateEl = document.getElementById('edit-date-' + editingRowId);
                    const userEl = document.getElementById('edit-user-' + editingRowId);

                    const toolbarQuest = document.getElementById('hltb-edit-quest-' + editingRowId);
                    const toolbarAnsw = document.getElementById('hltb-edit-answ-' + editingRowId);
                    const overlay = document.getElementById('image-overlay');

                    const isInsideInput =
                        (questEl && questEl.contains(e.target)) ||
                        (answEl && answEl.contains(e.target)) ||
                        (dateEl && dateEl.contains(e.target)) ||
                        (userEl && userEl.contains(e.target)) ||
                        (toolbarQuest && toolbarQuest.contains(e.target)) ||
                        (toolbarAnsw && toolbarAnsw.contains(e.target)) ||
                        (overlay && overlay.contains(e.target)) ||
                        e.target.closest('.hl-swatch') ||
                        e.target.closest('.hl-trigger') ||
                        (e.target.closest('label') && e.target.closest('label').querySelector('input[type="file"]'));

                    if (!isInsideInput) {
                        saveActiveRowChanges();
                    }
                }
                if (editingCategoryId) {
                    const catListEl = document.getElementById('categories-list');
                    const addCatForm = newCategoryInput.closest('.card-body');
                    if (catListEl && !catListEl.contains(e.target) && addCatForm && !addCatForm.contains(e.target)) {
                        cancelCategoryEditing();
                    }
                }
            });

            if (addRowBtn) {
                addRowBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const newRowId = 'page-' + Date.now();
                    const defaultCatId = selectedCategoryId || (activeCategories.length > 0 ? activeCategories[0].id : null);
                    const newPage = {
                        id: newRowId, categoryId: defaultCatId, title: 'New Question',
                        date: new Date().toISOString().split('T')[0],
                        username: 'anonymous', questionText: '',
                        resolutionText: '', images: [], isNew: true
                    };
                    activePages.unshift(newPage);
                    renderRows();
                    startEditingRow(newPage.id, 'question');
                });
            }

            // Lightbox Canvas Drawing Event Listeners
            const canvasEl = document.getElementById('lightbox-canvas');
            if (canvasEl) {
                const ctx = canvasEl.getContext('2d');

                function getCoords(e) {
                    const rect = canvasEl.getBoundingClientRect();
                    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
                    const clientY = e.touches ? e.touches[0].clientY : e.clientY;

                    const x = ((clientX - rect.left) / rect.width) * canvasEl.width;
                    const y = ((clientY - rect.top) / rect.height) * canvasEl.height;
                    return { x, y };
                }

                function saveCanvasState() {
                    drawingHistory.push(ctx.getImageData(0, 0, canvasEl.width, canvasEl.height));
                    if (drawingHistory.length > maxHistory) drawingHistory.shift();
                    document.getElementById('undo-btn').style.display = 'inline-flex';
                }

                window.undoDrawing = function () {
                    if (drawingHistory.length > 0) {
                        const state = drawingHistory.pop();
                        ctx.putImageData(state, 0, 0);
                        if (drawingHistory.length === 0) {
                            document.getElementById('undo-btn').style.display = 'none';
                            // If we undid everything, we could set unsaved changes to false, 
                            // but for safety we leave it as is unless we track the exact original state.
                        }
                    }
                };

                function startDrawing(e) {
                    if (!activePencil || isSpaceDown) return;
                    saveCanvasState();
                    isDrawing = true;
                    const { x, y } = getCoords(e);
                    lastX = x;
                    lastY = y;
                }

                function draw(e) {
                    if (!isDrawing || !activePencil || isSpaceDown) return;
                    e.preventDefault();

                    const { x, y } = getCoords(e);

                    ctx.beginPath();
                    ctx.moveTo(lastX, lastY);
                    ctx.lineTo(x, y);
                    ctx.strokeStyle = drawColor;
                    ctx.lineWidth = Math.max(3, Math.round(canvasEl.width / 250));
                    ctx.lineCap = 'round';
                    ctx.lineJoin = 'round';
                    ctx.stroke();

                    lastX = x;
                    lastY = y;

                    if (!window.lightboxHasUnsavedChanges) {
                        window.lightboxHasUnsavedChanges = true;
                        document.getElementById('save-img-btn').style.display = 'inline-flex';
                    }
                }

                function stopDrawing() {
                    isDrawing = false;
                }

                canvasEl.addEventListener('mousedown', startDrawing);
                canvasEl.addEventListener('mousemove', draw);
                canvasEl.addEventListener('mouseup', stopDrawing);
                canvasEl.addEventListener('mouseout', stopDrawing);

                canvasEl.addEventListener('touchstart', startDrawing, { passive: false });
                canvasEl.addEventListener('touchmove', draw, { passive: false });
                canvasEl.addEventListener('touchend', stopDrawing);
            }

            window.changeZoom = function (delta) {
                currentZoom += delta;
                if (currentZoom < 0.2) currentZoom = 0.2;
                if (currentZoom > 5) currentZoom = 5;
                const wrap = document.querySelector('.lightbox-img-wrap');
                if (wrap) wrap.style.transform = `translate(${currentPanX}px, ${currentPanY}px) scale(${currentZoom})`;
            };

            window.resetZoom = function () {
                currentZoom = 1;
                currentPanX = 0;
                currentPanY = 0;
                const wrap = document.querySelector('.lightbox-img-wrap');
                if (wrap) wrap.style.transform = `translate(0px, 0px) scale(1)`;
            };

            document.addEventListener('keydown', e => {
                const overlay = document.getElementById('image-overlay');
                if (overlay && overlay.classList.contains('show')) {
                    if (e.ctrlKey || e.metaKey) {
                        if (e.key === '+' || e.key === '=' || e.code === 'NumpadAdd') {
                            e.preventDefault();
                            changeZoom(0.2);
                        } else if (e.key === '-' || e.key === '_' || e.code === 'NumpadSubtract') {
                            e.preventDefault();
                            changeZoom(-0.2);
                        } else if (e.key === '0' || e.code === 'Numpad0') {
                            e.preventDefault();
                            resetZoom();
                        }
                    }
                }
            }, { passive: false });

            imageOverlay.addEventListener('wheel', e => {
                if (!imageOverlay.classList.contains('show')) return;
                e.preventDefault(); // Prevent browser zoom/scroll
                const zoomFactor = 0.1;
                if (e.deltaY < 0) {
                    changeZoom(zoomFactor);
                } else {
                    changeZoom(-zoomFactor);
                }
            }, { passive: false });
        });



        // ==========================================
        // THEME MANAGEMENT
        // ==========================================
        function initTheme() {
            const t = localStorage.getItem('kb_theme') || 'light';
            applyTheme(t);
            themeToggle.addEventListener('click', () => {
                const cur = document.documentElement.getAttribute('data-bs-theme');
                applyTheme(cur === 'dark' ? 'light' : 'dark');
            });
        }

        function applyTheme(t) {
            document.documentElement.setAttribute('data-bs-theme', t);
            localStorage.setItem('kb_theme', t);
            if (t === 'dark') { sunIcon.classList.add('d-none'); moonIcon.classList.remove('d-none'); }
            else { moonIcon.classList.add('d-none'); sunIcon.classList.remove('d-none'); }
        }

        let initialDeepLinkId = new URLSearchParams(window.location.search).get('id');

        // ==========================================
        // API & SEARCH LOGIC
        // ==========================================
        function fetchSearch() {
            const q = searchInput.value.trim();
            const sort = sortSelect.value;
            const params = new URLSearchParams({ sort, page: currentPage, page_size: currentPageSize });
            if (q) params.set('q', q);
            if (selectedCategoryId) params.set('category', selectedCategoryId);

            if (initialDeepLinkId) {
                params.set('target_id', initialDeepLinkId);
            }

            // Append a cache buster timestamp
            params.set('_t', Date.now());
            fetch('/api/search?' + params.toString(), { cache: 'no-store' })
                .then(r => r.json())
                .then(data => {
                    activePages = data.pages || [];
                    activeCategories = data.categories || [];
                    activeTrendingTags = data.trendingTags || [];
                    renderTrendingTags();
                    paginationMeta = data.pagination || paginationMeta;
                    if (initialDeepLinkId && data.pagination) {
                        currentPage = data.pagination.page;
                    }
                    renderCategories();
                    renderRows();
                    renderPagination();

                    if (initialDeepLinkId) {
                        const deepLinkTarget = initialDeepLinkId;
                        initialDeepLinkId = null;
                        window.history.replaceState({}, document.title, window.location.pathname);

                        setTimeout(() => {
                            const rowEl = document.getElementById('row-' + deepLinkTarget);
                            if (!rowEl) return;
                            rowEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            // Wait for smooth scroll to finish (~800ms) before flashing
                            setTimeout(() => {
                                rowEl.classList.add('flash-row');
                                setTimeout(() => {
                                    rowEl.classList.remove('flash-row');
                                    rowEl.classList.add('deep-link-target');
                                }, 4500);
                            }, 900);
                        }, 150);
                    }
                })
                .catch(e => console.error('Search error:', e));
        }

        // ==========================================
        // UTILITIES & FORMATTING
        // ==========================================
        function escapeHTML(str) {
            return String(str || '')
                .replace(/&/g, '&amp;').replace(/</g, '&lt;')
                .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
        }

        function formatDateDanish(dateStr) {
            if (!dateStr) return '';
            const parts = dateStr.split('-');
            if (parts.length === 3) return `${parts[2]}/${parts[1]}/${parts[0]}`;
            return dateStr;
        }

        function highlightMatch(text, query) {
            let safeText = escapeHTML(text);

            safeText = safeText.replace(/\[hl:(yellow|green|blue|pink|orange)\]/g, '<span class="hl-$1">');
            safeText = safeText.replace(/\[\/hl\]/g, '</span>');
            safeText = safeText.replace(/\*\*([^\*]+)\*\*/g, '<strong>$1</strong>');

            if (query && query.trim()) {
                const trimmedQuery = query.trim();
                const escapedPhrase = trimmedQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                
                const replaceGlobal = new RegExp('(^|[^a-zA-Z0-9æøåÆØÅ])(' + escapedPhrase + ')(?=[^a-zA-Z0-9æøåÆØÅ]|$)(?![^<]*>)', 'gi');
                safeText = safeText.replace(replaceGlobal, '$1<span class="search-hit">$2</span>');
            }

            return safeText;
        }

        function getCharWeight(ch) {
            if (ch === ' ') return 0.30;
            if (/[-.,:;!?'"()\[\]\/\\_]/.test(ch)) return 0.32;
            if (/[0-9]/.test(ch)) return 0.55;
            if (/[iljtfr]/.test(ch)) return 0.38;
            if (/[MWmw@%ÆØÅæøå]/.test(ch)) return 0.95;
            if (/[A-Z]/.test(ch)) return 0.75;
            return 0.55;
        }

        function calculateOffset(fullText, startIdx, matchLen) {
            let total = 0;
            for (let i = 0; i < fullText.length; i++) total += getCharWeight(fullText[i]);
            if (total === 0) total = 1;
            
            let prefix = 0;
            for (let i = 0; i < startIdx; i++) prefix += getCharWeight(fullText[i]);
            
            let match = 0;
            for (let i = startIdx; i < startIdx + matchLen; i++) match += getCharWeight(fullText[i]);
            
            return { leftRatio: prefix / total, widthRatio: match / total };
        }

        function getOcrHighlightBoxes(ocrData, query) {
            if (!query || !query.trim() || !ocrData) return [];
            const query_lower = query.trim().toLowerCase();
            const query_terms = query_lower.split(/\s+/).filter(t => t.length > 0);
            const rawBoxes = [];

            if (query_terms.length > 1) {
                let i = 0;
                while (i <= ocrData.length - query_terms.length) {
                    let match = true;
                    for (let j = 0; j < query_terms.length; j++) {
                        if (!(ocrData[i+j].text || '').toLowerCase().includes(query_terms[j])) {
                            match = false;
                            break;
                        }
                    }
                    if (match) {
                        const first = ocrData[i];
                        const last = ocrData[i + query_terms.length - 1];
                        const topVals = ocrData.slice(i, i + query_terms.length).map(w => w.top);
                        const topOrigVals = ocrData.slice(i, i + query_terms.length).map(w => w.top_orig || w.top);
                        const bottomVals = ocrData.slice(i, i + query_terms.length).map(w => w.top + (w.height || 0));
                        
                        rawBoxes.push({
                            left: first.left,
                            top: Math.min(...topVals) - 0.5,
                            right: (last.left + last.width),
                            bottom: Math.max(...bottomVals) + 0.5,
                            top_orig: Math.min(...topOrigVals),
                            text: query.trim()
                        });
                        i += query_terms.length;
                        continue;
                    }
                    i++;
                }
            }

            if (rawBoxes.length === 0) {
                const termsToSearch = query_lower.includes(' ') ? query_terms : [query_lower];
                
                ocrData.forEach(item => {
                    const raw = item.text || '';
                    const lower = raw.toLowerCase();
                    
                    termsToSearch.forEach(target => {
                        let startIdx = 0;
                        while ((startIdx = lower.indexOf(target, startIdx)) !== -1) {
                            const endIdx = startIdx + target.length;
                            const { leftRatio, widthRatio } = calculateOffset(raw, startIdx, target.length);
                            const paddingPct = Math.min(item.width * 0.035, 1.8);
                            
                            const calcLeft = item.left + (leftRatio * item.width);
                            const calcWidth = widthRatio * item.width;
                            const subLeft = Math.max(item.left, calcLeft - paddingPct);
                            const subWidth = Math.min(item.width, calcWidth + (2 * paddingPct));

                            rawBoxes.push({
                                left: subLeft,
                                top: item.top - 0.5,
                                right: subLeft + Math.max(subWidth, 2),
                                bottom: item.top + item.height + 0.5,
                                top_orig: item.top,
                                text: raw.substring(startIdx, endIdx)
                            });
                            startIdx = endIdx;
                        }
                    });
                });
            }

            if (rawBoxes.length === 0) return [];
            
            // Sort top-to-bottom, left-to-right
            rawBoxes.sort((a, b) => (Math.abs(a.top_orig - b.top_orig) < 2 ? a.left - b.left : a.top_orig - b.top_orig));

            const mergedBoxes = [];
            let currentBox = { ...rawBoxes[0] };

            for (let i = 1; i < rawBoxes.length; i++) {
                const box = rawBoxes[i];
                // Check if on the same line (top diff < 2%) and adjacent horizontally (gap < 3%)
                if (Math.abs(currentBox.top_orig - box.top_orig) < 2 && box.left - currentBox.right < 3) {
                    currentBox.right = Math.max(currentBox.right, box.right);
                    currentBox.top = Math.min(currentBox.top, box.top);
                    currentBox.bottom = Math.max(currentBox.bottom, box.bottom);
                    currentBox.text += ' ' + box.text;
                } else {
                    mergedBoxes.push(currentBox);
                    currentBox = { ...box };
                }
            }
            mergedBoxes.push(currentBox);

            return mergedBoxes.map(b => ({
                left: parseFloat(b.left.toFixed(2)),
                top: parseFloat(b.top.toFixed(2)),
                width: parseFloat((b.right - b.left).toFixed(2)),
                height: parseFloat((b.bottom - b.top).toFixed(2)),
                text: b.text || ''
            }));
        }

        const HL_SWATCH_COLORS = [
            { key: 'yellow', bg: '#facc15' },
            { key: 'green', bg: '#4ade80' },
            { key: 'blue', bg: '#60a5fa' },
            { key: 'pink', bg: '#f9a8d4' },
            { key: 'orange', bg: '#fb923c' },
        ];

        // ==========================================
        // HIGHLIGHTING & TEXT EDITOR LOGIC
        // ==========================================
        function buildHlToolbar(textareaId) {
            const swatchesHtml = HL_SWATCH_COLORS.map(c =>
                `<div class="hl-swatch swatch-${c.key}" title="Highlight ${c.key}" data-color="${c.key}" data-ta="${textareaId}" onmousedown="event.preventDefault()" onclick="event.stopPropagation();applyHighlight('${textareaId}','${c.key}')"></div>`
            ).join('');
            const clearHtml = `<div class="hl-swatch" data-color="clear" title="Remove highlight" data-ta="${textareaId}" onmousedown="event.preventDefault()" onclick="event.stopPropagation();applyHighlight('${textareaId}','clear')"><i class="fa-solid fa-eraser hl-swatch-icon"></i></div>`;
            const boldBtn = `<div class="hl-swatch" title="Bold text" onmousedown="event.preventDefault()" onclick="event.stopPropagation(); document.execCommand('bold', false, null); syncEditStateFromDOM();"><i class="fa-solid fa-bold hl-swatch-icon text-body"></i></div>`;

            return `<div class="hl-toolbar" id="hltb-${textareaId}" onmousedown="event.preventDefault()">`
                + `<div class="hl-swatches">${boldBtn}<div class="hl-swatch-divider"></div>${swatchesHtml}${clearHtml}</div>`
                + `</div>`;
        }


        function convertHtmlToBrackets(element) {
            let result = '';
            function traverse(node) {
                if (node.nodeType === Node.TEXT_NODE) {
                    result += node.nodeValue;
                } else if (node.nodeType === Node.ELEMENT_NODE) {
                    const tagName = node.tagName.toLowerCase();
                    const isSpan = tagName === 'span';
                    const hasHl = isSpan && (
                        node.classList.contains('hl-yellow') ||
                        node.classList.contains('hl-green') ||
                        node.classList.contains('hl-blue') ||
                        node.classList.contains('hl-pink') ||
                        node.classList.contains('hl-orange')
                    );

                    if (tagName === 'b' || tagName === 'strong') {
                        result += '**';
                        for (let child of node.childNodes) traverse(child);
                        result += '**';
                    } else if (hasHl) {
                        let color = '';
                        if (node.classList.contains('hl-yellow')) color = 'yellow';
                        else if (node.classList.contains('hl-green')) color = 'green';
                        else if (node.classList.contains('hl-blue')) color = 'blue';
                        else if (node.classList.contains('hl-pink')) color = 'pink';
                        else if (node.classList.contains('hl-orange')) color = 'orange';

                        result += `[hl:${color}]`;
                        for (let child of node.childNodes) {
                            traverse(child);
                        }
                        result += `[/hl]`;
                    } else if (tagName === 'br') {
                        result += '\n';
                    } else if (tagName === 'div' || tagName === 'p') {
                        if (result && !result.endsWith('\n')) {
                            result += '\n';
                        }
                        for (let child of node.childNodes) {
                            traverse(child);
                        }
                    } else {
                        for (let child of node.childNodes) {
                            traverse(child);
                        }
                    }
                }
            }
            for (let child of element.childNodes) {
                traverse(child);
            }
            return result;
        }

        window.applyHighlight = function (elementId, color) {
            const el = document.getElementById(elementId);
            if (!el) return;

            if (el.tagName === 'TEXTAREA') {
                let start = el.selectionStart;
                let end = el.selectionEnd;

                if (start === end && savedTextareaSelection.id === elementId) {
                    start = savedTextareaSelection.start;
                    end = savedTextareaSelection.end;
                }

                if (start === end) {
                    el.focus();
                    return;
                }

                const selected = el.value.slice(start, end);
                let replacement;
                if (color === 'clear') {
                    replacement = selected.replace(/\[hl:(?:yellow|green|blue|pink|orange)\](.*?)\[\/hl\]/gs, '$1');
                } else {
                    replacement = `[hl:${color}]${selected}[/hl]`;
                }
                const newVal = el.value.slice(0, start) + replacement + el.value.slice(end);
                el.value = newVal;
                const newEnd = start + replacement.length;
                el.setSelectionRange(newEnd, newEnd);
                el.focus();

                savedTextareaSelection = { id: null, start: 0, end: 0 };
            } else {
                // Contenteditable div
                let range = null;
                const selection = window.getSelection();

                if (selection.rangeCount > 0) {
                    const r = selection.getRangeAt(0);
                    if (!r.collapsed && el.contains(r.startContainer) && el.contains(r.endContainer)) {
                        range = r;
                    }
                }

                if (!range && savedDivRange && savedDivRangeElId === elementId) {
                    range = savedDivRange;
                }

                if (!range) {
                    return;
                }

                const fragment = range.extractContents();

                const spans = fragment.querySelectorAll('span[class^="hl-"]');
                spans.forEach(span => {
                    const parent = span.parentNode;
                    while (span.firstChild) {
                        parent.insertBefore(span.firstChild, span);
                    }
                    parent.removeChild(span);
                });

                let insertedNode;
                if (color === 'clear') {
                    insertedNode = document.createElement('span');
                    insertedNode.className = 'hl-clear-temp';
                    insertedNode.appendChild(fragment);
                    range.insertNode(insertedNode);
                } else {
                    insertedNode = document.createElement('span');
                    insertedNode.className = `hl-${color}`;
                    insertedNode.appendChild(fragment);
                    range.insertNode(insertedNode);
                }

                let p = insertedNode.parentNode;
                while (p && p !== el) {
                    if (p.tagName === 'SPAN' && p.className.match(/^hl-/)) {
                        const rightSpan = p.cloneNode(false);
                        let sibling = insertedNode.nextSibling;
                        while (sibling) {
                            const next = sibling.nextSibling;
                            rightSpan.appendChild(sibling);
                            sibling = next;
                        }
                        p.parentNode.insertBefore(rightSpan, p.nextSibling);
                        p.parentNode.insertBefore(insertedNode, rightSpan);
                        if (!p.textContent) p.parentNode.removeChild(p);
                        if (!rightSpan.textContent) rightSpan.parentNode.removeChild(rightSpan);
                        p = insertedNode.parentNode;
                    } else {
                        p = p.parentNode;
                    }
                }

                if (color === 'clear') {
                    const parent = insertedNode.parentNode;
                    while (insertedNode.firstChild) {
                        parent.insertBefore(insertedNode.firstChild, insertedNode);
                    }
                    parent.removeChild(insertedNode);
                }

                const allSpans = el.querySelectorAll('span[class^="hl-"]');
                allSpans.forEach(s => {
                    if (!s.textContent) s.parentNode.removeChild(s);
                });

                el.normalize();

                try {
                    selection.removeAllRanges();
                    if (color !== 'clear') {
                        const newRange = document.createRange();
                        newRange.selectNodeContents(insertedNode);
                        selection.addRange(newRange);
                    }
                } catch (e) {
                    console.warn("Could not adjust selection range:", e);
                }

                savedDivRange = null;
                savedDivRangeElId = null;
            }
            syncEditStateFromDOM();
        };

        // ==========================================
        // INLINE ROW EDITING & CRUD
        // ==========================================
        function syncEditStateFromDOM() {
            if (!editingRowId) return;
            const questEl = document.getElementById('edit-quest-' + editingRowId);
            const answEl = document.getElementById('edit-answ-' + editingRowId);
            const dateEl = document.getElementById('edit-date-' + editingRowId);
            const userEl = document.getElementById('edit-user-' + editingRowId);
            if (questEl) {
                editState.questionText = questEl.tagName === 'TEXTAREA' ? questEl.value : convertHtmlToBrackets(questEl);
            }
            if (answEl) {
                editState.resolutionText = answEl.tagName === 'TEXTAREA' ? answEl.value : convertHtmlToBrackets(answEl);
            }
            if (dateEl) editState.date = dateEl.value;
            if (userEl) editState.username = userEl.value;
        }

        function startEditingRow(pageId, field) {
            if (!userCanEdit) return;
            if (editingRowId === pageId && editingFieldName === field) return;

            if (editingRowId) {
                if (editingRowId !== pageId) {
                    saveActiveRowChanges();
                } else {
                    syncEditStateFromDOM();
                }
            }

            editingRowId = pageId;
            editingFieldName = field;

            if (!editState.id || String(editState.id) !== String(pageId)) {
                const page = activePages.find(p => String(p.id) === String(pageId));
                if (!page) return;
                editState = {
                    id: page.id, categoryId: page.categoryId, title: page.title || 'Untitled',
                    date: page.date || '', username: page.username || '',
                    questionText: page.questionText || '', resolutionText: page.resolutionText || '',
                    images: [...(page.images || [])]
                };
            }

            renderRows();
            setTimeout(() => {
                const ids = { date: 'edit-date-', username: 'edit-user-', question: 'edit-quest-', answer: 'edit-answ-' };
                const el = document.getElementById((ids[field] || 'edit-quest-') + pageId);
                if (el) {
                    el.focus();
                    if (el.type === 'date') {
                        try {
                            el.showPicker();
                        } catch (e) {
                            console.warn('showPicker not supported:', e);
                        }
                    } else if (el.setSelectionRange && el.value !== undefined) {
                        const len = el.value.length;
                        el.setSelectionRange(len, len);
                    } else if (window.getSelection && document.createRange) {
                        const range = document.createRange();
                        range.selectNodeContents(el);
                        range.collapse(false);
                        const sel = window.getSelection();
                        sel.removeAllRanges();
                        sel.addRange(range);
                    }
                }
            }, 60);
        }

        function cancelRowEditing() {
            if (editingRowId) {
                const idx = activePages.findIndex(p => String(p.id) === String(editingRowId));
                if (idx >= 0 && activePages[idx].isNew) {
                    activePages.splice(idx, 1);
                }
            }
            editingRowId = null; editingFieldName = null;
            editState = { id: null, categoryId: null, title: '', date: '', username: '', questionText: '', resolutionText: '', images: [] };
            renderRows();
        }

        function saveActiveRowChanges() {
            if (!editingRowId) return;
            syncEditStateFromDOM();
            const idx = activePages.findIndex(p => String(p.id) === String(editingRowId));
            if (idx >= 0) {
                const payload = { ...activePages[idx], ...editState };
                
                // If the user clicked away from a brand new row without typing anything, discard it.
                if (payload.isNew && (!payload.questionText || payload.questionText.trim() === '')) {
                    cancelRowEditing();
                    return;
                }
                
                if (payload.isNew) {
                    payload.id = null;
                    delete payload.isNew;
                }
                savePageToServer(payload, () => {
                    editingRowId = null; editingFieldName = null;
                    editState = { id: null, categoryId: null, title: '', date: '', username: '', questionText: '', resolutionText: '', images: [] };
                    fetchSearch();
                });
            }
        }

function savePageToServer(payload, cb) {
    // Show loading spinner on active row save button
    const saveBtn = document.querySelector(`#row-${editingRowId} .btn-outline-success i`);
    if (saveBtn) saveBtn.className = 'fa-solid fa-spinner fa-spin fa-xs';
    fetch('/api/pages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify(payload)
    })
    .then(async r => {
        if (!r.ok) {
            // If Azure returns a 504 or 500 HTML page, catch it cleanly
            let errText = await r.text();
            throw new Error(`HTTP ${r.status}: Server failed to respond properly.`);
        }
        return r.json();
    })
    .then(data => {
        if (data.page) {
            const idx = activePages.findIndex(p => String(p.id) === String(data.page.id));
            if (idx >= 0) { activePages[idx] = data.page; } else { activePages.unshift(data.page); }
        }
        if (data.categories) { activeCategories = data.categories; }
        if (data.trendingTags) { activeTrendingTags = data.trendingTags; renderTrendingTags(); }
        if (cb) cb(); else { renderCategories(); fetchSearch(); }
    }).catch(e => { 
        console.error('Save error:', e); 
        alert('Save failed: ' + e.message); 
    });
}

        function deleteRow(pageId) {
            if (!confirm('Delete this entry?')) return;
            fetch('/api/pages/' + pageId, { method: 'DELETE', headers: { 'X-CSRFToken': getCookie('csrftoken') } })
                .then(async r => {
                    if (!r.ok) {
                        let errText = await r.text();
                        throw new Error(`HTTP ${r.status}: ${errText}`);
                    }
                    return r.json();
                })
                .then(data => {
                    if (data.error) {
                        throw new Error(data.error);
                    }
                    activePages = activePages.filter(p => String(p.id) !== String(pageId));
                    if (data.categories) { activeCategories = data.categories; }
                    if (data.trendingTags) { activeTrendingTags = data.trendingTags; renderTrendingTags(); }
                    renderCategories();
                    renderRows();
                    fetchSearch();
                })
                .catch(e => {
                    console.error('Delete error:', e);
                    alert('Delete failed: ' + e.message);
                });
        }

        // ==========================================
        // IMAGE ATTACHMENTS
        // ==========================================
        function handleFileAttachment(file) {
            if (!file || !file.type.startsWith('image/')) return;
            const img = new Image();
            img.src = URL.createObjectURL(file);
            img.onload = () => {
                const canvas = document.createElement('canvas');
                canvas.width = img.width; canvas.height = img.height;
                canvas.getContext('2d').drawImage(img, 0, 0, img.width, img.height);
                const dataUrl = canvas.toDataURL('image/webp', 0.8);
                const cleanName = (file.name ? file.name.replace(/\.[^/.]+$/, '') : 'image') + '.webp';
                editState.images.push({ id: 'img-' + Date.now() + '-' + Math.floor(Math.random() * 1000), name: cleanName, dataUrl });
                renderEditStateImages();
                URL.revokeObjectURL(img.src);
            };
        }

        function renderEditStateImages() {
            const c = document.getElementById('edit-images-list-' + editingRowId);
            if (!c) return;
            c.innerHTML = '';
            editState.images.forEach(img => {
                const w = document.createElement('div');
                w.className = 'img-remove-wrap';
                w.innerHTML = `<img src="${img.dataUrl}" class="img-thumb">`
                    + `<button class="img-remove-btn" onclick="event.stopPropagation(); removeEditStateImage('${img.id}')"><i class="fa-solid fa-trash-can fa-xs"></i></button>`;
                c.appendChild(w);
            });
        }

        window.removeEditStateImage = id => { editState.images = editState.images.filter(i => String(i.id) !== String(id)); renderEditStateImages(); };

        // ==========================================
        // LIGHTBOX & CANVAS ANNOTATION
        // ==========================================
        function zoomImage(imgId) {
            activeZoomedImgId = imgId;
            let img = null;
            for (let page of activePages) { img = (page.images || []).find(i => String(i.id) === String(imgId)); if (img) break; }
            if (!img) return;
            overlayImg.src = img.dataUrl;
            overlayLabel.textContent = img.name || 'Attached Image';

            // Reset drawing variables

            currentZoom = 1;
            currentPanX = 0;
            currentPanY = 0;
            const wrap = document.querySelector('.lightbox-img-wrap');
            if (wrap) wrap.style.transform = `translate(0px, 0px) scale(1)`;

            window.lightboxHasUnsavedChanges = false;
            document.getElementById('save-img-btn').style.display = 'none';
            document.getElementById('undo-btn').style.display = 'none';
            drawingHistory = [];
            deactivateDrawing();

            const canvas = document.getElementById('lightbox-canvas');
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            const initCanvas = () => {
                canvas.width = overlayImg.naturalWidth;
                canvas.height = overlayImg.naturalHeight;
                ctx.clearRect(0, 0, canvas.width, canvas.height);
            };

            if (overlayImg.complete) {
                initCanvas();
            } else {
                overlayImg.onload = initCanvas;
            }

            const overlayContainer = document.getElementById('lightbox-highlight-container');
            overlayContainer.innerHTML = '';
            const q = searchInput.value.toLowerCase().trim();
            if (q && img.ocrData && img.ocrData.length) {
                getOcrHighlightBoxes(img.ocrData, q).forEach(b => {
                    const box = document.createElement('div');
                    box.className = 'search-hit position-absolute lightbox-hit';
                    box.style.left = `${b.left}%`; box.style.top = `${b.top}%`;
                    box.style.width = `${b.width}%`; box.style.height = `${b.height}%`;
                    box.style.display = 'flex';
                    box.style.alignItems = 'center';
                    box.style.justifyContent = 'center';
                    box.style.whiteSpace = 'nowrap';
                    box.style.overflow = 'hidden';
                    box.style.fontSize = 'min(1.5vw, 12px)';
                    box.textContent = b.text;
                    overlayContainer.appendChild(box);
                });
            }
            imageOverlay.classList.add('show');
        }

        window.closeOverlayFn = function () {
            const overlay = document.getElementById('image-overlay');
            if (overlay.classList.contains('show') && window.lightboxHasUnsavedChanges) {
                const toastEl = document.getElementById('lightboxConfirmToast');
                const toast = new bootstrap.Toast(toastEl);
                toast.show();
                return;
            }
            confirmCloseOverlay();
        };

        window.confirmCloseOverlay = function () {
            const overlay = document.getElementById('image-overlay');
            overlay.classList.remove('show');

            const toastEl = document.getElementById('lightboxConfirmToast');
            const toast = bootstrap.Toast.getInstance(toastEl);
            if (toast) toast.hide();


            currentZoom = 1;
            currentPanX = 0;
            currentPanY = 0;
            const wrap = document.querySelector('.lightbox-img-wrap');
            if (wrap) wrap.style.transform = `translate(0px, 0px) scale(1)`;

            window.lightboxHasUnsavedChanges = false;
            deactivateDrawing();
        };

        window.selectPencil = function (colorName, element) {
            const colors = {
                'red': '#ff5f56',
                'yellow': '#ffbd2e',
                'green': '#27c93f'
            };

            const canvas = document.getElementById('lightbox-canvas');

            if (activePencil === colorName) {
                deactivateDrawing();
                return;
            }

            document.querySelectorAll('.lightbox-pencils i').forEach(el => el.classList.remove('active'));

            activePencil = colorName;
            drawColor = colors[colorName];
            element.classList.add('active');

            canvas.style.pointerEvents = 'auto';
            canvas.style.cursor = 'crosshair';
        };

        function deactivateDrawing() {
            const canvas = document.getElementById('lightbox-canvas');
            activePencil = null;
            document.querySelectorAll('.lightbox-pencils i').forEach(el => el.classList.remove('active'));
            if (canvas) {
                canvas.style.pointerEvents = 'none';
                canvas.style.cursor = 'default';
            }
        }

        async function saveLightboxDrawing() {
            if (!activeZoomedImgId || !window.lightboxHasUnsavedChanges) return;

            const imgEl = document.getElementById('overlay-img');
            const canvasEl = document.getElementById('lightbox-canvas');
            const saveBtn = document.getElementById('save-img-btn');

            const saveLabel = document.getElementById('save-img-label');
            const saveIcon = saveBtn.querySelector('i');
            const originalText = saveLabel.textContent;
            saveLabel.textContent = 'Saving...';
            saveIcon.className = 'fa-solid fa-spinner fa-spin';

            const tempCanvas = document.createElement('canvas');
            tempCanvas.width = imgEl.naturalWidth;
            tempCanvas.height = imgEl.naturalHeight;
            const tempCtx = tempCanvas.getContext('2d');

            tempCtx.drawImage(imgEl, 0, 0);
            tempCtx.drawImage(canvasEl, 0, 0, canvasEl.width, canvasEl.height, 0, 0, tempCanvas.width, tempCanvas.height);

            const updatedDataUrl = tempCanvas.toDataURL('image/webp', 0.85);

            let found = false;
            let targetPage = null;
            for (let page of activePages) {
                const img = (page.images || []).find(i => String(i.id) === String(activeZoomedImgId));
                if (img) {
                    img.dataUrl = updatedDataUrl;
                    targetPage = page;
                    found = true;
                    break;
                }
            }

            if (found && targetPage) {
                savePageToServer(targetPage, () => {
                    imgEl.src = updatedDataUrl;

                    currentZoom = 1;
                    currentPanX = 0;
                    currentPanY = 0;
                    const wrap = document.querySelector('.lightbox-img-wrap');
                    if (wrap) wrap.style.transform = `translate(0px, 0px) scale(1)`;

                    window.lightboxHasUnsavedChanges = false;
                    const ctx = canvasEl.getContext('2d');
                    ctx.clearRect(0, 0, canvasEl.width, canvasEl.height);

                    saveLabel.textContent = 'Saved!';
                    saveIcon.className = 'fa-solid fa-check text-success';
                    drawingHistory = [];
                    document.getElementById('undo-btn').style.display = 'none';
                    setTimeout(() => {
                        saveBtn.style.display = 'none';
                        saveLabel.textContent = 'Save';
                        saveIcon.className = 'fa-solid fa-cloud-arrow-up';
                    }, 1500);
                });
            } else {
                alert('Could not find the target image to save.');
                saveLabel.textContent = 'Failed';
                saveIcon.className = 'fa-solid fa-triangle-exclamation';
                setTimeout(() => {
                    saveLabel.textContent = originalText;
                    saveIcon.className = 'fa-solid fa-cloud-arrow-up';
                }, 2000);
            }
        }

        async function copyLightboxImage() {
            const img = document.getElementById('overlay-img');
            const canvasEl = document.getElementById('lightbox-canvas');
            if (!img || !img.src) return;

            const btn = document.getElementById('copy-img-btn');
            const label = document.getElementById('copy-img-label');

            // Draw the image onto a canvas so we can export it as a blob
            const canvas = document.createElement('canvas');
            const tempImg = new Image();
            tempImg.crossOrigin = 'anonymous';

            const overlayAnnotations = (ctx) => {
                if (canvasEl) {
                    ctx.drawImage(canvasEl, 0, 0, canvasEl.width, canvasEl.height, 0, 0, canvas.width, canvas.height);
                }
            };

            tempImg.onload = async () => {
                canvas.width = tempImg.naturalWidth;
                canvas.height = tempImg.naturalHeight;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(tempImg, 0, 0);
                overlayAnnotations(ctx);

                if (navigator.clipboard && window.ClipboardItem) {
                    // Modern Clipboard API — copies actual image data
                    canvas.toBlob(async (blob) => {
                        try {
                            await navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })]);
                            showCopyFeedback(btn, label, true);
                        } catch (err) {
                            console.warn('Clipboard write failed, falling back to download:', err);
                            fallbackDownload(canvas, label);
                        }
                    }, 'image/png');
                } else {
                    // Fallback: trigger a download
                    fallbackDownload(canvas, label);
                }
            };
            tempImg.onerror = () => {
                // src is already loaded in the overlay img — use it directly
                canvas.width = img.naturalWidth;
                canvas.height = img.naturalHeight;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0);
                overlayAnnotations(ctx);
                fallbackDownload(canvas, label);
            };
            tempImg.src = img.src;
        }

        function showCopyFeedback(btn, label, success) {
            btn.classList.add(success ? 'copy-success' : 'copy-error');
            label.textContent = success ? '✓ Copied!' : 'Failed';
            setTimeout(() => {
                btn.classList.remove('copy-success', 'copy-error');
                label.textContent = 'Copy';
            }, 2000);
        }

        function fallbackDownload(canvas, label) {
            const a = document.createElement('a');
            const filename = (label ? label.textContent : 'screenshot') || 'screenshot';
            a.download = filename.replace(/\.[^.]+$/, '') + '.png';
            a.href = canvas.toDataURL('image/png');
            a.click();
        }

        // ==========================================
        // CATEGORY MANAGEMENT
        // ==========================================
        window.selectCategory = function (catId) {
            if (editingRowId) saveActiveRowChanges();
            searchInput.value = '';
            searchClearBtn.style.display = 'none';
            selectedCategoryId = catId;
            currentPage = 1;
            fetchSearch();
        };

        function addCategory() {
            const name = newCategoryInput.value.trim();
            if (!name) return;
            fetch('/api/categories', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') }, body: JSON.stringify({ name }) })
                .then(r => r.json())
                .then(data => {
                    activeCategories = data.categories || [];
                    activeTrendingTags = data.trendingTags || [];
                    renderTrendingTags(); newCategoryInput.value = ''; renderCategories();
                })
                .catch(e => console.error('Error adding category:', e));
        }

        window.startEditingCategory = function (catId) {
            editingCategoryId = catId; renderCategories();
            setTimeout(() => { const el = document.getElementById('edit-category-input-' + catId); if (el) { el.focus(); el.select(); } }, 50);
        };

        window.cancelCategoryEditing = function () { editingCategoryId = null; renderCategories(); };

        window.saveCategoryChanges = function (catId) {
            const el = document.getElementById('edit-category-input-' + catId);
            if (!el) return;
            const newName = el.value.trim();
            if (!newName) { alert('Category name cannot be empty'); return; }
            fetch('/api/categories', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') }, body: JSON.stringify({ id: catId, name: newName }) })
                .then(r => r.json())
                .then(data => {
                    activeCategories = data.categories || [];
                    activeTrendingTags = data.trendingTags || [];
                    renderTrendingTags(); editingCategoryId = null; renderCategories();
                })
                .catch(e => console.error('Error renaming category:', e));
        };

        window.deleteCategory = function (catId) {
            if (!confirm('Delete this category? ALL Q&As in this category will be deleted permanently!')) return;
            fetch('/api/categories/' + catId, { method: 'DELETE', headers: { 'X-CSRFToken': getCookie('csrftoken') } })
                .then(r => r.json())
                .then(data => {
                    activeCategories = data.categories || [];
                    activeTrendingTags = data.trendingTags || [];
                    renderTrendingTags();
                    if (String(selectedCategoryId) === String(catId)) { selectedCategoryId = null; }
                    renderCategories(); fetchSearch();
                })
                .catch(e => console.error('Error deleting category:', e));
        };

        function renderCategories() {
            // Find the container holding both the input and the icon (usually an .input-group)
            const searchWrapper = categorySearchInput.closest('.input-group') || categorySearchInput.parentElement;

            if (activeCategories.length > 7) {
                searchWrapper.style.display = '';
            } else {
                searchWrapper.style.display = 'none';
                categorySearchInput.value = ''; // clear any active filter when hidden
            }
            const query = categorySearchInput.value.toLowerCase().trim();
            categoriesList.innerHTML = '';
            const totalCount = paginationMeta.total !== undefined ? paginationMeta.total : activePages.length;

            const allLi = document.createElement('li');
            allLi.className = 'nav-item';
            allLi.innerHTML = `
            <a href="#" class="nav-link cat-link category-item d-flex justify-content-between align-items-center ${selectedCategoryId === null ? 'active' : ''}" data-id="null" onclick="selectCategory(null); return false;">
                <div class="d-flex align-items-center gap-2 overflow-hidden text-nowrap">
                    <i class="fa-solid fa-list-check fa-sm text-primary-subtle"></i>
                    <span class="category-name text-truncate cat-name-text">All Questions</span>
                </div>
                <span class="badge rounded-pill bg-secondary-subtle text-secondary cat-count-badge">${totalCount}</span>
            </a>
        `;
            categoriesList.appendChild(allLi);

            activeCategories.filter(cat => !query || cat.name.toLowerCase().includes(query)).forEach(cat => {
                const li = document.createElement('li');
                li.className = 'nav-item category-item-wrap';
                
                // FIX 1: Cast both to strings for rename mode
                if (String(editingCategoryId) === String(cat.id)) {
                    li.innerHTML = `
                    <div class="px-2 py-1" onclick="event.stopPropagation()">
                        <div class="input-group input-group-sm">
                            <input type="text" id="edit-category-input-${cat.id}" class="form-control form-control-sm" value="${escapeHTML(cat.name)}" onkeydown="if(event.key==='Enter')saveCategoryChanges('${cat.id}'); if(event.key==='Escape')cancelCategoryEditing();">
                            <button class="btn btn-success btn-sm px-2" onclick="saveCategoryChanges('${cat.id}')"><i class="fa-solid fa-check"></i></button>
                            <button class="btn btn-secondary btn-sm px-2" onclick="cancelCategoryEditing()"><i class="fa-solid fa-xmark"></i></button>
                        </div>
                    </div>
                `;
                } else {
                    const pageCount = cat.pageCount !== undefined ? cat.pageCount : 0;
                    li.innerHTML = `
                    <!-- FIX 2: Cast both to strings for active class -->
                    <a href="#" class="nav-link cat-link category-item d-flex justify-content-between align-items-center ${String(selectedCategoryId) === String(cat.id) ? 'active' : ''}" data-id="${cat.id}" onclick="selectCategory('${cat.id}'); return false;">
                        <div class="d-flex align-items-center gap-2 overflow-hidden text-nowrap">
                            <i class="fa-solid fa-tag fa-sm text-primary-subtle"></i>
                            <span class="category-name text-truncate cat-name-text">${escapeHTML(cat.name)}</span>
                        </div>
                        <div class="d-flex align-items-center gap-2">
                            <span class="badge rounded-pill bg-secondary-subtle text-secondary cat-count-badge">${pageCount}</span>
                            <div class="category-actions d-flex gap-2">
                                ${userCanEdit ? `<button class="p-0 hover-primary edit-cat-btn cat-action-btn" onclick="event.stopPropagation(); startEditingCategory('${cat.id}')" title="Rename"><i class="fa-solid fa-pen"></i></button>` : ''}
                                ${userIsSuperuser ? `<button class="p-0 delete-cat-btn cat-action-btn" onclick="event.stopPropagation(); deleteCategory('${cat.id}')" title="Delete"><i class="fa-solid fa-trash-can"></i></button>` : ''}
                            </div>
                        </div>
                    </div>
                `;
                }
                categoriesList.appendChild(li);
            });
        }


        // ==========================================
        // RENDERING & UI GENERATION
        // ==========================================
        function renderTrendingTags() {
            const container = document.getElementById('trending-tags-container');
            if (!container) return;
            container.innerHTML = '';
            if (!activeTrendingTags || activeTrendingTags.length === 0) {
                container.innerHTML = '<span class="text-secondary text-xs">No tags yet.</span>';
                return;
            }
            const currentQ = searchInput.value.trim().toLowerCase();
            activeTrendingTags.forEach(tag => {
                const badge = document.createElement('span');
                const isSelected = currentQ === tag.name.toLowerCase();
                badge.className = `badge rounded-pill px-2 py-1 cursor-pointer text-xs ${isSelected ? 'active shadow-sm' : ''}`;
                badge.textContent = `${tag.name} (${tag.count})`;
                badge.title = isSelected ? `Fjern filter: ${tag.name}` : `Filtrér efter ${tag.name}`;
                badge.onclick = () => {
                    if (isSelected) {
                        searchInput.value = '';
                    } else {
                        searchInput.value = tag.name;
                        selectedCategoryId = null;
                    }
                    searchClearBtn.style.display = searchInput.value.length > 0 ? 'inline-block' : 'none';
                    currentPage = 1;
                    fetchSearch();
                };
                container.appendChild(badge);
            });
        }

        function renderRows() {
            const q = searchInput.value.toLowerCase().trim();
            rowsList.innerHTML = '';
            let filtered = activePages;
            if (selectedCategoryId !== null) { 
                filtered = filtered.filter(p => String(p.categoryId) === String(selectedCategoryId)); 
            }
            categoryTitleDisplay.textContent = selectedCategoryId === null
                ? (categoryTitleDisplay.getAttribute('data-default-title') || 'All Questions')
                : (activeCategories.find(c => String(c.id) === String(selectedCategoryId))?.name || 'Filtered Category');

            filtered = filtered.filter(p => {
                if (!q) return true;
                const terms = q.split(/\s+/).filter(t => t.length > 0);
                return terms.every(term => {
                    const formattedDate = formatDateDanish(p.date);
                    const textMatch = [p.date, formattedDate, p.username, p.questionText, p.resolutionText].some(v => v && v.toLowerCase().includes(term));
                    if (textMatch) return true;
                    return (p.images || []).some(img => img.extractedText && img.extractedText.toLowerCase().includes(term));
                });
            });

            const sortBy = sortSelect.value;
            filtered.sort((a, b) => {
                if (sortBy === 'date-desc') return (b.date || '').localeCompare(a.date || '');
                if (sortBy === 'date-asc') return (a.date || '').localeCompare(b.date || '');
                if (sortBy === 'user-asc') return (a.username || '').localeCompare(b.username || '', undefined, { sensitivity: 'base' });
                if (sortBy === 'user-desc') return (b.username || '').localeCompare(a.username || '', undefined, { sensitivity: 'base' });
                return 0;
            });

            countBadge.textContent = paginationMeta.total !== undefined ? paginationMeta.total : filtered.length;
            if (!filtered.length) { emptyState.classList.remove('d-none'); return; }
            emptyState.classList.add('d-none');

            filtered.forEach(page => {
                const li = document.createElement('li');
                const isE = String(editingRowId) === String(page.id);

                const isDateEditing = isE && editingFieldName === 'date';
                const isUserEditing = isE && editingFieldName === 'username';

                const dateDisplay = isDateEditing
                    ? '<div class="d-flex flex-column gap-1 w-100">'
                    + '<div class="d-flex align-items-center gap-1 mb-1">'
                    + '<button class="btn btn-sm btn-outline-success py-0 px-1" onclick="event.stopPropagation();saveActiveRowChanges()" title="Save"><i class="fa-solid fa-check fa-xs"></i></button>'
                    + '<button class="btn btn-sm btn-outline-secondary py-0 px-1" onclick="event.stopPropagation();cancelRowEditing()" title="Cancel"><i class="fa-solid fa-xmark fa-xs"></i></button>'
                    + '</div>'
                    + '<input type="date" id="edit-date-' + page.id + '" value="' + escapeHTML(editState.date) + '" class="kb-edit-input font-mono m-0" onclick="this.showPicker()" onfocus="this.showPicker()" onkeydown="if(event.key===\'Enter\')saveActiveRowChanges();else if(event.key===\'Escape\')cancelRowEditing();else event.preventDefault();">'
                    + '</div>'
                    : '<span class="badge-date fw-semibold" ondblclick="event.stopPropagation();startEditingRow(\'' + page.id + '\',\'date\')">' + (highlightMatch(formatDateDanish(isE ? editState.date : page.date), q) || '—') + '</span>';

                const userDisplay = isUserEditing
                    ? '<div class="d-flex flex-column gap-1 w-100">'
                    + '<div class="d-flex align-items-center gap-1 mb-1">'
                    + '<button class="btn btn-sm btn-outline-success py-0 px-1" onclick="event.stopPropagation();saveActiveRowChanges()" title="Save"><i class="fa-solid fa-check fa-xs"></i></button>'
                    + '<button class="btn btn-sm btn-outline-secondary py-0 px-1" onclick="event.stopPropagation();cancelRowEditing()" title="Cancel"><i class="fa-solid fa-xmark fa-xs"></i></button>'
                    + '</div>'
                    + '<input type="text" id="edit-user-' + page.id + '" value="' + escapeHTML(editState.username) + '" class="kb-edit-input m-0" onkeydown="if(event.key===\'Enter\')saveActiveRowChanges();if(event.key===\'Escape\')cancelRowEditing();">'
                    + '</div>'
                    : '<span class="badge-user" ondblclick="event.stopPropagation();startEditingRow(\'' + page.id + '\',\'username\')">@' + highlightMatch(isE ? editState.username : page.username, q) + '</span>';

                const metaHtml = '<div class="d-flex flex-column gap-2 w-100 align-items-start">'
                    + dateDisplay
                    + userDisplay
                    + '</div>';

                let thumbsView = (page.images || []).map(img => {
                    let hlBoxes = '';
                    if (q && img.ocrData && img.ocrData.length) {
                        getOcrHighlightBoxes(img.ocrData, q).forEach(b => {
                            hlBoxes += '<div class="search-hit position-absolute" style="left:' + b.left + '%;top:' + b.top + '%;width:' + b.width + '%;height:' + b.height + '%;"></div>';
                        });
                    }
                    return '<div class="screenshot-container mb-2" onclick="event.stopPropagation()">'
                        + '<img src="' + img.dataUrl + '" class="img-screenshot img-fluid" onerror="handleImgError(this)" onclick="zoomImage(\'' + img.id + '\')" title="' + escapeHTML(img.name) + '">'
                        + (hlBoxes ? '<div class="ocr-highlight-layer">' + hlBoxes + '</div>' : '')
                        + '</div>';
                }).join('');

                const questTaId = 'edit-quest-' + page.id;
                const answTaId = 'edit-answ-' + page.id;
                const questHtml = isE && editingFieldName === 'question'
                    ? '<div class="d-flex flex-column w-100">'
                    + '<div class="d-flex align-items-center justify-content-between mb-1">'
                    + '<div class="d-flex align-items-center gap-1">'
                    + '<label class="btn btn-sm btn-outline-secondary py-0 px-1" title="Attach image"><i class="fa-solid fa-paperclip fa-xs"></i><input type="file" accept="image/*" class="d-none" onchange="handleFileAttachment(this.files[0])"></label>'
                    + '<button class="btn btn-sm btn-outline-success py-0 px-1" onclick="event.stopPropagation();saveActiveRowChanges()" title="Save"><i class="fa-solid fa-check fa-xs"></i></button>'
                    + '<button class="btn btn-sm btn-outline-secondary py-0 px-1" onclick="event.stopPropagation();cancelRowEditing()" title="Cancel"><i class="fa-solid fa-xmark fa-xs"></i></button>'
                    + '</div>'
                    + buildHlToolbar(questTaId)
                    + '</div>'
                    + '<div class="textarea-wrap">'
                    + '<div id="' + questTaId + '" contenteditable="true" class="kb-edit-textarea overflow-y-auto" onkeydown="if(event.key===\'Escape\')cancelRowEditing();">'
                    + highlightMatch(editState.questionText, '')
                    + '</div>'
                    + '</div>'
                    + '<div class="d-flex flex-wrap gap-1 mt-1" id="edit-images-list-' + page.id + '">'
                    + editState.images.map(img => '<div class="img-remove-wrap"><img src="' + img.dataUrl + '" class="img-thumb"><button class="img-remove-btn" onclick="event.stopPropagation();removeEditStateImage(\'' + img.id + '\')"><i class="fa-solid fa-trash-can fa-xs"></i></button></div>').join('')
                    + '</div>'
                    + '</div>'
                    : '<div class="w-100"><p class="mb-1 lh-base quest-text-render">' + highlightMatch(isE ? editState.questionText : page.questionText, q) + '</p>' + (thumbsView ? '<div class="d-flex flex-column gap-1 mt-2">' + thumbsView + '</div>' : '') + '</div>';

                const resTextVal = isE ? editState.resolutionText : page.resolutionText;
                const isUnanswered = !resTextVal || resTextVal.trim() === '';

                const answHtml = isE && editingFieldName === 'answer'
                    ? '<div class="d-flex flex-column w-100">'
                    + '<div class="d-flex align-items-center justify-content-between mb-1">'
                    + '<div class="d-flex align-items-center gap-1">'
                    + '<button class="btn btn-sm btn-outline-success py-0 px-1" onclick="event.stopPropagation();saveActiveRowChanges()" title="Save"><i class="fa-solid fa-check fa-xs"></i></button>'
                    + '<button class="btn btn-sm btn-outline-secondary py-0 px-1" onclick="event.stopPropagation();cancelRowEditing()" title="Cancel"><i class="fa-solid fa-xmark fa-xs"></i></button>'
                    + '</div>'
                    + buildHlToolbar(answTaId)
                    + '</div>'
                    + '<div class="textarea-wrap">'
                    + '<div id="' + answTaId + '" contenteditable="true" class="kb-edit-textarea overflow-y-auto mono" onkeydown="if(event.key===\'Escape\')cancelRowEditing();">'
                    + highlightMatch(editState.resolutionText, '')
                    + '</div>'
                    + '</div>'
                    + '</div>'
                    : (() => {
                        const resText = highlightMatch(resTextVal, q) || '<span class="text-secondary fst-italic needs-answer-placeholder"><i class="fa-solid fa-pen-to-square me-2"></i>Needs an answer...</span>';
                        return '<div class="resolution-container w-100">'
                            + '<div class="cell-hover-actions">'
                            + '<button class="btn-copy-resolution" onclick="event.stopPropagation(); copyRowLink(\'' + page.id + '\', this)" title="Copy Share Link"><i class="fa-solid fa-link"></i></button>'
                            + '<button class="btn-copy-resolution" onclick="event.stopPropagation(); copyResolutionText(this, \'' + page.id + '\')" title="Copy Resolution"><i class="fa-regular fa-copy"></i></button>'
                            + (userIsSuperuser ? '<button class="btn-delete-row-hover" onclick="event.stopPropagation(); deleteRow(\'' + page.id + '\')" title="Delete Row"><i class="fa-solid fa-trash-can"></i></button>' : '')
                            + '</div>'
                            + '<div class="w-100 font-mono lh-base resolution-text-render">' + resText + '</div>'
                            + '</div>';
                    })();

                const adminMetaHtml = isUnanswered ? '' : '<div class="d-flex flex-column gap-2 w-100 align-items-start">'
                    + '<span class="badge-date fw-semibold">' + (page.date ? formatDateDanish(page.date) : '—') + '</span>'
                    + '<span class="badge-user">@DKquality</span>'
                    + '</div>';

                li.innerHTML = '<div class="kb-row row g-0 m-0" id="row-' + page.id + '">'
                    + `<div class="kb-cell col-12 col-md-1">${metaHtml}</div>`
                    + `<div class="kb-cell col-12 col-md-5" ondblclick="${isE && editingFieldName === 'question' ? '' : 'event.stopPropagation();startEditingRow(\'' + page.id + '\',\'question\')'}">${questHtml}</div>`
                    + `<div class="kb-cell col-12 col-md-5 ${isUnanswered ? 'needs-answer-glow' : ''}" ondblclick="${isE && editingFieldName === 'answer' ? '' : 'event.stopPropagation();startEditingRow(\'' + page.id + '\',\'answer\')'}">${answHtml}</div>`
                    + `<div class="kb-cell col-12 col-md-1">${adminMetaHtml}</div>`
                    + '</div>';

                if (isE && editingFieldName === 'question') {
                    setTimeout(() => {
                        const ta = document.getElementById('edit-quest-' + page.id);
                        if (!ta) return;
                        ta.addEventListener('dragover', e => e.preventDefault());
                        ta.addEventListener('drop', e => { e.preventDefault(); if (e.dataTransfer.files[0]) handleFileAttachment(e.dataTransfer.files[0]); });
                        ta.addEventListener('paste', e => {
                            let hasImage = false;
                            if (e.clipboardData && e.clipboardData.items) {
                                for (const item of e.clipboardData.items) {
                                    if (item.type.startsWith('image/')) {
                                        handleFileAttachment(item.getAsFile());
                                        hasImage = true;
                                    }
                                }
                            }
                            if (hasImage) {
                                e.preventDefault();
                                return;
                            }
                            const text = e.clipboardData.getData('text/plain');
                            if (text) {
                                e.preventDefault();
                                const selection = window.getSelection();
                                if (!selection.rangeCount) return;
                                selection.deleteFromDocument();
                                selection.getRangeAt(0).insertNode(document.createTextNode(text));
                                selection.collapseToEnd();
                                syncEditStateFromDOM();
                            }
                        });
                    }, 30);
                }

                if (isE && editingFieldName === 'answer') {
                    setTimeout(() => {
                        const ta = document.getElementById('edit-answ-' + page.id);
                        if (!ta) return;
                        ta.addEventListener('paste', e => {
                            const text = e.clipboardData.getData('text/plain');
                            if (text) {
                                e.preventDefault();
                                const selection = window.getSelection();
                                if (!selection.rangeCount) return;
                                selection.deleteFromDocument();
                                selection.getRangeAt(0).insertNode(document.createTextNode(text));
                                selection.collapseToEnd();
                                syncEditStateFromDOM();
                            }
                        });
                    }, 30);
                }

                rowsList.appendChild(li);
            });

            setTimeout(initSearchNavigation, 50);
        }

        function initSearchNavigation() {
            searchHits = Array.from(document.querySelectorAll('.search-hit'));
            currentSearchHitIndex = -1;

            if (searchHits.length > 0) {
                searchNavControls.classList.remove('d-none');
                searchNavControls.classList.add('d-flex');
                searchInput.parentElement.classList.add('has-clear');
                jumpToSearchHit(0);
            } else {
                searchNavControls.classList.remove('d-flex');
                searchNavControls.classList.add('d-none');
                searchInput.parentElement.classList.remove('has-clear');
            }
        }

        function jumpToSearchHit(index) {
            if (searchHits.length === 0) return;
            
            if (currentSearchHitIndex >= 0 && currentSearchHitIndex < searchHits.length) {
                searchHits[currentSearchHitIndex].classList.remove('active-search-hit');
            }
            
            currentSearchHitIndex = index;
            if (currentSearchHitIndex < 0) currentSearchHitIndex = searchHits.length - 1;
            if (currentSearchHitIndex >= searchHits.length) currentSearchHitIndex = 0;
            
            const target = searchHits[currentSearchHitIndex];
            target.classList.add('active-search-hit');
            target.scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            searchNavText.textContent = `${currentSearchHitIndex + 1}/${searchHits.length}`;
        }

        if (searchNavPrev) {
            searchNavPrev.addEventListener('click', (e) => {
                e.preventDefault();
                jumpToSearchHit(currentSearchHitIndex - 1);
            });
        }

        if (searchNavNext) {
            searchNavNext.addEventListener('click', (e) => {
                e.preventDefault();
                jumpToSearchHit(currentSearchHitIndex + 1);
            });
        }

        // ==========================================
        // CLIPBOARD & GLOBAL EVENTS
        // ==========================================
        function copyResolutionText(btn, pageId) {
            const page = activePages.find(p => String(p.id) === String(pageId));
            if (!page) return;
            navigator.clipboard.writeText(page.resolutionText || '').then(() => {
                const icon = btn.querySelector('i');
                icon.className = 'fa-solid fa-check text-success';
                btn.style.borderColor = '#10b981';
                setTimeout(() => { icon.className = 'fa-regular fa-copy'; btn.style.borderColor = ''; }, 1500);
            }).catch(err => console.error('Failed to copy:', err));
        }

        function copyRowLink(pageId, btn) {
            const url = window.location.origin + window.location.pathname + '?id=' + pageId;
            navigator.clipboard.writeText(url).then(() => {
                const icon = btn.querySelector('i');
                icon.className = 'fa-solid fa-check text-success';
                btn.style.borderColor = '#10b981';
                setTimeout(() => { icon.className = 'fa-solid fa-link'; btn.style.borderColor = ''; }, 1500);
            }).catch(err => console.error('Failed to copy link:', err));
        }

        // Global paste-to-search
        document.addEventListener('paste', e => {
            const active = document.activeElement;
            if (active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.isContentEditable)) return;
            if (e.clipboardData) {
                const text = e.clipboardData.getData('text');
                if (text && text.trim()) {
                    e.preventDefault();
                    searchInput.value = text.trim();
                    searchInput.dispatchEvent(new Event('input'));
                    searchInput.focus();
                }
            }
        });
        // Auto-refresh timer (10 minutes)
        setInterval(() => {
            // Only auto-refresh if the user isn't actively inline-editing or viewing a lightbox image
            if (!editingRowId && !activeZoomedImgId && !window.lightboxHasUnsavedChanges) {
                fetchSearch();
            }
        }, 10 * 60 * 1000);
