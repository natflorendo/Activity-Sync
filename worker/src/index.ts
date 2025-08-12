// python version was still in beta :( (couldn't deploy it)
export interface Env {
  BACKEND_URL: string;
  STRAVA_VERIFY_TOKEN: string;
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    // Parse the URL to get path and query parameters
    const parsed_url = new URL(request.url);
    const is_webhook = parsed_url.pathname === "/strava/webhook";

    // GET: verification
    if (request.method === "GET" && is_webhook) {
      // parse_qs() always returns lists of values for each query parameter, even if there’s only one value.
      const hub_mode = parsed_url.searchParams.get("hub.mode");
      const hub_challenge = parsed_url.searchParams.get("hub.challenge");
      const verify_token = parsed_url.searchParams.get("hub.verify_token");

      if (hub_mode == "subscribe" && hub_challenge && verify_token == env.STRAVA_VERIFY_TOKEN) {
		return Response.json({ "hub.challenge": hub_challenge });
      }
      
      // Return empty object if not because the response should indicate status code 200. 
      // If it returned error it may consider the webhook endpoint unavailable or misconfigured
      // and might have to manually trigger another subscription request 
      return Response.json({});
    }

    // POST: events - return 200 immediately, forward once server is ready
    if (request.method === "POST" && is_webhook) {
      const body_text = await request.text();

      const forward_event = async () => {
        const max_attempts = 4; // 1 try and 3 retries
        const base_delay = 0.75; // seconds

        for (let attempt = 1; attempt <= max_attempts; attempt++) {
          try {
            const res = await fetch(
              `${env.BACKEND_URL}/strava/webhook`,
              {
                method: "POST",
                headers: {
                  "content-type": "application/json",
                },
                body: body_text,
              },
            );
            // Stop retrying (2xx success)
            if (res.ok) {
              return;
            }
            // Stop if there are client errors
            if (400 <= res.status && res.status < 500) {
              return;
            }
          } catch (_) {
            // Network/other error - retry
          }

          // Exponential backoff with small random jitter to avoid thundering herd
          // If many webhook events fail at once, the Worker might retry all of them at the same delay 
          // (e.g., exactly 0.75 seconds later, then 1.5s, then 3s…).
          // That means the backend would get a sudden “stampede” of retries at those exact moments, 
          // potentially crashing it. Jitter (a random delay) helps avoid this
          const delay = base_delay * (2 ** (attempt - 1)) + (0.3 * Math.random()); // a random extra wait time between 0 and 0.3 seconds.
          await new Promise((r) => setTimeout(r, delay * 1000));
        }
      };

      // Keep running until this task finishes, even if the response has already been sent.
      ctx.waitUntil(forward_event());

      // Give a fast resonse to Strava
      return Response.json({ status: "queued" });
    }

    return Response.json({ "Not found": null }, { status: 404 });
  },
};
