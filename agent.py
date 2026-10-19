"""
Module 3: AI Content Writer Agent (Enhanced NLP & NLG Engine)
============================================================
Academic AI Architecture: Goal-Based Agent (PEAS Framework)
Operation Mode: 100% Offline, Rule-Based Natural Language Generation (NLG) with controlled randomization.
Features:
- Arabic & English spelling normalization (orthographic fixes only)
- Context & intent domain classification (word-boundary keyword matching)
- Tone-aware NLG for every framework (Professional, Inspirational, Casual)
- Domain-aware vocabulary (productivity, tech, education, business, general topics)
- Varied phrasing on every call, so "Regenerate" gives a fresh take
- Platform syntactic calibration (LinkedIn, Instagram, Twitter/X within 280 characters, Facebook)
- Zero external LLMs. Templates contain no statistics, links, testimonials or invented stories:
  every claim in a post comes from the user's topic and keywords.
"""

import re
import random
from typing import List, Dict, Any, Optional

TWITTER_LIMIT = 280
ACTION, VALUE = "Action-driven", "Value-driven"
STORY = "Story-Lesson-Question"
HASHTAG_QUOTA = {"instagram": 10, "twitter": 3, "linkedin": 4, "facebook": 5}
HASHTAG_CATEGORY = {
    "tech_ai": "tech",
    "productivity_time": "productivity",
    "education_study": "education",
    "business_career": "business",
}


def keyword_in(keyword: str, text: str) -> bool:
    """Whether a lexicon keyword occurs in already-lowercased text.

    Arabic keywords match anywhere, because Arabic attaches prefixes such as "ال" to words.
    Latin keywords match at a word start. Keywords of up to 3 letters must be whole words
    (an optional plural "s" is allowed), so "ai" can't hit "maintain" and "app" can't hit
    "apple" or "approach"; longer stems may continue ("productiv" matches "productivity").
    Shared with image_generation.prompt_builder so text and image agree on the domain.
    """
    if not keyword.isascii():
        return keyword in text
    escaped = re.escape(keyword)
    pattern = rf"\b{escaped}s?\b" if len(keyword) <= 3 else rf"\b{escaped}"
    return re.search(pattern, text) is not None


# ─────────────────────────────────────────────────────────────────────────────
# NLG COPY BANK
# A post is assembled from slots: hook (framework × variation × tone), body layout
# (framework × variation), connective lines (tone), domain vocabulary and a CTA (tone).
# Each slot has several variants, so the same directive yields fresh phrasing on every call.
# Rule for all copy: no numbers, links, results, quotes or stories presented as real.
# Arabic lines never make a verb or adjective agree with {topic}, {kw} or {challenge}
# (their gender is unknown), and never glue a preposition such as "لـ" to them.
# ─────────────────────────────────────────────────────────────────────────────

BODY_LAYOUTS = {
    "AIDA": {
        ACTION: ["{bridge}\n\n{benefit_intro}\n{benefits}", "{bridge}\n\n{steps_intro}\n{steps}"],
        VALUE: ["{insight}\n\n{value_line}", "{bridge}\n\n{insight}"],
    },
    "PAS": {
        ACTION: ["{problem}\n{agitate}\n\n{steps_intro}\n{steps}", "{problem}\n\n{steps_intro}\n{steps}"],
        VALUE: ["{problem}\n{agitate}\n\n{insight}", "{problem}\n\n{insight}\n{value_line}"],
    },
    STORY: {
        ACTION: ["{scene}\n\n{lesson_intro}\n{insight}\n\n{steps_intro}\n{steps}",
                 "{scene}\n\n{lesson_intro}\n{insight}"],
        VALUE: ["{reflection}\n\n{insight}", "{reflection}\n\n{lesson_intro}\n{insight}"],
    },
}

