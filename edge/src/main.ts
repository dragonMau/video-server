import * as BunnySDK from "https://esm.sh/@bunny.net/edgescript-sdk@0.10.0";

// Initialize env object to store environment variables
const env: { [key: string]: string } = {};
let isEnvInitialized = false;

function getEnv(key: string): string {
    const val = Deno.env.get(key);
    if (!val) throw new Error(`Missing environment variable: ${key}`);
    return val;
}

function initializeEnv(): void {
    if (isEnvInitialized) return;

    try {
        env.AccessKey = getEnv("AccessKey");
        env.LibraryID = getEnv("LibraryID");
        env.CDNHostname = getEnv("CDNHostname");
        env.VideoHostName = getEnv("VideoHostName");
        env.QueryParams = getEnv("QueryParams");

        console.log(`[INFO]: Environment variables loaded successfully`);
        isEnvInitialized = true;
    } catch (error) {
        console.error(`[ERROR]: Failed to load environment variables:`, error);
        throw error;
    }
}

function getCDNThumbnailUrl(guid: string, filename: string): string {
    return `https://${env.CDNHostname}/${guid}/${filename}`;
}

function getEmbedUrl(guid: string): string {
    return `https://${env.VideoHostName}/embed/${env.LibraryID}/${guid}${env.QueryParams}`;
}

async function fetchWithHeaders(url: string): Promise<Response> {
    if (!env.AccessKey || !env.LibraryID) {
        throw new Error("Environment variables not initialized");
    }

    const headers = {
        'accept': 'application/json',
        'AccessKey': env.AccessKey,
        'Content-Type': 'application/json'
    };

    try {
        const response = await fetch(url, { method: 'GET', headers });

        if (!response.ok) {
            const errorText = await response.text();
            console.error(`[ERROR]: Request failed with status ${response.status}: ${errorText}`);
            throw new Error(`Request failed: ${response.status} ${response.statusText}`);
        }

        return response;
    } catch (error) {
        console.error(`[ERROR]: Fetch failed for URL ${url}:`, error);
        throw error;
    }
}

// Initialize environment variables at startup
initializeEnv();

BunnySDK.net.http.serve(async (req: Request): Promise<Response> => {
    const url = new URL(req.url);
    const params = url.searchParams;

    const contentParam = params.get("content");
    const playlistParam = params.get("playlist");

    let mode: "content" | "playlist" | null = null;
    let apiUrl = "";

    if (contentParam) {
        mode = "content";
        apiUrl = `https://video.bunnycdn.com/library/${env.LibraryID}/collections?includeThumbnails=true`;
    } else if (playlistParam) {
        mode = "playlist";
        apiUrl = `https://video.bunnycdn.com/library/${env.LibraryID}/videos?collection=${playlistParam}&includeThumbnails=true`;
    } else {
        return new Response(JSON.stringify({
            error: "Missing query parameter",
            message: "Provide either ?content or ?playlist in the query string."
        }), {
            status: 400,
            headers: { "content-type": "application/json" }
        });
    }

    console.log(`[INFO]: ${req.method} - ${url.toString()} - Mode: ${mode}`);

    try {
        const res = await fetchWithHeaders(apiUrl);
        const data = await res.json();

        if (mode === "playlist") {
            if (!Array.isArray(data.items)) {
                throw new Error("Invalid response format: expected 'items' to be an array");
            }

            for (const item of data.items) {
                item.previewImageUrls = [getCDNThumbnailUrl(item.guid, item.thumbnailFileName)];
                item.embedUrl = getEmbedUrl(item.guid);
            }
        }
        return new Response(JSON.stringify(data), {
            headers: {
                "content-type": "application/json",
                "Access-Control-Allow-Origin":
                    url.hostname === "localhost" || url.hostname === "127.0.0.1"
                        ? "http://127.0.0.1:5500"
                        : "https://api.chasidustv.com"
            }
        });
    } catch (error) {
        console.error("[ERROR]: Request handler failed:", error);

        return new Response(JSON.stringify({
            error: "Internal server error",
            message: error instanceof Error ? error.message : "Unknown error"
        }), {
            status: 500,
            headers: {
                "content-type": "application/json"
            }
        });
    }
});
