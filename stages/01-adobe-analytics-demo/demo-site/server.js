/**
 * Minimal static file + event collector server.
 * Replaces python3 -m http.server so the demo site can accept
 * POST /api/events and append them to data/events.jsonl for
 * migration-platform's AnalyticsEventsExtractor to read.
 */
const http = require("http");
const fs = require("fs");
const path = require("path");

const PORT = process.env.PORT || 8000;
const ROOT = __dirname;
const EVENTS_FILE = path.join(ROOT, "data", "events.jsonl");

const MIME = {
  ".html": "text/html", ".js": "application/javascript", ".css": "text/css",
  ".json": "application/json", ".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml",
};

fs.mkdirSync(path.dirname(EVENTS_FILE), { recursive: true });

const server = http.createServer((req, res) => {
  if (req.method === "POST" && req.url === "/api/events") {
    let body = "";
    req.on("data", (chunk) => (body += chunk));
    req.on("end", () => {
      try {
        const parsed = JSON.parse(body); // validate before writing
        if (!parsed.timestamp) parsed.timestamp = new Date().toISOString();
        const line = JSON.stringify(parsed) + "\n";        
	fs.appendFile(EVENTS_FILE, line, (err) => {
          if (err) {
            console.error("[events] write failed:", err);
            res.writeHead(500).end(JSON.stringify({ error: "write_failed" }));
            return;
          }
          res.writeHead(204).end();
        });
      } catch (e) {
        res.writeHead(400).end(JSON.stringify({ error: "invalid_json" }));
      }
    });
    return;
  }

  // Static file serving
  let filePath = path.join(ROOT, req.url === "/" ? "index.html" : req.url);
  if (!filePath.startsWith(ROOT)) {
    res.writeHead(403).end("Forbidden");
    return;
  }
  fs.readFile(filePath, (err, content) => {
    if (err) {
      fs.readFile(path.join(ROOT, "404.html"), (e2, fallback) => {
        res.writeHead(404, { "Content-Type": "text/html" }).end(fallback || "Not found");
      });
      return;
    }
    const ext = path.extname(filePath);
    res.writeHead(200, { "Content-Type": MIME[ext] || "application/octet-stream" }).end(content);
  });
});

server.listen(PORT, () => console.log(`Demo site running on http://localhost:${PORT}`));
