#!/usr/bin/env python3
"""Write chapters/index.html from the story below.

Every [[key]] in the prose is a receipt: a line I posted at the time, pulled
word for word out of buckets.json so it can never be misquoted. If the words
are not in the post, the build stops.

    cd _data && python3 chapters.py
"""
import html, json, os, re, sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PAGE = os.path.join(ROOT, "chapters", "index.html")
UPDATED = date(2026, 11, 10)

# key: (part of the post's URL, first words, last words)
RECEIPTS = {
    "dieppe":      ("i-was-the-only-brown-kid", "His family was Turkish.", "non-white families in town."),
    "grec":        ("1379200947520425985", "And I can’t wait to share", "to all of you soon."),
    "mum":         ("my-mum-spent-months-obsessing", "Testing recipes.", "until she got it perfect."),
    "gcse":        ("714799181404180480", "Remember after GCSEs", "that was mad"),
    "left":        ("after-5-amazing-years", "I joined the firm as a naive 18 year old", "How wrong I’ve been."),
    "announce":    ("1074079484264005633", "Alright guys I wanted to share", "It’s an app called @MiniDeed."),
    "countries":   ("1346069881641381888", "Without you we couldn’t have reached over 25 countries", "through just likes"),
    "jfk":         ("1350806436402622464", "After deliberating for months", "open up about my experiences."),
    "burgerguy":   ("1930348210918236639", "idk what I did to get him so angry", "so I guess that’s a win"),
    "ministruggle": ("1259666460735164419", "I love the safe space", "open up in this way"),
    "followers":   ("1764687245401809114", "We didn’t unlock any new growth", "serotonin hit they wanted"),
    "tru":         ("1254829285698920449", "#TRU : The Tiramisu Response Unit always delivers", "always delivers"),
    "ppe":         ("1257050219113598976", "HOW HAS MY DAD LANDED IN FULL PPE", "FULL PPE"),
    "days140":     ("1378814394692468739", "I’m going to build a food concept", "in 140 days."),
    "entertainment": ("1378820575800520704", "to take to the moon", "Either way it’s free entertainment"),
    "ramadan21":   ("1380942085885427715", "GREC will have to wait (but not for long)", "(but not for long)"),
    "grecuber":    ("1399724226618216456", "Alhamdulillah, @grec_uk all approved on UberEats", "on UberEats"),
    "doorsign":    ("1610652654807441408", "15 Jul 2021 - a month after", "We got our first door sign!"),
    "towerhamlets": ("we-sold-burgers-from-the-back-of-a-flower", "Only in Tower Hamlets", "the back of a flower shop."),
    "boris":       ("1659943645238161408", "Bro just opened the door", "and closed the door"),
    "barakahprofit": ("why-were-closing-our-restaurant", "It might not be what maximizes profit.", "But it maximizes barakah (blessing)."),
    "aurora":      ("my-dad-disappeared", "After 20 years in this industry,", "making customers happy."),
    "ifg":         ("2094386352829661262", "80k in 24 hours with IFG", "their greatest video yet"),
    "shahs":       ("1964790106205888664", "Think Shah’s Halal but Peruvian.", "but Peruvian."),
    "hoodiestory": ("fear-of-gods-essentials-hoodie", "The product isn't why it sold out though.", "The storytelling is."),
    "selfridges":  ("1738233982523723953", "He’s like oh I’ve heard of that brand somewhere", "looks sick"),
    "resume":      ("ive-been-lying-to-you", "My resume said: Restaurant Owner.", "Strategy Call with a16z Portfolio Company."),
    "tell":        ("last-october-i-fell-asleep", "I was a bit proud of the hours at the time.", "That was the tell."),
    "ramp":        ("2111099788124885045", "Excited to share that Ramp is now a Draper customer.", "Draper customer."),
    "bilalq":      ("1841527617150652915", "athan is the call to prayer", "actually call you to prayer?"),
    "bilalback":   ("2086140712693764552", "Just picking back up an old project", "Bilal is back!"),
    "asr":         ("2090508750599725538", "So I caught it,", "before bilal"),
    "uk82":        ("2110478059166216703", "we will get to 100% inshaAllah", "inshaAllah"),
    "logo":        ("2102859045237383596", "there is still a place for you", "answer the call"),
}

