#!/usr/bin/env python3
"""Builds demo/index.html: the prototype (../index.html, left untouched) plus a guided
walkthrough layer that drives the prototype's own functions. Re-run after editing the
prototype:  python3 demo/build.py
"""
import pathlib

root = pathlib.Path(__file__).resolve().parent
proto = (root.parent / "index.html").read_text()

TOUR = r'''
<!-- ════════ GUIDED WALKTHROUGH LAYER ════════ -->
<style>
.page{padding-bottom:50vh}
.c-mask{position:fixed;inset:0;z-index:600;display:none}
.c-mask.on{display:block}
.c-spot{position:fixed;border-radius:10px;border:2px solid var(--primary,#3B82F6);
  box-shadow:0 0 0 9999px rgba(15,23,42,.58);transition:all .3s cubic-bezier(.4,0,.2,1);pointer-events:none}
#coach{position:fixed;left:20px;bottom:20px;width:372px;max-width:calc(100vw - 40px);z-index:620;display:none;
  flex-direction:column;background:#fff;border:1px solid var(--border,#E5E7EB);border-radius:12px;
  box-shadow:0 20px 50px rgba(0,0,0,.3);max-height:min(74vh,620px);font-size:13px}
#coach.on{display:flex}
#coach.min{width:auto}
#coach.min .c-body,#coach.min .c-foot,#coach.min .c-prog{display:none}
.c-head{display:flex;align-items:center;gap:9px;padding:11px 14px;border-bottom:1px solid var(--border,#E5E7EB)}
.c-head .dot{width:7px;height:7px;border-radius:50%;background:var(--primary,#3B82F6)}
.c-head b{font-size:12.5px;color:var(--text-1,#111827)}
.c-head .sp{flex:1}
.c-head .cnt{font-size:11px;color:var(--text-4,#9CA3AF);font-variant-numeric:tabular-nums}
.c-head button{border:1px solid var(--border-strong,#D1D5DB);background:#fff;border-radius:6px;width:24px;height:24px;cursor:pointer;color:var(--text-3,#6B7280);padding:0}
.c-prog{height:3px;background:var(--bg-hover,#F3F4F6)}
.c-prog i{display:block;height:100%;background:var(--primary,#3B82F6);transition:width .35s ease}
.c-body{padding:14px;overflow-y:auto}
.c-fl{font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--primary,#3B82F6);font-weight:700;display:flex;align-items:center;gap:8px}
.c-g{font-size:10px;font-weight:700;letter-spacing:.06em;color:#92400E;background:var(--warn-light,#FEF3C7);border:1px solid #FDE68A;padding:1px 7px;border-radius:10px}
.c-t{font-size:15.5px;font-weight:700;color:var(--text-1,#111827);margin:6px 0 12px;line-height:1.35}
.c-note{border-left:3px solid var(--border-strong,#D1D5DB);padding-left:11px;margin-bottom:11px}
.c-note:last-child{margin-bottom:0}
.c-note h5{margin:0 0 3px;font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;color:var(--text-4,#9CA3AF)}
.c-note p{margin:0;font-size:12.8px;color:var(--text-2,#374151);line-height:1.58}
.c-note b{color:var(--text-1,#111827)}
.c-note.c-guard{border-left-color:var(--warn,#F59E0B);background:linear-gradient(90deg,#FFFBEB,transparent 75%);padding:8px 0 8px 11px;border-radius:0 6px 6px 0}
.c-note.c-guard h5{color:#B45309}
.c-foot{display:flex;gap:8px;align-items:center;padding:11px 14px;border-top:1px solid var(--border,#E5E7EB)}
.c-foot .rs{font-size:11.5px;color:var(--text-4,#9CA3AF);cursor:pointer;text-decoration:underline;margin-right:auto;background:none;border:0;padding:0}
.c-dots{display:flex;gap:3px;margin-right:auto;flex-wrap:wrap;max-width:200px}
.c-dots i{width:5px;height:5px;border-radius:50%;background:var(--border,#E5E7EB)}
.c-dots i.on{background:var(--primary,#3B82F6);width:12px;border-radius:3px}
.c-dots i.g{background:#FCD34D}
.c-dots i.g.on{background:#F59E0B}
.c-busy{display:inline-block;width:9px;height:9px;border:2px solid var(--primary,#3B82F6);border-right-color:transparent;border-radius:50%;animation:spin .6s linear infinite;vertical-align:-1px;margin-right:5px}
.demo-fab{position:fixed;left:20px;bottom:20px;z-index:590;display:inline-flex;align-items:center;gap:9px;padding:12px 20px 12px 16px;border:0;border-radius:26px;cursor:pointer;
  font:inherit;font-size:13.5px;font-weight:650;color:#fff;background:var(--primary,#3B82F6);box-shadow:0 10px 28px rgba(59,130,246,.38),0 2px 6px rgba(16,24,40,.14);transition:transform .18s}
.demo-fab:hover{background:var(--primary-hover,#2563EB);transform:translateY(-2px)}
.demo-fab .tri{display:grid;place-items:center;width:22px;height:22px;border-radius:50%;background:rgba(255,255,255,.22);font-size:9px;padding-left:2px}
.demo-fab .sub{font-weight:500;opacity:.8;font-size:12px}
.demo-fab.gone{display:none}
.demo-fab::after{content:"";position:absolute;inset:0;border-radius:26px;border:2px solid var(--primary,#3B82F6);animation:demoPing 2.4s cubic-bezier(.2,.7,.3,1) 3;pointer-events:none}
@keyframes demoPing{0%{opacity:.6;transform:scale(1)}70%,100%{opacity:0;transform:scale(1.25)}}
@media(max-width:820px){#coach{left:12px;right:12px;width:auto;bottom:12px;max-height:50vh}.demo-fab .sub{display:none}}
</style>

<div class="c-mask" id="c-mask"><div class="c-spot" id="c-spot"></div></div>
<div id="coach" role="dialog" aria-label="Guided walkthrough">
  <div class="c-head"><span class="dot"></span><b>Guided walkthrough</b><span class="sp"></span><span class="cnt" id="c-cnt"></span>
    <button onclick="cMin()" title="Minimise" aria-label="Minimise">–</button><button onclick="cEnd()" title="Close" aria-label="Close">×</button></div>
  <div class="c-prog"><i id="c-prog"></i></div>
  <div class="c-body" id="c-body"></div>
  <div class="c-foot"><div class="c-dots" id="c-dots"></div>
    <button class="btn btn-sm" id="c-prev" onclick="cGo(cI-1)">Back</button>
    <button class="btn btn-sm btn-primary" id="c-next" onclick="cGo(cI+1)">Next</button></div>
</div>
<button class="demo-fab" id="demo-fab" onclick="cStart()"><span class="tri">▶</span>Guided walkthrough<span class="sub">23 steps · ~5 min</span></button>

<script>
(function(){
function sleep(ms){ return new Promise(function(r){ setTimeout(r, AE_SPEED ? ms : 40); }); }
function N(kind, h, p){ return [kind, h, p]; }
var SOLVES = 'What this solves', WHY = 'Design decision', GUARD = 'Guardrail';

var STEPS = [
  /* ── F1 · Home ── */
  { fl:'F1 · Home', sel:'#kyc-card', t:'Verified once, used everywhere',
    run:async function(){ switchPage('f1'); },
    notes:[N('', SOLVES, 'One move means proving who you are to <b>15 separate organizations</b>. Every life-admin app today stops at reminders because it can\'t act for you.'),
           N('', WHY, 'KYC is the trust layer, not just a sign-up gate. A verified identity is what lets the agent file, sign and claim on your behalf. The alternative, a checklist app, was rejected.')] },
  { fl:'F1 · Home · onboarding', sel:'.kyc-window', g:1, t:'Onboarding ends with a permission choice',
    run:async function(){ kycOpen(); kycGo(2); },
    notes:[N('', WHY, 'Four steps: ID scan, liveness, permissions, connect sources. The permissions step comes <b>before</b> any data is read, so trust is set before the agent sees anything.'),
           N('c-guard', GUARD, 'The default is <b>Prepare and ask</b>. Even the most permissive tier can\'t file, pay or sign on its own. That rule isn\'t a setting.')] },
  { fl:'F1 · Home', sel:'#found-grid', t:'The first screen shows what the agent already found',
    run:async function(){ kycClose(); switchPage('f1'); },
    notes:[N('', SOLVES, 'The aha moment comes in the first minute: an expiring passport, a refund nobody claimed, a tax bill building up. These are things the user <b>didn\'t know</b>.'),
           N('', WHY, 'Each card leads into one module: Move, Renew, Claim, Tax. The rest of this walkthrough follows those four cards in order.')] },

  { fl:'F1 · Home · Ask Errand', sel:'#qa-panel', t:'Ask anything, answered only from your own records',
    run:async function(){ switchPage('f1'); qaAsk('When does my passport expire?'); await sleep(1300); },
    notes:[N('', SOLVES, 'Half of life admin is "when is X due, where is Y". Today the answer is buried in an inbox, a drawer or a portal login.'),
           N('', WHY, 'Copied from the RAG prototype: an always-on panel that answers with a <b>card showing its source and confidence</b>. The card opens the page where the action actually happens. You confirm on the page, never inside the chat.')] },
  { fl:'F1 · Home · Ask Errand', sel:'#qa-panel', g:1, t:'One clarifying question, only when the rules really differ',
    run:async function(){ openQA(); qaAsk('Can I deduct my home office?'); await sleep(1100); qaClarify(document.querySelector('#clarify-box .clarify-chip'), 'free'); await sleep(1200); },
    notes:[N('', WHY, '"Home office" has opposite answers for a W-2 job and for freelance work, so the agent asks which one. It then answers with Maya\'s own numbers: 120 sq ft × $5 = $600.'),
           N('c-guard', GUARD, 'It asks <b>at most once per session</b>. Ask again and it answers straight away. "Skip" shows both answers side by side instead of asking again.')] },
  { fl:'F1 · Home · Ask Errand', sel:'#qa-panel', g:1, t:'A range when it isn\'t sure',
    run:async function(){ openQA(); qaAsk('How much will I get back in taxes?'); await sleep(1400); },
    notes:[N('', WHY, 'With 2 of 5 inputs missing, the answer is a <b>range at 54% confidence</b>, on a dashed card that doesn\'t link onward. It names what\'s missing so you know how to narrow it.'),
           N('c-guard', GUARD, 'A precise-looking tax number built on guesses is the most dangerous answer it could give, so <b>it won\'t give one</b>.')] },
  { fl:'F1 · Home · Ask Errand', sel:'#qa-panel', g:1, t:'Nothing when it doesn\'t know',
    run:async function(){ openQA(); qaAsk("What's my car insurance policy number?"); await sleep(1200); },
    notes:[N('', WHY, 'The answer explains <b>why</b> it has nothing (the insurer isn\'t connected and there\'s no policy in the vault) and offers the one action that would fix that.'),
           N('c-guard', GUARD, '<b>Empty means empty.</b> It never makes up a policy number, a date or an amount.')] },

  /* ── F2 · Move ── */
  { fl:'F2 · Move', sel:'#move-summary', t:'One move, 15 accounts, sorted by who can do each',
    run:async function(){ $('qa-panel').classList.remove('open'); switchPage('f2'); },
    notes:[N('', SOLVES, 'A move touches banks, payroll, the postal service, voter registration, insurance and the DMV. People usually remember the first five and find the rest months later.'),
           N('', WHY, 'Accounts are sorted into four groups: <b>agent does it · you sign · you go in person · optional offers</b>. The rejected version was one flat checklist where every item looks equally easy.')] },
  { fl:'F2 · Move', sel:'#mg-agent', g:1, t:'Seven updates, one approval',
    run:async function(){ switchPage('f2'); moveApproveAgent(); await sleep(2700); },
    notes:[N('', WHY, 'The safest, lowest-risk changes are batched behind one tap. The payroll update also switches state withholding to Colorado, which the Tax module picks up later.'),
           N('c-guard', GUARD, 'Offers stay in their own group, labeled <b>sponsored</b>. Partner revenue never shows up inside a required step.')] },
  { fl:'F2 · Move · agent form fill', sel:'#ae-side', t:'It fills what it can infer, then asks only what\'s missing',
    run:async function(){ switchPage('f2'); aeOpen('usps'); await sleep(1300); },
    notes:[N('', SOLVES, 'Government forms ask for things you\'ve already proven elsewhere. Here, 4 of 8 fields come <b>pre-filled from KYC, the vault and the move plan</b>, and each one is tagged with its source.'),
           N('', WHY, 'The left side is an interview and the right side is the form. Questions are written in plain language, and the form fields are filled from the answers.')] },
  { fl:'F2 · Move · agent form fill', sel:'.ae-window', g:1, t:'Each answer is written straight into the form',
    run:async function(){ aeSend(); await sleep(1500); },
    notes:[N('', WHY, 'One plain-English answer fills four fields. A yellow flash shows which fields changed, and the counter moves to 8/8.'),
           N('c-guard', GUARD, 'The agent asked <b>who else lives there</b> because a household move would also forward the roommate\'s mail. It forwards only Maya\'s mail. It also says plainly that the $1.10 USPS card check is one thing its KYC can\'t replace.')] },

  /* ── F3 · Renew ── */
  { fl:'F3 · Renew', sel:'#renew-list', t:'Renewals already know about the move',
    run:async function(){ aeClose(); switchPage('f3'); },
    notes:[N('', SOLVES, 'Expiry reminders live in five different inboxes, each with a different lead time. A passport is "valid" until a country refuses it because it has under 6 months left.'),
           N('', WHY, 'Lead times are set per document. The Texas license isn\'t marked "renew" but <b>"replace"</b>, because the Move module already knows Maya is leaving Texas.')] },
  { fl:'F3 · Renew', sel:'#passport-detail', g:1, t:'The agent won\'t reuse a stale photo',
    run:async function(){ switchPage('f3'); renewPrepare(); },
    notes:[N('', WHY, 'DS-82 comes back 11 of 12 fields ready, with the mailing address taken from the move.'),
           N('c-guard', GUARD, 'The vault has a photo, but it\'s from 2021. Passport photos must be from the last 6 months, so the agent <b>stops instead of filling the field</b>. A rejected application would cost Maya weeks.')] },

  /* ── F4 · Claim ── */
  { fl:'F4 · Claim · agent form fill', sel:'.ae-window', t:'One question decides cash or credit',
    run:async function(){ switchPage('f4'); aeOpen('claim'); await sleep(1500); aeSend(); await sleep(1500); },
    notes:[N('', SOLVES, 'Airlines push vouchers. People often don\'t know a cancelled flight they didn\'t take means a <b>cash refund</b>, so the money is never claimed.'),
           N('', WHY, 'The same form-fill component as the USPS form, applied to a different form. It asks only the one question that changes the result: did you accept the rebooking or the voucher?')] },

  /* ── F5 · Tax ── */
  { fl:'F5 · Tax · plan', sel:'#tax-events', t:'Life events reach the tax file months before filing',
    run:async function(){ aeClose(); switchPage('f5'); taxPhase('plan'); },
    notes:[N('', SOLVES, 'TurboTax arrives once a year, after December 31, which is too late for most of the moves that save money. This agent works all year.'),
           N('', WHY, 'The move, the first freelance payment and the March sale all came from other modules. This is the moat: <b>by tax season the agent already knows about the year</b>.')] },
  { fl:'F5 · Tax · year-end', sel:'#strat-card', g:1, t:'Every strategy has a dollar figure, a deadline and your decision',
    run:async function(){ switchPage('f5'); taxPhase('yearend'); taxAccept('k401','yes'); taxAccept('hsa','yes'); },
    notes:[N('', WHY, 'Each strategy shows why it applies, what it saves and its deadline. Accepting two of them moves the projection from owing $460 to owing $100, live.'),
           N('c-guard', GUARD, '<b>Legal planning only.</b> The agent checks the wash-sale rule before suggesting a loss sale, and accepting only <b>drafts</b> the payroll change or transfer. Nothing moves money until Maya approves that specific action.')] },
  { fl:'F5 · Tax · file', sel:'#tax-start-card', g:1, t:'It checks the free options first',
    run:async function(){ switchPage('f5'); taxPhase('file'); },
    notes:[N('', WHY, 'Documents are collected automatically, and each one shows where it came from. The 1099-B is already flagged for a missing cost basis.'),
           N('c-guard', GUARD, 'Before selling anything, the agent checks <b>IRS Free File and VITA eligibility</b>. If you qualify, it sends you there. This is the lesson from Intuit\'s 2022 settlement over how it advertised "free".')] },
  { fl:'F5 · Tax · agent form fill', sel:'#ae-side', t:'7 of 15 fields filled before the first question',
    run:async function(){ switchPage('f5'); taxPhase('file'); aeOpen('tax'); await sleep(1800); },
    notes:[N('', SOLVES, 'TurboTax asks a hundred questions to find the ten that matter. Here, wages, withholding, interest, the IP PIN and <b>the Colorado move date</b> are already filled before the first question.'),
           N('', WHY, 'Kept from TurboTax: the interview format and a <b>live refund meter</b> at the top. Changed: the agent asks only what no document contains.')] },
  { fl:'F5 · Tax · agent form fill', sel:'#ae-side', t:'Two answers, eight fields, and the meter moves',
    run:async function(){ aeSend(); await sleep(1500); aeSend(); await sleep(1500); },
    notes:[N('', WHY, 'Answer one fills filing status, expenses and the home office (it chose the simplified method because it needs no receipts). Answer two adds the HSA and estimated payments. The meter goes from <b>owe $460 to a $612 refund</b>.'),
           N('', WHY, 'It compared itemizing ($6,480) against the standard deduction and <b>shows its working</b> instead of choosing silently.')] },
  { fl:'F5 · Tax · accuracy checks', sel:'#ae-checks', g:1, t:'The checks stop it filing a gap the IRS would read as income',
    run:async function(){ aeConfirm(); aeRunChecks(); await sleep(3000); },
    notes:[N('', SOLVES, 'Shares bought before 2011 often reach the IRS with no cost basis, so all $3,180 of proceeds looks like profit, and a notice follows months later.'),
           N('c-guard', GUARD, 'One of six checks fails, and the agent <b>won\'t let you sign</b>. It doesn\'t guess the basis. It asks.')] },
  { fl:'F5 · Tax · accuracy checks', sel:'#ae-checks', t:'Fixed with a question, not a form',
    run:async function(){ aeSend(); await sleep(1300); aeRunChecks(); await sleep(3000); },
    notes:[N('', WHY, 'The agent found a 2009 trade confirmation in Maya\'s email and asked to use it. One "yes" fills the field and attaches the evidence, and the gain drops to $1,450. The re-run passes 6/6.'),
           N('', WHY, 'Same pattern as the interview: <b>find the evidence, ask to use it, then write it in</b>.')] },
  { fl:'F5 · Tax · sign', sel:'#ae-success', t:'Signing is the only step that commits you',
    run:async function(){ aeSubmit(); await sleep(1300); },
    notes:[N('', WHY, 'A complexity check decides whether a CPA review is needed. For a W-2, a small Schedule C and one move, it\'s optional. A complex return goes to a credentialed reviewer before Maya signs.'),
           N('', WHY, 'Maya signs with the identity she verified at onboarding, and the return goes through an <b>authorized e-file partner</b>. The After filing tab now tracks the refund.')] },

  /* ── Close ── */
  { fl:'Close', sel:'#jobs-card', t:'One pattern runs through every module',
    run:async function(){ aeClose(); switchPage('f1'); },
    notes:[N('', 'The pattern', '<b>Infer → ask only for what\'s missing → write it in → you confirm → it checks → you sign.</b> USPS forwarding, a flight refund and a tax return all ran on the same engine. Adding a module means adding a form, not building a product.'),
           N('c-guard', 'Where it chooses to stop', 'It doesn\'t make up an answer, forward a roommate\'s mail, reuse a stale photo, guess a cost basis, mix sponsored offers into required steps, or move money without your approval.')] }
];

var cI = -1, busy = false;
window.cStart = function(){ $('demo-fab').classList.add('gone'); $('coach').classList.add('on'); $('c-mask').classList.add('on'); cGo(0, true); };
window.cEnd = function(){ $('coach').classList.remove('on','min'); $('c-mask').classList.remove('on'); $('demo-fab').classList.remove('gone'); cI = -1; };
window.cMin = function(){ var c = $('coach'); c.classList.toggle('min'); $('c-mask').classList.toggle('on', !c.classList.contains('min')); };
window.cGo = async function(i, fresh){
  if (busy) return;
  if (i >= STEPS.length) return cEnd();
  if (i < 0) return;
  busy = true; paintBusy(i);
  try {
    if (fresh || i !== cI + 1) {           // Back or Restart: replay from first load, instantly
      protoReset(); AE_SPEED = 0;
      for (var j = 0; j < i; j++) await STEPS[j].run();
      await sleep(60); AE_SPEED = 1;
    }
    cI = i;
    await STEPS[i].run();
  } finally { AE_SPEED = 1; busy = false; }
  paint(i);
};
Object.defineProperty(window, 'cI', { get:function(){ return cI; } });

function head(i){
  $('c-cnt').textContent = (i + 1) + ' / ' + STEPS.length;
  $('c-prog').style.width = ((i + 1) / STEPS.length * 100) + '%';
  $('c-dots').innerHTML = STEPS.map(function(s, j){ return '<i class="' + (s.g ? 'g ' : '') + (j === i ? 'on' : '') + '"></i>'; }).join('');
  $('c-prev').disabled = i === 0;
  $('c-next').textContent = i === STEPS.length - 1 ? 'Done' : 'Next';
}
function paintBusy(i){
  head(i);
  $('c-next').disabled = true;
  $('c-body').innerHTML = '<div class="c-fl">' + STEPS[i].fl + '</div><div class="c-t"><span class="c-busy"></span>Running the prototype…</div>';
}
function paint(i){
  var s = STEPS[i]; head(i); $('c-next').disabled = false;
  $('c-body').innerHTML = '<div class="c-fl">' + s.fl + (s.g ? '<span class="c-g">GUARDRAIL</span>' : '') + '</div><div class="c-t">' + s.t + '</div>' +
    s.notes.map(function(n){ return '<div class="c-note ' + n[0] + '"><h5>' + n[1] + '</h5><p>' + n[2] + '</p></div>'; }).join('');
  $('c-body').scrollTop = 0;
  spot(s.sel);
}
function spot(sel){
  var el = document.querySelector(sel), sp = $('c-spot');
  curEl = null;
  if (!el){ sp.style.cssText = 'top:50%;left:50%;width:0;height:0'; return; }
  var tall = el.getBoundingClientRect().height > innerHeight * 0.55 && el.closest('.page');
  el.scrollIntoView({ behavior:'smooth', block: tall ? 'start' : 'center' });
  if (tall) setTimeout(function(){ window.scrollBy({ top:-72, behavior:'smooth' }); }, 300);
  setTimeout(function(){ place(el); }, tall ? 700 : 420);
}
var curEl = null;
function geom(el){
  var r = el.getBoundingClientRect(), sp = $('c-spot'), pad = 6;
  var top = Math.max(r.top - pad, 4), bot = Math.min(r.bottom + pad, innerHeight - 4);
  sp.style.top = top + 'px'; sp.style.left = (r.left - pad) + 'px';
  sp.style.width = (r.width + pad * 2) + 'px'; sp.style.height = Math.max(bot - top, 20) + 'px';
  return r;
}
function place(el){
  curEl = el;
  var r = geom(el), pr = $('coach').getBoundingClientRect();
  if (r.height < innerHeight * 0.55 && r.left < pr.right + 12 && r.bottom > pr.top - 12 && el.closest('.page'))
    window.scrollBy({ top: Math.min(180, r.bottom - pr.top + 24), behavior:'smooth' });
}
addEventListener('scroll', function(){ if (curEl && cI >= 0) requestAnimationFrame(function(){ geom(curEl); }); }, true);
addEventListener('resize', function(){ if (cI >= 0) spot(STEPS[cI].sel); });
document.addEventListener('keydown', function(e){
  if (!$('coach').classList.contains('on') || busy) return;
  if (e.key === 'ArrowRight') { e.preventDefault(); cGo(cI + 1); }
  else if (e.key === 'ArrowLeft') { e.preventDefault(); cGo(cI - 1); }
}, true);
})();
</script>
<!-- ════════ END GUIDED WALKTHROUGH LAYER ════════ -->
'''

assert proto.count("</body>") == 1
out = proto.replace("</body>", TOUR + "\n</body>")
(root / "index.html").write_text(out)
print("wrote", root / "index.html", len(out), "bytes")
