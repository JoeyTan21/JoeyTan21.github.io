import { mkdir, readFile, rm, writeFile } from "node:fs/promises";

const root = new URL("./", import.meta.url);
const readText = (path) => readFile(new URL(path, root), "utf8");

const pages = {
  "/": await readText("index.html"),
  "/index.html": await readText("index.html"),
  "/projects": await readText("projects/index.html"),
  "/projects/": await readText("projects/index.html"),
  "/reading": await readText("reading/index.html"),
  "/reading/": await readText("reading/index.html"),
};
const styles = await readText("styles.css");
const profile = (await readFile(new URL("assets/profile.jpg", root))).toString("base64");

const worker = `const pages = ${JSON.stringify(pages)};
const styles = ${JSON.stringify(styles)};
const profile = Uint8Array.from(atob(${JSON.stringify(profile)}), (character) => character.charCodeAt(0));

export default {
  async fetch(request) {
    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Method Not Allowed", { status: 405, headers: { Allow: "GET, HEAD" } });
    }

    const path = new URL(request.url).pathname;
    let body;
    let type;

    if (path in pages) {
      body = pages[path];
      type = "text/html; charset=utf-8";
    } else if (path === "/styles.css") {
      body = styles;
      type = "text/css; charset=utf-8";
    } else if (path === "/assets/profile.jpg") {
      body = profile;
      type = "image/jpeg";
    } else {
      return new Response("Not Found", { status: 404 });
    }

    return new Response(request.method === "HEAD" ? null : body, {
      headers: { "Content-Type": type },
    });
  },
};
`;

const serverDirectory = new URL("dist/server/", root);
await rm(new URL("dist/", root), { recursive: true, force: true });
await mkdir(serverDirectory, { recursive: true });
await writeFile(new URL("index.js", serverDirectory), worker);
