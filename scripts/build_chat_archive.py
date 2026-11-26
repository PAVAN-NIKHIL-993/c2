#!/usr/bin/env python3
"""Inventory this workspace's export, preserve its bytes, and build a reviewable archive.

The three known text records are curated individually below. Unknown text/JSON is
preserved and flagged for review rather than silently treated as a conversation.
Run from the repository root. Refuses to overwrite an existing archive.
"""
from pathlib import Path
import hashlib, json, shutil, zipfile, re

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'refined-chat-archive'
ZIP = ROOT / 'refined-chat-archive.zip'
if OUT.exists() or ZIP.exists():
    raise SystemExit('Archive or ZIP already exists; move it aside before running.')

known = {
 'file_000000000848722f931ef87e35baaf2a.dat': {
  'folder':'undated_vi-track-health-dashboard',
  'title':'VI-TRACK health dashboard and pitch workspace',
  'date':'Unknown; a simulated date in the text is not proof of chat date.',
  'a':'Build a calming, premium futuristic VI-TRACK healthcare application with a cinematic intro, lavender/white glass styling, animated health metrics and ECG, responsive dashboard and 10-slide pitch workspace; rename the dashboard to vi - trak 637 and change selected metric fonts; add a heart-rate hover interaction and a six-day telemetry export; provide ten interactive patient profiles and CSV download/copy capabilities. The complete original wording is preserved in Section C and the raw source.',
  'b':'The source records a design brief and three apparent follow-ups, interleaved with reported implementation/action-history entries. The reported implementation includes an intro with a heart/ECG animation, health telemetry cards, simulated physiological states, a pitch editor, font and brand changes, hover effects, a six-day CSV preview/export and a ten-patient simulated matrix. These are claims in the source, not independently verified implementation or clinical capabilities. Full details and all action history remain in Section C.',
  's':'Verify the app code and build independently; treat telemetry as simulated until real-device provenance and clinical validation are established. Check accessibility, consent and patient-data security before any healthcare deployment; test CSV downloads, per-patient isolation, mobile layouts and animation-reduction preferences.',
  'lim':'Conversation date and whether the captured excerpt spans the entire original conversation are not established. The source is an interface transcript, not a native ChatGPT conversation tree.',
 },
 'file_000000004760820885211b0941a34d58.dat': {
  'folder':'2026-11-24_esp32-hextronik-esc-quadcopter',
  'title':'ESP32, Hextronik and ESC quadcopter',
  'date':'Prepared 24 November 2026 according to source; actual conversation dates/order are not established.',
  'a':'The available reconstruction records requests concerning ESP32, Hextronik, ESC and quadcopter wiring; the ESP32 RMT pin map, compilation and serial-monitor problems; serial and standalone control, arming and PWM; motor layout, ESC power and safety; and a request for a full copyable chat history. The source lists the recovered requests in detail; it does not provide every original user message.',
  'b':'The source is a technical reconstruction with chronological request notes, recoverable assistant guidance, code, pin details, wiring discussion, safety caveats and next steps. It states that earlier chat messages were skipped and unavailable; its original details and limitations are preserved in Section C. Reported working code and wiring are not independently validated here.',
  's':'Review the original export for missing turns. Confirm the actual pin assignments, RMT/core version, ESC signal levels, power and common-ground arrangement, motor order and rotation against hardware documentation. Bench-test without propellers, verify failsafe and arming behavior, and avoid assuming a BEC or mixer is correct without measurement.',
  'lim':'The source explicitly says some messages were skipped and unavailable. This is a reconstruction, not a complete verbatim transcript.',
 },
 'file_00000000ee4882119ed863a94f7d7e86.dat': {
  'folder':'2026-11-24_esp32-hextronik-esc-quadcopter/2026-11-24_esp32-rmt-serial-servo-esc',
  'title':'ESP32 RMT serial servo and ESC controller',
  'date':'24 November 2026 per source; ordering relative to the other ESP32 record is unknown.',
  'a':'The available record describes supplying two ESP32 Arduino sketches for correction and a fully functional serial-controlled servo/ESC controller, then requesting a copyable full chat history with questions, answers and a summary. The source retains the sketches, exact request excerpts and subsequent discussion; it is not evidence that all original turns are available.',
  'b':'The record includes two user-provided sketches, a reported consolidated RMT servo/ESC serial controller and its code, implementation and validation caveats, a second request, and a technical summary comparing the sketches. Preserve the source code and all caveats verbatim in Section C; do not assume the code was hardware-validated.',
  's':'Check the exact ESP32 Arduino core and RMT APIs, channel allocation, timing, parsing, limits, disconnection and failsafe behavior. Test servo and ESC pulse widths with suitable instrumentation; remove propellers for initial tests. Review the original export to verify completeness.',
  'lim':'This is an already prepared history/summary; its prose includes paraphrases and does not establish a complete verbatim original conversation. The ESP32/RMT nesting is a topical heuristic, not proof of a direct continuation.',
 },
}

