/**
 * SecondSpark — Projects JavaScript
 * Handles live search, filter updates, image upload previews, and project bookmarking
 */

document.addEventListener('DOMContentLoaded', () => {
  // Live Search Autocomplete
  const searchInput = document.getElementById('search-input');
  const searchResultsBox = document.getElementById('search-results-dropdown');

  let debounceTimer;
  if (searchInput && searchResultsBox) {
    searchInput.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      const query = searchInput.value.trim();

      if (query.length < 2) {
        searchResultsBox.style.display = 'none';
        searchResultsBox.innerHTML = '';
        return;
      }

      debounceTimer = setTimeout(() => {
        fetch(`/api/search?q=${encodeURIComponent(query)}`)
          .then(res => res.json())
          .then(data => {
            if (data.results && data.results.length > 0) {
              searchResultsBox.innerHTML = data.results.map(p => `
                <a href="${p.url}" class="search-result-item" style="display: flex; align-items: center; gap: 0.75rem; padding: 0.75rem 1rem; border-bottom: 1px solid var(--border-subtle); text-decoration: none; color: inherit;">
                  <img src="${p.image}" style="width: 38px; height: 38px; border-radius: 6px; object-fit: cover;" alt="${p.title}" />
                  <div style="flex: 1; min-width: 0;">
                    <div style="font-weight: 600; font-size: 0.9rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${p.title}</div>
                    <div style="font-size: 0.78rem; color: var(--text-muted);">${p.category} • <span style="color: var(--primary);">${p.status}</span></div>
                  </div>
                </a>
              `).join('');
              searchResultsBox.style.display = 'block';
            } else {
              searchResultsBox.innerHTML = `
                <div style="padding: 1rem; text-align: center; color: var(--text-muted); font-size: 0.88rem;">
                  No matching projects found.
                </div>
              `;
              searchResultsBox.style.display = 'block';
            }
          })
          .catch(() => {});
      }, 300);
    });

    // Close dropdown on outside click
    document.addEventListener('click', (e) => {
      if (!searchInput.contains(e.target) && !searchResultsBox.contains(e.target)) {
        searchResultsBox.style.display = 'none';
      }
    });
  }

  // Toggle Save Project Button (Handled globally by main.js with fallback)
  if (!window.handleProjectSaveToggle) {
    document.querySelectorAll('.save-project-btn').forEach(btn => {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        const projectId = this.getAttribute('data-project-id');
        if (!projectId) return;

        fetch(`/api/projects/${projectId}/save`, {
          method: 'POST',
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json'
          }
        })
          .then(res => {
            if (res.status === 401) {
              window.location.href = '/auth/login?next=' + window.location.pathname;
              return;
            }
            return res.json();
          })
          .then(data => {
            if (!data) return;
            if (data.saved) {
              this.classList.add('saved');
              this.innerHTML = '<i class="fa-solid fa-heart" style="color: #EF4444;"></i>';
            } else {
              this.classList.remove('saved');
              this.innerHTML = '<i class="fa-regular fa-heart"></i>';
            }
            const countEl = document.querySelector(`.save-count-${projectId}`);
            if (countEl) countEl.textContent = data.saves_count;
          })
          .catch(err => console.error('Save failed', err));
      });
    });
  }

  // Multiple Image Upload Previewer
  const imageInput = document.getElementById('project-images-input');
  const previewContainer = document.getElementById('image-previews-container');

  if (imageInput && previewContainer) {
    imageInput.addEventListener('change', function () {
      previewContainer.innerHTML = '';
      if (this.files) {
        Array.from(this.files).forEach(file => {
          if (!file.type.startsWith('image/')) return;
          const reader = new FileReader();
          reader.onload = (e) => {
            const previewCard = document.createElement('div');
            previewCard.style.cssText = 'position: relative; width: 90px; height: 90px; border-radius: 8px; overflow: hidden; border: 1px solid var(--border-subtle);';
            previewCard.innerHTML = `<img src="${e.target.result}" style="width: 100%; height: 100%; object-fit: cover;" alt="Preview" />`;
            previewContainer.appendChild(previewCard);
          };
          reader.readAsDataURL(file);
        });
      }
    });
  }

  // Modal backdrop click and Escape key dismissal
  document.querySelectorAll('.mobile-nav-overlay').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.style.display = 'none';
      }
    });
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.mobile-nav-overlay').forEach(m => {
        m.style.display = 'none';
      });
    }
  });
});

