document.addEventListener('DOMContentLoaded', function() {
  // --- COPY BUTTON LOGIC (from your index.html, slightly refactored for clarity) ---
  function initializeCopyButtons() {
    const preTags = document.querySelectorAll('pre');
    preTags.forEach(function(pre) {
      // Check if a copy button already exists for this pre-tag
      if (pre.parentNode.classList.contains('pre-container') && pre.parentNode.querySelector('.copy-btn')) {
        return; // Skip if button already there
      }

      const container = document.createElement('div');
      container.className = 'pre-container';

      const copyBtn = document.createElement('button');
      copyBtn.textContent = 'Copy';
      copyBtn.className = 'copy-btn';

      copyBtn.addEventListener('click', function() {
        const textToCopy = pre.innerText || pre.textContent;
        navigator.clipboard.writeText(textToCopy).then(
          function() {
            const originalText = copyBtn.textContent;
            copyBtn.textContent = 'Copied!';
            copyBtn.classList.add('copied');
            copyBtn.classList.remove('failed');

            setTimeout(function() {
              copyBtn.textContent = originalText;
              copyBtn.classList.remove('copied');
            }, 2000);
          },
          function() {
            const originalText = copyBtn.textContent;
            copyBtn.textContent = 'Failed!';
            copyBtn.classList.add('failed');
            copyBtn.classList.remove('copied');

            setTimeout(function() {
              copyBtn.textContent = originalText;
              copyBtn.classList.remove('failed');
            }, 2000);
          }
        );
      });

      if (pre.parentNode) {
        pre.parentNode.insertBefore(container, pre);
      }
      container.appendChild(pre);
      container.appendChild(copyBtn);
    });
  }

  // --- BOOKMARK LOADING LOGIC ---
  function loadBookmarks() {
    const bookmarksList = document.getElementById('bookmarks-list');
    if (!bookmarksList) {
      console.error('Bookmarks list container (#bookmarks-list) not found.');
      return;
    }

    fetch('./bookmarks.json') // Fetch the JSON file
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json(); // Parse it as JSON
      })
      .then(bookmarks => {
        bookmarksList.innerHTML = ''; // Clear any existing content (e.g., placeholder text)

        if (bookmarks.length === 0) {
          const li = document.createElement('li');
          li.textContent = 'No bookmarks yet. Add some to bookmarks.json!';
          bookmarksList.appendChild(li);
          return;
        }

        bookmarks.forEach(bookmark => {
          const li = document.createElement('li');
          const link = document.createElement('a');
          link.href = bookmark.url;
          link.textContent = bookmark.chapterTitle; // Or any combination you prefer

          li.innerHTML = `📌 ${bookmark.bookTitle} – `; // Add the book title
          li.appendChild(link); // Append the link
          bookmarksList.appendChild(li);
        });
      })
      .catch(error => {
        console.error('Error loading or parsing bookmarks:', error);
        bookmarksList.innerHTML = '<li>Error loading bookmarks. Check console.</li>';
      });
  }

  // --- INITIALIZE ---
  initializeCopyButtons();
  loadBookmarks();

});