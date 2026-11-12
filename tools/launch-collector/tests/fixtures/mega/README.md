# Mega event-board fixture provenance

Captured 2026-11-10 KST. These are derived test fixtures, not evidence that the local direct-network collector succeeded.

- Source listing: https://www.mega-mgccoffee.com/bbs/?bbs_category=3&bbs_page=1
- Source page 2: https://www.mega-mgccoffee.com/bbs/?bbs_category=3&bbs_page=2
- detail-1: event:708, winter menu event, official posted date 2026-10-26.
- detail-2: event:703, sandwich menu launch, official posted date 2026-10-20.
- detail-3: event:701, NCT 127 winners announcement, official posted date 2026-10-16.

Detail source URLs are the first three original gallery hrefs in list-page1.html. They contain a base64-encoded query with bbs_idx, bbs_category=3, bbs_detail_category and bbs_page.

Retrieval: public Jina Reader GET https://r.jina.ai/<official URL>, header X-Return-Format: html. No authentication, cookies, bypass tokens or TLS changes. The reader returned HTML with replacement characters in Korean text. Original reader DOM fragments (gallery plus pagination, or .board_detail) remain outside the repository in the local verification folder source/mega, with suffix .reader-original.html and no text repair. They are serialized DOM fragments, not byte-for-byte original HTTP responses. Global page header/footer/scripts were omitted.

The test *.html files without reader-original suffix derive from those fragments. Korean gallery titles were restored from the same official URLs rendered by the web tool. The three detail headings and metadata labels were similarly restored; numeric dates and image URLs are unchanged. Unrelated author blocks, previous/next links and list-return buttons were removed. Image filename title attributes were removed. Pagination labels were normalized; original href targets and board classes remain. Restored markup uses the same h1, title-div and metadata-div/span element types as the captured DOM. No synthetic posts, source IDs, dates, image URLs or article-body text were added.

Direct local httpx2 GET to the main official host, apex host, plain HTTP and resolved main IPv4 timed out. Public Google/Cloudflare DNS agreed with local DNS. The image host answered promptly; its /bbs path was 404. Reader fixture retrieval is intentionally not part of the runtime adapter. Tests use local fixtures with a wire-level HTTP fake; the direct Mega CLI remains unverified until main-host connectivity is restored.

Retention: these five derived HTML fragments and this provenance file remain as regression evidence with the adapter. They require no setup cache or installation. Original reader fragments are retained separately as local verification evidence.
