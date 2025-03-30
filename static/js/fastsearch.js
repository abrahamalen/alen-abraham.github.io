// Simple search functionality using Fuse.js
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM content loaded, initializing search...');
    
    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');
    
    if (!searchInput || !searchResults) {
        console.error('Search elements not found!');
        return;
    }
    
    // Check if Fuse.js is loaded, if not load it
    if (typeof Fuse === 'undefined') {
        console.warn('Fuse.js library not loaded! Attempting to load it dynamically...');
        
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/fuse.js@6.6.2';
        
        script.onload = function() {
            console.log('Fuse.js loaded dynamically');
            initializeSearch();
        };
        
        script.onerror = function() {
            console.error('Failed to load Fuse.js dynamically');
            searchResults.innerHTML = '<li class="error-message">Error: Fuse.js library could not be loaded</li>';
        };
        
        document.head.appendChild(script);
    } else {
        console.log('Fuse.js already loaded');
        initializeSearch();
    }
    
    function initializeSearch() {
        console.log('Initializing search...');
        
        // Try multiple paths to find index.json
        const possiblePaths = [
            '/index.json',
            '../index.json',
            '../../index.json',
            '/alen-abraham.github.io/index.json',
            window.location.origin + '/index.json',
            location.protocol + '//' + location.host + '/index.json'
        ];
        
        loadSearchIndex();
        
        function loadSearchIndex() {
            let loaded = false;
            let pathIndex = 0;
            
            tryNextPath();
            
            function tryNextPath() {
                if (pathIndex >= possiblePaths.length) {
                    console.error('Failed to load search index from all paths');
                    searchResults.innerHTML = '<li class="error-message">Error: Search index could not be loaded</li>';
                    return;
                }
                
                const path = possiblePaths[pathIndex];
                console.log(`Trying to load search index from ${path}...`);
                
                fetch(path)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP error! Status: ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        console.log(`Search index loaded successfully from ${path}`);
                        console.log('Index items:', data.length);
                        initFuse(data);
                        loaded = true;
                    })
                    .catch(error => {
                        console.warn(`Failed to load from ${path}:`, error);
                        pathIndex++;
                        tryNextPath();
                    });
            }
        }
        
        function initFuse(data) {
            // Initialize Fuse with the data
            const fuse = new Fuse(data, {
                keys: ['title', 'content', 'tags', 'categories', 'summary'],
                includeScore: true,
                shouldSort: true,
                threshold: 0.4
            });
            
            console.log('Fuse.js initialized successfully');
            
            // Add event listener for search input
            searchInput.addEventListener('input', function() {
                executeSearch(this.value, fuse, data);
            });
            
            // Execute search if there's an initial query
            const urlParams = new URLSearchParams(window.location.search);
            const initialQuery = urlParams.get('q');
            
            if (initialQuery) {
                searchInput.value = initialQuery;
                executeSearch(initialQuery, fuse, data);
            }
            
            // Focus search input on page load
            searchInput.focus();
        }
        
        // Function to execute search
        function executeSearch(query, fuse, data) {
            console.log('Executing search for:', query);
            
            if (!query || query.trim() === '') {
                searchResults.innerHTML = '';
                return;
            }
            
            if (!fuse) {
                console.error('Fuse.js not initialized');
                searchResults.innerHTML = '<li class="error-message">Search functionality not initialized</li>';
                return;
            }
            
            const results = fuse.search(query);
            console.log('Search results:', results.length);
            
            if (results.length === 0) {
                searchResults.innerHTML = '<li class="no-results">No results found</li>';
                return;
            }
            
            searchResults.innerHTML = '';
            
            // Display up to 10 results - only titles, no summaries
            results.slice(0, 10).forEach(result => {
                const item = result.item;
                const li = document.createElement('li');
                
                let content = `<a href="${item.permalink}">`;
                content += `<span class="title">${item.title}</span>`;
                content += '</a>';
                
                li.innerHTML = content;
                searchResults.appendChild(li);
            });
        }
    }

    // Handle keyboard navigation
    document.addEventListener('keydown', function(e) {
        // ESC key
        if (e.key === 'Escape') {
            searchInput.value = '';
            searchResults.innerHTML = '';
        }
    });
});