# (id, title, years, link, [paragraphs])
CHAPTERS = [
("dieppe", "Dieppe", "", None, [
 "Dieppe is a small seaside town in northern France with barely a halal takeaway in it, and for the first eight years of my life it had (as far as I could tell) exactly two families who weren’t white, ours and my best friend’s.[[dieppe]] Dad opened the only Indian restaurant in town, and on Saturdays he sold Dragon Ball Z toys off a market stall. I used to ride up front in his van on the supply runs while he worked out what would sell, which was my first lesson in going direct, even if I was six and only there for the toys.",
 "The best part of my childhood was the drive to Paris to see my uncle, because Paris meant a <em>grec</em>. A grec is a French doner from the halal street food scene in Paris, made with veal and turkey, and I’ve been chasing that sandwich professionally ever since.[[grec]]",
 "We moved to east London when I was eight, and I cried when I heard. Dad and my brother ran an Italian restaurant called Anima D’Italia. My brother had noticed that every tiramisu in London had alcohol in it, so he set Mum to work in our kitchen at home, and she spent months on YouTube videos before she had the first halal tiramisu in London.[[mum]] By sixteen I was waiting tables there.",
 "I got 6A* and 5As at GCSE, then BBDD at A-level. Nobody has mentioned the GCSEs since.[[gcse]] Goldman Sachs took me anyway.",
]),
("goldman", "The wrong team", "2016–2021", None, [
 "In my first week at Goldman Sachs I asked where I could pray. They found a Muslim on the floor to walk me down, and he took me to the basement, pointed at the prayer room door, said “don’t stay too long in this place,” and left. I was eighteen, I’d got in off Bs and Ds, and I wanted everything that building had to teach me. I had no idea what he was on about.",
 "Goldman had just launched a technology apprenticeship (first cohort ever, three days at work and two at uni) and I was meant to go into software engineering. They put me on the voice engineering team instead, where the second youngest person was at least double my age and nobody had a plan for me.",
 "So I started turning up to meetings nobody had invited me to. Voice engineering meant the hoots and the turrets; the hoots are the broadcast intercoms on a trading floor, and the turrets are the massive phone setups bolted to every trader’s desk. I sat in the corner while Amazon and Cisco pitched Goldman on replacing them, multimillion pound decisions, and I watched pitches fall apart and projects get greenlit and then quietly die six months later. Nobody was checking on me, and it would have been the easiest thing in the world to sit at my desk and coast. What I worked out from the corner was that the interesting stuff is everything around the engineering. I moved into a proper engineering role eventually and stayed five years.[[left]]",
 "It took me most of those years to work out what the man at the door meant. A couple of years in I noticed that I was the only one of my uni friends earning properly and I was saving less than all of them, and that I had the job everyone wanted and somehow less time than anyone. Goldman gave me more than I could have asked for at that age, and nothing was wrong on paper. There’s a word for what was missing, and it’s <em>barakah</em>. Blessing, roughly; the thing that makes a small amount go a long way, and whose absence makes a large amount quietly disappear. I never took it as a reason to leave. I took it as a reason to get so good at the job that nobody could question the half hour I took to pray.",
]),
("minideed", "MiniDeed", "2018–2021", ("../ventures/minideed/", "the posts from the time", False), [
 "That prayer room is also where I met Mehti. He was probably in his mid-thirties, he’d been at Goldman for years, and he prayed next to me every day. One afternoon on the way out I asked how he was doing, just being polite. He heard it as a question about his startup and told me everything. He’d coded it himself and it barely worked. Every like turned into a penny for charity (you set what yours was worth), so anyone could fundraise just by posting, and I couldn’t stop thinking about it. So I asked if I could work on it.[[announce]]",
 "It was two co-founders, one engineer and me. I did users and support, worked out what we should build next, and posted about all of it on Twitter because that felt like the obvious thing to do. We got into Fast Forward, an accelerator in Stratford, and I started skipping uni days to go there instead. We onboarded Islamic Relief and Human Relief Foundation, The New Arab wrote about us, and watching the live donation ticker go up was more addictive than any revenue dashboard.",
 "Donations went from £37 a month to £2.7k a month. Then one tweet went viral and Ramadan did the rest, which came to 47,000 posts, 800,000 taps, twenty-five countries and £26k raised through likes.[[countries]] All of it went to charity and none of it to us, and we never worked out how to make money from it.",
 "What I didn’t see coming was what people did with the place once they were in it. They started opening up about their mental health, and told us it was the only app where they felt safe doing that.[[ministruggle]] Someone would post something within the rules and outside the spirit of it, and other users would step in before we’d even seen it. Nobody asked them to. They cared that much, and that was also our ceiling, because we were trying to reach new kinds of people and we’d quietly built a room that only fit one kind. (We then took follower counts away because people said they were toxic, and a lot of users left over it.)[[followers]] Donations still come through the app daily, years later.",
]),
("jfk", "Twenty-five hours", "2019", ("https://x.com/mertesakib/status/1350806436402622464", "the three parts, as I posted them", True), [
 "On 17 January 2019 I flew to New York with my friend Arefin. I was interrogated and held at JFK for <span class=\"highlight\">twenty-five hours</span> and then refused entry, with no reason given. I kept it to myself for two years, and then wrote it up in three parts.[[jfk]]",
 "It wasn’t the last time. In June 2025 Ibrahim Javed and I tried to cross into the West Bank, and routine questions turned into eight hours in separate rooms. They’d found the Simply Smashed campaigns, the Palestine flags and the Gaza fundraising, everything we’d thought of as charity work from a burger joint, and eventually my interrogator snapped and told me to get out of his country.[[burgerguy]] Ibrahim and I walked out and burst into laughter. Both rooms are a big part of why I build.",
]),
("tiramisu", "The Tiramisu Response Unit", "2020", None, [
 "In March 2020 my parents got on a flight to Bangladesh and lockdown was announced while they were in the air. Dad was high risk and stuck there. Me and my brother suddenly had a restaurant with no customers, staff who needed paying, and rent that didn’t care about pandemics, so within the week we’d taken it over and were delivering Mum’s tiramisu across London in full trays of 24 slices. I called it the Tiramisu Response Unit. Through the worst months it brought in 40% of our revenue, and it’s still the best brand name I’ve come up with.[[tru]]",
 "On the side we ran a campaign called Help Our Heroes and delivered thousands of pizza slices to hospitals. The first run was for the staff at the Royal London. It was the busiest I had ever been. When Dad finally landed, he did it in full PPE.[[ppe]]",
 "When we started thinking about selling, a buyer came in, told my dad we were “bleeding out,” and made an offer so insulting that Dad slammed the table and walked out. We kept the kitchen. A year later Simply Smashed started in the corner of it.",
]),
("grec", "140 days", "2021", None, [
 "On 4 April 2021 I told Twitter I was going to build a food concept and get it up and running in 140 days.[[days140]] I was about to graduate, I was leaving for Egypt to study, and I’d be living on savings that wouldn’t last. What I did have was Dad’s kitchen, which had been shut through the lockdown; an empty kitchen in the heart of London that many food businesses would kill for, as I put it at the time, just sitting there. I promised to tweet all of it.[[entertainment]]",
 "Six days in, I posted an update to say I would not be working on it during Ramadan. The Ramadan before, I hadn’t been able to stop thinking about MiniDeed, and I didn’t want a second one like it. So the 140 days lost a month in their second week.[[ramadan21]]",
 "The plan was to launch three things and see which one lived. The first was a vegan burger brand. Vegan was everywhere in east London that year and it got real traction, just with a completely different audience to mine. The second was Grec, proper French grec sandwiches, and that was the one I had conviction on. I tested the name with Twitter polls and voice notes and built it in public. It had a logo, a menu, its own greaseproof paper and an approved listing on Uber Eats,[[grecuber]] and it died on the supply chain. We couldn’t get the meat into the country and it never fed a single person.",
 "The third was my brother’s idea, and Dad didn’t want to do it. He’d spent decades building a proper Italian restaurant and burgers felt like a step down. He came round when we showed him the numbers. By day 140 it wasn’t close.",
]),
("smashed", "Simply Smashed", "2021–2026", ("../ventures/simply-smashed/", "the posts from the time", False), [
 "My brother spent £100 on a grill and started making burgers in the corner of Dad’s restaurant.[[doorsign]] We pushed the tables away and shared the space with a flower shop to split the rent, so customers walked through rows of roses to pick up their burgers.[[towerhamlets]] A few weeks in, people asked if we’d show the Euros final, so I borrowed a projector and a screen from a friend. We took orders on notepads, crumpled them up and threw them to the back of house, and when we upgraded to printed receipts we printed doubles, because we kept losing them behind the fridges.",
 "Then I went to Egypt to study for nine months while my brother and Dad kept it running. When I came back my brother gave me one rule, which was that my job was to grow it. We had no money to do that properly, so I told people what we were building and let them watch us figure it out. (My sister-in-law came up with half the recipes we still serve.)",
 "There were long stretches where I couldn’t tell if any of it was working. One of the front of house guys found out about Goldman mid-shift and just went “you left Goldman Sachs for this?” He wasn’t taking the piss either. He actually felt sorry for me.",
 "The night I still think about, we’d missed a chicken burger off an Uber Eats order in the middle of a rush. I rang the customer for his address, ran outside, hired a Boris bike, put the bag in the basket and pedalled through Whitechapel. He opened the door, took the bag and shut it again.[[boris]] I stood there for a second, cycled back and got on with service.",
 "We also made a lot of decisions that looked stupid on paper. We closed for the first week of every Ramadan, which cost us up to 30% of the month’s revenue.[[barakahprofit]] We built a prayer space where more tables could have gone. We found a perfect empty pub at a reasonable rent, learned that the landlord made every tenant sell beer, and left. When we got review bombed for supporting Palestine, we put a burger on the menu with all of its profit going to Gaza, and the community answered with thousands of real five-star reviews.",
 "By 2025 it was <span class=\"highlight\">London’s highest rated burger joint on Google</span>, 4.9 stars across 3,000 reviews, and we never spent a pound on paid marketing. Order times went from 50 minutes to 8. The sign outside quotes a customer called Aurora (“The best burger I’ve ever had in London. Probably in my life, even.”), and one day she turned up with her parents, who were visiting from Indonesia, with no idea we’d used her words. Dad came rushing in to tell me Aurora was here, then disappeared into the kitchen and came back out with two tiramisu for the family.[[aurora]]",
 "The last thing to come out of that kitchen started as a lunch from my Goldman days, a Peruvian place near the office with senior bankers in Savile Row suits queuing outside it for chicken. I couldn’t get the green sauce out of my head, so I spent two months and sixteen attempts recreating it. It went on the menu, sold out in three hours and became its own kitchen, Peruvian Street Kitchen.[[shahs]]",
 "I stepped back in January 2026. My brother runs both kitchens day to day now, and I still help with the growth. In August IFG made a documentary about us that was as much about Dad as the burgers, and it’s the best telling of our story so far.[[ifg]]",
]),
("hoodie", "The hoodie", "2023", None, [
 "When I was seventeen I did a summer internship at Jack and Jones in Bangladesh and designed a few t-shirts that actually got printed. Eight years later I went back to make a hoodie with my uncle, a senior graphic designer in the clothing industry, and called it SIMPLYCLO. It came out heavier than a Fear of God Essentials hoodie (364 GSM against 347), from the same kind of factories, at £60 instead of £180. None of that matters if nobody knows you exist.",
 "So I documented all of it. I posted the factory visits and the fabric sourcing, ran the brand name as a Twitter poll and made TikToks from Bangladesh, and every decision got made in public. The Liberation Hoodie went on sale on 21 December 2023 with all profits going to Gaza. It sold out in three hours and raised £15k for Palestine, and the next day a man in Selfridges asked me where my hoodie was from.[[selfridges]] It sold out because people had watched it get made.[[hoodiestory]]",
 "Then I closed it. Bootstrapping clothing meant a production delay at every step, and I’d rather end something cleanly than let it rot.",
]),
("thoughtleadr", "Thoughtleadr", "2024–2025", None, [
 "I was running the highest rated burger joint in London when I took a junior, part-time job at someone else’s agency. Simply Smashed had grown on storytelling and I had no idea why it worked; I was doing it on instinct. Then my brother introduced me to someone doing it for a living, for founders backed by YC and a16z. That was Mustafa. So I asked for a job (part time, obviously, I still had a kitchen to run).",
 "Nobody at the restaurant knew. From a corner of the shop, next to the punching machine, with noise-cancelling headphones on, I was taking calls with founders who had just raised, then going back out to the pass.[[resume]] What I learned there isn’t on Google and it isn’t in ChatGPT, things like how a founder actually decides what to say, and which stories are ready and which need another month living in someone’s head. Before long they had me training the other writers, which still makes me laugh given how I got in the door. I was Head of Training by the time Mustafa and I left to build our own.",
]),
("draper", "Draper", "2025–", ("../ventures/draper/", "the posts from the time", False), [
 "Draper is me and Mustafa, and we run LinkedIn for founders and their teams. I’d been writing the thesis in public for two years before we had a name for it. Content is product and product is content. Builders should be building, and AI should be documenting you cooking.",
 "The problem underneath it is older than AI. The best thinkers I know don’t post. Their best ideas come out loud, in the ten minutes after a meeting, to one person, and then stay in the room. Every writing tool I’ve used sits at the wrong end of that, an empty box that makes something up from nothing. The one worth building is a witness, something that sits in the room when you say the thing and writes down what you meant, in your voice. I wrote that up properly as <a class=\"u\" href=\"../manifesto/\">The Corridor</a>.",
 "The first year nearly broke me. In October 2025 I fell asleep at the wheel in traffic and drove into the back of the car in front. Nobody was hurt. I was setting up Peruvian Street Kitchen, running the Simply Smashed kitchen and taking Draper calls at six in the morning before service.[[tell]] So we hired, and stacked every client call into Mondays and Wednesdays so the other three days are for building. Draper doesn’t run on how much sleep I got anymore.",
 "So far that’s 400M+ views for 100+ founders, from YC and a16z-backed companies to VC funds, and north of £20M in pipeline from the content.[[ramp]] People called these ideas crazy when I started posting them, and now the industry has names for them. The competition is well funded. One is a founder paying $1m salaries to learn the space, and another is a man whose last exit was $780m.",
 ("sign", "We’ll win, inshaAllah."),
]),
("bilal", "Bilal", "2024–", ("../ventures/bilal/", "the posts from the time", False), [
 "On 2 October 2024 I posted a question. In Muslim countries you hear the athan (the call to prayer) from the minaret and you get up and go to the mosque. On your phone it’s one more notification you swipe away. If you heard it out loud, at the time your own mosque actually prays, would it get you through the door?[[bilalq]] Two weeks later we were testing it, and then I shelved it.",
 "I picked it back up in August 2026 as a display for the TV in my front room, one that plays the call at the time your local mosque prays.[[bilalback]] Within a couple of weeks it was getting me to prayers I’d have missed. I missed the afternoon prayer at my local mosque one day, hit refresh, and it found me another one two minutes away that started later.[[asr]]",
 "It launched on 11 September 2026, a call to prayer that tells you when to leave for your mosque, not when the prayer starts. Before I’d announced anything it was already going round WhatsApp groups, and 1,400 people were on it in a couple of days. The iPhone app followed on 9 October. It’s on the Mac and the TV in your kitchen too, and it knows over 24,000 mosques around the world (82% of the UK’s, as of October).[[uk82]] There’s no sign up, and it’s free and stays free. Android is next, inshaAllah.",
 "The logo is a mosque arch, left open for you. Before you knew the way, someone took you to the mosque, and somewhere along the way most of us got lost again.[[logo]]",
]),
]