COPY_BANK = {
    "en": {
        "hooks": {
            "AIDA": {
                ACTION: {
                    "Professional": [
                        "A practical framework for getting {topic} right.",
                        "{topic}: where to focus first for real progress.",
                        "Getting started with {topic}? Begin with the essentials.",
                    ],
                    "Inspirational": [
                        "Your next chapter with {topic} can start today.",
                        "Imagine what {topic} could look like with the right approach.",
                        "Small steps today can change your experience with {topic}.",
                    ],
                    "Casual": [
                        "Thinking about {topic}? Let's make it easy 😊",
                        "Okay, let's talk {topic}, the simple way 👇",
                        "No need to overcomplicate {topic}. Here's the easy version 👇",
                    ],
                },
                VALUE: {
                    "Professional": [
                        "Why a clear approach to {topic} matters more than extra effort.",
                        "{topic}: what separates steady progress from wasted effort.",
                        "Rethinking {topic}: focus on what actually adds value.",
                    ],
                    "Inspirational": [
                        "{topic}: worth approaching with intention ✨",
                        "The best version of {topic} starts with believing it's possible.",
                        "There's real value in {topic} for anyone willing to start.",
                    ],
                    "Casual": [
                        "Real talk: things get easier with {topic} once you see what matters.",
                        "Here's a different way to look at {topic} 👀",
                        "Quick thought on {topic} ☕",
                    ],
                },
            },
            "PAS": {
                ACTION: {
                    "Professional": [
                        "Struggling to make progress with {topic}? Start here.",
                        "A common obstacle in {topic}, and how to address it.",
                        "If progress with {topic} feels harder than it should, structure may be what's missing.",
                    ],
                    "Inspirational": [
                        "Stuck with {topic}? This can be your turning point.",
                        "Every challenge in {topic} is a chance to grow.",
                        "Feeling stuck with {topic} is often where progress begins.",
                    ],
                    "Casual": [
                        "Ever feel stuck with {topic}? Here's what helps 🙌",
                        "{topic} giving you a hard time? Let's fix that.",
                        "If things feel messy with {topic} right now, you're not alone 😅",
                    ],
                },
                VALUE: {
                    "Professional": [
                        "Why making progress with {topic} is harder than it looks.",
                        "The hidden cost of ignoring {topic}.",
                        "Understanding the real challenge behind {topic}.",
                    ],
                    "Inspirational": [
                        "Struggling with {topic} isn't a sign to stop. It's a sign you're growing.",
                        "What {topic} can teach us about patience and progress.",
                        "Behind every challenge in {topic} is a better way forward.",
                    ],
                    "Casual": [
                        "Let's be honest: {topic} can be tricky.",
                        "Why can {topic} feel so hard sometimes? 🤔",
                        "Not every day with {topic} is easy, and that's okay.",
                    ],
                },
            },
            STORY: {
                ACTION: {
                    "Professional": [
                        "A common scenario in {topic}, and what it teaches us.",
                        "Picture a typical week working on {topic}.",
                        "Here's a situation many people face with {topic}.",
                    ],
                    "Inspirational": [
                        "Every journey with {topic} starts with a single decision.",
                        "Picture the moment everything about {topic} finally clicks ✨",
                        "Imagine looking back on your progress with {topic}.",
                    ],
                    "Casual": [
                        "Picture this: a busy day, and {topic} is on your list 😅",
                        "We've all been there with {topic}...",
                        "A quick scenario about {topic} 👇",
                    ],
                },
                VALUE: {
                    "Professional": [
                        "A lesson worth remembering about {topic}:",
                        "One principle that changes how we approach {topic}:",
                        "What {topic} can teach us about doing things well:",
                    ],
                    "Inspirational": [
                        "One lesson about {topic} worth carrying forward:",
                        "A reminder from {topic}: growth takes time ✨",
                        "The quiet lesson behind {topic}:",
                    ],
                    "Casual": [
                        "Something about {topic} worth remembering 💡",
                        "A little reminder about {topic}:",
                        "A lesson worth keeping about {topic} 😄",
                    ],
                },
            },
        },
        "lines": {
            "bridge": {
                "Professional": [
                    "Progress with {kw} depends on a clear structure.",
                    "Results with {kw} come from focusing on the right things.",
                    "A clear plan makes {kw} far more manageable.",
                ],
                "Inspirational": [
                    "Every step you take with {kw} builds momentum.",
                    "With the right mindset, working on {kw} becomes something to look forward to.",
                    "Your effort with {kw} deserves a path that leads somewhere.",
                ],
                "Casual": [
                    "Let's keep {kw} simple.",
                    "No need to overthink {kw}.",
                    "A few small habits make {kw} way easier.",
                ],
            },
            "benefit_intro": {
                "Professional": ["What a clear approach gives you:", "The benefits worth focusing on:"],
                "Inspirational": ["Here's what becomes possible:", "Picture what changes:"],
                "Casual": ["What you get out of it:", "The good stuff:"],
            },
            "steps_intro": {
                "Professional": ["A practical way to start:", "Recommended steps:"],
                "Inspirational": ["Your first steps forward:", "Start your journey here:"],
                "Casual": ["Here's what helps:", "Try this:"],
            },
            "problem": {
                "Professional": [
                    "The challenge with {kw} is often {challenge}.",
                    "Many people find {kw} difficult because of {challenge}.",
                ],
                "Inspirational": [
                    "It's easy to feel discouraged by {challenge} when working on {kw}.",
                    "Facing {challenge} with {kw} is part of the journey.",
                ],
                "Casual": [
                    "Working on {kw} usually means dealing with {challenge}. Sound familiar?",
                    "Let's be real: {challenge} can make {kw} tough.",
                ],
            },
            "agitate": {
                "Professional": [
                    "Left unaddressed, it slows progress and drains energy.",
                    "Over time, it adds friction to everything else.",
                ],
                "Inspirational": [
                    "But every obstacle is also a chance to find a better way.",
                    "The good news: this is exactly where growth begins.",
                ],
                "Casual": ["And honestly, it gets tiring fast.", "And it can really drain your motivation."],
            },
            "scene": {
                "Professional": [
                    "Consider a familiar situation: plenty of effort goes into {kw}, "
                    "yet progress keeps stalling because of {challenge}.",
                    "Picture a team working hard on {kw}, slowed down by {challenge}.",
                ],
                "Inspirational": [
                    "Imagine starting with {kw} feeling unsure, facing {challenge}, "
                    "and choosing to keep going anyway.",
                    "Picture someone who decides that {challenge} won't stop their progress with {kw}.",
                ],
                "Casual": [
                    "You finally sit down to work on {kw}, and then you run into {challenge}. Sound familiar?",
                    "You start the day excited about {kw}, and suddenly you're dealing with {challenge}.",
                ],
            },
            "reflection": {
                "Professional": [
                    "Working on {kw} often points to the same idea.",
                    "Time spent on {kw} tends to reveal something important.",
                ],
                "Inspirational": [
                    "Every step with {kw} carries a lesson worth keeping.",
                    "Growth with {kw} rarely comes from big leaps.",
                ],
                "Casual": [
                    "Spending time on {kw} teaches you a few things.",
                    "There's always something new to learn with {kw}.",
                ],
            },
            "lesson_intro": {
                "Professional": ["The takeaway:", "The key lesson:"],
                "Inspirational": ["The lesson:", "What it teaches us:"],
                "Casual": ["The big takeaway?", "Moral of the story:"],
            },
            "value_line": {
                "Professional": ["Focus on what adds value, and the rest becomes easier.", "Clarity first, speed second."],
                "Inspirational": ["Trust the process and keep showing up ✨",
                                  "Consistency is what turns intention into results."],
                "Casual": ["Keep it simple and enjoy the process 🙂", "Easy does it 🙂"],
            },
        },
        "ctas": {
            "action": {
                "Professional": [
                    "Which of these will you apply first? Share below.",
                    "Save this post as a reference for your next step.",
                    "What would you add to this list? Let's discuss in the comments.",
                ],
                "Inspirational": [
                    "Take your first step today, and tell us how it goes ✨",
                    "Save this as a reminder for the days you need a push.",
                    "Which one will you start with? Share it below.",
                ],
                "Casual": [
                    "Which one are you trying first? Tell us in the comments 👇",
                    "Save this for later and share it with a friend who needs it 🙌",
                    "Tag someone who'd find this useful 😄",
                ],
            },
            "question": {
                "Professional": [
                    "What has your experience been with this? Share your thoughts below.",
                    "Do you see it the same way? Let's discuss.",
                    "What would you add from your own experience?",
                ],
                "Inspirational": [
                    "What's one small step you can take this week? Share it below ✨",
                    "Who needs this reminder today? Share it with them.",
                    "What keeps you motivated? We'd love to hear from you.",
                ],
                "Casual": [
                    "Agree or disagree? Let us know in the comments 👇",
                    "What's your take? Drop it below 💬",
                    "Does this sound familiar? Tell us 😄",
                ],
            },
        },
        "save_prompt": "📌 Save this post for reference & share with someone who needs it",
        "domains": {
            "productivity_time": {
                "challenge": ["scattered tasks and constant interruptions", "a to-do list that keeps growing",
                              "busy days that don't add up to progress"],
                "benefit": ["Clear priorities at the start of each day", "Fewer context switches and more focused time",
                            "A routine that is easy to keep", "Room to rest without feeling behind"],
                "step": ["Pick the one task that matters most today", "Block focused time and silence notifications",
                         "Break big goals into small next actions", "Review what worked at the end of the week"],
                "insight": ["Being busy and making progress are not the same thing.",
                            "A simple routine you keep beats a perfect plan you drop.",
                            "Protecting your attention is the heart of managing your time."],
            },
            "tech_ai": {
                "challenge": ["tools that add complexity instead of removing it",
                              "tools that change faster than teams can adapt",
                              "technology that doesn't fit the way people actually work"],
                "benefit": ["Tools that fit the way you already work", "Less repetitive work and more time for decisions",
                            "A clearer view of what technology can and can't do", "Smoother collaboration across the team"],
                "step": ["Start from the problem, not from the tool", "Try a small pilot before rolling anything out",
                         "Keep a human review step for important outputs", "Check whether it actually saves time"],
                "insight": ["Technology works best when it serves a clear purpose.",
                            "The best tool is the one people actually use.",
                            "Understanding the problem comes before choosing the technology."],
            },
            "education_study": {
                "challenge": ["hard work that doesn't seem to stick", "long sessions that end in fatigue",
                              "the stress of falling behind"],
                "benefit": ["Study sessions that are shorter and more focused", "Better recall of what you learn",
                            "More confidence before exams", "A steady pace instead of last-minute pressure"],
                "step": ["Study in short, focused sessions", "Test yourself instead of rereading",
                         "Explain the idea in your own words", "Plan your week before it starts"],
                "insight": ["Learning sticks when you practice recalling it, not just reading it.",
                            "Consistency matters more than marathon sessions.",
                            "Understanding beats memorizing."],
            },
            "business_career": {
                "challenge": ["plans that never leave the whiteboard", "growth goals without a clear path",
                              "competing priorities across the team"],
                "benefit": ["A clearer direction for the team", "Decisions grounded in what customers actually need",
                            "Steady, sustainable growth", "A stronger, more consistent brand"],
                "step": ["Talk to your customers before building more", "Focus on one clear goal at a time",
                         "Track the few metrics that really matter", "Share progress openly with your team"],
                "insight": ["Knowing your customer well simplifies almost every decision.",
                            "Strategy is also about deciding what not to do.",
                            "Small, consistent improvements add up over time."],
            },
            "general": {
                "challenge": ["uncertainty about where to start", "too much information and too little clarity",
                              "motivation that fades after the first excitement"],
                "benefit": ["A clearer idea of where to start", "Practical tips you can try right away",
                            "More confidence along the way", "A fresh perspective on something familiar"],
                "step": ["Start small and keep it simple", "Learn from people who share the same interest",
                         "Make it part of your routine", "Notice what you enjoy and do more of it"],
                "insight": ["Small, steady steps make any new interest easier to enjoy.",
                            "Curiosity is a great place to start.",
                            "The details are what make an experience memorable."],
            },
        },
    },
    "ar": {
        "hooks": {
            "AIDA": {
                ACTION: {
                    "Professional": [
                        "إطار عملي لإتقان {topic}.",
                        "{topic}: أين تركّز أولًا لتحقق تقدمًا حقيقيًا؟",
                        "تبدأ في {topic}؟ ابدأ بالأساسيات الصحيحة.",
                    ],
                    "Inspirational": [
                        "فصل جديد في {topic} يمكن أن يبدأ اليوم.",
                        "تخيّل تجربتك مع {topic} بالنهج الصحيح.",
                        "خطوات صغيرة اليوم قد تغيّر تجربتك مع {topic}.",
                    ],
                    "Casual": [
                        "تفكر في {topic}؟ لنجعل الأمر بسيطًا 😊",
                        "حديث سريع وبسيط عن {topic} 👇",
                        "الأمر في {topic} أبسط مما يبدو، إليك الطريقة السهلة 👇",
                    ],
                },
                VALUE: {
                    "Professional": [
                        "لماذا يهم النهج الواضح في {topic} أكثر من الجهد الإضافي؟",
                        "{topic}: ما الذي يميّز التقدم الثابت عن الجهد الضائع؟",
                        "إعادة التفكير في {topic}: ركّز على ما يضيف قيمة حقيقية.",
                    ],
                    "Inspirational": [
                        "رحلتك مع {topic} تستحق أن تخوضها بوعي ✨",
                        "أفضل تجربة في {topic} تبدأ بالإيمان بأنها ممكنة.",
                        "في {topic} قيمة حقيقية لكل من يقرر البدء.",
                    ],
                    "Casual": [
                        "بصراحة، تصبح الأمور في {topic} أسهل عندما تعرف ما المهم.",
                        "طريقة مختلفة للنظر إلى {topic} 👀",
                        "فكرة سريعة عن {topic} ☕",
                    ],
                },
            },
            "PAS": {
                ACTION: {
                    "Professional": [
                        "هل تجد صعوبة في إحراز تقدم في {topic}؟ ابدأ من هنا.",
                        "عقبة شائعة في {topic}، وكيف تتعامل معها.",
                        "إذا بدا لك التقدم في {topic} أصعب مما ينبغي، فربما ينقصك التنظيم.",
                    ],
                    "Inspirational": [
                        "تشعر بالتوقف في {topic}؟ قد تكون هذه نقطة التحول.",
                        "كل تحدٍّ في {topic} فرصة جديدة للنمو.",
                        "الشعور بالتعثر في {topic} غالبًا ما يكون بداية التقدم.",
                    ],
                    "Casual": [
                        "تشعر أنك عالق في {topic}؟ إليك ما يساعد 🙌",
                        "التعامل مع {topic} صار مرهقًا؟ لنصلح ذلك معًا.",
                        "إذا كانت الأمور في {topic} فوضوية الآن، فلست وحدك 😅",
                    ],
                },
                VALUE: {
                    "Professional": [
                        "لماذا يبدو التقدم في {topic} أصعب مما يتوقعه كثيرون؟",
                        "التكلفة الخفية لإهمال {topic}.",
                        "فهم التحدي الحقيقي وراء {topic}.",
                    ],
                    "Inspirational": [
                        "الصعوبة في {topic} ليست إشارة للتوقف، بل علامة على أنك تنمو.",
                        "ماذا تعلّمنا تجربة {topic} عن الصبر والتقدم؟",
                        "خلف كل تحدٍّ في {topic} طريق أفضل إلى الأمام.",
                    ],
                    "Casual": [
                        "لنكن صريحين: التعامل مع {topic} ليس سهلًا دائمًا.",
                        "لماذا نشعر أحيانًا بالصعوبة في {topic}؟ 🤔",
                        "ليست كل الأيام مع {topic} سهلة، ولا بأس بذلك.",
                    ],
                },
            },
            STORY: {
                ACTION: {
                    "Professional": [
                        "موقف شائع في {topic}، وما الذي يعلّمنا إياه.",
                        "تخيّل أسبوعًا عاديًا من العمل على {topic}.",
                        "إليك موقفًا يواجهه كثيرون في {topic}.",
                    ],
                    "Inspirational": [
                        "كل رحلة في {topic} تبدأ بقرار واحد.",
                        "تخيّل اللحظة التي يصبح فيها كل شيء في {topic} واضحًا ✨",
                        "تخيّل نفسك تنظر إلى تقدمك في {topic} بعد فترة من الآن.",
                    ],
                    "Casual": [
                        "تخيّل معي: يوم مزدحم، وعليك أن تنجز شيئًا في {topic} 😅",
                        "كلنا مررنا بهذا الموقف مع {topic}...",
                        "موقف سريع عن {topic} 👇",
                    ],
                },
                VALUE: {
                    "Professional": [
                        "درس يستحق التذكر عن {topic}:",
                        "مبدأ واحد يغيّر طريقة تعاملنا مع {topic}:",
                        "ماذا نتعلم من {topic} عن إتقان العمل؟",
                    ],
                    "Inspirational": [
                        "درس من {topic} يستحق أن نحمله معنا:",
                        "تذكير من {topic}: النمو يحتاج وقتًا ✨",
                        "الدرس الهادئ خلف {topic}:",
                    ],
                    "Casual": [
                        "شيء عن {topic} يستحق أن تتذكره 💡",
                        "تذكير صغير عن {topic}:",
                        "درس يستحق الاحتفاظ به عن {topic} 😄",
                    ],
                },
            },
        },
        "lines": {
            "bridge": {
                "Professional": [
                    "يعتمد التقدم في {kw} على هيكل واضح.",
                    "تأتي النتائج في {kw} من التركيز على الأمور الصحيحة.",
                    "الخطة الواضحة تجعل التعامل مع {kw} أسهل بكثير.",
                ],
                "Inspirational": [
                    "كل خطوة تخطوها في {kw} تبني زخمًا جديدًا.",
                    "بالعقلية الصحيحة، يصبح العمل على {kw} شيئًا تتطلع إليه.",
                    "جهدك في {kw} يستحق طريقًا يوصلك إلى ما تريد.",
                ],
                "Casual": [
                    "لنبقِ الأمور في {kw} بسيطة.",
                    "لا داعي لتعقيد الأمور في {kw}.",
                    "بعض العادات الصغيرة تجعل التعامل مع {kw} أسهل بكثير.",
                ],
            },
            "benefit_intro": {
                "Professional": ["ما يمنحك إياه النهج الواضح:", "أهم المكاسب التي تستحق التركيز:"],
                "Inspirational": ["إليك ما يصبح ممكنًا:", "تخيّل ما الذي سيتغير:"],
                "Casual": ["ماذا ستستفيد؟", "الجزء الجميل:"],
            },
            "steps_intro": {
                "Professional": ["طريقة عملية للبدء:", "خطوات مقترحة:"],
                "Inspirational": ["خطواتك الأولى إلى الأمام:", "ابدأ رحلتك من هنا:"],
                "Casual": ["إليك ما يساعد:", "جرّب هذا:"],
            },
            "problem": {
                "Professional": [
                    "غالبًا ما يكمن التحدي في {kw} في {challenge}.",
                    "يجد كثيرون صعوبة في {kw} بسبب {challenge}.",
                ],
                "Inspirational": [
                    "من السهل أن تشعر بالإحباط أمام {challenge} أثناء العمل على {kw}.",
                    "مواجهة {challenge} في {kw} جزء من الرحلة.",
                ],
                "Casual": [
                    "العمل على {kw} يعني غالبًا التعامل مع {challenge}. مألوف؟",
                    "لنكن واقعيين: مع {challenge} يصبح العمل على {kw} أصعب.",
                ],
            },
            "agitate": {
                "Professional": [
                    "وإذا تُرك الأمر دون معالجة، فإنه يبطئ التقدم ويستنزف الطاقة.",
                    "ومع الوقت، يضيف ذلك عبئًا على كل شيء آخر.",
                ],
                "Inspirational": [
                    "لكن كل عقبة هي أيضًا فرصة لإيجاد طريقة أفضل.",
                    "والخبر الجيد: من هنا تحديدًا يبدأ النمو.",
                ],
                "Casual": ["وبصراحة، هذا متعب جدًا.", "وقد يؤثر ذلك فعلًا على حماسك."],
            },
            "scene": {
                "Professional": [
                    "لنأخذ موقفًا مألوفًا: جهد كبير يُبذل في {kw}، لكن التقدم يتعطل بسبب {challenge}.",
                    "تخيّل فريقًا يعمل بجد على {kw}، بينما يتباطأ كل شيء بسبب {challenge}.",
                ],
                "Inspirational": [
                    "تخيّل أن تبدأ في {kw} وأنت متردد، وتواجه {challenge}، ثم تقرر أن تستمر رغم ذلك.",
                    "تخيّل شخصًا قرر أن يستمر في {kw} مهما واجه من {challenge}.",
                ],
                "Casual": [
                    "تجلس أخيرًا لتعمل على {kw}، ثم تجد نفسك أمام {challenge}. مألوف؟",
                    "تبدأ يومك متحمسًا للعمل على {kw}، ثم تجد نفسك غارقًا في {challenge}.",
                ],
            },
            "reflection": {
                "Professional": [
                    "العمل على {kw} يكشف غالبًا عن أمر مهم.",
                    "الوقت الذي تقضيه في {kw} يقود عادةً إلى الفكرة نفسها.",
                ],
                "Inspirational": [
                    "كل خطوة في {kw} تحمل درسًا يستحق الاحتفاظ به.",
                    "النمو في {kw} نادرًا ما يأتي بقفزات كبيرة.",
                ],
                "Casual": [
                    "قضاء الوقت في {kw} يعلّمك أشياء كثيرة.",
                    "هناك دائمًا شيء جديد تتعلمه في {kw}.",
                ],
            },
            "lesson_intro": {
                "Professional": ["الخلاصة:", "الدرس الأهم:"],
                "Inspirational": ["الدرس:", "ما يعلّمنا إياه ذلك:"],
                "Casual": ["الفكرة الأهم؟", "الخلاصة ببساطة:"],
            },
            "value_line": {
                "Professional": ["ركّز على ما يضيف قيمة، وسيصبح الباقي أسهل.", "الوضوح أولًا، ثم السرعة."],
                "Inspirational": ["ثق بالطريق واستمر في الحضور ✨", "استمراريتك هي ما يحوّل النية إلى نتائج."],
                "Casual": ["اجعلها بسيطة واستمتع بالرحلة 🙂", "خطوة بخطوة، وعلى راحتك 🙂"],
            },
        },
        "ctas": {
            "action": {
                "Professional": [
                    "أي هذه النقاط ستطبّقها أولًا؟ شاركنا في التعليقات.",
                    "احفظ هذا المنشور كمرجع لخطوتك القادمة.",
                    "ما الذي تضيفه إلى هذه القائمة؟ لنتناقش في التعليقات.",
                ],
                "Inspirational": [
                    "ابدأ خطوتك الأولى اليوم، وأخبرنا كيف سارت ✨",
                    "احفظ هذا المنشور كتذكير في الأيام التي تحتاج فيها إلى دفعة.",
                    "بأي نقطة ستبدأ؟ شاركنا بها في التعليقات.",
                ],
                "Casual": [
                    "أيها ستجرّب أولًا؟ أخبرنا في التعليقات 👇",
                    "احفظ المنشور وشاركه مع صديق يحتاجه 🙌",
                    "اذكر شخصًا سيجد هذا مفيدًا 😄",
                ],
            },
            "question": {
                "Professional": [
                    "ما تجربتك مع هذا الموضوع؟ شاركنا رأيك في التعليقات.",
                    "هل ترى الأمر بالطريقة نفسها؟ لنتناقش.",
                    "ما الذي تضيفه من تجربتك الخاصة؟",
                ],
                "Inspirational": [
                    "ما الخطوة الصغيرة التي يمكنك اتخاذها هذا الأسبوع؟ شاركنا بها ✨",
                    "من يحتاج هذا التذكير اليوم؟ شاركه معه.",
                    "ما الذي يبقيك متحفزًا؟ يسعدنا أن نسمع منك.",
                ],
                "Casual": [
                    "توافق أم لا؟ أخبرنا في التعليقات 👇",
                    "ما رأيك؟ اكتبه في التعليقات 💬",
                    "هل يبدو هذا مألوفًا؟ احكِ لنا 😄",
                ],
            },
        },
        "save_prompt": "📌 احفظ المنشور لترجع له وشاركه مع زملائك المهتمين",
        "domains": {
            "productivity_time": {
                "challenge": ["تشتت المهام وكثرة المقاطعات", "قائمة مهام لا تنتهي",
                              "أيام مزدحمة لا تقود إلى تقدم حقيقي"],
                "benefit": ["أولويات واضحة مع بداية كل يوم", "تنقل أقل بين المهام ووقت تركيز أطول",
                            "روتين سهل الالتزام به", "مساحة للراحة دون الشعور بالتأخر"],
                "step": ["اختر المهمة الأهم لليوم وابدأ بها", "خصص وقتًا للتركيز وأوقف الإشعارات",
                         "قسّم الأهداف الكبيرة إلى خطوات صغيرة", "راجع ما نجح معك في نهاية الأسبوع"],
                "insight": ["الانشغال لا يعني بالضرورة التقدم.",
                            "روتين بسيط تلتزم به أفضل من خطة مثالية تتركها.",
                            "حماية تركيزك هي جوهر إدارة الوقت."],
            },
            "tech_ai": {
                "challenge": ["أدوات تزيد التعقيد بدل أن تقلله", "ملاحقة أدوات تتغير باستمرار",
                              "تقنيات لا تناسب طريقة العمل الفعلية"],
                "benefit": ["أدوات تناسب طريقة عملك الحالية", "عمل متكرر أقل ووقت أكبر للقرارات",
                            "فهم أوضح لما تستطيع التقنية فعله وما لا تستطيعه", "تعاون أسهل داخل الفريق"],
                "step": ["ابدأ من المشكلة لا من الأداة", "جرّب على نطاق صغير قبل التعميم",
                         "احتفظ بمراجعة بشرية للمخرجات المهمة", "تأكد أن الأداة توفر وقتك فعلًا"],
                "insight": ["تعمل التقنية بأفضل شكل عندما تخدم هدفًا واضحًا.",
                            "أفضل أداة هي التي يستخدمها الناس فعلًا.",
                            "فهم المشكلة يأتي قبل اختيار التقنية."],
            },
            "education_study": {
                "challenge": ["مذاكرة طويلة دون أن تثبت المعلومة", "جلسات طويلة تنتهي بالإرهاق",
                              "التأخر وعدم معرفة من أين تبدأ من جديد"],
                "benefit": ["جلسات مذاكرة أقصر وأكثر تركيزًا", "تذكّر أفضل لما تتعلمه",
                            "ثقة أكبر قبل الامتحانات", "وتيرة ثابتة بدل ضغط اللحظة الأخيرة"],
                "step": ["ذاكر على جلسات قصيرة ومركزة", "اختبر نفسك بدل إعادة القراءة",
                         "اشرح الفكرة بأسلوبك الخاص", "خطط لأسبوعك قبل أن يبدأ"],
                "insight": ["تثبت المعلومة عندما تتدرب على استرجاعها لا بمجرد قراءتها.",
                            "الاستمرارية أهم من الجلسات الطويلة المتقطعة.",
                            "الفهم أقوى من الحفظ."],
            },
            "business_career": {
                "challenge": ["خطط لا تتجاوز الورق", "أهداف نمو بلا طريق واضح", "تضارب الأولويات داخل الفريق"],
                "benefit": ["اتجاه أوضح للفريق", "قرارات مبنية على احتياجات العملاء الفعلية",
                            "نمو ثابت ومستدام", "علامة تجارية أقوى وأكثر اتساقًا"],
                "step": ["تحدث مع عملائك قبل أن تبني المزيد", "ركّز على هدف واضح واحد في كل مرحلة",
                         "تابع عددًا قليلًا من المؤشرات المهمة فعلًا", "شارك التقدم بشفافية مع فريقك"],
                "insight": ["فهمك الجيد لعميلك يبسّط معظم القرارات.",
                            "الاستراتيجية تعني أيضًا أن تقرر ما لن تفعله.",
                            "التحسينات الصغيرة المستمرة تتراكم مع الوقت."],
            },
            "general": {
                "challenge": ["عدم معرفة من أين تبدأ", "كثرة المعلومات وقلة الوضوح",
                              "صعوبة الاستمرار بعد أن يخفت الحماس"],
                "benefit": ["فكرة أوضح عن نقطة البداية", "نصائح عملية تستطيع تجربتها فورًا",
                            "ثقة أكبر خطوة بعد خطوة", "نظرة جديدة لشيء مألوف"],
                "step": ["ابدأ بخطوة صغيرة وبسيطة", "تعلّم ممن يشاركونك الاهتمام نفسه",
                         "اجعله جزءًا من روتينك", "لاحظ ما تستمتع به وزد منه"],
                "insight": ["الخطوات الصغيرة الثابتة تجعل أي اهتمام جديد أسهل وأمتع.",
                            "الفضول نقطة بداية رائعة.",
                            "التفاصيل هي ما يجعل التجربة لا تُنسى."],
            },
        },
    },
}


