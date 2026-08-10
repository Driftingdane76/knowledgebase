const lower = "annulleret skader";
const trimmed = "mere end 100 resultater";
const terms = trimmed.split(/\s+/).filter(t => t.length >= 2);
const targets = (trimmed.length > 2 && lower.includes(trimmed)) ? [trimmed] : terms;

console.log("Targets:", targets);

targets.forEach(target => {
    let startIdx = 0;
    while ((startIdx = lower.indexOf(target, startIdx)) !== -1) {
        console.log(`Matched '${target}' at index ${startIdx}`);
        startIdx += target.length;
    }
});