files = sorted(p for p in ROOT.rglob('*') if p.is_file() and p.suffix.lower() in ('.json','.dat') and not any(x in {'.git','refined-chat-archive'} for x in p.relative_to(ROOT).parts))
OUT.mkdir(); (OUT/'raw_dat_attachments').mkdir(); (OUT/'raw_text_sources').mkdir(); (OUT/'raw_json_sources').mkdir()
counts={'json':0,'json_dat':0,'text_dat':0,'binary_dat':0}
records=[]; found=set(); review=[]
for path in files:
    rel=path.relative_to(ROOT); b=path.read_bytes()
    sha=hashlib.sha256(b).hexdigest(); md5=hashlib.md5(b).hexdigest()
    if path.suffix.lower()=='.json':
        kind='json'; counts[kind]+=1; dest=OUT/'raw_json_sources'/rel
        try: json.loads(b.decode('utf-8-sig'))
        except (UnicodeError, json.JSONDecodeError): review.append(f'{rel}: invalid JSON; preserved for review')
        else: review.append(f'{rel}: JSON preserved; conversation parsing requires review')
    else:
        try:
            text=b.decode('utf-8')
            # Valid UTF-8 is not sufficient for a text classification if NUL/control bytes occur.
            if any(ord(ch)<32 and ch not in '\r\n\t\f' for ch in text): raise UnicodeError('binary controls')
        except UnicodeError:
            kind='binary_dat'; dest=OUT/'raw_dat_attachments'/rel
        else:
            try: json.loads(text)
            except json.JSONDecodeError: kind='text_dat'; dest=OUT/'raw_text_sources'/rel
            else: kind='json_dat'; dest=OUT/'raw_json_sources'/rel; review.append(f'{rel}: JSON .dat preserved; conversation parsing requires review')
        counts[kind]+=1
    dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(b)
    assert hashlib.sha256(dest.read_bytes()).hexdigest()==sha
    records.append((str(rel),kind,len(b),sha,md5,str(dest.relative_to(OUT))))
    # Recognize exact unique filenames only; do not mistake similarly named sources for these records.
    if path.name in known and rel == Path(path.name) and kind == 'text_dat':
        c=known[path.name]; found.add(path.name); folder=OUT/c['folder']; folder.mkdir(parents=True,exist_ok=True)
        intro=(f"# {c['title']}\n\nSource: {rel}\nDate: {c['date']}\nLimitation: {c['lim']}\n\n"
          f"## Section A: Consolidated User Questions (Single Paragraph)\n\n{c['a']}\n\n"
          f"## Section B: Comprehensive Chat Summary & Actionable Suggestions\n\n### Full Summary\n\n{c['b']}\n\n### Suggestions & Next Steps\n\n{c['s']}\n\n"
          "## Section C: Complete Pin-to-Pin Refined Transcript\n\n"
          "The following is the complete *available source text*, unchanged. Its original speaker labels, if any, and source limitations are retained; reconstructed passages cannot be converted into verbatim turns without inventing content. The separate raw source preserves exact bytes and line endings.\n\n--- BEGIN AVAILABLE SOURCE ---\n")
        (folder/'refined_chat.txt').write_bytes(intro.encode('utf-8')+b+b'\n--- END AVAILABLE SOURCE ---\n')
    elif kind=='text_dat':
        review.append(f'{rel}: UTF-8 text preserved; not identified as a conversation record')

index=['# Refined chat archive', '',
 '## Important completeness limitations',
 'This archive preserves every scanned source byte, not necessarily the entire ChatGPT export. No native conversation JSON was found in this snapshot. Three text files contain chat-like records; two explicitly consist of reconstructions or summaries. The quadcopter record says earlier messages are missing. Counts below refer to observed records, not proof of the number of original conversations. Do not treat reconstructed prose as a complete verbatim transcript.',
 'The VI-TRACK date is unknown; `undated` avoids inventing a date. The two ESP32 records are nested due to shared ESP32/RMT/ESC subject matter; neither a direct continuation nor their same-day order is established. Other binary attachments could not be reliably linked to individual chats.', '',
 '## Scan and verification',
 f"JSON files: {counts['json']}; JSON .dat: {counts['json_dat']}; UTF-8 text .dat: {counts['text_dat']}; binary .dat: {counts['binary_dat']}.",
 f"Recognized chat-like records: {len(found)}; generated refined_chat.txt files: {len(list(OUT.rglob('refined_chat.txt')))}. All {len(records)} scanned source files were copied and SHA-256 checked.",
 '', '## Topic tree and chronology (where known)', '```', 'refined-chat-archive/', '├── undated_vi-track-health-dashboard/', '│   └── refined_chat.txt', '├── 2026-11-24_esp32-hextronik-esc-quadcopter/', '│   ├── refined_chat.txt', '│   └── 2026-11-24_esp32-rmt-serial-servo-esc/', '│       └── refined_chat.txt', '├── raw_dat_attachments/  (binary .dat sources, original relative paths)', '├── raw_text_sources/     (all UTF-8 text .dat sources, original relative paths)', '└── raw_json_sources/     (JSON sources if any)', '```', '', '## Record details']
for name in known:
 if name in found:
  c=known[name]; index.extend([f"- [{c['title']}]({c['folder']}/refined_chat.txt) — source `{name}` (text .dat). {c['date']} {c['lim']}"])
index += ['', '## Source inventory (original path, type, bytes, SHA-256, MD5, archive copy)', '']
for path,kind,size,sha,md5,dest in records:
 index.append(f'- `{path}` | {kind} | {size} bytes | SHA-256 `{sha}` | MD5 `{md5}` | [{dest}]({dest})')
index += ['', '## Review / unclassified source notes', ''] + ([f'- {x}' for x in review] if review else ['- None.']) + ['']
(OUT/'INDEX.md').write_text('\n'.join(index),encoding='utf-8')
assert found == set(known), f'Missing known records: {set(known)-found}'
assert len(list(OUT.rglob('refined_chat.txt')))==len(found)
assert sum(counts.values())==len(records)
with zipfile.ZipFile(ZIP,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted(OUT.rglob('*')):
  if p.is_file(): z.write(p,p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(ZIP) as z:
 assert z.testzip() is None
 for p in OUT.rglob('*'):
  if p.is_file(): assert z.read(p.relative_to(ROOT).as_posix())==p.read_bytes()
print('Counts:',counts,'known chat-like records:',len(found),'raw sources verified:',len(records),'zip bytes:',ZIP.stat().st_size)
print('Review:',*review,sep='\n- ')
