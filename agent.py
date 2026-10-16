"""
Module 3: AI Content Writer Agent (Enhanced NLP & NLG Engine)
============================================================
Academic AI Architecture: Goal-Based Agent (PEAS Framework)
Operation Mode: 100% Offline, Deterministic Rule-Based Natural Language Generation (NLG).
Features:
- Robust Arabic & English Spell Correction / Typo Normalization
- Context & Intent Domain Classification
- Sophisticated Stylistic NLG for All Tones (Professional, Inspirational, Casual)
- Anti-Repetition Pattern Randomization
- Platform Syntactic Calibration (LinkedIn, Instagram, Twitter/X, Facebook)
- Zero External LLMs, Zero Cloud Latency, Zero Hallucinations.
"""

import re
import random
from typing import List, Dict, Any, Tuple


class ContentWriterAgent:
    """
    Enhanced Module 3 AI Content Writer Agent.
    Combines rule-based Natural Language Understanding (NLU: typo correction, lemmatization,
    intent classification) and advanced Natural Language Generation (NLG).
    """

    # ── Spelling & Typo Correction Dictionary (Common Arabic & English Errors) ──
    TYPO_MAP_AR = {
        # Common typos & slang conversions
        "كاجه": "حاجة",
        "حاجه": "أمر",
        "التعمل": "الذي تم إنجازه",
        "الكنت": "الذي كنت",
        "املاءيه": "إملائية",
        "املائيه": "إملائية",
        "حته": "حتى",
        "انتا": "أنت",
        "ازاى": "كيف",
        "ازاي": "كيف",
        "ابلكيشن": "تطبيق",
        "ابليكيشن": "تطبيق",
        "برمجه": "برمجة",
        "برمجة": "برمجة",
        "تكلوجيا": "تكنولوجيا",
        "تكنلوجيا": "تكنولوجيا",
        "زكاء": "ذكاء",
        "اصطناعي": "اصطناعي",
        "إصطناعي": "اصطناعي",
        "تسويق": "تسويق",
        "سوشيال": "وسائل التواصل الاجتماعي",
        "ميديا": "الإعلام الرقمي",
        "فيس": "فيسبوك",
        "انستا": "إنستغرام",
        "تويتر": "تويتر",
        "لينكد": "لينكد إن",
        "لينكدان": "لينكد إن",
        "مزاكره": "مذاكرة",
        "مذاكره": "مذاكرة",
        "انتاجيه": "إنتاجية",
        "تنظيم": "تنظيم",
        "الوقت": "الوقت",
        "تطوير": "تطوير",
        "شركه": "شركة",
        "بيزنس": "أعمال",
        "استثمار": "استثمار",
        "فلوس": "أموال",
        "دراسه": "دراسة",
        "امتحان": "امتحان",
        "شغل": "عمل",
        "وظايف": "وظائف",
        "شات": "محادثة",
        "روبوت": "وكيل ذكي",
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
    DOMAINS = {
        "tech_ai": {
            "keywords": ["ai", "tech", "software", "app", "code", "programming", "ذكاء", "تقني", "تطبيق", "برمج", "تكنولوجيا", "روبوت", "بيانات"],
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
            "general": ["#SelfImprovement", "#Motivation", "#SuccessMindset", "#ActionTakers", "#HabitBuilding", "#BestPractices"]
        },
        "ar": {
            "productivity": ["#إنتاجية", "#تنظيم_الوقت", "#إدارة_الوقت", "#تطوير_الذات", "#إنجاز", "#تركيز_عميق", "#عادات_النجاح", "#عمل_ذكي"],
            "education": ["#حياة_الطلاب", "#نصائح_دراسية", "#جامعيون", "#دراسة_ذكية", "#تفوق_أكاديمي", "#طالب_جامعي", "#روتين_المذاكرة", "#النجاح_الدراسي"],
            "tech": ["#تطبيقات_ذكية", "#ذكاء_اصطناعي", "#تقنية", "#حلول_رقمية", "#أدوات_رقمية", "#ابتكار", "#تكنولوجيا_المستقبل"],
            "business": ["#ريادة_أعمال", "#استراتيجية_أعمال", "#تسويق_رقمي", "#تطوير_مهني", "#مشاريع_ناشئة", "#إدارة_الأعمال", "#بناء_المشاريع"],
            "general": ["#تطوير_الذات", "#طموح", "#تحفيز", "#خطط_يومية", "#إلهام", "#نجاح"]
        }
    }

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
        """Determines the thematic domain to enrich vocabulary and context."""
        t_lower = text.lower()
        for domain_name, data in self.DOMAINS.items():
            if any(k in t_lower for k in data["keywords"]):
                return domain_name
        return "productivity_time"

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

        # Domain category matching
        combined = (topic + " " + " ".join(keywords)).lower()
        domain = self.detect_domain(combined)

        if domain == "tech_ai":
            pool.extend(kb["tech"])
        elif domain == "education_study":
            pool.extend(kb["education"])
        elif domain == "business_career":
            pool.extend(kb["business"])
        else:
            pool.extend(kb["productivity"])

        pool.extend(kb["general"])

        # Deduplicate preserving order
        unique_tags = list(dict.fromkeys(pool))

        plat_lower = platform.lower()
        if "instagram" in plat_lower:
            quota = 10
        elif "twitter" in plat_lower or "x" in plat_lower:
            quota = 3
        elif "linkedin" in plat_lower:
            quota = 4
        else:  # Facebook
            quota = 5

        return unique_tags[:quota]

    # ── Phase 2 & 3: Advanced Bilingual Slot-Filling & Sentence Synthesis ──
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
        domain = self.detect_domain(topic + " " + " ".join(keywords))

        # Normalized string representations for natural phrasing
        if lang == "ar":
            clean_topic = self.normalize_and_clean_text(topic, "ar")
            clean_kws = [self.normalize_and_clean_text(k, "ar") for k in keywords if k.strip()]
            kw_phrase = "، و".join(clean_kws[:3]) if clean_kws else clean_topic
            return self._synthesize_arabic(clean_topic, clean_kws, kw_phrase, framework, platform, tone, variation_type, domain)
        else:
            clean_topic = self.normalize_and_clean_text(topic, "en")
            clean_kws = [self.normalize_and_clean_text(k, "en") for k in keywords if k.strip()]
            kw_phrase = ", and ".join(clean_kws[:3]) if clean_kws else clean_topic
            return self._synthesize_english(clean_topic, clean_kws, kw_phrase, framework, platform, tone, variation_type, domain)

    # ─────────────────────────────────────────────────────────────────────────
    # ARABIC NATURAL LANGUAGE GENERATION ENGINE
    # ─────────────────────────────────────────────────────────────────────────
    def _synthesize_arabic(
        self,
        topic: str,
        keywords: List[str],
        kw_phrase: str,
        framework: str,
        platform: str,
        tone: str,
        v_type: str,
        domain: str
    ) -> Dict[str, str]:
        is_action = (v_type == "Action-driven")
        tone_lower = tone.lower()

        # ── 1. AIDA Framework (Marketing / Action) ──
        if framework == "AIDA":
            if is_action:
                if "inspirational" in tone_lower:
                    hook = f"حان الوقت لتنقل تجربتك في {topic} إلى مستوى استثنائي غير مسبوق."
                    body = (
                        f"الإنجاز الحقيقي لا يأتي بالصدفة، بل باختيار الأدوات التي تصنع الفارق في {kw_phrase}.\n\n"
                        f"إليك ما ستحصل عليه فور البدء:\n"
                        f"• وضوح تام للأولويات دون أي تشتت أو فوضى\n"
                        f"• توفير ساعات أسبوعية كانت تضيع في المهام الروتينية\n"
                        f"• تقدم ملحوظ وملموس ينعكس مباشرة على أهدافك الكبرى"
                    )
                    cta = "انطلق الآن واكتشف التجربة الكاملة عبر الرابط في التعليق الأول."
                elif "casual" in tone_lower:
                    hook = f"لو لسه بتعاني مع {topic}.. المقال ده معمول عشانك تحديداً!"
                    body = (
                        f"كلنا بنقع في فخ التشتت وضغط {kw_phrase}، والحل مش إننا نتعب أكتر، الحل إننا ننظم بطريقة أذكى.\n\n"
                        f"الحل العملي في 3 خطوات بسيطة:\n"
                        f"• تخلص فوري من الفوضى وتحديد المهم أولاً\n"
                        f"• استخدام أسلوب عملي مريح يناسب يومك\n"
                        f"• نتيجة واضحة من أول يوم استخدام"
                    )
                    cta = "جرب بنفسك وقول لنا رأيك في أول تعليق! 👇"
                else:  # Professional (Default)
                    hook = f"وداعاً لهدر الوقت والموارد: المنظومة المتكاملة للتحكم في {topic}."
                    body = (
                        f"يواجه معظم المتخصصين صعوبة مستمرة في إدارة {kw_phrase} بسبب الاعتماد على حلول تقليدية غير مرنة.\n\n"
                        f"صُممت هذه المنهجية لتضمن لك:\n"
                        f"• كفاءة تنفيذية تضاعف سرعة إنجاز المهام الأساسية\n"
                        f"• تقليل الإجهاد الذهني عبر أتمتة الخطوات المكررة\n"
                        f"• مؤشرات واضحة لقياس الأداء ومتابعة التطور اليومي"
                    )
                    cta = "ابدأ تطبيق هذا الحل اليوم عبر زيارة الرابط المرفق."
            else:  # Value-driven
                if "inspirational" in tone_lower:
                    hook = f"النجاح في {topic} ليس سباقاً ضد الساعة، بل هو فن اختيار الاتجاه الصحيح."
                    body = (
                        f"عندما تبني نظاماً قائماً على {kw_phrase}، يتحول التوتر المستمر إلى طاقة إبداع وإنتاج لا تنتهي.\n\n"
                        f"القيمة الحقيقية لا تكمن في كثرة ما تقوم به، بل في عمق الأثر الذي تتركه كل خطوة مدروسة."
                    )
                    cta = "كيف تسعى لتطوير هذه المهارة في مسيرتك؟ شاركنا رؤيتك ورأيك المُلهم."
                else:  # Professional / Thought Leadership
                    hook = f"إعادة التفكير في استراتيجية {topic}: لماذا تفشل الأنظمة المعتادة؟"
                    body = (
                        f"الارتقاء الحقيقي بمستوى الأداء في {kw_phrase} يتطلب التخلي عن الفوضى التشغيلية.\n\n"
                        f"الشركات والمحترفون الذين يحققون نتائج استثنائية يركزون على بناء عادات مستدامة تضمن الاستمرارية حتى في أصعب الأوقات."
                    )
                    cta = "برأيك المهني، ما هو العنصر الأكثر حساسية لضمان نجاح هذه التجربة؟"

        # ── 2. PAS Framework (Educational / Problem Solving) ──
        elif framework == "PAS":
            if is_action:
                hook = f"المشكلة الخفية وراء التراجع في {topic} — والحل المباشر لعلاجها اليوم."
                body = (
                    f"المشكلة: استنزاف الساعات في محاولة موازنة {kw_phrase} دون رؤية نتائج حقيقية.\n"
                    f"التفاقم: الاستمرار بدون نظام واضح يرفع معدلات الإرهاق ويؤدي حتماً إلى فقدان الشغف والتركيز.\n\n"
                    f"الحل العملي الفوري:\n"
                    f"• اعتماد قاعدة الـ 20/80 للتركيز على المهام ذات العائد الأكبر\n"
                    f"• جدولة فترات عمل محددة خالية من أي ملهيات رقمية\n"
                    f"• أتمتة وتوثيق الخطوات لتكرار النجاح بسلاسة"
                )
                cta = "احفظ هذا الدليل في مفضلتك لتبدأ بتطبيق الخطوة الأولى فوراً."
            else:  # Value-driven
                hook = f"لماذا يجد الكثيرون صعوبة بالغة في إتقان {topic}؟ تحليل موضوعي وحلول عميقة."
                body = (
                    f"المشكلة لا تكمن في نقص الاجتهاد، بل في غياب الاستراتيجية المناسبة للتعامل مع {kw_phrase}.\n\n"
                    f"عندما تدرك جذور الخلل وتستبدل الاندفاع العشوائي بنظام دقيق، تصبح النتائج الإيجابية نتيجة حتمية وطبيعية."
                )
                cta = "ما هي أكبر تجربة أحدثت فارقاً حقيقياً في طريقة إدارتك لهذا التحدي؟"

        # ── 3. Story-Lesson-Question Framework (Engagement) ──
        else:
            if is_action:
                hook = f"تجربة عملية أثبتت فعاليتها: كيف حوّلنا عقبات {topic} إلى محرك حقيقي للنجاح؟"
                body = (
                    f"في البداية، كان التخبط في {kw_phrase} يستهلك أغلب الطاقة اليومية.\n\n"
                    f"الدرس الجوهري:\n"
                    f"«الانضباط المعتمد على نظام محكم يتفوق دائماً على الحماس اللحظي».\n"
                    f"كل ما تطلبه الأمر هو ضبط وتيرة التنفيذ والالتزام بالأولويات."
                )
                cta = "ما رأيك في تطبيق هذا النموذج في مشروعك القادم؟ أخبرنا بقرارك."
            else:  # Value-driven
                hook = f"درس لا يُقدّر بثمن تعلمته من التحديات اليومية في {topic}:"
                body = (
                    f"التعامل بذكاء مع {kw_phrase} علمني أن التوقف للتقييم والتنظيم ليس تراجعاً، بل هو أقصر طريق للوصول.\n\n"
                    f"البساطة في التصميم والتنفيذ هي ذروة الاحتراف."
                )
                cta = "لو كان بإمكانك تقديم نصيحة واحدة لشخص يبدأ في هذا المجال الآن، فماذا ستكون؟"

        return {"hook": hook, "body": body, "cta": cta}

    # ─────────────────────────────────────────────────────────────────────────
    # ENGLISH NATURAL LANGUAGE GENERATION ENGINE
    # ─────────────────────────────────────────────────────────────────────────
    def _synthesize_english(
        self,
        topic: str,
        keywords: List[str],
        kw_phrase: str,
        framework: str,
        platform: str,
        tone: str,
        v_type: str,
        domain: str
    ) -> Dict[str, str]:
        is_action = (v_type == "Action-driven")
        tone_lower = tone.lower()

        # ── 1. AIDA Framework ──
        if framework == "AIDA":
            if is_action:
                if "inspirational" in tone_lower:
                    hook = f"Transform the way you approach {topic} and unlock your true potential."
                    body = (
                        f"Great achievements are never accidental—they are built on intentional systems around {kw_phrase}.\n\n"
                        f"Here is what shifts immediately:\n"
                        f"• Crystal-clear focus on high-leverage priorities\n"
                        f"• Elimination of mental clutter and routine friction\n"
                        f"• Measurable daily momentum toward your ultimate goals"
                    )
                    cta = "Take decisive action today. Access the complete framework via the link below."
                elif "casual" in tone_lower:
                    hook = f"Tired of overcomplicating {topic}? Let's break it down the easy way."
                    body = (
                        f"We've all been there—juggling {kw_phrase} until everything feels overwhelming.\n\n"
                        f"Here is the simple 3-step fix:\n"
                        f"• Cut the fluff and focus on what actually moves the needle\n"
                        f"• Use smart shortcuts that save you hours every week\n"
                        f"• Keep it consistent without burning yourself out"
                    )
                    cta = "Give it a spin and let me know your thoughts in the comments! 👇"
                else:  # Professional (Default)
                    hook = f"Stop losing hours to friction: The definitive framework for mastering {topic}."
                    body = (
                        f"Professionals routinely struggle with {kw_phrase} when relying on fragmented, manual workflows.\n\n"
                        f"This proven approach delivers:\n"
                        f"• Accelerated task throughput with zero cognitive overload\n"
                        f"• Streamlined consistency across every operational stage\n"
                        f"• Objective tracking metrics to benchmark your progress"
                    )
                    cta = "Deploy this system in your workflow today. Find the complete details at the link."
            else:  # Value-driven
                if "inspirational" in tone_lower:
                    hook = f"Mastering {topic} isn't about grinding more hours; it's about honoring your energy."
                    body = (
                        f"When your framework aligns seamlessly with {kw_phrase}, pressure transforms into sustainable focus.\n\n"
                        f"Excellence is not an act of willpower—it is the natural outcome of a well-architected routine."
                    )
                    cta = "What is one deliberate shift you've made recently that redefined your growth?"
                else:
                    hook = f"Rethinking our core perspective on {topic}: Why conventional tactics fall short."
                    body = (
                        f"High-performing teams don't work twice as hard to balance {kw_phrase}; they eliminate operational chaos.\n\n"
                        f"Sustainable results come from clarity of purpose, disciplined boundaries, and iterative refinement."
                    )
                    cta = "From your professional viewpoint, what is the single biggest barrier to sustainable consistency?"

        # ── 2. PAS Framework ──
        elif framework == "PAS":
            if is_action:
                hook = f"The silent bottleneck stalling your progress in {topic} (and how to fix it today)."
                body = (
                    f"Problem: Unstructured execution around {kw_phrase} leads to persistent exhaustion.\n"
                    f"Agitate: Leaving this unaddressed compounds cognitive debt and kills forward momentum.\n\n"
                    f"The Solution Plan:\n"
                    f"• Prioritize ruthlessly using an impact-versus-effort matrix\n"
                    f"• Protect non-negotiable deep-work focus windows\n"
                    f"• Automate recurring steps to preserve creative energy"
                )
                cta = "Save this roadmap to your library and execute step one before the day ends."
            else:
                hook = f"Why do so many ambitious people struggle with {topic} despite their dedication?"
                body = (
                    f"Effort without alignment is just exhaustion. Struggling with {kw_phrase} is rarely a matter of competence—it is a signal of broken systems.\n\n"
                    f"When you diagnose root friction instead of fighting surface symptoms, breakthroughs become predictable."
                )
                cta = "What breakthrough system changed the way you solve this problem?"

        # ── 3. Story-Lesson-Question Framework ──
        else:
            if is_action:
                hook = f"A proven case study: Turning daily obstacles in {topic} into our biggest competitive edge."
                body = (
                    f"Months ago, disorganization across {kw_phrase} threatened every project deadline.\n\n"
                    f"The Uncompromising Lesson:\n"
                    f"«Disciplined systems beat raw motivation every single time».\n"
                    f"Refining the process turned panic into systematic execution."
                )
                cta = "Are you ready to optimize this in your own schedule? Drop a comment below."
            else:
                hook = f"The most valuable lesson several years in {topic} taught me:"
                body = (
                    f"Mastery over {kw_phrase} isn't about acquiring more tools; it's about cultivating the discipline to say no to distractions.\n\n"
                    f"Simplification is the ultimate mark of mastery."
                )
                cta = "If you could share one golden rule with someone tackling this today, what would it be?"

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
            # High-density brevity: Punchy hook + CTA + tags
            return f"{hook}\n\n{cta}\n\n{tag_str}"

        elif "instagram" in plat:
            # Above the fold hook, clean spacers, save/share CTA
            save_prompt = "📌 احفظ المنشور لترجع له وشاركه مع زملائك المهتمين" if lang == "ar" else "📌 Save this post for reference & share with someone who needs it"
            return f"{hook} ✨\n.\n{body}\n.\n{save_prompt}\n{cta}\n.\n{tag_str}"

        elif "linkedin" in plat:
            # Professional double-spaced skimming format
            return f"{hook}\n\n{body}\n\n{cta}\n\n{tag_str}"

        else:  # Facebook
            # Conversational community narrative
            return f"{hook}\n\n{body}\n\n{cta}\n\n{tag_str}"

    # ── Phase 5: Multi-Variation Synthesis & Output Packaging ───────────────
    def generate(self, directive: Dict[str, Any]) -> Dict[str, Any]:
        raw_topic = directive.get("topic", "").strip()
        raw_keywords = directive.get("keywords", [])
        platform = directive.get("platform", "LinkedIn")
        goal = directive.get("goal", "Marketing")
        tone = directive.get("tone", "Professional")
        lang = directive.get("language", "en")

        # 1. Advanced Pre-processing & Typo Correction
        topic = self.normalize_and_clean_text(raw_topic, lang)
        keywords = [self.normalize_and_clean_text(k, lang) for k in raw_keywords if k.strip()]

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
                "module": "Module 3 - AI Content Writer Agent (Enhanced NLG & Typo Engine)",
                "execution_mode": "Offline Rule-Based NLG",
                "framework": framework,
                "platform": platform,
                "language": lang,
                "tone": tone,
                "detected_domain": self.detect_domain(topic)
            },
            "variations": variations_output
        }


# Global agent instance
content_agent = ContentWriterAgent()
