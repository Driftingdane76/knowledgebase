function renderPagination() {
    const bar = document.getElementById('pagination-bar');
    const info = document.getElementById('pagination-info');
    const pages = document.getElementById('pagination-pages');
    const prevBtn = document.getElementById('page-prev-btn');
    const nextBtn = document.getElementById('page-next-btn');
    
    if (!paginationMeta || paginationMeta.total < currentPageSize) { 
        bar.classList.add('d-none'); 
        return; 
    }
    
    bar.classList.remove('d-none');
    const start = (currentPage - 1) * currentPageSize + 1;
    const end = Math.min(currentPage * currentPageSize, paginationMeta.total);
    
    const showingStr = gettext('Showing');
    const ofStr = gettext('of');
    const entriesStr = gettext('entries');
    const pageStr = gettext('Page');
    
    info.textContent = `${showingStr} ${start}–${end} ${ofStr} ${paginationMeta.total} ${entriesStr}`;
    pages.textContent = `${pageStr} ${currentPage} / ${paginationMeta.total_pages}`;
    prevBtn.disabled = !paginationMeta.has_prev;
    nextBtn.disabled = !paginationMeta.has_next;
}
