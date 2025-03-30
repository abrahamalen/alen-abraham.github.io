// Search functionality
var fuse; // holds our search engine
var list = document.getElementById('searchResults'); // targets the <ul>
var first = list.firstChild; // first child of search list
var last = list.lastChild; // last child of search list
var maininput = document.getElementById('searchInput'); // input box for search
var resultsAvailable = false; // Did we get any search results?

// Load search index
window.addEventListener('DOMContentLoaded', function() {
    loadSearch();
});

// ==========================================
// execute search as each character is typed
//
document.getElementById("searchInput").onkeyup = function(e) {
    // Only perform search if the Enter key wasn't pressed (to prevent double-triggers)
    if (e.key !== 'Enter') {
        executeSearch(this.value);
    }
}

// ==========================================
// fetch some json without jquery
//
function fetchJSONFile(path, callback) {
    var httpRequest = new XMLHttpRequest();
    httpRequest.onreadystatechange = function() {
        if (httpRequest.readyState === 4) {
            if (httpRequest.status === 200) {
                var data = JSON.parse(httpRequest.responseText);
                if (callback) callback(data);
            }
        }
    };
    httpRequest.open('GET', path);
    httpRequest.send(); 
}

// ==========================================
// load our search index
//
function loadSearch() { 
    fetchJSONFile('/index.json', function(data){
        var options = {
            shouldSort: true,
            location: 0,
            distance: 100,
            threshold: 0.4,
            minMatchCharLength: 2,
            keys: [
                'title',
                'permalink',
                'summary',
                'content'
            ]
        };
        fuse = new Fuse(data, options); // build the index from the json file
    });
}

// ==========================================
// using the index we loaded, run a search query
//
function executeSearch(term) {
    let results = fuse.search(term); // the actual query being run using fuse.js
    let searchitems = ''; // our results bucket

    if (results.length === 0) { // no results based on what was typed into the input box
        resultsAvailable = false;
        searchitems = '';
    } else { // build our html 
        // Show only first 5 results
        results.slice(0,5).forEach(function(result) {
            const item = result.item;
            searchitems = searchitems + `<li>
                <a href="${item.permalink}" tabindex="0">
                    <span class="title">${item.title}</span><br>
                    <span class="search-summary">${item.summary || item.content.substring(0, 200)}...</span>
                </a>
            </li>`;
        });
        resultsAvailable = true;
    }

    document.getElementById("searchResults").innerHTML = searchitems;
    if (results.length > 0) {
        first = list.firstChild;
        last = list.lastChild;
    }
}

// ==========================================
// Keyboard Navigation
//
document.addEventListener('keydown', function(event) {
    // DOWN (40) arrow
    if (event.keyCode == 40) {
        if (resultsAvailable) {
            event.preventDefault(); // stop window from scrolling
            if (document.activeElement == maininput) { first.firstElementChild.focus(); } // if the currently focused element is the main input --> focus the first <li>
            else if (document.activeElement.parentElement == last) { last.firstElementChild.focus(); } // if we're at the bottom, stay there
            else { document.activeElement.parentElement.nextSibling.firstElementChild.focus(); } // otherwise select the next search result
        }
    }

    // UP (38) arrow
    if (event.keyCode == 38) {
        if (resultsAvailable) {
            event.preventDefault(); // stop window from scrolling
            if (document.activeElement == maininput) { maininput.focus(); } // If we're in the input box, do nothing
            else if (document.activeElement.parentElement == first) { maininput.focus(); } // If we're at the first item, go to input box
            else { document.activeElement.parentElement.previousSibling.firstElementChild.focus(); } // Otherwise, select the search result above the current active one
        }
    }
});
