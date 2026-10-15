#!/usr/bin/env python3
"""Generate the README user-journey flow charts.

Each chart is a swimlane SVG wrapped in a self-contained HTML page
(docs/flows/<slug>.html), then rendered to a 2x PNG with headless Chrome
(docs/flows/<slug>.png) so GitHub can show it inside the README.

    python3 docs/flows/build.py            # HTML + PNG
    python3 docs/flows/build.py --no-png   # HTML only
"""
import html
import pathlib
import subprocess
import sys

OUT = pathlib.Path(__file__).resolve().parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# meaning -> (fill, stroke)
KIND = {
    "user":    ("#dae8fc", "#6c8ebf"),
    "agent":   ("#d9f0f2", "#4f9da6"),
    "backend": ("#eee5f5", "#9673a6"),
    "decide":  ("#fff2cc", "#d6b656"),
    "ok":      ("#d5e8d4", "#82b366"),
    "fail":    ("#fff7f6", "#b85450"),
    "note":    ("#f5f5f5", "#8a94a3"),
}
EDGE = {"user": "#6c8ebf", "agent": "#4f9da6", "backend": "#9673a6",
        "decide": "#b8962e", "ok": "#5f9a4c", "fail": "#b85450", "note": "#8a94a3"}

LABEL_W = 170      # lane label column
COL_W = 230        # column pitch
NODE_W = 172
DIAMOND = (176, 108)
TOP = 128          # header height
PHASE_H = 34       # optional phase strip


def esc(s):
    return html.escape(s, quote=True)


