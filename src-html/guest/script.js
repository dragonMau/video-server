let _contentCache = null;

// Function to load and display playlist content
async function loadContent() {
    try {
        const library_data = await getContent();


        if (library_data.items.length > 0) {
            // Show playlist grid
            const playlistGrid = document.getElementById('playlistGrid');
            const template = document.getElementById('playlistTemplate');

            // Generate playlist cards
            library_data.items.forEach(playlist => {
                // Clone the template
                const playlistCard = template.cloneNode(true);
                playlistCard.classList.remove('hidden');

                // Update content
                const img = playlistCard.querySelector('img');
                const title = playlistCard.querySelector('.playlist-title');
                const length = playlistCard.querySelector('.length-text');

                title.textContent = playlist.name || 'Untitled List';
                playlistCard.id = playlist.id || '';
                img.src = [...playlist.previewImageUrls, NO_IMAGE][0];
                img.alt = playlist.name || 'Playlist thumbnail';
                length.textContent = playlist.videoCount || '0';

                // Add click event (optional)
                playlistCard.addEventListener('click', () => {
                    window.location.href = `/guest/playlist/playlist.html?id=${playlist.guid}`;
                });

                // Append to grid
                playlistGrid.appendChild(playlistCard);
            });

            playlistGrid.classList.remove('hidden');
        } else {
            // Show error message if no playlists
            document.getElementById('errorMessage').textContent = 'No playlist content available.';
            document.getElementById('errorMessage').classList.remove('hidden');
        }
        
        // Hide loading placeholder
        document.getElementById('loadingPlaceholder').classList.add('hidden');

    } catch (error) {
        console.error('Error loading content:', error);

        // Hide loading placeholder
        document.getElementById('loadingPlaceholder').classList.add('hidden');

        // Show error message
        document.getElementById('errorMessage').classList.remove('hidden');
    }
}

// Load content when page loads
document.addEventListener('DOMContentLoaded', () => {
    loadContent();
});
