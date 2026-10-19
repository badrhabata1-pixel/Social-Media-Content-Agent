# تقرير تسليم المشروع: Social Media Content Agent

> **تاريخ الفحص:** 2026-10-19 · **الفرع:** `main` · **آخر commit:** `e9f4733`
> كل ما في هذا التقرير تم التحقق منه بتشغيل الكود فعليًا (اختبارات، طلبات HTTP عبر `TestClient`، وسكربت فحص سلوك)، إلا ما هو مذكور صراحةً أنه لم يُختبر.

> **تحديث، المرحلة 1 (إصلاحات الاستقرار)، 2026-10-19، لسه مالهاش commit:**
>
> **اللي اتحل:**
> - **ملف الاختبارات المكسور** (§5، رقم 2) اتمسح، واتعمل بداله [tests/test_content_agent.py](tests/test_content_agent.py) (42 اختبار).
> - **`"keywords": null`** (§5، رقم 6) بقى بيرجّع 200 بدل 500.
> - **التحقق من المدخلات في `/generate`** (§5، رقم 7) بقى موجود:
>   - `DirectiveRequest` بقى بيستخدم `Literal` للمنصة والهدف والنبرة واللغة.
>   - الموضوع بيتشال منه المسافات، وطوله من 1 لـ 500.
>   - الكلمات المفتاحية الفاضية بتتشال.
>   - أي قيمة غلط بترجع 422.
> - **تحذيرات Pydantic** (§5، رقم 20) اختفت، بعد ما `example=` اتغيّرت لـ `json_schema_extra`.
> - **كشف المجال** (§5، رقم 10) بقى بيطابق على حدود الكلمة:
>   - عن طريق دالة واحدة `keyword_in()` في `agent.py`، و`prompt_builder.py` بيستخدمها هي كمان.
>   - `detected_domain` بقى بيتحسب من الموضوع والكلمات المفتاحية، زي الهاشتاجات بالظبط.
>
> **النتيجة:** `python -m pytest` بيطلع 69 passed، من غير أخطاء ولا تحذيرات.

> **تحديث، المرحلة 2 (إعادة بناء محرك الكتابة)، 2026-10-19، لسه مالهاش commit:**
>
> **محرك القوالب في `agent.py` اتبنى من جديد:**
> - بقى بيركّب المنشور من أجزاء موجودة في `COPY_BANK` و`BODY_LAYOUTS`:
>   - **الـ hook:** بيتحدد بالإطار ونوع النسخة والنبرة، وفيه 3 صيغ لكل حالة.
>   - **هيكل الـ body:** بيتحدد بالإطار ونوع النسخة.
>   - **جُمل الربط:** بتتحدد بالنبرة.
>   - **مفردات المجال:** لخمس مجالات، منها `general`.
>   - **الـ CTA:** سؤال أو خطوة.
> - `_synthesize_arabic` و`_synthesize_english` اتشالوا، وحلّت محلهم دالة واحدة `_synthesize()`.
>
> **اللي اتحل من §5:**
> - **رقم 8:** القوالب مفيهاش ادعاءات مختلقة ولا روابط ولا أرقام.
> - **رقم 9:** النص بقى بيتكيّف مع المجال، والمواضيع اللي مالهاش مجال بقت `general`، بنص وهاشتاجات محايدة.
> - **رقم 11:** Regenerate بقى بيطلع صياغة جديدة كل مرة، عن طريق `random.Random(seed)`.
> - **رقم 12:** النبرة بقت بتأثر في كل الأطر.
> - **رقم 13:** تويتر مابيعدّيش 280 حرف أبدًا. بيشيل الـ CTA الأول، بعدها الهاشتاجات الثانوية، وفي الآخر بيقص الـ hook عند نهاية كلمة.
> - **رقم 14:** `TYPO_MAP_AR` بقى بيصحح الإملاء بس.
> - **رقم 15:** إزالة الهاشتاجات المكررة بقت من غير حساسية لحالة الأحرف.
> - **رقم 16:** الـ Casual العربي بقى فصحى مبسطة بدل العامية.
> - **رقم 18:** الكلمات المفتاحية المبعوتة كنص بقت بتتقسم صح.
> - **رقم 19:** `"funny"` بقت بتتحول لـ Casual.
> - **الكلمات القصيرة:** أي كلمة 3 حروف أو أقل لازم تتطابق ككلمة كاملة (`app` و`apps`)، و`application` اتضافت لمجال `tech_ai`.
>
> **النتيجة:** `python -m pytest` بيطلع 136 passed.
>
> **لسه موجود:** بنود الواجهة (§5، من 27 لـ 34)، وإن Regenerate في الواجهة بيمسح الصورة اللي اتولدت (`key={generationId}`)، وهاشتاج الموضوع الطويل (زي `#tools_small`).

> **تحديث، Module 5 (النشر على فيسبوك والمقاييس)، 2026-10-19، لسه مالهاش commit:**
>
> **الملفات الجديدة:**
> - [social_integrations/facebook_service.py](social_integrations/facebook_service.py)، فيه `FacebookService` بالدوال:
>   - `publish_text_post`
>   - `publish_photo_post`
>   - `get_post_metrics`
>   - `inspect_token`
> - مسارات جديدة في `app.py`: `POST /publish/facebook` و`GET /metrics/facebook/{post_id}`.
> - سكربت حي: [scripts/test_facebook_live.py](scripts/test_facebook_live.py).
> - 40 اختبار في [tests/test_facebook_service.py](tests/test_facebook_service.py)، كلها بشبكة مزيّفة.
>
> **الإعدادات:** `FACEBOOK_PAGE_ID` و`FACEBOOK_PAGE_ACCESS_TOKEN` في `.env`، والملف ده متجاهَل في git.
>
> **حالة النشر الحي:** مانجحش.
> - التوكن تبع صفحة ID بتاعها `1443854245469364`، مش `61595326210901`.
> - التوكن مفيهوش `pages_manage_posts` ولا `pages_read_engagement`.
> - التوكن بينتهي 2026-10-19 21:00 UTC.
>
> **النتيجة:** `python -m pytest` بيطلع 176 passed.

> **تحديث، المرحلة 4 (قاعدة البيانات والتحليلات ولوحة الواجهة)، 2026-10-20، لسه مالهاش commit:**
>
> **الباك اند:**
> - **`analytics/db.py`:** الكلاس `PostsDatabase` بيتعامل مع جدول `posts_log` في SQLite، والملف بيتحفظ في `data/analytics.db` أو في المسار المحدد في `ANALYTICS_DB_PATH`.
> - **`analytics/engine.py`:** الكلاس `AnalyticsEngine`:
>   - `sync_all_metrics()` بتجيب المقاييس من فيسبوك.
>   - `generate_comparative_report()` بتقارن حسب المجال والموضوع والنبرة، بمعادلة `score = reactions + 2×comments + 3×shares`.
> - **التسجيل:** `POST /publish/facebook` بقى بيسجّل المنشور في القاعدة، ومعاه `topic` و`domain` و`tone` اختياري.
> - **مسارات جديدة:** `POST /analytics/sync` و`GET /analytics/report`.
>
> **الفرونت:**
> - `recharts@3.10.1`.
> - `components/AnalyticsDashboard.jsx` في تبويب "Analytics Dashboard"، وبيتحمّل لما التبويب يتفتح بس.
>
> **ناقص:**
> - الواجهة مفيهاش زرار نشر على فيسبوك، فالقاعدة بتتملا من الـ API بس.
> - عنصر "Analytics" في الـ Sidebar مش متوصل بالتبويب.
>
> **النتيجة:** `python -m pytest` بيطلع 209 passed.

