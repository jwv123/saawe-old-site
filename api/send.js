// ponytail: contact-form mail via Resend, replacing the n8n webhook on Railway.
// Ceilings: plain-text body, no HTML template, no rate limit/honeypot — add those if form spam appears.
const RESEND_ENDPOINT = "https://api.resend.com/emails";

function isEmail(v) {
  return typeof v === "string" && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
}

function validate(body) {
  if (typeof body.name !== "string" || !body.name.trim()) return "Missing name.";
  if (!isEmail(body.email)) return "Invalid email address.";
  if (typeof body.message !== "string" || !body.message.trim()) return "Missing message.";
  return null;
}

function buildEmail(body, to) {
  var name = body.name.trim();
  var email = body.email.trim();
  return {
    from: "SAAWE <message@saawe.org.za>",
    to: [to],
    reply_to: email, // replies go straight to the visitor
    subject: "A Message from " + name,
    text:
      "Name: " + name +
      "\nEmail Address: " + email +
      "\n\nMessage:\n" + body.message.trim() + "\n",
  };
}

async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "POST only." });
  }
  var len = Number(req.headers["content-length"] || 0);
  if (len > 10240) {
    return res.status(413).json({ error: "Payload too large." });
  }
  var err = validate(req.body || {});
  if (err) {
    return res.status(400).json({ error: err });
  }
  var key = process.env.RESEND_API_KEY;
  if (!key) {
    return res.status(500).json({ error: "Server not configured." });
  }
  var to = process.env.MAIL_TO || "james@clearpathai.co.za"; // test recipient until the flow is confirmed; flip via env
  var payload = buildEmail(req.body, to);
  try {
    var r = await fetch(RESEND_ENDPOINT, {
      method: "POST",
      headers: { Authorization: "Bearer " + key, "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!r.ok) {
      var detail = "";
      try { detail = (await r.json()).message || ""; } catch (e) { /* body not JSON */ }
      console.error("Resend error", r.status, detail);
      return res.status(502).json({ error: "Sending failed." });
    }
    return res.status(200).json({ ok: true });
  } catch (e) {
    console.error("Send threw", e);
    return res.status(502).json({ error: "Sending failed." });
  }
}

module.exports = handler;
module.exports.__test = { validate: validate, isEmail: isEmail, buildEmail: buildEmail };