class ContentWriterAgent:
    """
    Enhanced Module 3 AI Content Writer Agent.
    Combines rule-based Natural Language Understanding (NLU: spelling normalization,
    intent and domain classification) and slot-based Natural Language Generation (NLG).
    Pass ``seed`` for reproducible output (tests); leave it ``None`` for varied output.
    """

    # ── Spelling normalization (orthography only: hamza, taa marbuta, alif maqsura, letter swaps) ──
    # Only real misspellings belong here. Never map a word to a different word or phrase:
    # that changes the user's meaning and can break gender agreement in their sentence.
    TYPO_MAP_AR = {
        "املاءيه": "إملائية",
        "املائيه": "إملائية",
        "حته": "حتى",
        "انتا": "أنت",
        "برمجه": "برمجة",
        "تكلوجيا": "تكنولوجيا",
        "تكنلوجيا": "تكنولوجيا",
        "زكاء": "ذكاء",
        "إصطناعي": "اصطناعي",
        "لينكدان": "لينكد إن",
        "مزاكره": "مذاكرة",
        "مذاكره": "مذاكرة",
        "انتاجيه": "إنتاجية",
        "شركه": "شركة",
        "دراسه": "دراسة",
        "وظايف": "وظائف",
    }

    TYPO_MAP_EN = {
        "teh": "the",
        "producitvity": "productivity",
        "producitivity": "productivity",
        "managment": "management",
        "studdy": "study",
        "colledge": "college",
        "aplication": "application",
        "appliction": "application",
        "softwere": "software",
        "programing": "programming",
        "artifical": "artificial",
        "inteligence": "intelligence",
        "buisness": "business",
        "busines": "business",
        "markting": "marketing",
        "stratgy": "strategy",
        "succes": "success",
        "sucess": "success",
        "focuss": "focus",
        "habbit": "habit",
    }

    # ── Category & Domain Lexicon ───────────────────────────────────────────
    # Checked in this order; the first domain with a matching keyword wins (see keyword_in).
    DOMAINS = {
        "tech_ai": {
            "keywords": ["ai", "tech", "software", "app", "application", "applications", "code", "programming",
                         "ذكاء", "تقني", "تطبيق", "تطبيقات", "ابلكيشن", "ابليكيشن", "برمج", "تكنولوجيا", "روبوت",
                         "بيانات"],
            "ar_terms": ["التحول الرقمي", "الأتمتة الذكية", "التطوير البرمجي", "الحلول التكنولوجية"],
            "en_terms": ["digital transformation", "smart automation", "scalable engineering", "cutting-edge tools"]
        },
        "productivity_time": {
            "keywords": ["time", "productiv", "habit", "focus", "manage", "organiz", "task", "وقت", "إنتاج", "عادات", "تركيز", "مهام", "تنظيم", "إنجاز"],
            "ar_terms": ["إدارة الوقت", "الإنتاجية العالية", "التركيز العميق", "بناء العادات المستدامة"],
            "en_terms": ["time management", "peak productivity", "deep work", "sustainable habits"]
        },
        "education_study": {
            "keywords": ["study", "student", "college", "school", "learn", "exam", "course", "طالب", "دراس", "جامع", "مذاكرة", "امتحان", "تعليم", "تعلّم"],
            "ar_terms": ["التحصيل الأكاديمي", "الروتين الدراسي الذكي", "التفوق الجامعي", "مهارات التعلم الفعّال"],
            "en_terms": ["academic excellence", "smart study routines", "higher education success", "effective learning"]
        },
        "business_career": {
            "keywords": ["business", "marketing", "startup", "sales", "lead", "career", "money", "أعمال", "تسويق", "مشروع", "مبيعات", "استثمار", "ريادة", "وظيفة"],
            "ar_terms": ["نمو الأعمال", "بناء العلامة التجارية", "استراتيجيات التسويق", "الريادة والابتكار"],
            "en_terms": ["business growth", "brand positioning", "strategic marketing", "entrepreneurial excellence"]
        }
    }

    HASHTAG_KB = {
        "en": {
            "productivity": ["#Productivity", "#TimeManagement", "#DeepWork", "#FocusMode", "#Efficiency", "#GrowthMindset", "#WorkSmart", "#DailyHabits"],
            "education": ["#StudentLife", "#StudyHacks", "#CollegeTips", "#HigherEd", "#AcademicSuccess", "#LearnSmart", "#StudyRoutine", "#StudentSuccess"],
            "tech": ["#TechTrends", "#ArtificialIntelligence", "#AppDevelopment", "#DigitalInnovation", "#SmartTools", "#EdTech", "#SoftwareEngineering"],
            "business": ["#BusinessStrategy", "#Entrepreneurship", "#Leadership", "#MarketingTips", "#Startups", "#BrandGrowth", "#ProfessionalDevelopment"],
            # Topic-neutral tags, appended for every domain and used alone for general topics.
            "general": ["#Tips", "#LearnSomethingNew", "#Inspiration", "#Community", "#Lifestyle", "#ShareYourThoughts"]
        },
        "ar": {
            "productivity": ["#إنتاجية", "#تنظيم_الوقت", "#إدارة_الوقت", "#تطوير_الذات", "#إنجاز", "#تركيز_عميق", "#عادات_النجاح", "#عمل_ذكي"],
            "education": ["#حياة_الطلاب", "#نصائح_دراسية", "#جامعيون", "#دراسة_ذكية", "#تفوق_أكاديمي", "#طالب_جامعي", "#روتين_المذاكرة", "#النجاح_الدراسي"],
            "tech": ["#تطبيقات_ذكية", "#ذكاء_اصطناعي", "#تقنية", "#حلول_رقمية", "#أدوات_رقمية", "#ابتكار", "#تكنولوجيا_المستقبل"],
            "business": ["#ريادة_أعمال", "#استراتيجية_أعمال", "#تسويق_رقمي", "#تطوير_مهني", "#مشاريع_ناشئة", "#إدارة_الأعمال", "#بناء_المشاريع"],
            "general": ["#نصائح", "#معلومة_مفيدة", "#إلهام", "#مجتمع", "#أسلوب_حياة", "#شاركنا_رأيك"]
        }
    }

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)

    # ── Natural Language Understanding: Normalization & Correction ───────────
    def normalize_and_clean_text(self, text: str, lang: str = "ar") -> str:
        """
        Cleans typographical mistakes, corrects spelling of common words,
        normalizes Arabic letters (همزات، تاء مربوطة، ياء/ألف مقصورة).
        """
        if not text:
            return ""

        cleaned = text.strip()

        if lang == "ar":
            # Fix duplicate spaces and erratic punctuation
            cleaned = re.sub(r'\s+', ' ', cleaned)

            # Dictionary-based whole-word correction
            words = cleaned.split()
            corrected_words = []
            for w in words:
                # Strip leading/trailing punctuation for lookup
                core = re.sub(r'^[^\w\s]+|[^\w\s]+$', '', w)
                if core in self.TYPO_MAP_AR:
                    replacement = self.TYPO_MAP_AR[core]
                    w = w.replace(core, replacement)
                corrected_words.append(w)
            cleaned = " ".join(corrected_words)

            # Rule-based Arabic Normalization
            # 1. Normalize final ه to ة where commonly misspelled
            cleaned = re.sub(r'\b(انتاجيه|انتاجية)\b', 'إنتاجية', cleaned)
            cleaned = re.sub(r'\b(اداره|ادارة)\b', 'إدارة', cleaned)
            cleaned = re.sub(r'\b(مزاكره|مذاكره)\b', 'مذاكرة', cleaned)
            cleaned = re.sub(r'\b(دراسه)\b', 'دراسة', cleaned)
            cleaned = re.sub(r'\b(تطبيقات ذكيه)\b', 'تطبيقات ذكية', cleaned)
            cleaned = re.sub(r'\b(استراتيجيه)\b', 'استراتيجية', cleaned)
            # 2. Fix common Alef Hamza
            cleaned = re.sub(r'\b(انتاج)\b', 'إنتاج', cleaned)
            cleaned = re.sub(r'\b(انجاز)\b', 'إنجاز', cleaned)
            cleaned = re.sub(r'\b(اهميه)\b', 'أهمية', cleaned)
            cleaned = re.sub(r'\b(افضل)\b', 'أفضل', cleaned)
        else:
            # English normalization
            words = cleaned.split()
            corrected_words = []
            for w in words:
                core = re.sub(r'^[^\w\s]+|[^\w\s]+$', '', w).lower()
                if core in self.TYPO_MAP_EN:
                    replacement = self.TYPO_MAP_EN[core]
                    w = re.sub(re.escape(core), replacement, w, flags=re.IGNORECASE)
                corrected_words.append(w)
            cleaned = " ".join(corrected_words)

        return cleaned

    def detect_domain(self, text: str) -> str:
        """Determines the thematic domain to pick vocabulary and hashtags. Falls back to "general"."""
        t_lower = text.lower()
        for domain_name, data in self.DOMAINS.items():
            if any(keyword_in(k, t_lower) for k in data["keywords"]):
                return domain_name
        return "general"

    # ── Phase 1: Reasoning Framework Selection ──────────────────────────────
    @staticmethod
    def resolve_framework(goal: str) -> str:
        goal_lower = goal.lower()
        if "market" in goal_lower or "launch" in goal_lower:
            return "AIDA"
        elif "educat" in goal_lower or "problem" in goal_lower:
            return "PAS"
        else:
            return STORY

    @staticmethod
    def resolve_tone(tone: str) -> str:
        """Maps any tone label (including legacy ones such as "funny") to a supported tone."""
        t = (tone or "").lower()
        if "inspir" in t:
            return "Inspirational"
        if any(word in t for word in ("casual", "funny", "friendly", "playful")):
            return "Casual"
        return "Professional"

    @staticmethod
    def _platform_key(platform: str) -> str:
        p = (platform or "").strip().lower()
        if "insta" in p:
            return "instagram"
        if "linked" in p:
            return "linkedin"
        if "twitter" in p or p == "x":
            return "twitter"
        return "facebook"

    # ── Phase 4: Categorical Hashtag Extraction & Distribution ──────────────
    def allocate_hashtags(self, keywords: List[str], topic: str, platform: str, lang: str) -> List[str]:
        pool = []
        kb = self.HASHTAG_KB.get(lang, self.HASHTAG_KB["en"])

        # Clean keywords & extract meaningful tags
        for kw in keywords:
            clean_kw = re.sub(r'[^\w\s]', '', kw).strip().replace(" ", "_")
            if clean_kw and len(clean_kw) > 1:
                pool.append(f"#{clean_kw}")

        # Derive 1-2 clean topic tags (exclude long sentences)
        clean_topic = re.sub(r'[^\w\s]', '', topic).strip()
        words = clean_topic.split()
        if 1 <= len(words) <= 3:
            pool.append(f"#{'_'.join(words)}")
        elif len(words) > 3:
            # take most salient words
            salient = [w for w in words if len(w) > 3][:2]
            if salient:
                pool.append(f"#{'_'.join(salient)}")

        # Domain category tags, then topic-neutral ones
        category = HASHTAG_CATEGORY.get(self.detect_domain(f"{topic} {' '.join(keywords)}"))
        if category:
            pool.extend(kb[category])
        pool.extend(kb["general"])

        # Deduplicate case-insensitively, preserving order
        seen, unique_tags = set(), []
        for tag in pool:
            if tag.lower() not in seen:
                seen.add(tag.lower())
                unique_tags.append(tag)

        return unique_tags[:HASHTAG_QUOTA[self._platform_key(platform)]]

    # ── Phase 2 & 3: Bilingual Slot-Filling & Sentence Synthesis ───────────
    def generate_copy_sections(
        self,
        topic: str,
        keywords: List[str],
        platform: str,
        goal: str,
        tone: str,
        lang: str,
        variation_type: str,
        domain: Optional[str] = None,
        avoid_insight: Optional[str] = None,
    ) -> Dict[str, str]:
        lang = "ar" if lang == "ar" else "en"
        clean_topic = self.normalize_and_clean_text(topic, lang)
        clean_kws = [self.normalize_and_clean_text(k, lang) for k in keywords if k.strip()]
        if domain is None:
            domain = self.detect_domain(f"{clean_topic} {' '.join(clean_kws)}")
        return self._synthesize(
            lang=lang,
            topic=clean_topic,
            kw_phrase=self._join_keywords(clean_kws, lang) or clean_topic,
            framework=self.resolve_framework(goal),
            tone=self.resolve_tone(tone),
            v_type=ACTION if variation_type == ACTION else VALUE,
            domain=domain,
            avoid_insight=avoid_insight,
        )

    @staticmethod
    def _join_keywords(keywords: List[str], lang: str) -> str:
        items = keywords[:3]
        if len(items) < 2:
            return items[0] if items else ""
        if lang == "ar":
            # "أ وب" for two items, "أ، وب، وج" for three
            return " و".join(items) if len(items) == 2 else "، و".join(items)
        if len(items) == 2:
            return f"{items[0]} and {items[1]}"
        return f"{items[0]}, {items[1]}, and {items[2]}"

    def _synthesize(self, lang: str, topic: str, kw_phrase: str, framework: str,
                    tone: str, v_type: str, domain: str, avoid_insight: Optional[str] = None) -> Dict[str, str]:
        bank = COPY_BANK[lang]
        vocab = bank["domains"].get(domain, bank["domains"]["general"])
        pick = self._rng.choice
        challenge = pick(vocab["challenge"])

        # Fill the connective lines first; the layout then receives finished strings only,
        # so braces typed by the user can never be read as template fields.
        slots = {
            name: pick(variants[tone]).format(kw=kw_phrase, challenge=challenge, topic=topic)
            for name, variants in bank["lines"].items()
        }
        slots["insight"] = pick([i for i in vocab["insight"] if i != avoid_insight] or vocab["insight"])
        slots["benefits"] = "\n".join(f"• {item}" for item in self._rng.sample(vocab["benefit"], 3))
        slots["steps"] = "\n".join(f"• {item}" for item in self._rng.sample(vocab["step"], 3))

        # Story posts and value posts end on a question; action posts may end on a next step.
        cta_kind = "question" if framework == STORY or v_type == VALUE else "action"
        return {
            "hook": pick(bank["hooks"][framework][v_type][tone]).format(topic=topic),
            "body": pick(BODY_LAYOUTS[framework][v_type]).format(**slots),
            "cta": pick(bank["ctas"][cta_kind][tone]),
            # One self-contained sentence for platforms that skip the body (X/Twitter),
            # so hooks such as "A lesson worth remembering about ...:" are never left hanging.
            "summary": slots["insight"],
        }

    # ── Phase 2: Platform Formatting & Assembly ─────────────────────────────
    def format_full_caption(
        self,
        hook: str,
        body: str,
        cta: str,
        hashtags: List[str],
        platform: str,
        lang: str,
        summary: Optional[str] = None,
    ) -> str:
        plat = self._platform_key(platform)
        tag_str = " ".join(hashtags)

        if plat == "twitter":
            # High-density brevity: hook + key sentence + CTA + tags, always within 280 characters
            return self._fit_twitter(hook, cta, hashtags, summary)

        elif plat == "instagram":
            # Above the fold hook, clean spacers, save/share CTA
            opener = f"{hook} ✨" if hook[-1:].isalnum() or hook[-1:] in ".:!?؟" else hook
            parts = [opener, ".", body, "."]
            if not re.search(r"\bsave\b|احفظ", cta, re.IGNORECASE):
                parts.append(COPY_BANK["ar" if lang == "ar" else "en"]["save_prompt"])
            parts += [cta, ".", tag_str]
            return "\n".join(parts)

        elif plat == "linkedin":
            # Professional double-spaced skimming format
            return f"{hook}\n\n{body}\n\n{cta}\n\n{tag_str}"

        else:  # Facebook
            # Conversational community narrative
            return f"{hook}\n\n{body}\n\n{cta}\n\n{tag_str}"

    @staticmethod
    def _truncate_words(text: str, limit: int) -> str:
        """Shortens text to ``limit`` characters at a word boundary, ending with "..."."""
        if len(text) <= limit:
            return text
        cut = text[: limit - 3]
        if " " in cut:
            cut = cut[: cut.rfind(" ")]
        return cut.rstrip(" ,.;:!?،؛-—") + "..."

    def _fit_twitter(self, hook: str, cta: str, hashtags: List[str], summary: Optional[str] = None) -> str:
        """Builds the longest post that fits the X/Twitter limit.

        Drops the CTA first, then secondary hashtags, then the key sentence. If the hook alone is
        still too long, it keeps the primary hashtag (when there is room) and trims the hook at a
        word boundary.
        """
        def join(*parts: Optional[str]) -> str:
            return "\n\n".join(part for part in parts if part)

        tag_sets = [" ".join(hashtags), " ".join(hashtags[:2]), " ".join(hashtags[:1])]
        candidates = [(hook, summary, cta, tag_sets[0])]
        candidates += [(hook, summary, tags) for tags in tag_sets]
        candidates += [(hook, tags) for tags in tag_sets]
        for parts in candidates:
            text = join(*parts)
            if len(text) <= TWITTER_LIMIT:
                return text

        tag = hashtags[0] if hashtags else ""
        budget = TWITTER_LIMIT - (len(tag) + 2 if tag else 0)
        if budget < 100:  # an oversized tag must not crowd out the message
            tag, budget = "", TWITTER_LIMIT
        return join(self._truncate_words(hook, budget), tag)

    # ── Phase 5: Multi-Variation Synthesis & Output Packaging ───────────────
    def generate(self, directive: Dict[str, Any]) -> Dict[str, Any]:
        # `or` (not a .get default) so explicit nulls from callers fall back too.
        raw_topic = str(directive.get("topic") or "").strip()
        raw_keywords = directive.get("keywords") or []
        if isinstance(raw_keywords, str):
            raw_keywords = raw_keywords.split(",")
        platform = directive.get("platform") or "LinkedIn"
        goal = directive.get("goal") or "Marketing"
        tone = self.resolve_tone(directive.get("tone") or "Professional")
        lang = "ar" if directive.get("language") == "ar" else "en"

        # 1. Advanced Pre-processing & Typo Correction
        topic = self.normalize_and_clean_text(raw_topic, lang)
        keywords = [self.normalize_and_clean_text(str(k), lang) for k in raw_keywords if k and str(k).strip()]

        framework = self.resolve_framework(goal)
        hashtags = self.allocate_hashtags(keywords, topic, platform, lang)
        # Same text the hashtags were classified from, so metadata and hashtags agree.
        domain = self.detect_domain(f"{topic} {' '.join(keywords)}")

        variations_config = [
            {"id": 1, "type": ACTION},
            {"id": 2, "type": VALUE}
        ]

        variations_output = []
        previous_insight = None  # the two variations should not share their key sentence
        for v in variations_config:
            parts = self.generate_copy_sections(
                topic=topic,
                keywords=keywords,
                platform=platform,
                goal=goal,
                tone=tone,
                lang=lang,
                variation_type=v["type"],
                domain=domain,
                avoid_insight=previous_insight,
            )
            previous_insight = parts["summary"]
            full_caption = self.format_full_caption(
                hook=parts["hook"],
                body=parts["body"],
                cta=parts["cta"],
                hashtags=hashtags,
                platform=platform,
                lang=lang,
                summary=parts["summary"],
            )
            # X/Twitter may drop hashtags to fit the limit: report only the ones actually posted.
            posted = set(full_caption.split())
            variations_output.append({
                "version_id": v["id"],
                "type": v["type"],
                "hook": parts["hook"],
                "body": parts["body"],
                "call_to_action": parts["cta"],
                "full_caption": full_caption,
                "hashtags": [tag for tag in hashtags if tag in posted]
            })

        return {
            "agent_metadata": {
                "module": "Module 3 - AI Content Writer Agent (Enhanced NLG & Typo Engine)",
                "execution_mode": "Offline Rule-Based NLG",
                "framework": framework,
                "platform": platform,
                "language": lang,
                "tone": tone,
                "detected_domain": domain
            },
            "variations": variations_output
        }


# Global agent instance
content_agent = ContentWriterAgent()
