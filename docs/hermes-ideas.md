# Hermes Agent: ideas

What Hermes Agent could take over, from patterns that have become common for personal agents to a few less obvious
ones. Nothing here is set up; it is a menu to pick from. Setup and the security model: [hermes-agent.md](hermes-agent.md).

## How these ideas fit the setup

Hermes can **chat on Telegram, browse and search the web, run shell commands and scripts in its container, remember
things, and run scheduled tasks** (its cron scheduler sends the result to the home channel, your private chat).

Three rules keep the ideas safe and cheap:

| Rule | Why |
|---|---|
| **Watch, summarise, ask: you act** | The agent finds the flight, the flat or the bug; you book, pay, apply or merge. It never gets payment details or a password, so a prompt injection on some web page cannot spend your money |
| **Read-only access, own keys** | If an idea needs an account (GitHub, calendar), give it a token that can only read, used for nothing else, revocable |
| **Small, scheduled, bounded** | A daily job with Claude Haiku 5.5 costs fractions of a cent to a few cents, depending on how many pages it reads. Long browsing sessions cost more; the prepaid credit caps everything |

The [egress guard](hermes-agent.md#layers) keeps Hermes away from this server: it cannot reach the apps hosted here,
not even through their public URLs. Ideas that test these apps need another copy elsewhere (e.g. GitHub Pages) or an
outside monitoring service.

## Established

Patterns that many people run with personal agents.

| Idea | What Hermes does | Needs | Watch out |
|---|---|---|---|
| **Morning briefing** | At 7:00: weather, calendar of the day, top news of chosen topics, one reminder | Weather and news are public; the calendar needs a read-only link (iCal) | Keep the topic list short, or the briefing gets long and costs more |
| **Read later** | You forward a link or PDF; it answers with a five-line summary and keeps it in its memory | Nothing | Pages with instructions in hidden text are the classic prompt injection; it only summarises |
| **Reminders in plain language** | "Remind me on Friday at 16:00 to submit the expenses" becomes a scheduled message | Nothing | – |
| **Price watch** | Checks a product page once a day and writes when the price falls below a threshold | Nothing | Some shops block automated visits; respect their terms |
| **Research digest** | Every Monday: new papers on chosen topics (arXiv, Semantic Scholar), one line each, links | Public APIs | – |
| **Weekly review** | Sunday evening: what you asked it this week, open points, three questions for the next week | Its memory | – |
| **Notes and lists** | Shopping list, packing list, book list, kept in its memory and sent on request | Nothing | Its memory is in the volume: back it up |
| **Translate and rephrase** | E-mails or messages in a clearer tone, German ↔ English ↔ French | Nothing | – |

## Travel

| Idea | What Hermes does | Needs | Watch out |
|---|---|---|---|
| **Cheap flights** | Watches fixed routes and flexible dates (e.g. Zurich → Lisbon, any weekend in March), writes when a price falls below your limit or is clearly below the usual, with the link. You book | Public flight search sites or a flight price API | **No booking by the agent:** no card, no account password. Prices change by the hour; check again before paying. Some sites forbid scraping, an API is cleaner |
| **Weekend trips by train** | Every Thursday: SBB Supersaver tickets and connections for a weekend trip under a budget | [transport.opendata.ch](https://transport.opendata.ch) (public, no key) for connections | Supersaver prices themselves are on sbb.ch, not in the open API |
| **Delays on your route** | On work days before you leave: disruptions and delays on your usual connection | transport.opendata.ch | – |
| **Trip preparation** | Before a trip: entry rules, plugs, local SIM, weather, packing list from earlier trips | Its memory | Entry rules: always confirm on the official site |
| **Hotel price drops** | After you book with free cancellation, checks the price daily and writes if it drops | The booking page | You rebook yourself |

## Studies, work and the portfolio

| Idea | What Hermes does | Needs | Watch out |
|---|---|---|---|
| **GitHub digest** | Daily: new issues, pull requests and Dependabot updates across your repositories, with a one-line assessment each | Fine-grained token, read-only on your repositories | No write access, so it cannot merge or push |
| **Job alerts** | Watches jobs.ch / LinkedIn searches for your profile (data, ML, software, Zurich) and explains why a job fits | The search pages | Apply yourself; many job sites forbid scraping |
| **Conference and CFP deadlines** | Keeps a list of venues (e.g. CHI, ACL, NeurIPS workshops) and reminds you four and one week before deadlines | Public pages | – |
| **Thesis follow-up** | Monthly: new work on SDG classification, gamified labeling and human-in-the-loop annotation, compared with your thesis | arXiv, Semantic Scholar | Nice material for a blog post or the next application |
| **Portfolio uptime from outside** | Not possible from this server (egress guard). Use an external free monitoring service, or let Hermes check the GitHub Pages copies | – | – |
| **Release notes** | For a repository, turns the commits since the last tag into readable release notes and sends them to you | Read-only token | You publish them |

## Everyday life in Switzerland

| Idea | What Hermes does | Needs | Watch out |
|---|---|---|---|
| **Flat search** | Watches Flatfox, Homegate or Comparis searches and writes within minutes of a new match, with a short assessment | The search pages | Respond yourself; respect the sites' terms |
| **Second hand** | Watches Ricardo or Tutti for something specific (a bike frame size, a lens) under a price | The search pages | – |
| **Weather triggers** | "Write me if it rains tomorrow at 7:30 in Zurich" or "if the snow line drops below 1500 m this weekend" | Public weather APIs (MeteoSwiss, Open-Meteo) | – |
| **Lunch menus** | At 11:00: the menus of the mensas and two restaurants near the university | Public menu pages | – |
| **Discounts** | Weekly: Migros and Coop offers matching your shopping list | Public offer pages | – |
| **Deadlines** | Tax return, insurance, half-fare travelcard, passport expiry: reminders with lead time | Its memory | – |

## Creative

| Idea | What Hermes does | Needs | Watch out |
|---|---|---|---|
| **Playtest Tower Defense** | Plays the GitHub Pages copy of Tower Defense Remastered with its browser, tries strategies and reports balancing issues ("wave 7 is unbeatable without the frost tower") | The public GitHub Pages URL (the copy on this server is blocked) | Browsing is slow and uses more tokens: run it now and then, not daily |
| **Dummy dataset author** | Writes new, realistic abstracts for the SDG Tag Heroes dummy dataset on a theme ("600 papers on Swiss water research") | Nothing; the dataset generator runs on your machine | Fictional content only, no real author names |
| **SDG paper of the week** | Every week a real open-access paper on one SDG, summarised in three sentences, with the SDG it fits best and why: a small game of its own | arXiv, Semantic Scholar | – |
| **Ticket drops** | Watches when concerts or festivals open their presales, or resale tickets appear, and writes at once | The ticket pages | Buy yourself |
| **Fridge chef** | Send a photo of the fridge; it suggests three recipes from what is there and adds the missing items to the shopping list | A model that reads images | – |
| **Language sparring** | Ten minutes a day in French or Italian on Telegram, with corrections and words it remembers you struggled with | Its memory | – |
| **Decision journal** | You note decisions with your reasoning; a few months later it asks how they turned out and shows patterns | Its memory | Personal content: keep the volume backed up and private |
| **Quiz from your own notes** | Turns lecture notes or papers you sent into spaced-repetition questions, a few per day | Its memory | – |

## Not for Hermes

| Idea | Why not |
|---|---|
| Booking and paying on its own | Payment details in an agent's reach are the most expensive kind of prompt injection |
| Reading and answering your e-mail | Full mailbox access is a large blast radius, and incoming mail is untrusted input; a forwarding address for selected mails is safer |
| Trading, transfers, crypto | Real money, irreversible |
| Managing this server (SSH, Docker, Coolify) | It is deliberately walled off from it; an agent with root on the host it runs on undoes every other layer |
| Messaging other people in your name | Hard to undo, and it may misjudge tone or context |
