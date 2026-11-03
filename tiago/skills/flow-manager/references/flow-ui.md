# Operating Google Flow (for the art agent)

Flow's interface changes; treat the labels below as what worked, look for the equivalent when they move, and report
any difference you find so the skill can be updated. The UI may be in the user's language (Portuguese labels are
given in parentheses where they were observed).

## Tools

Load all Chrome tools in one ToolSearch call:
`select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__computer,mcp__claude-in-chrome__read_page,mcp__claude-in-chrome__tabs_create_mcp,mcp__claude-in-chrome__tabs_close_mcp,mcp__claude-in-chrome__find,mcp__claude-in-chrome__form_input,mcp__claude-in-chrome__get_page_text,mcp__claude-in-chrome__browser_batch`
If a call says Claude in Chrome is not connected, stop and report: the user has to connect the extension.

## Session

1. `tabs_context_mcp` with `createIfEmpty: true`, open a NEW tab (the user may be using the others) and `navigate`
   to the project URL from the brief. Wait ~4 s.
2. Open a **new agent session** in Flow's agent panel for each piece (or batch of related pieces): old conversations
   leak into new generations. The button is "Start new session" ("Iniciar nova sessão"), next to "Open session
   history" ("Abrir histórico de sessões"); the new one shows as "Untitled session" ("Sessão sem título"). The panel
   may already be open; if it is closed, reopen it with the "Agent" ("Agente") button in the bottom bar.
3. Settings ("Configurações" in the agent panel): "Confirm before generating" ("Confirmar antes de gerar") = Never;
   aspect ratio as the brief says (1:1 for icon sheets and masters, 16:9 for sheets of poses/effects and for video);
   x2; the model from the brief (default Nano Banana 2.1) → Save ("Salvar").
   - **These settings belong to the whole project** ("agent settings in this project") and persist. Write down the
     values you found, and put them back when you finish. If the session history shows another generation still
     running or queued (e.g. a video "queued due to high demand"), another agent may be using the project: do not
     change settings under it; report and wait, or ask the main session.
   - Even with x2, Flow often returns a single image per prompt. Count the attempt by prompts sent, not images.

## Prompting

- Click the prompt textbox by ref, then `computer` `type` the whole prompt on ONE line, starting with
  `Generate an image (do not rewrite or shorten these instructions).` (video: `Generate a video with <model> using
  the attached image as the first frame (do not rewrite or shorten these instructions).`). Flow's agent otherwise
  rewrites and shortens prompts. Press Enter; confirm with `get_page_text` that it was sent.
- Store the prompt in provenance WITHOUT that opener.

## Attaching references (no uploads)

- Use the "+" button of the prompt field → the picker tabs ("Uploads"/"Envios", "All"/"Tudo", images). Search by
  name. Check the thumbnail before attaching: items can have several versions (see below).
- Never execute JavaScript on the page and never try to reach the hidden file input: that produced the
  "We noticed unusual activity" ("Notamos uma atividade incomum") warning. If the needed reference is not in the
  project, stop and ask the main session to have the user add it.

## Waiting and judging

- Wait 30–45 s in 10 s blocks (`browser_batch` with waits), then screenshot at scale 0.6 and zoom on the result.
- Judge against the brief before downloading: grid and count, every part inside its cell with margin, background
  flat and of the right color, no text, same character in every frame, colors, look-alikes.

## Downloading

- The download button in the results list sometimes fails ("Failed to download media"/"Falha ao baixar a mídia").
  Then open the item page and use "Download media" ("Baixar mídia"), which opens a size menu: pick "1K Original
  size" ("1K Tamanho original"). Not "2K Enhanced" (an upscale, not the original) and never "4K" (asks for an
  upgrade). Videos: original 720p.
- Files land in the user's Downloads folder with Flow's own names. Take the newest (`ls -t`), COPY it to the scratch
  `dl<N>/` folder from the brief. Never delete or move files in Downloads.
- Read the item URL (`/project/<id>/edit/<item-id>`) for provenance (`flow_url`).

## Versions: a known side effect

When you ask Flow's agent to EDIT an image that came from the project (e.g. a master attached as reference), the
result may be stored as a new version of that same item instead of a new item. The item's thumbnail then shows
the new version, and later prompts that attach "that" item get the new version. Report this every time it
happens (the original stays in the item's history and can be restored by the user).

## Finishing

Close only the tabs you opened. Report: files, flow_url per piece, model, final prompt, references used, attempts
with the reason for each discard, credits spent on video, and an honest evaluation including weak points.