# Every chapter's rule ends at a door: (how it was left, what it was, its shape)
DOORS = {
    "dieppe":       ("open", "dad’s restaurant", "rect"),
    "goldman":      ("ajar", "the prayer room, basement", "rect"),
    "minideed":     ("ajar", "talked my way in", "rect"),
    "jfk":          ("shut", "refused entry, no reason given", "rect"),
    "tiramisu":     ("shut", "shut, March 2020", "rect"),
    "grec":         ("shut", "never opened", "rect"),
    "smashed":      ("open", "through the flower shop", "rect"),
    "hoodie":       ("open", "Selfridges, the day after", "rect"),
    "thoughtleadr": ("ajar", "how I got in the door", "rect"),
    "draper":       ("open", "the corridor", "arch"),
    "bilal":        ("open", "come in", "masjid"),
}

# drawn by hand on a 20 by 27 grid, a little off square on purpose
DOOR_SHAPES = {
    "rect": {
        "frame": "M2.1 26.4 L2.5 1.9 L17.7 1.5 L18 26.5",
        "glow":  "M3.5 26.2 L3.8 3.1 L16.5 2.8 L16.7 26.2 Z",
        "panel": "M3.3 26.2 L3.6 3 L16.7 2.7 L16.9 26.3 Z",
    },
    "arch": {
        "frame": "M2.1 26.4 L2.3 10.2 C2.4 4.8 5.6 1.7 10 1.5 C14.5 1.7 17.6 4.8 17.8 10.2 L18 26.5",
        "glow":  "M3.5 26.2 L3.7 10.4 C3.8 5.9 6.3 3.1 10 2.9 C13.8 3.1 16.4 5.9 16.5 10.4 L16.7 26.2 Z",
        "panel": "M3.3 26.2 L3.5 10.3 C3.6 5.7 6.2 2.9 10 2.8 C13.9 2.9 16.6 5.7 16.7 10.3 L16.9 26.3 Z",
    },
    "masjid": {
        "frame": "M2.1 26.4 L2.2 12 C2 8 5.4 5 10 1.1 C14.6 5 18 8 17.9 12 L18 26.5",
        "glow":  "M3.5 26.2 L3.6 12.2 C3.5 8.8 6.4 6.2 10 3 C13.6 6.2 16.6 8.8 16.5 12.2 L16.7 26.2 Z",
        "panel": None,
    },
}