class Chart:
    def __init__(self, slug, title, subtitle, lanes, cols, note, lane_h=130, phases=None):
        self.slug, self.title, self.subtitle = slug, title, subtitle
        self.lanes, self.cols, self.note = lanes, cols, note
        self.lane_h = lane_h if isinstance(lane_h, list) else [lane_h] * len(lanes)
        self.phases = phases or []
        self.nodes, self.edges = {}, []
        self.width = LABEL_W + cols * COL_W + 40
        self.lane_top = TOP + (PHASE_H if self.phases else 0)

    # geometry ---------------------------------------------------------
    def cx(self, col):
        return LABEL_W + 20 + col * COL_W + COL_W / 2

    def ly(self, lane):
        return self.lane_top + sum(self.lane_h[:lane])

    def cy(self, lane):
        return self.ly(lane) + self.lane_h[lane] / 2

    def lanes_bottom(self):
        return self.lane_top + sum(self.lane_h)

    def node(self, nid, lane, col, kind, title, subs=(), shape="rect"):
        titles = title.split("\n")
        if shape == "diamond":
            w, h = DIAMOND
        else:
            w, h = NODE_W, max(62, 24 + 18 * len(titles) + 16 * len(subs))
        self.nodes[nid] = dict(x=self.cx(col), y=self.cy(lane), w=w, h=h, kind=kind,
                               titles=titles, subs=list(subs), shape=shape)

    def port(self, nid, side, off=0):
        n = self.nodes[nid]
        x, y, w, h = n["x"], n["y"], n["w"], n["h"]
        return {"r": (x + w / 2, y + off), "l": (x - w / 2, y + off),
                "t": (x + off, y - h / 2), "b": (x + off, y + h / 2)}[side]

    def edge(self, a, b, mode="h", label=None, kind="agent", dashed=False,
             mx=None, my=None, sp=None, ep=None, so=0, eo=0, pts=None, lseg=None):
        """Orthogonal connector. mode: h | v | hvh | vh | hv | vhv | pts."""
        if mode == "h":
            s, e = self.port(a, sp or "r", so), self.port(b, ep or "l", eo)
            path = [s, (e[0], s[1])]
        elif mode == "v":
            na, nb = self.nodes[a], self.nodes[b]
            down = nb["y"] > na["y"]
            s = self.port(a, sp or ("b" if down else "t"), so)
            e = self.port(b, ep or ("t" if down else "b"), eo)
            path = [s, (s[0], e[1])]
        elif mode == "hvh":
            s, e = self.port(a, sp or "r", so), self.port(b, ep or "l", eo)
            x = mx if mx is not None else (s[0] + e[0]) / 2
            path = [s, (x, s[1]), (x, e[1]), e]
        elif mode == "vh":
            na, nb = self.nodes[a], self.nodes[b]
            s = self.port(a, sp or ("b" if nb["y"] > na["y"] else "t"), so)
            e = self.port(b, ep or ("l" if nb["x"] > na["x"] else "r"), eo)
            path = [s, (s[0], e[1]), e]
        elif mode == "hv":
            na, nb = self.nodes[a], self.nodes[b]
            s = self.port(a, sp or ("r" if nb["x"] > na["x"] else "l"), so)
            e = self.port(b, ep or ("t" if nb["y"] > na["y"] else "b"), eo)
            path = [s, (e[0], s[1]), e]
        elif mode == "vhv":
            s, e = self.port(a, sp, so), self.port(b, ep, eo)
            path = [s, (s[0], my), (e[0], my), e]
        elif mode == "pts":
            s, e = self.port(a, sp, so), self.port(b, ep, eo)
            path = [s, *pts, e]
        self.edges.append(dict(path=path, label=label, kind=kind, dashed=dashed, lseg=lseg))

    # rendering --------------------------------------------------------
    def render_node(self, n):
        fill, stroke = KIND[n["kind"]]
        x, y, w, h = n["x"], n["y"], n["w"], n["h"]
        out = []
        if n["shape"] == "diamond":
            pts = f"{x},{y - h/2} {x + w/2},{y} {x},{y + h/2} {x - w/2},{y}"
            out.append(f'<polygon class="shape" points="{pts}" fill="{fill}" stroke="{stroke}"/>')
            lines = [(t, "title sm") for t in n["titles"]] + [(s, "sub") for s in n["subs"]]
            step = 16
        else:
            out.append(f'<rect class="shape" x="{x - w/2}" y="{y - h/2}" width="{w}" height="{h}" '
                       f'rx="7" fill="{fill}" stroke="{stroke}"/>')
            lines = [(t, "title") for t in n["titles"]] + [(s, "sub") for s in n["subs"]]
            step = 17
        y0 = y - (len(lines) - 1) * step / 2 + 4
        for i, (t, cls) in enumerate(lines):
            out.append(f'<text class="{cls}" x="{x}" y="{y0 + i * step}">{esc(t)}</text>')
        return "\n".join(out)

    def render_edge(self, e):
        color = EDGE[e["kind"]]
        pts = " ".join(f"{px},{py}" for px, py in e["path"])
        dash = ' stroke-dasharray="7 5"' if e["dashed"] else ""
        out = [f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2.2"'
               f'{dash} marker-end="url(#arrow-{e["kind"]})"/>']
        if e["label"]:
            segs = list(zip(e["path"], e["path"][1:]))
            i = e["lseg"] if e["lseg"] is not None else len(segs) - 1
            (x1, y1), (x2, y2) = segs[i]
            tw = len(e["label"]) * 6.6 + 12
            if y1 == y2:   # horizontal: centered, above the line
                lx, ly = (x1 + x2) / 2, y1 - 10
                out.append(f'<rect x="{lx - tw/2}" y="{ly - 12}" width="{tw}" height="17" rx="4" class="lblbg"/>')
                out.append(f'<text class="elabel" x="{lx}" y="{ly}" fill="{color}">{esc(e["label"])}</text>')
            else:          # vertical: beside the line, at the middle
                lx, ly = x1 + 8, (y1 + y2) / 2 + 4
                out.append(f'<rect x="{lx - 3}" y="{ly - 12}" width="{tw}" height="17" rx="4" class="lblbg"/>')
                out.append(f'<text class="elabel" x="{lx + 3}" y="{ly}" fill="{color}" '
                           f'style="text-anchor:start">{esc(e["label"])}</text>')
        return "\n".join(out)

    def svg(self):
        W = self.width
        note_y = self.lanes_bottom() + 22
        note_lines = self.note
        note_h = 26 + 19 * len(note_lines)
        H = note_y + note_h + 24
        p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
        p.append("<defs>" + "".join(
            f'<marker id="arrow-{k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
            f'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
            for k, c in EDGE.items()) + "</defs>")
        # header
        p.append(f'<text class="h1" x="28" y="44">{esc(self.title)}</text>')
        p.append(f'<text class="h2" x="28" y="70">{esc(self.subtitle)}</text>')
        legend = [("user", "User"), ("agent", "Agent"), ("decide", "Decision / check"),
                  ("backend", "Vault / records"), ("ok", "Done"), ("fail", "Failure / fallback")]
        lx = 28
        for k, t in legend:
            f, s = KIND[k]
            p.append(f'<rect x="{lx}" y="88" width="16" height="12" rx="3" fill="{f}" stroke="{s}" stroke-width="1.5"/>')
            p.append(f'<text class="legend" x="{lx + 22}" y="98">{esc(t)}</text>')
            lx += len(t) * 7 + 40
        # phases
        if self.phases:
            for i, (label, c0, c1) in enumerate(self.phases):
                x0 = LABEL_W + 20 + c0 * COL_W + 4
                x1 = LABEL_W + 20 + (c1 + 1) * COL_W - 4
                p.append(f'<rect x="{x0}" y="{TOP + 2}" width="{x1 - x0}" height="{PHASE_H - 8}" rx="5" class="phase"/>')
                p.append(f'<text class="phasetxt" x="{(x0 + x1)/2}" y="{TOP + 20}">{esc(label)}</text>')
                if i:
                    p.append(f'<line x1="{x0 - 4}" y1="{TOP}" x2="{x0 - 4}" y2="{self.lanes_bottom()}" class="phaseline"/>')
        # lanes
        for i, name in enumerate(self.lanes):
            y, h = self.ly(i), self.lane_h[i]
            p.append(f'<rect x="20" y="{y}" width="{W - 40}" height="{h}" fill="{"#ffffff" if i % 2 == 0 else "#f8fafc"}" stroke="#e3e8ef"/>')
            p.append(f'<rect x="20" y="{y}" width="{LABEL_W - 20}" height="{h}" fill="#eef2f7" stroke="#e3e8ef"/>')
            for j, part in enumerate(name.split("\n")):
                p.append(f'<text class="lane" x="{20 + (LABEL_W - 20)/2}" y="{y + h/2 + 5 + (j - (len(name.split(chr(10))) - 1)/2) * 17}">{esc(part)}</text>')
        for e in self.edges:
            p.append(self.render_edge(e))
        for n in self.nodes.values():
            p.append(self.render_node(n))
        # note
        p.append(f'<rect x="20" y="{note_y}" width="{W - 40}" height="{note_h}" rx="7" fill="#f5f5f5" stroke="#8a94a3" stroke-width="1.2"/>')
        for i, line in enumerate(note_lines):
            p.append(f'<text class="note" x="38" y="{note_y + 27 + i * 19}">{esc(line)}</text>')
        p.append("</svg>")
        return "\n".join(p), W, H

    def write(self):
        svg, W, H = self.svg()
        page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(self.title)}</title>