---

## 0. الخلاصة السريعة (اقرأ هذا أولًا)

- **ما هو المشروع:** نظام يولّد منشورات سوشيال ميديا (نص وصورة). الـ Backend مبني بـ FastAPI على Python 3.13، والـ Frontend بـ React 19 وVite 8.
- **فيه وحدتان شغالتان:**
  - **Module 3، كاتب المحتوى:** [agent.py](agent.py)، الكلاس `ContentWriterAgent`. بيكتب النص من قوالب ثابتة، ومن غير أي API أو LLM خارجي.
  - **Module 4، توليد الصور:** [image_generation/](image_generation/). بيبني prompt للصورة، ولو فيه `GEMINI_API_KEY` بيستدعي Gemini عن طريق `google-genai`. من غير المفتاح بيرجّع الـ prompt ودليل تصميم بس (`mode: "prompt_only"`).
- **قاعدة البيانات:** مفيش. النص بيتعالج في الذاكرة ومش بيتخزن، والصور بتتحفظ كملفات في `generated_images/`.
- **أخطر المشاكل الحالية:**
  1. `python -m pytest` من غير معاملات بيتوقف بالكامل، بسبب ملف اختبارات قديم مش متتبَّع في git: `tests/test_module3_agent.py` (§5، رقم 2).
  2. `POST /generate` مع `"keywords": null` بيرجّع **500 Internal Server Error** (§5، رقم 3).
  3. `/generate` مفيهوش تحقق من المدخلات: بيقبل موضوع فاضي ومنصة أو لغة أو نبرة غير مدعومة (§5، رقم 4).
  4. القوالب فيها ادعاءات مختلقة، زي "Months ago" و"A proven case study" و"قاعدة الـ 20/80" و"الرابط المرفق". ومحتوى القوالب كله عن الإنتاجية أيًا كان الموضوع (§5، رقم 5 و6).
  5. زرار **Regenerate بيرجّع نفس النص حرفيًا**، وكمان بيمسح الصورة اللي اتولّدت (§5، رقم 7).
- **مكتبة `google-genai` كانت ناقصة في `venv`**، فكان `uvicorn app:app` بيقع وقت الاستيراد. ثبّتها أثناء الفحص (الإصدار 2.31.0). أي حد تاني لازم يشغّل `pip install -r requirements.txt`.

---

## 1. نظرة عامة وهيكل المشروع

### 1.1 التقنيات والمكتبات

**Backend** (البيئة: `venv/`):

| المكتبة | الإصدار المثبت | الاستخدام |
|---|---|---|
| Python | 3.13.2 | |
| fastapi | 0.142.4 | الـ API ([app.py](app.py) و[image_generation/router.py](image_generation/router.py)) |
| starlette | 1.7.0 | جزء من FastAPI (CORS و`FileResponse`) |
| pydantic | 2.13.5 | نماذج الطلبات (`DirectiveRequest` و`ImageDirective`) |
| uvicorn[standard] | 0.54.0 | السيرفر |
| python-dotenv | 1.2.4 | تحميل `.env` في [nano_banana.py](image_generation/nano_banana.py) |
| google-genai | 2.31.0 | Gemini لتوليد الصور (Module 4 بس) |
| pytest | 9.1.1 | الاختبارات |

- **موجودة في [requirements.txt](requirements.txt) لكن مش مستخدمة في أي ملف:** `streamlit` و`langchain` و`google-generativeai` (الـ SDK القديم).
- **الإصدارات مش مثبّتة (unpinned)،** والملف مفيهوش سطر جديد في آخره.

**Frontend** ([frontend/package.json](frontend/package.json)، مع Node 22.17.1 وnpm 10.9.2):

| المكتبة | الإصدار | ملاحظات |
|---|---|---|
| react / react-dom | 19.3.0 | |
| vite | 8.3.3 | مع `@vitejs/plugin-react` 6.1.2، ومفيش proxy في [vite.config.js](frontend/vite.config.js) |
| lucide-react | 1.56.0 | الأيقونات، وهي المكتبة الوحيدة وقت التشغيل غير React |
| eslint | 10.x | flat config مع `react-hooks` و`react-refresh` |

- **مفيش Tailwind ولا React Router ولا axios ولا مكتبة لإدارة الحالة.**
- **التنسيق** CSS عادي: [App.css](frontend/src/App.css) (626 سطر، ثيم بنفسجي "Plansova" بمتغيرات CSS) و[ImagePanel.css](frontend/src/components/ImagePanel.css).
- **الخط** Inter من Google Fonts، ومحمّل في [index.html](frontend/index.html).

### 1.2 شجرة الملفات (من غير `venv` و`node_modules` و`dist`)

```
SocialMediaAgent/
├── app.py                        # تطبيق FastAPI: /generate و/generate-legacy و/health، وبيضم راوتر الصور
├── agent.py                      # Module 3: الكلاس ContentWriterAgent والكائن الجاهز content_agent
├── image_generation/             # Module 4
│   ├── __init__.py               # بيصدّر router
│   ├── router.py                 # ImageDirective والمسارات /generate-image و/image-service/status و/images/{filename}
│   ├── service.py                # ImageGenerationService: الخطة، التوليد، حفظ الصورة وملف JSON جنبها
│   ├── prompt_builder.py         # build_image_plan(): بيبني الـ prompt وImagePlan (التوجيه البصري)
│   └── nano_banana.py            # NanoBananaClient: عميل Gemini بموديلات بديلة وترجمة رسائل الأخطاء
├── tests/
│   ├── test_image_generation.py  # 27 اختبار لـ Module 4، متتبَّع في git وكلهم بينجحوا
│   └── test_module3_agent.py     # غير متتبَّع، قديم ومكسور (§5، رقم 2)
├── pytest.ini                    # pythonpath = . و testpaths = tests
├── requirements.txt
├── .env.example                  # GEMINI_API_KEY، وIMAGE_MODEL اختياري
├── .env                          # موجود بس فاضي (0 بايت)، ومش متتبَّع
├── .gitignore                    # venv و__pycache__ و.env و*.db وgenerated_images/ و.pytest_cache وnode_modules وdist
├── package-lock.json             # ملف فاضي متبقي في الجذر من غير package.json، مش مستخدم
├── generated_images/             # بيتعمل تلقائيًا مع أول صورة، ومش موجود دلوقتي
└── frontend/
    ├── index.html                # العنوان والخط
    ├── vite.config.js
    ├── eslint.config.js
    ├── package.json
    ├── README.md                 # قالب Vite الافتراضي من غير تعديل
    ├── public/favicon.svg        # مستخدم
    ├── public/icons.svg          # مش مستخدم
    └── src/
        ├── main.jsx              # createRoot و<StrictMode> و<App/>
        ├── App.jsx               # الصفحة الوحيدة: فورم المدخلات، عرض النسختين، وImagePanel
        ├── App.css               # 11 قسم (المتغيرات، التخطيط، الفورم، الأزرار، المخرجات، شريط PEAS، الاستجابة للشاشات)
        ├── index.css             # فاضي
        ├── assets/               # hero.png وreact.svg وvite.svg، ومفيش واحد منهم مستخدم
        ├── components/
        │   ├── Sidebar.jsx       # قايمة جانبية شكل بس
        │   ├── ImagePanel.jsx    # واجهة Module 4
        │   ├── ImagePanel.css
        │   ├── Header.jsx        # فاضي (أسطر فاضية بس)
        │   └── Loader.jsx        # فاضي
        └── pages/CreatePost.jsx  # فاضي
```