def door(state, says, shape="rect", href=None, cls=""):
    """One small door. A span when it only decorates a heading, a link when
    it leads somewhere."""
    sh = DOOR_SHAPES[shape]
    leaf = ""
    if sh["panel"]:
        leaf = ('<svg class="leaf" viewBox="0 0 20 27" aria-hidden="true"><path class="panel" d="%s"/>'
                '<circle class="knob" cx="14.3" cy="14.9" r="0.9"/></svg>' % sh["panel"])
    classes = " ".join(c for c in ("door", state, shape, cls) if c)
    if href:
        open_tag = '<a class="%s" href="%s" aria-label="%s">' % (classes, href, html.escape(says))
        close_tag = "</a>"
    else:
        open_tag = '<span class="%s" aria-hidden="true">' % classes
        close_tag = "</span>"
    said = '<span class="says" aria-hidden="true">%s</span>' % html.escape(says, quote=False) if says else ""
    return ('%s<span class="room"><svg class="frame" viewBox="0 0 20 27" aria-hidden="true">'
            '<path class="glow" d="%s"/><path class="line" pathLength="1" d="%s"/></svg>%s</span>%s%s'
            % (open_tag, sh["glow"], sh["frame"], leaf, said, close_tag))


MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def corpus():
    b = json.load(open(os.path.join(HERE, "buckets.json")))
    by_url = {}
    for rows in b.values():
        for p in rows:
            by_url.setdefault(p.get("url") or p["id"], p)
    return list(by_url.values())


