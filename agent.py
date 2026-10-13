"""
Module 3: AI Content Writer Agent
==================================
Academic AI Architecture: Goal-Based Agent (PEAS Framework)
Operation Mode: 100% Offline, Deterministic Rule-Based Natural Language Generation (NLG).
Zero External LLM APIs, Zero Cloud Latency, Zero Hallucinations.
"""

from typing import List, Dict, Any


class ContentWriterAgent:
    """
    Module 3 AI Content Writer Agent.
    Implements rule-based NLG, framework selection (AIDA, PAS, Story-Lesson-Question),
    platform syntactic calibration, bilingual template assembly (AR/EN),
    hashtag allocation quotas, and dual-variation synthesis.
    """

    HASHTAG_KB = {
        "en": {
            "productivity": [
                "#Productivity", "#TimeManagement", "#Focus", "#DeepWork",
                "#Efficiency", "#GrowthMindset", "#WorkSmart"
            ],
            "education": [
                "#StudentLife", "#StudyHacks", "#CollegeTips", "#HigherEd",
                "#AcademicSuccess", "#LearnSmart", "#StudyRoutine"
            ],
            "tech": [
                "#AppDesign", "#MobileApp", "#EdTech", "#SmartTools",
                "#DigitalTransformation", "#TechTrends", "#Innovation"
            ],
            "business": [
                "#Leadership", "#Strategy", "#Entrepreneurship", "#Startups",
                "#BusinessGrowth", "#ProfessionalDevelopment"
            ],
            "general": [
                "#LifeHacks", "#SelfImprovement", "#Motivation", "#Success",
                "#DailyHabits", "#GoalSetting"
            ]
        },
        "ar": {
            "productivity": [
                "#إنتاجية", "#تنظيم_الوقت", "#إدارة_الوقت", "#تطوير_الذات",
                "#إنجاز", "#تركيز", "#عمل_ذكي"
            ],
            "education": [
                "#حياة_الطلاب", "#نصائح_دراسية", "#جامعيون", "#دراسة_ذكية",
                "#تفوق_أكاديمي", "#طالب_جامعي", "#روتين_المذاكرة"
            ],
            "tech": [
                "#تطبيقات_ذكية", "#تقنية", "#حلول_رقمية", "#أدوات_العمل",
                "#ابتكار", "#تكنولوجيا", "#تحول_رقمي"
            ],
            "business": [
                "#ريادة_أعمال", "#قيادة", "#استراتيجية", "#أعمال",
                "#تطوير_مهني", "#مشاريع_ناشئة"
            ],
            "general": [
                "#نجاح", "#تطوير", "#خطط_يومية", "#تحفيز", "#طموح", "#عادات_يومية"
            ]
        }
    }

    # ── Phase 1: Reasoning Framework Selection ──────────────────────────────
    @staticmethod
    def resolve_framework(goal: str) -> str:
        goal_lower = goal.lower()
        if "market" in goal_lower or "launch" in goal_lower:
            return "AIDA"
        elif "educat" in goal_lower or "problem" in goal_lower:
            return "PAS"
        else:
            return "Story-Lesson-Question"

    # ── Phase 4: Categorical Hashtag Extraction & Quotas ────────────────────
    def allocate_hashtags(self, keywords: List[str], topic: str, platform: str, lang: str) -> List[str]:
        pool = []
        kb = self.HASHTAG_KB.get(lang, self.HASHTAG_KB["en"])

        # Topic & Keywords derived tags
        if topic:
            clean_topic = topic.strip().replace(" ", "_").replace("-", "_")
            if clean_topic:
                pool.append(f"#{clean_topic}")

        for kw in keywords:
            clean_kw = kw.strip().replace(" ", "_").replace("-", "_")
            if clean_kw:
                pool.append(f"#{clean_kw}")

        # Domain category matching
        combined_text = (topic + " " + " ".join(keywords)).lower()
        if any(w in combined_text for w in ["time", "manage", "productiv", "task", "وقت", "تنظيم", "إنتاج"]):
            pool.extend(kb["productivity"])
        if any(w in combined_text for w in ["student", "study", "college", "school", "طالب", "دراس", "جامع"]):
            pool.extend(kb["education"])
        if any(w in combined_text for w in ["app", "tech", "mobile", "software", "تطبيق", "تقني", "رقمي"]):
            pool.extend(kb["tech"])
        if any(w in combined_text for w in ["work", "business", "career", "مهن", "أعمال", "وظيفة"]):
            pool.extend(kb["business"])

        # Fallback pool
        pool.extend(kb["general"])

        # Deduplicate preserving order
        unique_tags = list(dict.fromkeys(pool))

        # Enforce platform quotas
        platform_normalized = platform.lower()
        if "instagram" in platform_normalized:
            quota = 10
        elif "twitter" in platform_normalized or "x" in platform_normalized:
            quota = 3
        elif "linkedin" in platform_normalized:
            quota = 4
        else:  # Facebook
            quota = 5

        return unique_tags[:quota]

    # ── Phase 2 & 3: Bilingual NLG Slot-Filling Engine ─────────────────────
    def generate_copy_sections(
        self,
        topic: str,
        keywords: List[str],
        platform: str,
        goal: str,
        tone: str,
        lang: str,
        variation_type: str
    ) -> Dict[str, str]:
        framework = self.resolve_framework(goal)
        kw_highlight = "، ".join(keywords[:3]) if lang == "ar" else ", ".join(keywords[:3])
        if not kw_highlight:
            kw_highlight = topic

        if lang == "ar":
            return self._build_arabic_copy(topic, kw_highlight, framework, platform, tone, variation_type)
        else:
            return self._build_english_copy(topic, kw_highlight, framework, platform, tone, variation_type)

    def _build_arabic_copy(
        self,
        topic: str,
        kw: str,
        framework: str,
        platform: str,
        tone: str,
        v_type: str
    ) -> Dict[str, str]:
        is_action = (v_type == "Action-driven")

        if framework == "AIDA":
            if is_action:
                hook = f"وداعاً لهدر الساعات: إليك الطريقة العملية للسيطرة على {topic} اليوم."
                body = (
                    f"معظمنا يفقد تركيزه بسبب تشتت المهام وغياب النظام الواضح ({kw}).\n\n"
                    f"الحل يكمن في خطوات محددة تصنع فارقاً فورياً:\n"
                    f"• تركيز مباشر على الأولويات اليومية دون تسويف\n"
                    f"• تنظيم ذكي يختصر نصف الوقت المستهلك\n"
                    f"• نظام تتبع يضمن إنجاز كل خطوة بنجاح"
                )
                cta = "ابدأ تطبيق هذا النظام الآن من الرابط المرفق واكتشف الفرق بنفسك."
            else:  # Value-driven
                hook = f"النجاح في {topic} لا يعتمد على المجهود المضاعف، بل على النظام الصحيح."
                body = (
                    f"عندما تواجه ضغط {kw}، فإن الحل ليس السهر لساعات أطول، بل بناء روتين ذكي.\n\n"
                    f"الوضوح الذهني وترتيب الأولويات هما السلاح الحقيقي للتفوق المستمر."
                )
                cta = "ما هي أكبر عقبة تواجهك في تطبيق هذا الروتين؟ شاركنا تجربتك في التعليقات."

        elif framework == "PAS":
            if is_action:
                hook = f"مشكلة شائعة: هل تشعر أن {topic} يستنزف طاقتك اليومية دون تقدم ملموس؟"
                body = (
                    f"تراكم المهام وتخبط ({kw}) يؤدي دائماً إلى الإرهاق وفقدان الحماس.\n\n"
                    f"لكن الحل أصبح في متناول يدك من خلال 3 خطوات واضحة:\n"
                    f"• تحديد 3 أولويات قصوى لكل يوم\n"
                    f"• استخدام أدوات تنظيم رقمية تمنع الفوضى\n"
                    f"• مراجعة الإنجاز أسبوعياً بثبات"
                )
                cta = "احفظ هذا المنشور وطبّق الخطوة الأولى فوراً لترى النتيجة اليوم."
            else:  # Value-driven
                hook = f"الحقيقة الصادمة حول صعوبات {topic} وكيف تتغلب عليها بوعي."
                body = (
                    f"الضغط الناجم عن ({kw}) ليس مشكلتك وحدك، بل نتيجة عادات غير منتظمة.\n\n"
                    f"تغيير بسيط في طريقة إدارتك ليومك يعيد لك راحة البال ويرفع جودة إنجازك بنسبة 200%."
                )
                cta = "برأيك، ما هي الخطوة الأهم للبدء من جديد؟ بانتظار رأيك أدناه."

        else:  # Story-Lesson-Question
            if is_action:
                hook = f"قصة واقعية: كيف تحول التحدي في {topic} إلى قصة إنجاز عملية؟"
                body = (
                    f"قبل شهور، كانت الفوضى في ({kw}) تحول دون تحقيق أي هدف حقيقي.\n\n"
                    f"الدرس المستفاد:\n"
                    f"النظام البسيط والصارم يتفوق دائماً على الحماس المؤقت."
                )
                cta = "ابدأ بوضع جدولك لليوم القادم الآن وشاركنا قرارك الأول."
            else:  # Value-driven
                hook = f"درس تعلمته بعد تجارب طويلة في عالم {topic}:"
                body = (
                    f"التركيز على الأساسيات وحل تحديات ({kw}) يبدأ بقرار التخلي عن العشوائية.\n\n"
                    f"كل دقيقة تقضيها في التخطيط توفر عليك عشرات الدقائق في التنفيذ."
                )
                cta = "كيف تتعامل مع هذه التحديات في روتينك؟ يسعدني الاستماع لتجربتك."

        return {"hook": hook, "body": body, "cta": cta}

    def _build_english_copy(
        self,
        topic: str,
        kw: str,
        framework: str,
        platform: str,
        tone: str,
        v_type: str
    ) -> Dict[str, str]:
        is_action = (v_type == "Action-driven")

        if framework == "AIDA":
            if is_action:
                hook = f"Stop wasting hours: Master {topic} with a system that actually works."
                body = (
                    f"Most people get overwhelmed managing {kw} because they rely on memory instead of systems.\n\n"
                    f"Here is how you fix it today:\n"
                    f"• Zero in on your top 3 daily priorities\n"
                    f"• Automate and streamline repetitive friction\n"
                    f"• Build a streak that turns consistency into results"
                )
                cta = "Take control right now — access the complete blueprint via the link."
            else:  # Value-driven
                hook = f"Mastering {topic} isn't about working harder; it's about removing friction."
                body = (
                    f"When you struggle with {kw}, discipline is rarely the culprit. Your system is.\n\n"
                    f"A deliberate routine protects your mental clarity and turns daily pressure into sustainable momentum."
                )
                cta = "What is the single biggest roadblock in your current routine? Let's discuss below."

        elif framework == "PAS":
            if is_action:
                hook = f"Are you feeling overwhelmed trying to stay on top of {topic}?"
                body = (
                    f"Ignoring the chaos in {kw} costs you precious hours, focus, and energy every single week.\n\n"
                    f"Here is your direct action plan:\n"
                    f"• Categorize tasks by true impact, not urgency\n"
                    f"• Dedicate distraction-free focus blocks\n"
                    f"• Review and iterate your workflow every Friday"
                )
                cta = "Bookmark this post and execute step one today."
            else:  # Value-driven
                hook = f"The hidden cost of unorganized routines in {topic}."
                body = (
                    f"The friction around {kw} isn't just about lost productivity — it creates constant background fatigue.\n\n"
                    f"When you adopt intentional frameworks, peace of mind and top-tier output naturally follow."
                )
                cta = "How do you protect your focus during high-pressure weeks? Drop your insights below."

        else:  # Story-Lesson-Question
            if is_action:
                hook = f"From burnout to breakthrough: A realistic approach to {topic}."
                body = (
                    f"Trying to balance {kw} without structure is an uphill battle.\n\n"
                    f"The key takeaway:\n"
                    f"Systems beat motivation every single time. Consistent tiny habits create massive results."
                )
                cta = "Set your top objective for tomorrow right now."
            else:  # Value-driven
                hook = f"The best lesson I learned about {topic} this year:"
                body = (
                    f"Clarifying your priorities around {kw} eliminates 80% of unnecessary stress.\n\n"
                    f"True productivity is not doing more things; it is doing the right things with intention."
                )
                cta = "What is one habit that completely changed the way you work?"

        return {"hook": hook, "body": body, "cta": cta}

    # ── Phase 2: Platform Formatting & Assembly ─────────────────────────────
    def format_full_caption(
        self,
        hook: str,
        body: str,
        cta: str,
        hashtags: List[str],
        platform: str,
        lang: str
    ) -> str:
        plat = platform.lower()
        tag_str = " ".join(hashtags)

        if "twitter" in plat or "x" in plat:
            # High-density brevity: Hook + brief CTA + tags
            return f"{hook}\n\n{cta}\n\n{tag_str}"

        elif "instagram" in plat:
            # Front-load hook above the fold, clean spacers, save/share CTA
            save_prompt = "📌 احفظ المنشور وشاركه مع زميلك" if lang == "ar" else "📌 Save this for later & share with a friend"
            return f"{hook} ✨\n.\n{body}\n.\n{save_prompt}\n{cta}\n.\n{tag_str}"

        elif "linkedin" in plat:
            # Double-spaced readability, max 2 emojis, professional line breaks
            return f"{hook}\n\n{body}\n\n{cta}\n\n{tag_str}"

        else:  # Facebook
            # Conversational community layout
            return f"{hook}\n\n{body}\n\n{cta}\n\n{tag_str}"

    # ── Phase 5: Multi-Variation Synthesis & Output Packaging ───────────────
    def generate(self, directive: Dict[str, Any]) -> Dict[str, Any]:
        topic = directive.get("topic", "").strip()
        keywords = directive.get("keywords", [])
        platform = directive.get("platform", "LinkedIn")
        goal = directive.get("goal", "Marketing")
        tone = directive.get("tone", "Professional")
        lang = directive.get("language", "en")

        framework = self.resolve_framework(goal)
        hashtags = self.allocate_hashtags(keywords, topic, platform, lang)

        variations_config = [
            {"id": 1, "type": "Action-driven"},
            {"id": 2, "type": "Value-driven"}
        ]

        variations_output = []
        for v in variations_config:
            parts = self.generate_copy_sections(
                topic=topic,
                keywords=keywords,
                platform=platform,
                goal=goal,
                tone=tone,
                lang=lang,
                variation_type=v["type"]
            )
            full_caption = self.format_full_caption(
                hook=parts["hook"],
                body=parts["body"],
                cta=parts["cta"],
                hashtags=hashtags,
                platform=platform,
                lang=lang
            )
            variations_output.append({
                "version_id": v["id"],
                "type": v["type"],
                "hook": parts["hook"],
                "body": parts["body"],
                "call_to_action": parts["cta"],
                "full_caption": full_caption,
                "hashtags": hashtags
            })

        return {
            "agent_metadata": {
                "module": "Module 3 - AI Content Writer Agent",
                "execution_mode": "Offline Rule-Based NLG",
                "framework": framework,
                "platform": platform,
                "language": lang,
                "tone": tone
            },
            "variations": variations_output
        }


# Global agent instance
content_agent = ContentWriterAgent()