### 1.3 تاريخ git المهم

| commit | الكاتب | التاريخ | المحتوى |
|---|---|---|---|
| `fe01ae9` | abdallahalaa222-coder | 2026-10-13 | أول نسخة من Module 3، وواجهة الحقول الحالية |
| `769689f` | abdallahalaa222-coder | 2026-10-16 | إعادة كتابة `agent.py`: تصحيح الأخطاء الإملائية، المجالات (domains)، النبرات |
| `e9f4733` | Karim Shetewy | 2026-10-19 | Module 4 (الصور)، و`ImagePanel`، و27 اختبار |

> **ملاحظة مهمة:**
> - **تعديلات Claude يوم 2026-10-14 ضاعت.** كانت على `agent.py` و`app.py` و`App.jsx` (تحقق من المدخلات بـ `DirectiveError`، حد 280 حرف لتويتر، `VITE_API_URL`، عرض رسائل الخطأ الحقيقية). ماتعملهاش commit، وضاعت لما الملفات اتحدّثت، **فالكود الحالي مفيهوش أي حاجة منها.** الأثر الوحيد الباقي منها هو ملف الاختبارات المكسور `tests/test_module3_agent.py`.
> - **فيه نسخة بديلة قديمة من الـ agent** بقاعدة معرفة من 10 مواضيع (حزمة `content_agent/`). محفوظة **خارج المشروع** في `D:\tmp\content_agent_backup`، ومش مرتبطة بأي حاجة.

---

## 2. منظور مادة الـ Intelligent Agents (PEAS والمنطق)

### 2.1 نوع الـ Agent

الـ docstring في [agent.py](agent.py) بيوصفه بإنه **"Goal-Based Agent"**. لكن فعليًا، من الكود، هو **Simple Reflex Agent قائم على قواعد (condition–action rules)**:

- **مالوش حالة داخلية بين الطلبات** (stateless) ولا ذاكرة ولا نموذج للعالم.
- **مابيبحثش بين بدائل ومابيقيّمش ناتجه** مقابل أي هدف: مفيش goal test ولا utility function.
- **حقل `goal` مجرد مدخل** بيختار قالب بسلسلة `if/elif` (`resolve_framework`).
- **حتمي 100%:** نفس المدخلات بتطلع نفس المخرجات (اتأكدت من ده). `import random` موجود في السطر 16 بس مش مستخدم.

**Module 4** بنفس الطابع (قواعد) في بناء الـ prompt. لكن المنفّذ النهائي (Gemini) نموذج توليدي خارجي مش حتمي.

**بيئة المهمة (Task Environment) للنص:** Fully observable، Deterministic، Episodic، Static، Discrete، Single-agent.

> **اقتراح للتبرير الأكاديمي:** عشان يبقى Goal-based أو Utility-based فعلًا، الـ agent يولّد كذا مرشح، ويقيّمهم بمقياس (الالتزام بطول المنصة، وجود الموضوع والكلمات المفتاحية، عدم التكرار، عدد الهاشتاجات)، ويختار الأعلى.

### 2.2 جدول PEAS

| العنصر | المعلن في الواجهة (شريط PEAS في `App.jsx`) | الواقع في الكود |
|---|---|---|
| **P**erformance | "AIDA / PAS Structural Adherence" | **مفيش أي مقياس أداء محسوب في الكود.** المقترح: الالتزام بحدود المنصة، وتغطية الموضوع والكلمات، وجودة اللغة |
| **E**nvironment | "LinkedIn · Instagram · X · Facebook" | المستخدم عن طريق واجهة الويب. Module 4 كمان بيتعامل مع Gemini API |
| **A**ctuators | "Hooks · Body · CTAs · Hashtags" | JSON فيه نسختين، كل نسخة فيها `hook` و`body` و`call_to_action` و`full_caption` و`hashtags`، ومعاهم `agent_metadata`. وModule 4 بيطلع صورة أو prompt مع `visual_direction` |
| **S**ensors | "Directive Schema (JSON)" | حقول `DirectiveRequest` (§2.3) |

### 2.3 الـ Sensors بالتفصيل

