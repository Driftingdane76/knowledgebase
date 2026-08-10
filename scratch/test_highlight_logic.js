/**
 * STANDALONE TEST SCRIPT: Highlight Logic Verification
 * Run with: node scratch\test_highlight_logic.js
 *
 * Tests:
 *   1. Multi-word query must highlight ONLY the full phrase, not individual words
 *   2. Single-word query highlights all instances of that word
 *   3. Phrase at start/end of string is highlighted
 */

// ---- COPY OF CURRENT highlightMatch LOGIC (unchanged from app.js) ----
function escapeHTML(str) {
    return String(str || '')
        .replace(/&/g, '&amp;').replace(/</g, '&lt;')
        .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}

function highlightMatch(text, query) {
    let safeText = escapeHTML(text);
    safeText = safeText.replace(/\[hl:(yellow|green|blue|pink|orange)\]/g, '<span class="hl-$1">');
    safeText = safeText.replace(/\[\/hl\]/g, '</span>');
    safeText = safeText.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    if (query && query.trim()) {
        const trimmedQuery = query.trim();
        const escapedPhrase = trimmedQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const phraseRegex = new RegExp('(^|[^a-zA-Z0-9\u00e6\u00f8\u00e5\u00c6\u00d8\u00c5])(' + escapedPhrase + ')(?=[^a-zA-Z0-9\u00e6\u00f8\u00e5\u00c6\u00d8\u00c5]|$)(?![^<]*>)', 'gi');

        if (phraseRegex.test(safeText)) {
            const replaceGlobal = new RegExp('(^|[^a-zA-Z0-9\u00e6\u00f8\u00e5\u00c6\u00d8\u00c5])(' + escapedPhrase + ')(?=[^a-zA-Z0-9\u00e6\u00f8\u00e5\u00c6\u00d8\u00c5]|$)(?![^<]*>)', 'gi');
            safeText = safeText.replace(replaceGlobal, '$1<span class="search-hit">$2</span>');
        } else if (!trimmedQuery.includes(' ')) {
            // Single-word fallback only
            const terms = trimmedQuery.split(/\s+/).filter(t => t.length >= 2).map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
            if (terms.length > 0) {
                const regex = new RegExp('(^|[^a-zA-Z0-9\u00e6\u00f8\u00e5\u00c6\u00d8\u00c5])(' + terms.join('|') + ')(?=[^a-zA-Z0-9\u00e6\u00f8\u00e5\u00c6\u00d8\u00c5]|$)(?![^<]*>)', 'gi');
                safeText = safeText.replace(regex, '$1<span class="search-hit">$2</span>');
            }
        }
    }
    return safeText;
}

// ---- TEST RUNNER ----
let passed = 0;
let failed = 0;

function contains(desc, actual, sub) {
    if (actual.includes(sub)) { console.log('  PASS: ' + desc); passed++; }
    else { console.log('  FAIL: ' + desc); console.log('     Expected to contain: ' + sub); console.log('     Got: ' + actual); failed++; }
}
function notContains(desc, actual, sub) {
    if (!actual.includes(sub)) { console.log('  PASS: ' + desc); passed++; }
    else { console.log('  FAIL: ' + desc); console.log('     Expected NOT to contain: ' + sub); console.log('     Got: ' + actual); failed++; }
}

// TEST GROUP 1: Multi-word phrase — full phrase only, no word fragments
console.log('\n[GROUP 1] Multi-word query: full phrase only\n');
const q = 'Kunden har ingen inboforsikring';
const withPhrase  = 'Vi har tjekket sagen. Kunden har ingen inboforsikring registreret.';
const withoutPhrase = 'Vi har undersøgt sagen for kunden.'; // has "har" and "kunden" but NOT full phrase

const r1 = highlightMatch(withPhrase, q);
const r2 = highlightMatch(withoutPhrase, q);

contains(    'Full phrase is wrapped as one span', r1, '<span class="search-hit">Kunden har ingen inboforsikring</span>');
notContains( '"har" must NOT be highlighted alone when multi-word phrase missing', r2, '<span class="search-hit">har</span>');
notContains( '"kunden" must NOT be highlighted alone when multi-word phrase missing', r2, '<span class="search-hit">kunden</span>');

// TEST GROUP 2: Single-word query — highlight all instances
console.log('\n[GROUP 2] Single-word query: highlight all instances\n');
const rSingle = highlightMatch('Kunden ringer ind. Vi hjalp kunden.', 'kunden');
contains( 'First "Kunden" highlighted', rSingle, '<span class="search-hit">Kunden</span>');
contains( 'Second "kunden" highlighted', rSingle, '<span class="search-hit">kunden</span>');

// TEST GROUP 3: Boundary positions
console.log('\n[GROUP 3] Phrase at string boundaries\n');
contains('Word at start highlighted', highlightMatch('inboforsikring mangler.', 'inboforsikring'), '<span class="search-hit">inboforsikring</span>');
contains('Word at end highlighted',   highlightMatch('Kunden mangler inboforsikring', 'inboforsikring'), '<span class="search-hit">inboforsikring</span>');

// SUMMARY
console.log('\n' + '='.repeat(50));
console.log('RESULTS: ' + passed + ' passed, ' + failed + ' failed');
if (failed > 0) { console.log('TESTS FAILED — do NOT edit live code yet.'); process.exit(1); }
else { console.log('ALL PASSED — safe to proceed.'); process.exit(0); }
