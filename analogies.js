let editingIndex = null;
let editingId = null;
let currentLanguage = "all";
let currentUser = sessionStorage.getItem("loggedInUser") || "admin"; // Default to "admin" if not logged in

const API_BASE_URL = "http://127.0.0.1:5002/api";

let analogies = [];

// Load analogies from database (but don't display them)
async function loadAnalogies() {
  try {
    const languages = ['en', 'hi', 'te', 'zh', 'de'];
    let allAnalogies = [];
    
    for (const lang of languages) {
      // Always fetch all idioms from database (no username filter)
      const url = `${API_BASE_URL}/idioms/list?language=${lang}`;
      
      const response = await fetch(url);
      const data = await response.json();
      
      if (data.success && data.idioms) {
        const formatted = data.idioms.map(idiom => ({
          id: idiom.id,
          title: idiom.idiom,
          description: idiom.meaning,
          language: lang,
          username: idiom.username
        }));
        allAnalogies = allAnalogies.concat(formatted);
      }
    }
    
    analogies = allAnalogies;
    return allAnalogies;
  } catch (error) {
    console.error("Error loading analogies:", error);
    return [];
  }
}

// Search for specific idioms - now searches database directly
async function performSearch() {
  const searchTerm = document.getElementById("searchInput").value.trim();
  
  if (!searchTerm) {
    alert("Please enter a search term");
    return;
  }
  
  if (searchTerm.length < 2) {
    alert("Please enter at least 2 characters to search");
    return;
  }
  
  // Show loading state
  const searchButton = document.querySelector('.search-btn');
  const originalText = searchButton.textContent;
  searchButton.textContent = 'Searching...';
  searchButton.disabled = true;
  
  try {
    // Search entire database (no username filtering)
    console.log("Searching database for:", searchTerm);
    
    const url = `${API_BASE_URL}/idioms/search?q=${encodeURIComponent(searchTerm)}`;
    console.log("API URL:", url);
    
    const response = await fetch(url);
    console.log("Response status:", response.status);
    
    const data = await response.json();
    console.log("Response data:", data);
    
    if (data.success) {
      displaySearchResults(data.results, searchTerm, data.total_found);
    } else {
      alert("Search failed: " + (data.error || "Unknown error"));
    }
  } catch (error) {
    console.error("Search error:", error);
    alert("Failed to search idioms. Please try again.");
  } finally {
    // Reset button state
    searchButton.textContent = originalText;
    searchButton.disabled = false;
  }
}

// Handle Enter key in search box
function handleSearchKeyPress(event) {
  if (event.key === 'Enter') {
    performSearch();
  }
}

// Display search results - updated for database search results
function displaySearchResults(results, searchTerm, totalFound = 0) {
  const resultsContainer = document.getElementById("searchResults");
  const resultsList = document.getElementById("searchResultsList");
  
  if (results.length === 0) {
    resultsList.innerHTML = `
      <div class="no-results">
        <p>No idioms found matching "${searchTerm}"</p>
        <p>Would you like to add it?</p>
        <button onclick="openAddModal()" class="add-btn">+ Add Idiom</button>
      </div>
    `;
  } else {
    const resultsHeader = totalFound > 0 ? 
      `<p class="search-summary">Found ${totalFound} idiom${totalFound > 1 ? 's' : ''} matching "<strong>${searchTerm}</strong>"</p>` : '';
    
    resultsList.innerHTML = resultsHeader + results.map((result, index) => `
      <div class="search-result-item">
        <div>
          <strong>${highlightMatch(result.idiom, searchTerm)}</strong>
          <span class="lang">[${result.language_name || result.language_code?.toUpperCase() || 'UNKNOWN'}]</span>
          <p>${highlightMatch(result.meaning, searchTerm)}</p>
          <div class="result-meta">
            <small>Added by: ${result.username} | ${formatDate(result.created_at)}</small>
          </div>
        </div>
      </div>
    `).join('');
  }
  
  resultsContainer.style.display = "block";
}

// Helper function to highlight search matches
function highlightMatch(text, searchTerm) {
  if (!text || !searchTerm) return text;
  
  const regex = new RegExp(`(${searchTerm})`, 'gi');
  return text.replace(regex, '<mark>$1</mark>');
}

// Helper function to format date
function formatDate(dateString) {
  if (!dateString) return '';
  
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric' 
  });
}

