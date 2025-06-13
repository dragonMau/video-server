const params = new URLSearchParams(window.location.search);
const videoId = params.get('id');

async function loadContent() {
    try {
        const videoData = await getVideo(videoId);
        if (!videoData) {
            throw new Error('Video not found');
        }
        // Update video title
        document.getElementById('videoTitle').textContent = videoData.title || 'Untitled Video';
        // Update video source
        const videoElement = document.getElementById('videoPlayer');
        if (videoElement && videoData.embedUrl) {
            videoElement.src = videoData.embedUrl;
        }

        // Update video description
        let description = '';
        if (Array.isArray(videoData.metaTags)) {
            const descTag = videoData.metaTags.find(tag => tag.property === 'description');
            if (descTag && descTag.value) {
                description = descTag.value;
            }
        }
        document.getElementById('videoDescription').textContent = description;
        document.getElementById('link-back').href = `/guest/playlist/playlist.html?id=${videoData.collectionId}`;

    } catch (error) {
        console.error(error);
        document.getElementById('videoTitle').textContent = 'Error loading video';
        document.getElementById('videoDescription').textContent = '';
        const videoElement = document.getElementById('videoPlayer');
        if (videoElement) {
            videoElement.src = '';
        }
    }
}


// Load content when page loads
document.addEventListener('DOMContentLoaded', () => {
  loadContent();
});
