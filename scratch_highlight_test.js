// scratch_highlight_test.js
// TDD tests for Step 1 of getOcrHighlightBoxes (from static/js/app.js)
// Run with: node scratch_highlight_test.js

// ==========================================
// FUNCTION UNDER TEST (verbatim from app.js lines 557-623)
// ==========================================
function getOcrHighlightBoxes(ocrData, query) {
    if (!query || !query.trim() || !ocrData || !ocrData.length) return [];
    const trimmedQuery = query.trim().toLowerCase();
    const terms = trimmedQuery.split(/\s+/).filter(t => t.length > 0);
    if (!terms.length) return [];

    const boxes = [];

    // 1. If multi-word phrase query, look for matching word sequence to form a single continuous box
    if (terms.length > 1) {
        for (let i = 0; i <= ocrData.length - terms.length; i++) {
            let match = true;
            for (let j = 0; j < terms.length; j++) {
                const wordText = (ocrData[i + j].text || '').toLowerCase().replace(/^[^\wæøå]+|[^\wæøå]+$/gi, '');
                if (wordText !== terms[j] && !wordText.includes(terms[j])) {
                    match = false;
                    break;
                }
            }
            if (match) {
                const firstWord = ocrData[i];
                const lastWord = ocrData[i + terms.length - 1];
                const top = Math.min(...ocrData.slice(i, i + terms.length).map(w => w.top));
                const bottom = Math.max(...ocrData.slice(i, i + terms.length).map(w => w.top + w.height));
                const left = firstWord.left;
                const right = lastWord.left + lastWord.width;
                boxes.push({
                    left: Math.round(left * 100) / 100,
                    top: Math.round(top * 100) / 100,
                    width: Math.round(Math.max(right - left, 2) * 100) / 100,
                    height: Math.round(Math.max(bottom - top, 2) * 100) / 100
                });
                i += terms.length - 1;
            }
        }
        if (boxes.length > 0) return boxes;
    }

    // 2. Sub-box slicing: check full query phrase first, then individual terms
    ocrData.forEach(item => {
        const rawText = item.text || '';
        const lowerText = rawText.toLowerCase();
        const totalLen = rawText.length || 1;

        const targets = (trimmedQuery.length > 2 && lowerText.includes(trimmedQuery)) ? [trimmedQuery] : terms;

        targets.forEach(target => {
            let startIdx = 0;
            while ((startIdx = lowerText.indexOf(target, startIdx)) !== -1) {
                const endIdx = startIdx + target.length;
                const subLeft = item.left + (startIdx / totalLen) * item.width;
                const subWidth = Math.max((target.length / totalLen) * item.width, 2);
                boxes.push({
                    left: Math.round(subLeft * 100) / 100,
                    top: item.top,
                    width: Math.round(subWidth * 100) / 100,
                    height: item.height
                });
                startIdx = endIdx;
            }
        });
    });

    return boxes;
}

// ==========================================
// TEST RUNNER
// ==========================================
let passed = 0;
let failed = 0;

function assert(label, condition, detail) {
    if (condition) {
        console.log('  PASS: ' + label);
        passed++;
    } else {
        console.error('  FAIL: ' + label);
        if (detail !== undefined) console.error('       Got: ' + detail);
        failed++;
    }
}

// ==========================================
// STEP 1 TEST CASES
// ==========================================

// TC-1: 2-word phrase, perfect adjacent match
// Step 1 must merge firstWord.left to lastWord.left + lastWord.width into one box
console.log('\n[TC-1] 2-word phrase -- perfect adjacent match -> 1 merged box');
{
    const ocr = [
        { text: 'Mere', left: 10.0, top: 20.0, width: 8.0, height: 4.0 },
        { text: 'end',  left: 19.0, top: 20.0, width: 6.0, height: 4.0 },
    ];
    const boxes = getOcrHighlightBoxes(ocr, 'Mere end');
    assert('Exactly 1 merged box produced',               boxes.length === 1,                                     boxes.length);
    assert('Box left anchors to firstWord.left (10)',     boxes[0] && boxes[0].left === 10,                       boxes[0] && boxes[0].left);
    assert('Box right edge = lastWord.left + width (25)', boxes[0] && (boxes[0].left + boxes[0].width) === 25,    boxes[0] && (boxes[0].left + boxes[0].width));
    assert('Box height matches OCR word height (4)',      boxes[0] && boxes[0].height === 4,                      boxes[0] && boxes[0].height);
}

