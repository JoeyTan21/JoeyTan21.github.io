import test from "node:test";
import assert from "node:assert/strict";
import site from "../dist/server/index.js";

test("serves every public route", async () => {
  for (const path of ["/", "/projects/", "/reading/", "/styles.css", "/assets/profile.jpg"]) {
    const response = await site.fetch(new Request(`https://example.com${path}`));
    assert.equal(response.status, 200, path);
  }

  assert.equal((await site.fetch(new Request("https://example.com/missing"))).status, 404);
});