**`DirectiveRequest`** في [app.py:26-32](app.py#L26-L32)، للمسار `/generate`:

| الحقل | النوع | الافتراضي | القيم اللي الـ agent فاهمها فعلًا | التحقق الحالي |
|---|---|---|---|---|
| `topic` | `str`، مطلوب | — | أي نص | ❌ بيقبل `""` |
| `keywords` | `Optional[List[str]]` | `[]` | أول 3 بس بيدخلوا في النص، وكلهم بيتحولوا لهاشتاجات | ❌ قيمة `null` بتوقّع السيرفر بـ 500 |
| `platform` | `Optional[str]` | `"LinkedIn"` | `LinkedIn` و`Instagram` و`Twitter` و`Facebook` (مطابقة بجزء من النص) | ❌ أي قيمة تانية بتتنسّق زي Facebook |
| `goal` | `Optional[str]` | `"Marketing"` | فيها `market` أو `launch` تبقى AIDA، وفيها `educat` أو `problem` تبقى PAS، وأي حاجة تانية Story-Lesson-Question | ❌ |
| `tone` | `Optional[str]` | `"Professional"` | `Professional` و`Inspirational` و`Casual` (فيها الكلمة) | ❌ أي قيمة تانية بتتعامل كـ Professional |
| `language` | `Optional[str]` | `"en"` | `"ar"`، وأي قيمة غيرها بتتكتب بالإنجليزي | ❌ `"fr"` بتتقبل، والنص بيطلع إنجليزي، والـ metadata بتفضل مكتوب فيها `"fr"` |

**`ImageDirective`** في [image_generation/router.py:17-28](image_generation/router.py#L17-L28)، للمسار `/generate-image`. ✅ **تحققه سليم:**

| الحقل | القيد |
|---|---|
| `topic` | بيتشال منه المسافات من الأطراف، وطوله من 1 لـ 500 |
| `keywords` | قايمة أقصاها 15 عنصر، وكل عنصر أقصاه 60 حرف |
| `platform` و`goal` و`tone` | نصوص، أقصاها 40 حرف |
| `language` | `Literal["en","ar"]` |
| `hook` | أقصاه 600 حرف |
| `post_id` | أقصاه 64 حرف |
| `visual_style` | `auto` أو `photo` أو `3d` أو `illustration` |
| `aspect_ratio` | `Literal` من قايمة نسب ثابتة |
| `generate_image` | `bool` |

### 2.4 منطق اتخاذ القرار والتوليد (Reasoning Engine) في `agent.py`

دالة الدخول هي `ContentWriterAgent.generate(directive: dict) -> dict` ([agent.py:537](agent.py#L537)). والـ `app.py` طبقة رفيعة: بتحوّل الطلب لـ dict، وتنادي `content_agent.generate()`، وتلفّ النتيجة في `{"status": "success", "data": ...}` **من غير أي `try/except`**.

**الخطوات بالترتيب:**

1. **قراءة المدخلات بالقيم الافتراضية** ([agent.py:538-543](agent.py#L538-L543)) عن طريق `directive.get(...)`.
2. **فهم اللغة (NLU)، `normalize_and_clean_text(text, lang)`** ([agent.py:140](agent.py#L140)):
   - **عربي:** يدمج المسافات المكررة، ويستبدل الكلمة كاملة من `TYPO_MAP_AR` بعد ما يشيل علامات الترقيم من أطرافها (`w.replace(core, replacement)`)، وبعدها تصحيحات regex محددة (انتاجيه→إنتاجية، اداره→إدارة، مذاكره→مذاكرة، انجاز→إنجاز، افضل→أفضل...).
   - **إنجليزي:** يستبدل الكلمة من `TYPO_MAP_EN` من غير حساسية لحالة الأحرف.
   - **بتتنفذ على الموضوع وعلى كل كلمة مفتاحية**، ومرة تانية كمان جوه `generate_copy_sections`.
3. **اختيار الإطار، `resolve_framework(goal)`** ([agent.py:203](agent.py#L203)، static، ومستخدمة كمان في Module 4).
4. **الهاشتاجات، `allocate_hashtags(keywords, topic, platform, lang)`** ([agent.py:213](agent.py#L213)):
   1. **هاشتاج لكل كلمة مفتاحية:** يشيل الرموز، ويحوّل المسافات لـ `_`، ويتجاهل أي كلمة طولها حرف واحد.
   2. **هاشتاج من الموضوع:** لو 1 لـ 3 كلمات بيتربطوا بـ `_`. لو أكتر، ياخد أول كلمتين طولهم أكتر من 3 أحرف.
   3. **`detect_domain(topic + keywords)`:**
      - بيلف على `DOMAINS` بالترتيب: `tech_ai`، بعدها `productivity_time`، بعدها `education_study`، بعدها `business_career`.
      - أول مجال **أي كلمة فيه موجودة كجزء من النص** (substring) هو اللي بيكسب، والافتراضي `productivity_time`.
      - على حسب المجال بيضيف قايمة من `HASHTAG_KB[lang]`: `tech` أو `education` أو `business`، وإلا `productivity`.
   4. **يضيف `HASHTAG_KB[lang]["general"]`**، ويشيل المكرر مع الحفاظ على الترتيب. **الإزالة حساسة لحالة الأحرف.**
   5. **حد أقصى لكل منصة:** Instagram 10، وTwitter/X 3، وLinkedIn 4، وأي حاجة تانية 5.
5. **توليد نسختين** بالنوع `"Action-driven"` (رقم 1) و`"Value-driven"` (رقم 2). لكل نسخة، `generate_copy_sections(...)` ([agent.py:265](agent.py#L265)) بتعمل الآتي:
   - **`kw_phrase`:** أول 3 كلمات مفتاحية مربوطة بـ `"، و"` في العربي أو `", and "` في الإنجليزي. لو مفيش كلمات، بتبقى الموضوع نفسه.
   - **التوجيه:** على حسب اللغة بتروح لـ `_synthesize_arabic` ([agent.py:293](agent.py#L293)) أو `_synthesize_english` ([agent.py:401](agent.py#L401)).
   - **جوه كل دالة شجرة `if` ثابتة:** الإطار، بعده نوع النسخة، بعده النبرة. **النبرة بتتفحص في AIDA بس.**
   - **الناتج:** قوالب f-string بـ `{topic}` و`{kw_phrase}` بتطلع `hook` و`body` و`cta`.
   - **المجال** بيتحسب ويتبعت للدالة باسم `domain`، **بس مش مستخدم جوّاها خالص.** وقوائم `ar_terms` و`en_terms` في `DOMAINS` مش مستخدمة في أي مكان.

   **عدد القوالب لكل لغة 9 مجموعات** (المجموع 18):

   | الإطار | نوع النسخة | النبرات المدعومة | عدد المجموعات |
   |---|---|---|---|
   | AIDA | Action | Inspirational، Casual، Professional | 3 |
   | AIDA | Value | Inspirational، وأي نبرة تانية | 2 |
   | PAS | Action، Value | مفيش (النبرة متجاهلة) | 2 |
   | Story-Lesson-Question | Action، Value | مفيش (النبرة متجاهلة) | 2 |

6. **تنسيق المنشور، `format_full_caption(...)`** ([agent.py:507](agent.py#L507)):
   - **Twitter:** `hook + cta + hashtags`، **من غير الـ body، ومن غير أي حد للطول.**
   - **Instagram:** `hook ✨`، بعدها فواصل `.`، بعدها `body`، بعدها سطر "📌 Save this post..." أو "احفظ المنشور..."، بعدها `cta`، وفي الآخر الهاشتاجات.
   - **LinkedIn وFacebook:** نفس التنسيق بالظبط: `hook\n\nbody\n\ncta\n\nhashtags`.
7. **الناتج:** `agent_metadata` و`variations` (الشكل في §3.1). **`detected_domain` في الـ metadata بيتحسب من الموضوع بس** ([agent.py:594](agent.py#L594))، مع إن الهاشتاجات اتحسبت من الموضوع والكلمات المفتاحية.

### 2.5 منطق Module 4 (الصور)

**`build_image_plan(...)`** في [prompt_builder.py:180](image_generation/prompt_builder.py#L180):

1. **التنظيف:** `_clean()` بيدمج المسافات ويغيّر `"` لـ `'`.
2. **المنصة:** `_platform_key()` بيحدد المنصة، ومنها النسبة الافتراضية: Instagram ‎4:5، وFacebook ‎1:1، وLinkedIn وX ‎16:9.
3. **النبرة:** `_tone_key()`. الكلمات `casual` و`funny` و`friendly` و`playful` بتتعامل كـ casual. النبرة بتحدد mood وlighting ولوحة ألوان من 4 ألوان بكود hex.
4. **الإطار والأسلوب:** `ContentWriterAgent.resolve_framework(goal)`، والأسلوب الافتراضي من `FRAMEWORKS`: AIDA وStory صورة فوتوغرافية، وPAS رسم 3D. وتقدر تغيّره بـ `visual_style`.
5. **المجال:** `detect_visual_domain()` بيستخدم نفس كلمات `ContentWriterAgent.DOMAINS`، لكن **بمطابقة على حدود الكلمة** (`_keyword_in`)، والافتراضي `"general"`. **ده مختلف عن `agent.detect_domain`** (§5، رقم 10).
6. **بناء الـ prompt من جمل بالترتيب:**
   1. الأسلوب.
   2. المنصة والموضوع.
   3. الكلمات المفتاحية.
   4. الـ hook.
   5. التكوين (composition).
   6. إشارات المجال.
   7. الجو والإضاءة والألوان.
   8. جماليات المنصة.
   9. لو اللغة عربي: أشخاص بملامح عربية ولبس محتشم.
   10. ترك ثلث فاضي للعنوان: يمين للعربي، وشمال للإنجليزي.
   11. `NO_TEXT_RULE`: ممنوع أي نص أو أرقام أو شعارات جوه الصورة.
7. **الناتج:** `ImagePlan` (dataclass)، و`visual_direction()` بترجّعها كـ dict من غير الـ prompt.

**`ImageGenerationService.create(directive)`** في [service.py:26](image_generation/service.py#L26):

1. يبني الخطة، ويجهّز `result` بـ `mode="prompt_only"`.
2. لو `generate_image=False` يرجع على طول ومعاه `notice`.
3. يستدعي `client.generate(prompt, aspect_ratio)`. لو حصل `ImageGenerationUnavailable` يرجّع `prompt_only`، ورسالة الخطأ تبقى في `notice`.
4. لو نجح، يحفظ `<uuid32>.png|jpg|webp` ومعاه ملف `<uuid32>.json` جنبه (فيه النتيجة والـ `directive`) في `generated_images/`.

**`NanoBananaClient`** في [nano_banana.py:37](image_generation/nano_banana.py#L37):

- **المفتاح:** من `GEMINI_API_KEY` أو `GOOGLE_API_KEY`، والـ `.env` بيتحمّل من جذر المشروع.
- **الموديلات:** `IMAGE_MODEL` لو متحدد، وإلا `DEFAULT_MODELS = ("gemini-nano-banana-2.1", "gemini-3.1-flash-image", "gemini-2.5-flash-image")`. خطأ 404 بيعدّي للموديل اللي بعده.
- **المهلة وإعادة المحاولة:** المهلة 120 ثانية، و3 محاولات عند 429 أو 5xx.
- **رسائل الأخطاء:** `_client_error_message` بتترجم الأخطاء لرسائل مفهومة: API مش مفعّل (`SERVICE_DISABLED`)، مفتاح مرفوض، الخطة المجانية مالهاش حصة صور، تجاوز الحصة.
- **استخراج الصورة:** `_extract_image` بياخد أول جزء صورة في الرد. ولو مفيش، بيوضّح هل السبب فلتر الأمان.

---

## 3. حالة الـ Backend (FastAPI)

### 3.1 الـ Endpoints

| Method | Path | الملف | الوصف |
|---|---|---|---|
| POST | `/generate` | [app.py:41](app.py#L41) | توليد النص (Module 3) |
| POST | `/generate-legacy` | [app.py:58](app.py#L58) | توافق قديم: `topic` و`platform` و`tone` مطلوبين. بيستخدم `keywords=[topic]` و`goal="Marketing"` و`language="en"` |
| GET | `/health` | [app.py:74](app.py#L74) | فحص الحالة |
| POST | `/generate-image` | [router.py:56](image_generation/router.py#L56) | توليد صورة أو prompt (Module 4) |
| GET | `/image-service/status` | [router.py:64](image_generation/router.py#L64) | هل المفتاح موجود، وقايمة الموديلات |
| GET | `/images/{filename}` | [router.py:69](image_generation/router.py#L69) | بيقدّم الصورة. الاسم لازم يطابق `^[0-9a-f]{32}\.(png\|jpg\|webp)$`، و`?download=true` بيخلي التحميل كمرفق |
| GET | `/docs` و`/redoc` و`/openapi.json` | تلقائي من FastAPI | التوثيق |

**`POST /generate`، الطلب:**
```json
{
  "topic": "Time management mobile application for college students",
  "keywords": ["tasks", "productivity", "study routine"],
  "platform": "LinkedIn",
  "goal": "Marketing",
  "tone": "Professional",
  "language": "en"
}
```

**`POST /generate`، الرد (200):**
```json
{
  "status": "success",
  "data": {
    "agent_metadata": {
      "module": "Module 3 - AI Content Writer Agent (Enhanced NLG & Typo Engine)",
      "execution_mode": "Offline Rule-Based NLG",
      "framework": "AIDA | PAS | Story-Lesson-Question",
      "platform": "LinkedIn",
      "language": "en",
      "tone": "Professional",
      "detected_domain": "tech_ai | productivity_time | education_study | business_career"
    },
    "variations": [
      {
        "version_id": 1,
        "type": "Action-driven",
        "hook": "...",
        "body": "...",
        "call_to_action": "...",
        "full_caption": "hook + body + cta + hashtags منسّقة حسب المنصة",
        "hashtags": ["#..."]
      },
      { "version_id": 2, "type": "Value-driven", "...": "نفس الحقول" }
    ]
  }
}
```

**`POST /generate-image`، الطلب:** نفس حقول النص، وزيادة عليها الحقول دي كلها اختيارية:
```json
{ "hook": "...", "post_id": "...", "visual_style": "auto", "aspect_ratio": "4:5", "generate_image": true }
```

**`POST /generate-image`، الرد (200):**
```json
{
  "status": "success",
  "data": {
    "image_id": "32-hex | null",
    "post_id": "null (الواجهة مابتبعتهوش)",
    "mode": "ai_generated | prompt_only",
    "model": "gemini-... | null",
    "prompt": "...",
    "visual_direction": {
      "platform": "Instagram", "aspect_ratio": "4:5", "dimensions": "1080x1350",
      "visual_style": "Photorealistic photography", "framework": "AIDA", "domain": "general",
      "mood": "...", "lighting": "...", "composition": "...", "text_overlay": "...",
      "platform_notes": "...", "palette": [{ "name": "Amber", "hex": "#F59E0B" }]
    },
    "notice": "سبب وضع prompt_only | null",
    "created_at": "ISO-8601 UTC",
    "image_url": "http://127.0.0.1:8000/images/<id>.png | null"
  }
}
```

**أشكال الأخطاء:**
- **أخطاء Pydantic:** 422 بشكل FastAPI الافتراضي `{"detail": [{"type", "loc", "msg", "input"}]}`. مفيش غلاف خطأ موحّد للمشروع.
- **أي exception مش متعالج:** 500 بنص عادي "Internal Server Error"، زي حالة `keywords: null`.
- **صورة مش موجودة:** 404 `{"detail": "Image not found"}`.

### 3.2 قاعدة البيانات والتخزين

**مفيش قاعدة بيانات** (لا SQLite ولا ORM). وجود `*.db` في `.gitignore` احتياط بس.

- **Module 3:** كله في الذاكرة، ومابيتخزنش أي حاجة.
- **Module 4:** ملفات على القرص في `generated_images/` (الصورة وملف JSON جنبها، فيه الـ `directive` و`post_id` والـ `prompt` والموديل).
  - **مفيش حذف تلقائي ولا حد أقصى للتخزين.**
  - **الواجهة مابتبعتش `post_id`،** فالربط بين الصورة والمنشور مش مستخدم فعليًا.

### 3.3 الاختبارات

**`tests/test_image_generation.py` (27 اختبار، متتبَّع في git):** ✅ **كلهم بينجحوا.**

- **أمر التشغيل:** `python -m pytest tests/test_image_generation.py -q`، والنتيجة `27 passed, 6 warnings`.
- **بيستخدم** `FakeClient` و`app.dependency_overrides[get_image_service]` و`tmp_path`، ومفيش أي طلب حقيقي لـ Gemini.
- **بيغطّي:**
  - النسب لكل منصة، وتغيير النسبة يدويًا.
  - اختيار الإطار والأسلوب.
  - محتوى الـ prompt: علامات التنصيص، الكلمات المفتاحية، الـ hook، الإضاءة، ثلث العنوان، منع النص.
  - تكييف الصورة للعربي.
  - كشف المجال.
  - الوضع من غير مفتاح.
  - حفظ الصورة وملف JSON.
  - الرجوع لوضع الـ prompt عند الفشل.
  - رسائل الحصة والـ API المعطّل.
  - `generate_image=False`.
  - رابط الصورة وهيدر التحميل.
  - 422 للموضوع الفاضي وللنسبة غير المدعومة.
  - الحماية من path traversal (404).
  - مسار الحالة.

**`tests/test_module3_agent.py` (غير متتبَّع):** ❌ **مكسور.**

- **أصله:** كتبه Claude يوم 2026-10-14 لنسخة من `agent.py` كان فيها `DirectiveError` و`normalize_directive`، والنسخة دي اتشالت.
- **النتيجة:** `ImportError` وقت جمع الاختبارات، فـ **`python -m pytest` من غير معاملات بيقف بالكامل** برسالة `Interrupted: 1 error during collection`، وحتى الـ 27 اختبار السليمين مابيشتغلوش.
- **الحل:** امسحه أو أعد كتابته على الكود الحالي.

**باقي الحالة:**
- **مفيش ولا اختبار في git لـ `agent.py` الحالي (Module 3)**، ومفيش اختبارات للـ Frontend.
- **الـ 6 تحذيرات** كلها `PydanticDeprecatedSince20` بسبب `Field(..., example=...)` في [app.py:27-32](app.py#L27-L32).

---

## 4. حالة الـ Frontend (React / Vite)

### 4.1 الصفحات والمكونات

| الملف | الحالة | الوظيفة |
|---|---|---|
| [main.jsx](frontend/src/main.jsx) | ✅ | بيركّب `<App/>` جوه `StrictMode` |
| [App.jsx](frontend/src/App.jsx) | ✅ الصفحة الوحيدة الفعلية | فورم المدخلات، تبويبين للنسختين (Option A وOption B)، عرض الـ hook والـ body والـ CTA، شرائح الهاشتاجات، زرار نسخ `full_caption`، زرار Regenerate، `ImagePanel`، وشريط PEAS بنص ثابت |
| [ImagePanel.jsx](frontend/src/components/ImagePanel.jsx) | ✅ | التفاصيل تحت الجدول |
| [Sidebar.jsx](frontend/src/components/Sidebar.jsx) | ⚠️ شكل بس | قايمة ثابتة: Dashboard (متعلّم active ثابت)، Content planner، Posts library، AI Agent، Analytics، Monetization. زرار "New Post" مالوش `onClick`، ومفيش routing |
| `Header.jsx` و`Loader.jsx` و`pages/CreatePost.jsx` و`index.css` | ❌ فاضيين | مش مستخدمين |

**تفاصيل `ImagePanel`:**
- **الـ props:** `directive` و`hook`.
- **عند التركيب:** بيعمل `GET /image-service/status`، ولو المفتاح مش موجود بيعرض "Prompt-only mode".
- **`handleGenerate`:** بيعمل `POST /generate-image` بالـ body `{...directive, hook}`.
- **العرض:** الصورة أو رسالة الـ `notice`، وشرائح (النسبة، الأبعاد، الأسلوب، الإطار، الموديل)، وعينات الألوان، و`<details>` فيها الـ prompt ودليل التصميم.
- **الأزرار:** تحميل، ونسخ الـ prompt، وإعادة التوليد.

**State في `App.jsx`:**

| المتغير | القيمة الابتدائية |
|---|---|
| `topic` | **مملوء مسبقًا** بـ "Time management mobile application for college students" |
| `keywords` | "tasks, productivity, study routine" |
| `platform` | `'LinkedIn'` |
| `goal` | `'Marketing'` |
| `tone` | `'Professional'` |
| `language` | `'en'` |
| `activeTab` | `0` |
| `result` | `null` |
| `error` | `''` |
| `loading` | `false` |
| `copied` | `false` |
| `submittedDirective` | `null` |
| `generationId` | `0` |

**الثوابت:** `PLATFORMS` و`GOALS` و`TONES` و`LANGUAGES`.

### 4.2 الحقول وطريقة إرسال البيانات

| الحقل في الواجهة | العنصر | الـ state | المفتاح في JSON | القيم |
|---|---|---|---|---|
| What is your post idea / topic? | `<textarea>` | `topic` | `topic` | نص (بيتشال منه المسافات من الأطراف) |
| Keywords (Comma-separated) | `<input type="text">` | `keywords` | `keywords` | بتتقسم عند `,` وتتنضف، وتتشال الفاضية، وتتبعت كقايمة |
| Target Language | `<select>` | `language` | `language` | `en` و`ar` |
| Target Platform | `<select>` | `platform` | `platform` | `LinkedIn` و`Instagram` و`Twitter` و`Facebook` |
| Campaign Goal & Framework | `<select>` | `goal` | `goal` | `Marketing` و`Educational` و`Engagement` |
| Tone of Voice | `<select>` | `tone` | `tone` | `Professional` و`Inspirational` و`Casual` |

**مسار البيانات في `handleGenerate`** ([App.jsx:50](frontend/src/App.jsx#L50)):

1. يتأكد إن `topic` مش فاضي.
2. يبني `directive`.
3. يعمل `fetch('http://127.0.0.1:8000/generate', {method: 'POST', ...})` ([App.jsx:69](frontend/src/App.jsx#L69)).
4. لو `data.status === 'success'`: ينفذ `setResult(data.data)` و`setActiveTab(0)` و`setSubmittedDirective(directive)` و`setGenerationId(id + 1)`.
5. غير كده يعرض رسالة خطأ عامة.
6. لو الطلب فشل تمامًا (`catch`) يعرض "Could not connect to backend server...".

**بعدها `ImagePanel`** بياخد `submittedDirective` و`currentVariation.hook`.

**العربي:**
- الحاوية بتاعة النتيجة بتاخد `dir="rtl"` لو `agent_metadata.language === 'ar'`.
- الجذر بياخد كلاس `lang-arabic`، **ومفيش أي CSS ليه.**

### 4.3 المكتبات المثبتة
- **`lucide-react`** بس، جنب React، للأيقونات.
- **مفيش Tailwind**: التنسيق كله CSS عادي.
- **الخط** Inter من Google Fonts.

---

## 5. المشاكل الحالية والقصور

المفتاح: 🔴 حرج · 🟠 مهم · 🟡 بسيط. كل حالة اتجربت فعليًا إلا لو مكتوب غير كده.

### بيئة التشغيل والمشروع

1. 🔴 **`google-genai` ماكانتش متثبتة في `venv`:**
   - **الأثر:** `uvicorn app:app` كان بيقع بـ `ImportError: cannot import name 'genai' from 'google'`.
   - **الحالة:** **اتثبّتت أثناء الفحص** (2.31.0). أي جهاز تاني محتاج `pip install -r requirements.txt`.
2. 🔴 **ملف الاختبارات `tests/test_module3_agent.py` بيكسر `pytest` كله** (§3.3).
   - **الحل:** امسحه، أو أعد كتابته لـ `ContentWriterAgent` الحالي.
3. 🟡 **ملف `requirements.txt`:**
   - الإصدارات مش مثبّتة.
   - فيه مكتبات تقيلة مش مستخدمة: `streamlit` و`langchain` و`google-generativeai`.
4. 🟡 **ملف `package-lock.json` في الجذر** فاضي ومتبقي.
5. 🟡 **`vite build` ماقدرتش أتأكد منه النهارده:**
   - **السبب:** وقع بـ `memory allocation failed` لأن الذاكرة الافتراضية المتاحة على الجهاز كانت حوالي 220 ميجا. **دي مشكلة في الجهاز مش في الكود.**
   - **البديل:** `npx eslint .` قرا كل الملفات من غير أي خطأ syntax.
   - **ملحوظة:** آخر build ناجح كان يوم 2026-10-14، قبل ما يتضاف `ImagePanel`.

### Backend: `app.py` و`agent.py`

6. 🔴 **خطأ 500 لما `keywords` تبقى `null`:**
   - **السبب:** [agent.py:539](agent.py#L539) فيه `directive.get("keywords", [])`، والمفتاح موجود وقيمته `None`. بعدها [agent.py:547](agent.py#L547) بيعمل `for k in raw_keywords`، فيحصل `TypeError`.
   - **الحل:** `directive.get("keywords") or []`.
7. 🔴 **مفيش تحقق من المدخلات في `/generate`.** اتجرّب:
   - `topic: ""` بيرجّع 200 بنص مكسور: "...framework for mastering ."
   - `platform: "TikTok"` و`language: "fr"` و`tone: "angry"` بيتقبلوا من غير أي رسالة.
   - `goal: "sales"` بيتحول بصمت لـ Story-Lesson-Question.
   - **الحل:** استخدام `Literal` و`min_length` في `DirectiveRequest`، زي اللي معمول في `ImageDirective`.
8. 🔴 **ادعاءات مختلقة في القوالب** (حاجات المستخدم ماقالهاش):
   - **عربي:**
     - [agent.py:316](agent.py#L316): "توفير ساعات أسبوعية".
     - [agent.py:319](agent.py#L319): "الرابط في التعليق الأول".
     - [agent.py:335](agent.py#L335): "تضاعف سرعة".
     - [agent.py:339](agent.py#L339): "الرابط المرفق".
     - [agent.py:364](agent.py#L364): "قاعدة الـ 20/80".
     - [agent.py:380](agent.py#L380): "تجربة عملية أثبتت فعاليتها".
   - **إنجليزي:**
     - [agent.py:427](agent.py#L427): "via the link below".
     - [agent.py:442](agent.py#L442): "This proven approach".
     - [agent.py:447](agent.py#L447): "at the link".
     - [agent.py:488](agent.py#L488): "A proven case study".
     - [agent.py:490](agent.py#L490): "Months ago...".
     - [agent.py:497](agent.py#L497): "several years".
   - **الأثر:** المنشورات بتشير لرابط مش موجود، وبتحكي قصص وأرقام مختلقة.
9. 🔴 **المحتوى كله عن الإنتاجية مهما كان الموضوع:**
   - **المثال:** موضوع زي "Cooking pasta" بيطلع فيه "deep-work focus windows" و"impact-versus-effort matrix"، وهاشتاجات زي `#Productivity` و`#TimeManagement`.
   - **السبب:** `domain` بيتحسب ومش مستخدم في النص، وقوائم `ar_terms` و`en_terms` مش مستخدمة خالص.
10. 🟠 **كشف المجال بيطلع نتايج غلط، ومش متسق مع Module 4:**
    - **السبب:** `detect_domain` بيطابق جزء من النص (substring)، ومجال `tech_ai` بيتفحص الأول.
    - **أمثلة اتجربت (كلها طلعت `tech_ai` في `agent.py` و`general` في Module 4):**
      - "Healthy breakfast for a happy family": "ai" جوه "happy"، فطلعت هاشتاجات زي `#TechTrends` و`#ArtificialIntelligence`.
      - "How to maintain a garden".
      - "Daily email campaign tips".
      - "Training for a marathon".
    - **مثال تاني:** "Learning to paint" طلع `tech_ai` في `agent.py` بسبب "ai" جوه "paint"، و`education_study` في Module 4.
    - **مواضيع مش مرتبطة بأي مجال** (Travel، Cooking، Yoga، Personal finance) بتاخد `productivity_time`.
    - **`detected_domain` في الـ metadata** بيتحسب من الموضوع بس ([agent.py:594](agent.py#L594))، والهاشتاجات من الموضوع والكلمات. مثال: "Weekly planner" مع `[exam, study]` بيطلع metadata بـ `productivity_time` وهاشتاجات تعليمية.
    - **الحل:** استخدام `_keyword_in` من `prompt_builder.py` جوه `agent.py`.
11. 🟠 **زرار Regenerate مالوش أي تأثير:**
    - **السبب:** المخرجات حتمية تمامًا. `import random` في [agent.py:16](agent.py#L16) مش مستخدم، والـ docstring بيقول "Anti-Repetition Pattern Randomization" ومفيش حاجة زي كده متنفّذة.
    - **في الواجهة:** Regenerate بيزوّد `generationId`، فـ `ImagePanel` بيتعمل من جديد (`key={generationId}` في [App.jsx:293](frontend/src/App.jsx#L293)) و**الصورة اللي اتولدت بتختفي.**
12. 🟠 **النبرة مالهاش تأثير غير في AIDA:**
    - **PAS وStory-Lesson-Question بيتجاهلوها تمامًا:** الـ body طلع متطابق في التلات نبرات (اتجرّب).
    - **في AIDA مع Value-driven:** Casual بيقع في فرع Professional.
13. 🟠 **تويتر مالوش حد 280 حرف:**
    - **الواقع:** `format_full_caption` بيحط `hook + cta + hashtags` من غير أي قص.
    - **الاختبار:** موضوع طويل طلّع منشور **460 حرف**. مع الموضوع الافتراضي أكبر طول كان 263.
14. 🟠 **التصحيح الإملائي في `TYPO_MAP_AR` بيبوّظ المعنى** (اتجرّب):

    | المدخل | الناتج |
    |---|---|
    | "سوشيال ميديا" | "وسائل التواصل الاجتماعي الإعلام الرقمي" |
    | "روبوت ذكي" | "وكيل ذكي ذكي" |
    | "حاجه مهمة" | "أمر مهمة" (التذكير والتأنيث بقوا غلط) |
    | "التعمل" | "الذي تم إنجازه" |

    - **في الإنجليزي** الكلمة اللي بتتصحح بتتحول لحروف صغيرة: "Teh Producitvity" بقت "the productivity".
    - **التصحيح بيتنفذ مرتين** (في `generate()` وفي `generate_copy_sections()`).
15. 🟡 **الهاشتاجات:**
    - إزالة المكرر حساسة لحالة الأحرف، فـ `["Meal Prep","meal prep"]` بتطلع `#Meal_Prep` و`#meal_prep`.
    - الكلمات زي "C++" بتتشال.
    - هاشتاج الموضوع الطويل ممكن يطلع من غير معنى، زي `#Healthy_breakfast`.
16. 🟡 **العربي مع Casual:**
    - بيتكتب بالعامية المصرية، وباقي النبرات بالفصحى.
    - بيسمّي المنشور "المقال" ([agent.py:321](agent.py#L321)).
17. 🟡 **التنسيق بين المنصات:**
    - Facebook وLinkedIn ليهم نفس التنسيق بالظبط.
    - المطابقة بجزء من النص (`"x" in plat`) هشة.
18. 🟡 **لو المنسّق (Coordinator) نادى الـ agent مباشرة** وبعت `keywords` كنص زي `"a,b"`، النص بيتلف عليه حرف حرف، والناتج بيبقى "a, and ,, and b".
19. 🟡 **`/generate-legacy`:** النبرة القديمة `"funny"` بتتحول بصمت لـ Professional.
20. 🟡 **تحذيرات Pydantic** في [app.py:27-32](app.py#L27-L32): `example=` بقت deprecated، والمفروض تستخدم `json_schema_extra`.
21. 🟡 **imports مش مستخدمة:** `random` و`Tuple` في `agent.py`.
22. 🟡 **CORS:** `allow_origins=["*"]` مع `allow_credentials=True`. ينفع للتطوير بس.

### Module 4 (الصور)

23. 🟠 **توليد صورة حقيقية ماتجرّبش:**
    - **السبب:** ملف `.env` فاضي، فـ `/generate-image` بيرجّع `prompt_only` بس (ودي اشتغلت صح).
    - **أسماء الموديلات** `gemini-nano-banana-2.1` و`gemini-3.1-flash-image` ماتأكدتش إنها موجودة، لكن سلسلة البدائل بتتعامل مع 404.
    - **الحصة:** على حسب رسائل الكود نفسه، الخطة المجانية مالهاش حصة صور، ومحتاجة billing.
24. 🟡 **مجلد `generated_images/`** بيكبر من غير حد ولا تنضيف. و`post_id` مابيتبعتش من الواجهة.
25. 🟡 **`get_image_service`** متعمل بـ `@lru_cache`، فبيقرا الـ env مرة واحدة. أي تغيير في `.env` محتاج إعادة تشغيل السيرفر.
26. 🟡 **`image_url`** رابط كامل متبني من `request.url_for`. شغال محليًا، لكن ممكن يتكسر ورا proxy أو على host مختلف.

### Frontend

27. 🟠 **عنوان الـ API مكتوب ثابت في مكانين:** [App.jsx:69](frontend/src/App.jsx#L69) و[ImagePanel.jsx:5](frontend/src/components/ImagePanel.jsx#L5)، وقيمته `http://127.0.0.1:8000`.
28. 🟠 **التعامل مع الأخطاء:**
    - أي رد مش ناجح (زي 422) بيطلع رسالة عامة "Agent returned an unexpected error response." ([App.jsx:81](frontend/src/App.jsx#L81)).
    - الـ 500 بيرجع نص مش JSON، فـ `response.json()` بيفشل، والواجهة بتقول **"Could not connect to backend server"** (رسالة مضللة).
    - `ImagePanel` كمان بيطلع رسالة عامة.
29. 🟠 **خانة Keywords (`<input type="text">`) من غير تنسيق:**
    - **السبب:** `App.css` بينسّق `textarea, select` بس ([App.css:263](frontend/src/App.css#L263)).
    - **الأثر:** الخانة بتطلع صغيرة وخام.
30. 🟡 **CSS ناقص:**
    - كلاس `lang-arabic` ([App.jsx:101](frontend/src/App.jsx#L101)) مالوش أي CSS.
    - التبويبات بتستخدم `var(--border, …)` ([App.jsx:244](frontend/src/App.jsx#L244))، والمتغير ده مش معرّف.
31. 🟡 **`handleCopy` و`handleCopyPrompt` مفيهمش `try/catch`.** النسخ للحافظة ممكن يفشل لو الصفحة مش HTTPS أو مفيش صلاحية.
32. 🟡 **ملفات وأجزاء مش مستخدمة:**
    - الـ Sidebar شكل بس.
    - `Header.jsx` و`Loader.jsx` و`CreatePost.jsx` و`index.css` فاضيين.
    - `hero.png` و`react.svg` و`vite.svg` و`public/icons.svg` مش مستخدمين.
    - `README.md` هو قالب Vite.
33. 🟡 **ESLint:** خطأين `no-unused-vars` لـ `React` في [App.jsx:1](frontend/src/App.jsx#L1) و[Sidebar.jsx:1](frontend/src/components/Sidebar.jsx#L1).
34. 🟡 **الموضوع والكلمات المفتاحية** مملوءين مسبقًا في الـ state.

---

## 6. طريقة التشغيل الحالية

### الـ Backend (PowerShell)
```powershell
cd D:\SocialMediaAgent
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt          # ضروري: بيثبّت google-genai
# اختياري لتوليد صور حقيقية: اكتب GEMINI_API_KEY=... في .env (انسخ .env.example)
uvicorn app:app --reload --port 8000
```
- **لو PowerShell منع التفعيل،** شغّل من غير تفعيل:
  ```powershell
  .\venv\Scripts\python.exe -m uvicorn app:app --reload --port 8000
  ```
  أو اسمح بالسكربتات مرة واحدة:
  ```powershell
  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
  ```
- **للتأكد إن السيرفر شغال:** افتح http://127.0.0.1:8000/health، والتوثيق التفاعلي على http://127.0.0.1:8000/docs
- **قبل التشغيل اتأكد إن مفيش سيرفر قديم على البورت 8000.** حصل قبل كده إن نسخ قديمة فضلت شغالة ورجّعت نتايج قديمة:
  ```powershell
  Get-NetTCPConnection -LocalPort 8000 -State Listen
  ```

### الـ Frontend (ترمنال تاني)
```powershell
cd D:\SocialMediaAgent\frontend
npm install
npm run dev                              # http://localhost:5173
```
الواجهة **لازم** تلاقي الـ Backend على `http://127.0.0.1:8000` بالظبط، لأن العنوان مكتوب ثابت في الكود.

### الاختبارات والفحص
```powershell
cd D:\SocialMediaAgent
python -m pytest -v                                  # 209 passed (109 نص + 40 فيسبوك + 33 تحليلات + 27 صور)
cd frontend
npx eslint .                                         # خطأين no-unused-vars
```

---

## 7. خطوات مقترحة للمطور الجديد (بالأولوية)

1. **الاختبارات:** امسح `tests/test_module3_agent.py` أو أعد كتابته، وضيف اختبارات لـ `ContentWriterAgent` الحالي.
2. **التحقق من المدخلات في `DirectiveRequest`:** `Literal` للمنصة والهدف والنبرة واللغة، و`min_length=1` للموضوع. وكمان الإصلاح `directive.get("keywords") or []`.
3. **تنضيف القوالب:** شيل الادعاءات المختلقة والإشارات لروابط مش موجودة (§5، رقم 8). وخلي الـ body محايد أو مبني على المجال باستخدام `ar_terms` و`en_terms`.
4. **تنويع حقيقي:** أكتر من صيغة لكل جزء، والاختيار يبقى بـ `random`، عشان Regenerate يبقى ليه معنى. ومايتعملش reset لـ `ImagePanel` لما النص يتولد من جديد.
5. **النبرة:** تطبيقها في PAS وStory-Lesson-Question.
6. **تويتر:** قص المنشور لحد 280 حرف.
7. **كشف المجال:** توحيده بين `agent.py` و`prompt_builder.py` (مطابقة على حدود الكلمة).
8. **`TYPO_MAP_AR`:** تصحيح العناصر الضارة، وعدم تنفيذ التصحيح مرتين.
9. **الواجهة:**
   - ثابت واحد لعنوان الـ API من `import.meta.env.VITE_API_URL`.
   - عرض رسالة `detail` أو `error` الحقيقية.
   - تنسيق `input[type="text"]`.
   - تنضيف الملفات الفاضية والأصول اللي مش مستخدمة.
10. **`requirements.txt`:** تثبيت الإصدارات، وشيل `streamlit` و`langchain` و`google-generativeai`.

---

## 8. ما تم تغييره أثناء هذا الفحص

- **تثبيت `google-genai` 2.31.0** في `venv`. ده إعداد للبيئة، ومفيش تعديل كود.
- **إنشاء الملف ده:** `HANDOFF_REPORT.md`.
- **مفيش أي ملف كود اتعدّل.** سكربت الفحص اتشغّل من مجلد مؤقت برا المشروع.
