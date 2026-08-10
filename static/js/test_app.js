function getOcrHighlightBoxes(ocrData, query) {
    if (!query || !query.trim() || !ocrData) return [];
    const trimmed = query.trim().toLowerCase();
    
    // We split into terms to find candidate OCR boxes (because OCR often splits phrases into individual words)
    const terms = trimmed.split(/\s+/).filter(t => t.length >= 2);
    const searchTerms = terms.length > 0 ? terms : [trimmed];
    
    const rawBoxes = [];
    ocrData.forEach(item => {
        const raw = item.text || '';
        const lower = raw.toLowerCase();
        
        searchTerms.forEach(target => {
            let startIdx = 0;
            // Exact substring match mimicking Django's icontains
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

    if (rawBoxes.length === 0) return [];
    
    rawBoxes.sort((a, b) => (Math.abs(a.top_orig - b.top_orig) < 2 ? a.left - b.left : a.top_orig - b.top_orig));

    const mergedBoxes = [];
    let currentBox = { ...rawBoxes[0] };

    for (let i = 1; i < rawBoxes.length; i++) {
        const box = rawBoxes[i];
        if (Math.abs(currentBox.top_orig - box.top_orig) < 2 && box.left - currentBox.right < 4) {
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

    // FILTER: Ensure the merged box contains exactly what the user typed!
    const finalBoxes = mergedBoxes.filter(b => {
        const normalizedText = (b.text || '').toLowerCase().replace(/\s+/g, ' ');
        const normalizedQuery = trimmed.replace(/\s+/g, ' ');
        return normalizedText.includes(normalizedQuery);
    });

    return finalBoxes.map(b => ({
        left: parseFloat(b.left.toFixed(2)),
        top: parseFloat(b.top.toFixed(2)),
        width: parseFloat((b.right - b.left).toFixed(2)),
        height: parseFloat((b.bottom - b.top).toFixed(2)),
        text: b.text || ''
    }));
}

function highlightMatch(text, query) {
    let safeText = escapeHTML(text);

    safeText = safeText.replace(/\[hl:(yellow|green|blue|pink|orange)\]/g, '<span class="hl-$1">');
    safeText = safeText.replace(/\[\/hl\]/g, '</span>');
    safeText = safeText.replace(/\*\*([^\*]+)\*\*/g, '<strong>$1</strong>');

    if (query && query.trim()) {
        const trimmedQuery = query.trim();
        const escapedPhrase = trimmedQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        
        // Exact substring match mimicking Django's `icontains`, strictly enforcing exactly what the user typed.
        // The negative lookahead (?![^<]*>) prevents matching inside HTML tags.
        const replaceGlobal = new RegExp('(' + escapedPhrase + ')(?![^<]*>)', 'gi');
        safeText = safeText.replace(replaceGlobal, '<span class="search-hit">$1</span>');
    }

    return safeText;
}