def flat(t):
    return re.sub(r"\s+", " ", t).strip()


def receipt(posts, key):
    frag, first, last = RECEIPTS[key]
    hits = [p for p in posts if frag in (p.get("url") or "")]
    if len(hits) != 1:
        sys.exit("receipt %r: %d posts match %r" % (key, len(hits), frag))
    p = hits[0]
    # keep his line breaks: the shape of a post is part of what he wrote.
    # one character per break, so positions match the flattened text exactly
    lines = re.sub(r"[ \t]*\n[ \t\n]*", "\n", re.sub(r"[ \t]+", " ", p["text"])).strip()
    text = lines.replace("\n", " ")
    a = text.find(first)
    b = text.find(last, a if a >= 0 else 0)
    if a < 0 or b < 0:
        sys.exit("receipt %r: the words are not in the post\n  %s" % (key, text[:300]))
    quote = re.sub(r"\s*https://t\.co/\S+", "", lines[a:b + len(last)])
    y, m, d = p["date"].split("-")
    where = "LinkedIn" if p.get("src") == "li" else "X"
    return {"quote": quote, "url": p["url"],
            "when": "%s, %d %s %s" % (where, int(d), MONTHS[int(m) - 1], y)}


def build():
    posts = corpus()
    n = 0
    out, toc = [], []
    for ci, (cid, title, years, link, paras) in enumerate(CHAPTERS, 1):
        toc.append('    <a href="#%s">%s</a>' % (cid, title))
        quiet = ' <span class="quiet">%s</span>' % years if years else ""
        out.append('\n  <h2 id="%s"><span class="chno">%d.</span> %s%s%s</h2>'
                   % (cid, ci, title, quiet, door(*DOORS[cid])))
        if link:
            href, label, ext = link
            out.append('  <p class="chapter-link"><a class="u"%s href="%s">%s</a></p>'
                       % (" data-out" if ext else "", href, label))
        for para in paras:
            if isinstance(para, tuple):
                out.append('  <p class="%s">%s</p>' % para)
                continue
            notes = []

            def mark(m):
                nonlocal n
                n += 1
                r = receipt(posts, m.group(1))
                notes.append(
                    '      <div class="receipt" id="r%d"><span class="n">%d</span>'
                    '<span class="body"><q>%s</q> <a class="src" data-out href="%s">%s</a></span></div>'
                    % (n, n, html.escape(r["quote"], quote=False).replace("\n", "<br>"), r["url"], r["when"]))
                return ('<sup class="ref"><a href="#r%d" aria-label="Receipt %d">%d</a></sup>'
                        % (n, n, n))

            body = re.sub(r"\[\[(\w+)\]\]", mark, para)
            # the bike rides past when this paragraph is reached
            hook = ' id="boris"' if "hired a Boris bike" in para else ""
            if notes:
                out.append('  <div class="anchored"%s>\n    <p>%s</p>\n    <aside class="receipts">\n%s\n    </aside>\n  </div>'
                           % (hook, body, "\n".join(notes)))
            else:
                out.append("  <p>%s</p>" % body)

    src = open(PAGE).read()
    head = src[:src.index('  <a class="crumb')]
    foot = src[src.index('  <footer class="foot">'):]
    iso = UPDATED.isoformat()
    human = "%d %s %d" % (UPDATED.day, ["January", "February", "March", "April", "May", "June", "July",
                                         "August", "September", "October", "November", "December"][UPDATED.month - 1],
                          UPDATED.year)
    top = '''  <a class="crumb rise" style="--i:0" href="../"><span class="back">←</span> Sakib Ahmed</a>

  <header class="article-head rise" style="--i:1">
    <h1>Chapters</h1>
    <p class="when"><time datetime="%s">%s</time></p>
    <p class="stand">The long version, in eleven parts. The red numbers are receipts, which is to say what I was posting at the time. It isn’t always how I tell it now.</p>
  </header>

  <nav class="toc" aria-label="Index">
%s
  </nav>
''' % (iso, human, "\n".join(toc))
    # the story ends at the arch from its last paragraph, big enough to walk through
    out.append('\n  <p class="last-door">%s</p>'
               % door("open", "Bilal", "masjid", href="https://bilalathan.co.uk"))
    out.append('''
  <nav class="prevnext path" aria-label="Where next">
    <a class="prev" rel="prev" href="../"><span class="dir">Before this</span><span class="t">The memo</span></a>
    <a class="next" rel="next" href="../manifesto/"><span class="dir">Next</span><span class="t">The Corridor</span></a>
  </nav>''')
    open(PAGE, "w").write(head + top + "\n".join(out) + "\n\n" + foot)
    print("chapters: %d chapters, %d receipts, all word for word" % (len(CHAPTERS), n))


if __name__ == "__main__":
    build()