<style>
  html, body {{ margin: 0; background: #f4f6fa;
    background-image: radial-gradient(#d9dee7 1px, transparent 1px); background-size: 14px 14px; }}
  .canvas {{ width: {W}px; margin: 24px auto; background: #fff; border: 1px solid #dbe2ea;
    border-radius: 10px; box-shadow: 0 2px 10px rgba(16, 24, 40, .06); }}
  svg {{ display: block; font-family: Inter, "PingFang SC", "Helvetica Neue", Arial, sans-serif; }}
  .h1 {{ font-size: 22px; font-weight: 700; fill: #1f2933; }}
  .h2 {{ font-size: 13.5px; fill: #5b6675; }}
  .legend {{ font-size: 12px; fill: #5b6675; }}
  .lane {{ font-size: 13px; font-weight: 700; fill: #3e4c5e; text-anchor: middle; }}
  .shape {{ stroke-width: 1.8; filter: drop-shadow(0 1px 2px rgba(16, 24, 40, .10)); }}
  .title {{ font-size: 14px; font-weight: 700; fill: #1f2933; text-anchor: middle; }}
  .title.sm {{ font-size: 13px; }}
  .sub {{ font-size: 12px; fill: #4a5563; text-anchor: middle; }}
  .elabel {{ font-size: 11.5px; font-weight: 700; text-anchor: middle; }}
  .lblbg {{ fill: #fff; opacity: .92; }}
  .note {{ font-size: 13px; fill: #3e4c5e; }}
  .phase {{ fill: #eef2f7; stroke: #d5dce6; }}
  .phasetxt {{ font-size: 12.5px; font-weight: 700; fill: #3e4c5e; text-anchor: middle; }}
  .phaseline {{ stroke: #c5cedb; stroke-dasharray: 4 4; }}
</style></head>
<body><div class="canvas">
{svg}
</div></body></html>
"""
        path = OUT / f"{self.slug}.html"
        path.write_text(page)
        return path, W, H


def png(path, W, H):
    out = path.with_suffix(".png")
    tmp = OUT / f".{path.stem}.shot.html"
    # screenshot only the canvas: same page without page margins/background
    tmp.write_text(path.read_text().replace("margin: 24px auto", "margin: 0")
                   .replace("border: 1px solid #dbe2ea;", "border: 0;"))
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=2", f"--window-size={W},{H}",
                    f"--screenshot={out}", tmp.as_uri()],
                   check=True, capture_output=True)
    tmp.unlink()
    return out


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

def core_loop():
    c = Chart("00-core-loop", "Every journey · one loop",
              "The agent does everything up to the commitment; the user makes the commitment.",
              ["Life & sources", "Agent", "User · approves", "User · in person", "Human operator", "Vault"],
              cols=7, lane_h=[110, 130, 110, 110, 110, 130],
              note=["Steps are sorted by who can do them, not listed flat — the user sees at a glance what is handled and what needs them.",
                    "Every completed step leaves a receipt in the vault and updates the account map and tax file, which become context for the next trigger."])
    c.node("trigger", 0, 0, "note", "Trigger", ["life event · deadline", "new document"])
    c.node("read", 1, 1, "agent", "Read context", ["vault + account map"])
    c.node("plan", 1, 2, "agent", "Build the plan", ["steps + deadlines"])
    c.node("who", 1, 3, "decide", "Who can do\neach step?", shape="diamond")
    c.node("exec", 1, 4, "agent", "Agent executes", ["via API or form fill"])
    c.node("esign", 2, 4, "user", "Approve + e-sign", ["pre-filled for the user"])
    c.node("guide", 3, 4, "user", "Guided task", ["in person · checklist"])
    c.node("human", 4, 4, "fail", "Human operator", ["finishes it, named owner"])
    c.node("track", 5, 5, "backend", "Tracker + receipts", ["saved to the vault"])
    c.node("map", 5, 6, "ok", "Account map + tax file", ["updated"])
    c.edge("trigger", "read", "hvh", kind="note")
    c.edge("read", "plan", "h")
    c.edge("plan", "who", "h")
    c.edge("who", "exec", "h", "API")
    c.edge("who", "esign", "vh", "needs signature", kind="user", sp="b")
    c.edge("who", "guide", "vh", "in person", kind="user", sp="b")
    c.edge("who", "human", "vh", "automation fails", kind="fail", sp="b")
    for nid, k in [("exec", "agent"), ("esign", "user"), ("guide", "user"), ("human", "fail")]:
        c.edge(nid, "track", "hv", kind=k)
    c.edge("track", "map", "h", kind="backend")
    yb = c.ly(5) + c.lane_h[5] - 14
    c.edge("map", "trigger", "pts", "next trigger", kind="note", dashed=True, sp="b", ep="b",
           pts=[(c.cx(6), yb), (c.cx(0), yb)], lseg=1)
    return c


def onboarding():
    c = Chart("01-onboarding", "J0 · Onboarding and verification",
              "Verify once, choose how much the agent may do, and show something useful within five minutes.",
              ["User", "Errand app", "Agent", "KYC vendor", "Manual review"], cols=8,
              note=["Aha moment: within 5 minutes the agent shows something the user didn't know — a renewal coming up, a forgotten subscription, or last year's refund.",
                    "Permission tiers: Notify only → Prepare and ask (default) → Act within limits, e.g. \"cancel subscriptions under $20 without asking\". Filing, paying, and signing always ask.",
                    "No agent action of any kind runs until KYC has passed."])
    c.node("hook", 0, 0, "user", "Lands from a hook", ["move · tax · renewal"])
    c.node("signup", 0, 1, "user", "Sign up")
    c.node("kyc", 3, 1, "backend", "ID scan + liveness", ["selfie check"])
    c.node("pass", 3, 2, "decide", "KYC passed?", shape="diamond")
    c.node("manual", 4, 2, "fail", "Manual review", ["or retry the scan"])
    c.node("tier", 0, 3, "user", "Choose permission tier", ["default: Prepare and ask"])
    c.node("connect", 0, 4, "user", "Connect sources", ["email · bank · payroll", "brokerage · IRS"])
    c.node("map", 2, 5, "agent", "Build the life map", ["accounts · IDs", "policies · dates"])
    c.node("found", 1, 6, "ok", "First \"found for you\"", ["e.g. passport expiring"])
    c.node("pick", 0, 7, "user", "Pick a first job")
    c.edge("hook", "signup", "h", kind="user")
    c.edge("signup", "kyc", "v", kind="user")
    c.edge("kyc", "pass", "h", kind="backend")
    c.edge("pass", "tier", "vh", "pass", kind="ok", sp="t")
    c.edge("pass", "manual", "v", "fail", kind="fail")
    c.edge("manual", "kyc", "hv", "re-check", kind="fail", sp="l", lseg=0)
    c.edge("tier", "connect", "h", kind="user")
    c.edge("connect", "map", "hvh", "read-only", kind="user", lseg=1)
    c.edge("map", "found", "hvh")
    c.edge("found", "pick", "hvh", kind="ok")
    return c


def move():
    c = Chart("02-move", "J1 · Move — change my address everywhere",
              "One plan in four lanes, sorted by who can do each step; finished steps feed other modules.",
              ["User", "Agent", "Needs signature", "In person", "Optional offers", "Other modules"],
              cols=8, lane_h=[110, 130, 110, 110, 110, 120],
              note=["Prototype: 15 accounts with the old address → 7 agent updates, 4 need a signature, 2 in person, 2 optional offers.",
                    "Sponsored offers live in their own lane and never appear inside a required step.",
                    "Edge cases: moving to another state (part-year resident returns), moving abroad, temporary moves, two people moving together. Success: % of accounts updated within 14 days."])
    c.node("start", 0, 0, "user", "\"I'm moving\"", ["new address + date"])
    c.node("scan", 1, 1, "agent", "Find old addresses", ["scan email + bank"])
    c.node("plan", 1, 2, "agent", "Plan in four lanes")
    c.node("d1", 1, 3, "agent", "Agent updates directly", ["bank · card · brokerage", "payroll · phone · subs"])
    c.node("d2", 2, 3, "user", "Pre-filled e-sign", ["USPS · voter reg · insurance"])
    c.node("d3", 3, 3, "user", "Do it in person", ["license · vehicle reg"])
    c.node("d4", 4, 3, "note", "Internet · utilities", ["labeled sponsored"])
    c.node("track", 1, 4, "ok", "Tracker until done", ["receipts per account"])
    c.node("tax", 5, 5, "backend", "Tax", ["part-year residency"])
    c.node("renew", 5, 6, "backend", "Renew", ["replace, don't renew"])
    c.node("pay", 5, 7, "backend", "Payroll", ["state withholding"])
    c.edge("start", "scan", "hvh", kind="user")
    c.edge("scan", "plan", "h")
    c.edge("plan", "d1", "h", "agent")
    c.edge("plan", "d2", "vh", "signature", kind="user")
    c.edge("plan", "d3", "vh", "in person", kind="user")
    c.edge("plan", "d4", "vh", "optional", kind="note")
    c.edge("d1", "track", "h", "1 tap")
    c.edge("d2", "track", "hv", kind="user", eo=-30)
    c.edge("d3", "track", "hv", kind="user", eo=30)
    for nid in ["tax", "renew", "pay"]:
        c.edge("track", nid, "hv", "hand off", kind="backend", lseg=1)
    return c


def renew():
    c = Chart("03-renew", "J2 · Renew — never miss an expiry",
              "Lead times are per document; anything the user can't submit online becomes a ready-to-go packet.",
              ["User", "Agent", "Checks", "User · offline", "Vault"], cols=8,
              note=["Lead times: passport about 6 months (many countries require 6 months' validity), visa by type, insurance 30 days so there is time to shop around.",
                    "The passport packet stops on a vault photo older than 6 months instead of reusing it. Insurance quotes are compared on the same coverage.",
                    "Success: lapses prevented; insurance savings per renewal."])
    c.node("scan", 1, 0, "agent", "Scan the vault", ["passport · license", "registration · insurance"])
    c.node("cal", 1, 1, "agent", "Expiry calendar", ["per-document lead time"])
    c.node("inside", 2, 2, "decide", "Inside the\nlead time?", shape="diamond")
    c.node("prep", 1, 3, "agent", "Prepare the renewal", ["pre-filled form + checks"])
    c.node("ins", 1, 4, "agent", "Re-quote insurance", ["same coverage"])
    c.node("online", 2, 4, "decide", "Submittable\nonline?", shape="diamond")
    c.node("approve", 0, 5, "user", "User approves", ["this specific renewal"])
    c.node("submit", 1, 6, "agent", "Agent submits", ["signed with KYC identity"])
    c.node("packet", 3, 4, "user", "Printable packet", ["or booked appointment"])
    c.node("saved", 4, 7, "ok", "New doc saved", ["calendar resets"])
    c.edge("scan", "cal", "h")
    c.edge("cal", "inside", "hvh")
    yb = c.ly(2) + c.lane_h[2] - 10
    c.edge("inside", "cal", "pts", "no · wait", kind="decide", sp="b", ep="b",
           pts=[(c.cx(2), yb), (c.cx(1), yb)], lseg=1)
    c.edge("inside", "prep", "hvh", "yes", kind="decide", lseg=2)
    c.edge("prep", "ins", "h", "insurance")
    c.edge("prep", "online", "hvh", "documents", lseg=1)
    c.edge("online", "approve", "hv", "yes", kind="decide", lseg=1)
    c.edge("online", "packet", "v", "no", kind="decide")
    c.edge("approve", "submit", "hvh", kind="user")
    c.edge("submit", "saved", "hv", eo=30)
    c.edge("packet", "saved", "hv", kind="user", eo=-30)
    return c


def claim():
    c = Chart("04-claim", "J3 · Claim — get my money back",
              "The agent finds the claim, asks the one question that decides it, and keeps going until it is paid.",
              ["User", "Agent", "Institution", "Vault & tax"], cols=8,
              note=["Prototype: three claims worth $1,338 — a $412 cancelled flight, $286 of FSA receipts, a $640 out-of-network bill.",
                    "Appeals are drafted for review; nothing is sent until the user approves it.",
                    "Revenue: a share of what's recovered, or included in the subscription."])
    c.node("trig", 1, 0, "note", "Claim found", ["cancelled flight · FSA", "surprise bill"])
    c.node("elig", 1, 1, "decide", "Check eligibility", ["terms + deadline"])
    c.node("evid", 1, 2, "agent", "Gather evidence", ["emails · receipts", "statements"])
    c.node("fill", 1, 3, "agent", "Agent form fill", ["asks the deciding question"])
    c.node("sign", 0, 4, "user", "Confirm + sign")
    c.node("file", 1, 5, "agent", "File + follow up", ["re-check in 7 days"])
    c.node("out", 2, 6, "decide", "Outcome", shape="diamond")
    c.node("appeal", 1, 6, "fail", "Draft an appeal", ["for the user to review"])
    c.node("paid", 3, 7, "ok", "Paid · logged", ["→ tax file"])
    c.edge("trig", "elig", "h", kind="note")
    c.edge("elig", "evid", "h", "eligible", kind="decide")
    c.edge("evid", "fill", "h")
    c.edge("fill", "sign", "hvh")
    c.edge("sign", "file", "hvh", kind="user")
    c.edge("file", "out", "hvh")
    c.edge("out", "appeal", "v", "denied", kind="fail")
    yt = c.ly(0) + 14
    c.edge("appeal", "sign", "pts", "approve appeal", kind="fail", sp="t", ep="t",
           pts=[(c.cx(6), yt), (c.cx(4), yt)], lseg=0)
    c.edge("out", "paid", "hv", "paid", kind="ok", lseg=0)
    return c


def tax_year():
    c = Chart("05-tax-year-round", "J4 · Tax — a year-round copilot",
              "Most strategies that save money have to happen before December 31, so the journey runs all year.",
              ["User", "Agent", "Other modules"], cols=8,
              phases=[("All year · Plan", 0, 2), ("Oct–Dec · Year-end", 3, 4),
                      ("Jan–Apr · File", 5, 5), ("After filing", 6, 7)],
              note=["Life events arrive from Move (residency dates), Claim (HSA and medical records), Renew (open enrollment), payroll, bank, and brokerage.",
                    "Accepting a strategy only drafts the change; nothing moves money until that specific action is approved.",
                    "After filing, the agent also reads IRS letters, explains them, and drafts a reply for approval."])
    c.node("events", 2, 0, "backend", "Life events", ["Move · Claim · Renew", "payroll · brokerage"])
    c.node("pic", 1, 1, "agent", "Running tax picture", ["payroll · bank · brokerage"])
    c.node("proj", 1, 2, "agent", "Projection", ["updated monthly"])
    c.node("strat", 1, 3, "decide", "Year-end strategies", ["$ effect + deadline"])
    c.node("accept", 0, 4, "user", "Accept a strategy", ["agent drafts the change"])
    c.node("file", 1, 5, "agent", "File the return", ["see the filing flow"])
    c.node("refund", 1, 6, "ok", "Refund tracking")
    c.node("carry", 1, 7, "backend", "Carry forward", ["into next year's plan"])
    c.edge("events", "pic", "hvh", kind="backend")
    c.edge("pic", "proj", "h")
    c.edge("proj", "strat", "h")
    c.edge("strat", "accept", "hvh", kind="decide")
    c.edge("accept", "file", "hvh", kind="user")
    c.edge("file", "refund", "h")
    c.edge("refund", "carry", "h", kind="ok")
    yt = c.ly(0) + 14
    c.edge("carry", "pic", "pts", "next year", kind="backend", dashed=True, sp="t", ep="t",
           pts=[(c.cx(7), yt), (c.cx(1), yt)], lseg=0)
    return c


def tax_file():
    c = Chart("06-tax-filing", "J4 · Tax — filing",
              "Free options first, prefill before asking, and a failed accuracy check blocks signing until it is fixed.",
              ["User", "Checks", "Agent", "IRS & partners"], cols=9, lane_h=[120, 140, 120, 120],
              note=["Prototype return: 7 of 15 fields pre-filled before the first question; 2 answers fill the other 8; the refund meter moves from owe $460 to a refund.",
                    "The cost-basis check fails on a 2009 stock sale; the agent finds the trade confirmation in email and asks to use it. Checks then pass 6/6.",
                    "Any edit after Confirm reopens the interview and invalidates the confirmation and the checks."])
    c.node("free", 1, 0, "decide", "Qualifies for\nfree filing?", shape="diamond")
    c.node("vita", 3, 0, "ok", "IRS Free File / VITA", ["agent sends them there"])
    c.node("docs", 2, 1, "agent", "Collect documents", ["with sources + flags"])
    c.node("pre", 2, 2, "agent", "Prefill from vault", ["7 of 15 fields"])
    c.node("ask", 0, 3, "user", "Answer the gap", ["2 answers → 8 fields"])
    c.node("conf", 0, 4, "user", "Confirm draft", ["locks this version"])
    c.node("chk", 1, 5, "decide", "Accuracy\nchecks", shape="diamond")
    c.node("fix", 2, 5, "fail", "Fix with evidence", ["e.g. missing cost basis"])
    c.node("cx", 1, 6, "decide", "Complex\nreturn?", shape="diamond")
    c.node("cpa", 3, 6, "note", "CPA / EA review", ["credentialed, on demand"])
    c.node("sign", 0, 7, "user", "User signs", ["with the KYC identity"])
    c.node("efile", 3, 8, "ok", "E-file", ["via authorized partner"])
    c.edge("free", "vita", "v", "yes", kind="ok")
    c.edge("free", "docs", "hvh", "no", kind="decide", lseg=0)
    c.edge("docs", "pre", "h")
    c.edge("pre", "ask", "hvh")
    c.edge("ask", "conf", "h", kind="user")
    c.edge("conf", "chk", "vh", kind="user")
    c.edge("chk", "fix", "v", "fail", kind="fail")
    c.edge("fix", "chk", "pts", "re-run", kind="fail", sp="l", ep="l",
           pts=[(c.cx(4.5) - 4, c.cy(2)), (c.cx(4.5) - 4, c.cy(1))], lseg=1)
    c.edge("chk", "cx", "h", "pass", kind="ok")
    c.edge("cx", "sign", "vh", "simple", kind="decide", sp="t")
    c.edge("cx", "cpa", "v", "complex", kind="decide")
    c.edge("cpa", "sign", "hv", kind="note", eo=-30)
    c.edge("sign", "efile", "hvh", kind="user", mx=c.cx(7.5))
    return c


def ask():
    c = Chart("07-ask-errand", "Ask Errand · always-on Q&A",
              "Answers come only from the user's own records — with a source, a confidence, and an honest empty state.",
              ["User", "Checks", "Ask agent", "Product page"], cols=5,
              note=["Clarifies at most once per session (with \"Skip · show both\"); asking again answers directly.",
                    "LOW_CONFIDENCE shows a range, never a single number, names the missing inputs, and cannot navigate onward.",
                    "Actions happen on their page, not inside chat — \"Do it for me\" is P2."])
    c.node("q", 0, 0, "user", "Ask from any page")
    c.node("ans", 1, 1, "decide", "In the user's\nrecords?", shape="diamond")
    c.node("none", 2, 1, "fail", "NO_RESULT", ["says so · offers Connect"])
    c.node("clar", 0, 2, "agent", "NEED_CLARIFICATION", ["one chip question"])
    c.node("conf", 1, 3, "decide", "Confidence", shape="diamond")
    c.node("low", 2, 3, "fail", "LOW_CONFIDENCE", ["range · names the gaps", "no navigation"])
    c.node("card", 2, 4, "agent", "ANSWER_CARD", ["source + confidence %"])
    c.node("page", 3, 4, "ok", "Open the page", ["act there"])
    c.edge("q", "ans", "hvh", kind="user")
    c.edge("ans", "none", "v", "no", kind="fail")
    c.edge("ans", "clar", "vh", "ambiguous", kind="decide", sp="t")
    c.edge("ans", "conf", "h", "yes", kind="decide")
    c.edge("clar", "conf", "hv")
    c.edge("conf", "low", "v", "low", kind="fail")
    c.edge("conf", "card", "hvh", "high", kind="decide", lseg=0)
    c.edge("card", "page", "v", kind="ok")
    return c


CHARTS = [core_loop, onboarding, move, renew, claim, tax_year, tax_file, ask]

if __name__ == "__main__":
    for make in CHARTS:
        path, W, H = make().write()
        line = f"{path.relative_to(OUT.parent.parent)}  {W}x{H}"
        if "--no-png" not in sys.argv:
            line += f"  -> {png(path, W, H).name}"
        print(line)
