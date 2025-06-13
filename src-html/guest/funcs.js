NO_IMAGE = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjY2NjIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvcnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPk5vIEltYWdlPC90ZXh0Pjwvc3ZnPg==';
API_URL = 'https://api.chasidustv.com';

async function fetchData(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error('Failed to fetch content');
    }
    const data = await response.json();
    return data;
}
async function getData(cacheKey, url) {
    const cacheStr = localStorage.getItem(cacheKey);
    if (cacheStr) {
        try {
            const cached = JSON.parse(cacheStr);
            if (cached && cached.timestamp && Date.now() - cached.timestamp < 1000 * 60 * 10) { // 10 min cache
                return cached.data;
            }
        } catch (e) {
            // ignore parse errors, fallback to fetch
        }
    }
    const data = await fetchData(url);
    localStorage.setItem(cacheKey, JSON.stringify({ data, timestamp: Date.now() }));
    return data;
}
async function getContent() { // all playlists in the library
    return await getData(
        'library_content_cache',
        `${API_URL}/?content=true`);
}
async function getPlaylist(playlistId) { // videos in a playlist
    return await getData(
        `playlist_${playlistId}_cache`,
        `${API_URL}/?playlist=${playlistId}`);
}
async function getCollection(collectionId) { // collecion information
    const library = await getContent();
    return library.items.find(item => item.guid === collectionId) || null;
}
async function getVideo(videoId) {
    const library = await getContent();
    for (const playlist of library.items) {
        const videos = await getPlaylist(playlist.guid);
        const found = videos.items.find(item => item.guid === videoId);
        if (found) return found;
    }
    return null;
}

function formatDuration(seconds) {
    seconds = Number(seconds) || 0;
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    if (h > 0) {
        return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    }
    return `${m}:${s.toString().padStart(2, '0')}`;
}