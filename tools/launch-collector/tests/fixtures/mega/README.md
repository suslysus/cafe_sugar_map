# Mega event-board fixtures

Trimmed copies of the public Mega event board, captured 2026-11-10 KST, used only by the parser tests.

- list-page1.html / list-page2.html: https://www.mega-mgccoffee.com/bbs/?bbs_category=3&bbs_page=1 and `bbs_page=2`
- detail-1.html: event:708, winter menu event, posted 2026-10-26
- detail-2.html: event:703, sandwich menu launch, posted 2026-10-20
- detail-3.html: event:701, NCT 127 winners announcement, posted 2026-10-16

Detail URLs are the first three gallery links in list-page1.html; each carries a base64-encoded query with `bbs_idx`, `bbs_category=3`, `bbs_detail_category` and `bbs_page`.

Page headers, footers, scripts and unrelated blocks were removed. Korean titles and labels were restored from the official pages; IDs, dates and image URLs are unchanged, and no posts or body text were invented. Tests read these files through an in-memory HTTP fake and make no network requests.
