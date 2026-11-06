// ponytail: local dev only — static mirror + /api/send wired to the real handler.
// (`python -m http.server` can't run a serverless function.) Do not deploy expecting this to run.
const { createServer } = require("http");
const fs = require("fs");
const path = require("path");
const handler = require("./api/send.js");

const ROOT = __dirname;
const PORT = 8000;

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css",
  ".js": "text/javascript",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
  ".ttf": "font/ttf",
  ".eot": "application/vnd.ms-fontobject",
  ".pdf": "application/pdf",
  ".doc": "application/msword",
  ".mp3": "audio/mpeg",
  ".json": "application/json",
};

createServer(function (req, res) {
  var urlPath = decodeURIComponent(req.url.split("?")[0]);

  if (req.method === "POST" && urlPath === "/api/send") {
    var body = "";
    req.on("data", function (c) { body += c; });
    req.on("end", async function () {
      var parsed;
      try { parsed = JSON.parse(body); } catch (e) { parsed = {}; }
      var mockReq = { method: "POST", headers: req.headers, body: parsed };
      var out = { code: 200 };
      out.status = function (c) { out.code = c; return out; };
      out.json = function (j) { out.payload = j; return out; };
      await handler(mockReq, out);
      res.writeHead(out.code, { "Content-Type": "application/json" });
      res.end(JSON.stringify(out.payload || {}));
      console.log("[api/send]", out.code, out.payload || "");
    });
    return;
  }

  if (req.method !== "GET" && req.method !== "HEAD") {
    res.writeHead(405).end();
    return;
  }
  if (urlPath.endsWith("/")) urlPath += "index.html";
  var file = path.resolve(ROOT, "." + urlPath);
  if (!file.startsWith(ROOT)) {
    res.writeHead(403).end();
    return;
  }
  fs.readFile(file, function (err, data) {
    if (err) {
      res.writeHead(404, { "Content-Type": "text/plain" });
      res.end("Not found (dev mirror: /api/send is the only dynamic route)");
      return;
    }
    var mime = MIME[path.extname(file).toLowerCase()] || "application/octet-stream";
    res.writeHead(200, { "Content-Type": mime });
    res.end(req.method === "HEAD" ? undefined : data);
  });
}).listen(PORT, function () {
  console.log("Dev mirror on http://localhost:" + PORT + "/ — contact forms POST to /api/send");
  console.log("RESEND_API_KEY is " + (process.env.RESEND_API_KEY ? "set" : "NOT set (sends will fail with 500)"));
});