// Save analogy to database
async function saveAnalogyToDB(title, description, language) {
  try {
    const response = await fetch(`${API_BASE_URL}/idioms/add`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        language: language,
        idiom: title,
        meaning: description,
        username: currentUser
      })
    });
    
    const data = await response.json();
    
    if (data.success) {
      console.log("Idiom saved successfully!");
      return { success: true, id: data.id };
    } else {
      alert("Error saving idiom: " + data.error);
      return { success: false };
    }
  } catch (error) {
    console.error("Error saving analogy:", error);
    alert("Failed to save idiom. Please try again.");
    return { success: false };
  }
}

// Delete analogy from database
async function deleteAnalogyFromDB(language, id) {
  try {
    const response = await fetch(`${API_BASE_URL}/idioms/delete`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        language: language,
        id: id,
        username: currentUser
      })
    });
    
    const data = await response.json();
    
    if (data.success) {
      console.log("Idiom deleted successfully!");
      return true;
    } else {
      alert("Error deleting idiom: " + data.error);
      return false;
    }
  } catch (error) {
    console.error("Error deleting analogy:", error);
    alert("Failed to delete idiom. Please try again.");
    return false;
  }
}

function renderAnalogies(filter = "") {
  // Don't render idioms by default - only show search results
  return;
}

// Add translation function (only for search results)
async function translateAnalogy(index) {
  const descElem = document.getElementById(`analogy-desc-${index}`);
  const loadingElem = document.getElementById(`translate-loading-${index}`);
  const translatedElem = document.getElementById(`translated-text-${index}`);
  const btnElem = document.getElementById(`translate-btn-${index}`);

  loadingElem.style.display = "inline";
  btnElem.disabled = true;
  translatedElem.textContent = "";

  try {
    const response = await fetch("http://127.0.0.1:5000/api/translate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: descElem.textContent })
    });
    const data = await response.json();
    translatedElem.textContent = data.translated_text || data.translation || "[No translation returned]";
  } catch (err) {
    translatedElem.textContent = "Translation failed.";
  } finally {
    loadingElem.style.display = "none";
    btnElem.disabled = false;
  }
}

function filterByLanguage() {
  currentLanguage = document.getElementById("languageFilter").value;
  // Don't auto-filter, user must search
  document.getElementById("searchResults").style.display = "none";
}

function openAddModal() {
  editingIndex = null;
  editingId = null;
  document.getElementById("modalTitle").innerText = "Add New Analogy";
  document.getElementById("analogyTitle").value = "";
  document.getElementById("analogyDescription").value = "";
  document.getElementById("analogyLanguage").value = "en";
  document.getElementById("analogyModal").style.display = "flex";
}

async function saveAnalogy() {
  const title = document.getElementById("analogyTitle").value.trim();
  const description = document.getElementById("analogyDescription").value.trim();
  const language = document.getElementById("analogyLanguage").value;

  if (!title || !description) {
    alert("Please fill in both title and description");
    return;
  }

  if (editingIndex !== null) {
    // For editing, delete old and create new
    const oldAnalogy = analogies[editingIndex];
    await deleteAnalogyFromDB(oldAnalogy.language, oldAnalogy.id);
  }
  
  // Save to database
  const result = await saveAnalogyToDB(title, description, language);
  
  if (result.success) {
    alert("Idiom saved successfully to the database!");
    closeModal();
    await loadAnalogies();
    // Don't render, just clear search results
    document.getElementById("searchResults").style.display = "none";
    document.getElementById("searchInput").value = "";
  }
}

function editAnalogy(index) {
  // Disable editing for now since we're not showing the list
  alert("Editing is not available. Please delete and re-add if needed.");
  return;
}

async function deleteAnalogy(index) {
  // Disable deletion for now since we're not showing the list
  alert("Direct deletion is not available in this view.");
  return;
}

function closeModal() {
  document.getElementById("analogyModal").style.display = "none";
}

function searchAnalogies() {
  // User must click search button or press Enter
  return;
}

// Remove the input event listener that auto-searches
// document.getElementById("searchInput").addEventListener("input", searchAnalogies);

// Initial render
async function initialize() {
  currentUser = sessionStorage.getItem("loggedInUser");
  await loadAnalogies();
  // Don't render idioms by default - only show on search
}

// Update current user on page load
document.addEventListener('DOMContentLoaded', initialize);