// TC-2: 3-word phrase across 3 adjacent OCR items
// The span must run from firstWord.left to lastWord.left + lastWord.width
console.log('\n[TC-2] 3-word phrase across 3 items -- span covers first word to last word');
{
    const ocr = [
        { text: 'Mere', left: 10.0, top: 20.0, width: 8.0, height: 4.0 },
        { text: 'end',  left: 19.0, top: 20.0, width: 6.0, height: 4.0 },
        { text: '100',  left: 26.0, top: 20.0, width: 6.0, height: 4.0 },
    ];
    const boxes = getOcrHighlightBoxes(ocr, 'Mere end 100');
    const expectedWidth = (26.0 + 6.0) - 10.0; // 22.0
    assert('Exactly 1 merged box produced',               boxes.length === 1,                       boxes.length);
    assert('Box left = 10 (firstWord.left)',               boxes[0] && boxes[0].left === 10,         boxes[0] && boxes[0].left);
    assert('Box width = ' + expectedWidth + ' (full span)', boxes[0] && boxes[0].width === expectedWidth, boxes[0] && boxes[0].width);
}

// TC-3: Adjacent words have surrounding punctuation
// Step 1 strip regex /^[^\wæøå]+|[^\wæøå]+$/gi must normalise them before comparing to terms
console.log('\n[TC-3] Adjacent words with surrounding punctuation -- strip regex must normalise');
{
    const ocr = [
        { text: '(Mere', left: 10.0, top: 20.0, width: 8.0, height: 4.0 },
        { text: 'end!',  left: 19.0, top: 20.0, width: 6.0, height: 4.0 },
    ];
    const boxes = getOcrHighlightBoxes(ocr, 'Mere end');
    assert('Punctuation stripped: 1 merged box produced', boxes.length === 1,                                     boxes.length);
    assert('Box left anchors to firstWord.left (10)',     boxes[0] && boxes[0].left === 10,                       boxes[0] && boxes[0].left);
    assert('Box right edge = 25',                         boxes[0] && (boxes[0].left + boxes[0].width) === 25,    boxes[0] && (boxes[0].left + boxes[0].width));
}

// TC-4: Query words present but non-adjacent (intervening word between them)
// Step 1 must NOT produce a merged box; falls through to Step 2 which returns 2 individual boxes
console.log('\n[TC-4] Query words non-adjacent -- Step 1 skips, Step 2 returns 2 individual boxes');
{
    const ocr = [
        { text: 'Mere',   left: 10.0, top: 20.0, width: 8.0,  height: 4.0 },
        { text: 'fundet', left: 19.0, top: 20.0, width: 10.0, height: 4.0 },
        { text: 'end',    left: 30.0, top: 20.0, width: 6.0,  height: 4.0 },
    ];
    // i=0: "mere" matches terms[0], "fundet" !== "end" -> no match at this position
    // i=1: "fundet" !== "mere" -> no match
    // Step 1 finds 0 boxes -> falls to Step 2 -> 2 individual boxes
    const boxes = getOcrHighlightBoxes(ocr, 'Mere end');
    assert('Step 1 skipped; Step 2 produced 2 boxes',    boxes.length === 2,                       boxes.length);
}

// TC-5: Two separate occurrences of the phrase in the OCR array
// Step 1 must produce 2 merged boxes (i advances by terms.length - 1 on each match)
console.log('\n[TC-5] Two separate phrase occurrences in OCR array -> 2 merged boxes');
{
    const ocr = [
        { text: 'Mere', left: 0.0,  top: 20.0, width: 8.0, height: 4.0 },
        { text: 'end',  left: 9.0,  top: 20.0, width: 6.0, height: 4.0 },
        { text: 'Mere', left: 20.0, top: 20.0, width: 8.0, height: 4.0 },
        { text: 'end',  left: 29.0, top: 20.0, width: 6.0, height: 4.0 },
    ];
    const boxes = getOcrHighlightBoxes(ocr, 'Mere end');
    assert('2 merged boxes for 2 phrase occurrences',    boxes.length === 2,                                       boxes.length);
    assert('First box left = 0',                         boxes[0] && boxes[0].left === 0,                          boxes[0] && boxes[0].left);
    assert('Second box left = 20',                       boxes[1] && boxes[1].left === 20,                         boxes[1] && boxes[1].left);
    assert('First box right edge = 15',                  boxes[0] && (boxes[0].left + boxes[0].width) === 15,      boxes[0] && (boxes[0].left + boxes[0].width));
    assert('Second box right edge = 35',                 boxes[1] && (boxes[1].left + boxes[1].width) === 35,      boxes[1] && (boxes[1].left + boxes[1].width));
}

// ==========================================
// SUMMARY
// ==========================================
console.log('\n==========================================');
console.log('STEP 1 RESULTS: ' + passed + ' passed, ' + failed + ' failed out of ' + (passed + failed) + ' assertions');
console.log('==========================================');
if (failed > 0) process.exit(1);
