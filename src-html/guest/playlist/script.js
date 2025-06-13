const params = new URLSearchParams(window.location.search);
const playlistId = params.get('id');
const configData = window.configData || {};

// Function to load and display playlist content
async function loadContent() {
  try {
    const playlist_data = await getPlaylist(playlistId);
    const collection_data = await getCollection(playlistId);

    document.getElementById('playlistName').textContent = collection_data.name || 'Untitled Playlist';

    if (playlist_data.items.length > 0) {
      // Show video grid
      const videoGrid = document.getElementById('videoGrid');
      const template = document.getElementById('videoTemplate');

      // Generate video cards
      playlist_data.items.forEach(video => {
        // Clone the template
        const videoCard = template.cloneNode(true);
        videoCard.classList.remove('hidden');

        // Update content
        const img = videoCard.querySelector('img');
        const title = videoCard.querySelector('.video-title');
        const duration = videoCard.querySelector('.length-text');

        title.textContent = video.title || 'Untitled Video';
        img.src = [...video.previewImageUrls, NO_IMAGE][0];
        img.alt = video.title || 'Video thumbnail';
        duration.textContent = formatDuration(video.length);

        // Add click event (optional)
        videoCard.addEventListener('click', () => {
          window.location.href = `/guest/watch/watch.html?id=${video.guid}`;
        });

        // Append to grid
        videoGrid.appendChild(videoCard);
      });

      videoGrid.classList.remove('hidden');
    } else {
      // Show error message if no videos
      document.getElementById('errorMessage').textContent = 'No videos available in this playlist.';
      document.getElementById('errorMessage').classList.remove('hidden');
    }
    document.getElementById('loadingPlaceholder').classList.add('hidden');

  } catch (error) {
    console.error('Error loading playlist content:', error);
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
