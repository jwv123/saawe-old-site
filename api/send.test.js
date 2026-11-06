// Self-check for api/send.js: `node api/send.test.js` from the repo root.
const assert = require("assert");
const { validate, isEmail, buildEmail } = require("./send.js").__test;

// validation
assert(validate({}) !== null, "empty body rejected");
assert(validate({ name: " ", email: "a@b.c", message: "m" }) !== null, "blank name rejected");
assert(
  validate({ name: "A", email: "not an email", message: "m" }) !== null,
  "bad email rejected"
);
assert(validate({ name: "A", email: "a@b.co", message: " hi " }) === null, "valid body accepted");
assert(!isEmail("a@b"), "a@b rejected");
assert(isEmail("person@example.co.za"), "real-looking email accepted");

// payload shape sent to Resend
var p = buildEmail(
  { name: " Jane Doe ", email: "jane@x.io", message: " Hello,\nhow are you? ", page: "https://saawe.org.za/contact-us/" },
  "test@example.com"
);
assert.deepStrictEqual(p.to, ["test@example.com"], "recipient");
assert.deepStrictEqual(
  [p.from, p.reply_to, p.subject],
  ["SAAWE <message@saawe.org.za>", "jane@x.io", "A Message from Jane Doe"],
  "from/reply_to/subject"
);
assert(
  p.text === "Name: Jane Doe\nEmail Address: jane@x.io\n\nMessage:\nHello,\nhow are you?\n",
  "text body layout"
);

// missing page field is irrelevant now (body is name/email/message only)
var p2 = buildEmail({ name: "A", email: "a@b.co", message: "m" }, "t@e.io");
assert.deepStrictEqual([p2.to, p2.from], [["t@e.io"], "SAAWE <message@saawe.org.za>"], "defaults");
assert(p2.text === "Name: A\nEmail Address: a@b.co\n\nMessage:\nm\n", "defaults");

console.log("all checks passed");
