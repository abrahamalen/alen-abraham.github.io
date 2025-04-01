// Simple search functionality using Fuse.js
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM content loaded, initializing search...');
    
    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');
    const entries = document.querySelectorAll('.daily-entry');
    
    if (!searchInput || !searchResults) {
        console.error('Search elements not found!');
        return;
    }
    
    // Create a simple index of all entries
    const entriesData = [];
    entries.forEach(entry => {
        const titleElement = entry.querySelector('.entry-title a');
        if (titleElement) {
            entriesData.push({
                title: titleElement.textContent,
                url: titleElement.getAttribute('href'),
                element: entry
            });
        }
    });
    
    // Show all entries initially
    function showAllEntries() {
        entries.forEach(entry => {
            entry.style.display = '';
        });
        
        // Show all year and month headers
        document.querySelectorAll('.year-group, .month-group').forEach(group => {
            group.style.display = '';
        });
        
        searchResults.style.display = 'none';
    }
    
    // Perform search
    function performSearch() {
        const query = searchInput.value.toLowerCase().trim();
        
        if (query === '') {
            showAllEntries();
            return;
        }
        
        // Hide all entries initially
        entries.forEach(entry => {
            entry.style.display = 'none';
        });
        
        // Filter entries by search query
        const filteredEntries = entriesData.filter(entry => 
            entry.title.toLowerCase().includes(query)
        );
        
        // Show matching entries
        filteredEntries.forEach(entry => {
            entry.element.style.display = '';
        });
        
        // Hide empty year and month groups
        document.querySelectorAll('.year-group').forEach(yearGroup => {
            const visibleEntries = yearGroup.querySelectorAll('.daily-entry[style=""]').length;
            yearGroup.style.display = visibleEntries > 0 ? '' : 'none';
        });
        
        document.querySelectorAll('.month-group').forEach(monthGroup => {
            const visibleEntries = monthGroup.querySelectorAll('.daily-entry[style=""]').length;
            monthGroup.style.display = visibleEntries > 0 ? '' : 'none';
        });
        
        // Update results count
        if (filteredEntries.length === 0) {
            searchResults.innerHTML = 'No results found';
            searchResults.style.display = 'block';
        } else {
            searchResults.innerHTML = `Found ${filteredEntries.length} result${filteredEntries.length === 1 ? '' : 's'}`;
            searchResults.style.display = 'block';
        }
    }
    
    // Event listeners
    searchInput.addEventListener('input', performSearch);
    searchInput.addEventListener('keydown', function(e) {
        // Clear search on Escape
        if (e.key === 'Escape') {
            searchInput.value = '';
            showAllEntries();
        }
    });
});
