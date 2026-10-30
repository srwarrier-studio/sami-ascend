# synapse-web/07 board-export

## Goal
A user downloads the board they are looking at as a one-page infographic PDF that matches what is drawn on screen and stays sharp when printed or zoomed.

## Behavior
- A board page (not in Edit mode) has an `Export PDF` button. It downloads `<board name>-<yyyy-mm-dd>.pdf` with no print dialog.
- Made in the browser, because only the browser has the board as drawn. Route: raster capture at 3x pixel ratio with `html-to-image` (`toPng`, waiting for `document.fonts.ready` so IBM Plex is embedded), placed on the page with `jsPDF`. Charts are SVG, so they rasterise cleanly at 3x. Text in the PDF is an image, not selectable; accepted.
- One page, sized to the capture (width and height of the sheet in mm from its CSS pixels at 96 dpi), so a tall board never splits across pages.
- The sheet captured is an `ExportFrame` around the board: top, the company logo and title; middle, the board exactly as drawn (no app header, no page bar, no edit controls); bottom, a small line `Generated <local date and time> by <user name>`. The header and footer exist in the page but are visible only while exporting.
- Logo and title are placeholders from one `companyBrand` constant (name `Company name`, a grey square with the first letter as logo). The real name and logo come from a later phase.
- If any widget still shows its loading skeleton, nothing is exported and a toast says `Widgets are still loading`. A widget that failed is exported as drawn (its error alert).
- The capture and PDF writing sit behind a `BoardExporter` interface (`export(element, fileName)`); `PdfBoardExporter` is the real one and a fake serves tests. jsdom cannot rasterise, so sharpness is checked by the owner on a real export.
- New dependencies `html-to-image` and `jspdf`: licence and supplier checked before install, then added to `specs/tech-stack.md` under dependencies.

## Acceptance cases
- Button: shown on the board page, hidden in Edit mode, calls the exporter once with the board frame and the file name `<board name>-<date>.pdf`.
- Loading guard: with a skeleton on screen the exporter is not called and the toast is shown.
- Frame: header shows the placeholder logo and company name; footer shows the generation time and the signed-in user's name; both are hidden when not exporting.
- Exporter: `PdfBoardExporter` captures with pixel ratio 3, makes a page sized to the capture and saves the file name (library calls faked).

## Out of scope
Selectable-text or vector PDF, splitting a tall board over pages, real company name and logo, PNG export, exporting from AI Mode, email or scheduled export.

## Depends on
synapse-web 06.
