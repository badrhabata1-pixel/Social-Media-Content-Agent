from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sensors: البيانات اللي الـ Agent هيستقبلها
class PostRequest(BaseModel):
    topic: str
    platform: str
    tone: str

# بناء الـ Agent 
class SocialMediaAgent:
    def __init__(self):
        # قاعدة المعرفة (Knowledge Base) للـ Agent
        self.templates = {
            "Facebook": {
                "funny": "مين فينا مش بيعاني من {topic}؟ 😂 شاركونا مواقفكم في الكومنتات!",
                "professional": "موضوع {topic} أصبح من أهم النقاط التي يجب التركيز عليها في مجتمعنا اليوم. ما رأيكم؟",
            },
            "Twitter": {
                "funny": "حرفياً أنا لما أفكر في {topic} 🤡 #ضحك #{topic_nospace}",
                "professional": "نقطة سريعة للنقاش: {topic} لها تأثير كبير على إنتاجيتنا. #{topic_nospace}",
            },
            "Instagram": {
                "funny": "حالي مع {topic} 🤪 swipe left عشان تشوفوا الكارثة ⬅️ ✨",
                "professional": "سر النجاح في التعامل مع {topic} 💡 (اقرأ الكابشن) 👇",
            }
        }
        
        self.visual_rules = {
            "Facebook": "نصيحة للمصمم: استخدم صورة تفاعلية مكتوب عليها سؤال للنقاش.",
            "Twitter": "نصيحة للمصمم: استخدم ميم (Meme) أو صورة جيف (GIF) سريعة.",
            "Instagram": "نصيحة للمصمم: استخدم كاروسيل (صور متعددة) بتصميم جذاب ومريح للعين."
        }

    # Reasoning: عملية التفكير واتخاذ القرار
    def generate_post(self, topic, platform, tone):
        topic_nospace = topic.replace(" ", "_")
        
        # اختيار القالب المناسب بناء على المعطيات
        if platform in self.templates and tone in self.templates[platform]:
            caption = self.templates[platform][tone].format(topic=topic, topic_nospace=topic_nospace)
        else:
            caption = f"بوست عن {topic} بأسلوب {tone} على منصة {platform}."
        
        # اختيار الصورة المناسبة
        visual = self.visual_rules.get(platform, "صورة تعبيرية عن الموضوع.")
        
        # ابتكار الهاشتاجات
        hashtags = f"#{topic_nospace} #تريند #تفاعل"

        # Actuator: المخرجات النهائية
        final_result = f"""
📝 Caption: 
{caption}

#️⃣ Hashtags: 
{hashtags}

🎨 Visual Concept: 
{visual}
        """
        return final_result

# إنشاء نسخة من الـ Agent
agent = SocialMediaAgent()

@app.post("/generate")
def generate_content(request: PostRequest):
    # إرسال المعطيات للـ Agent عشان يبتكر البوست
    response = agent.generate_post(request.topic, request.platform, request.tone)
    return {"status": "success", "data": response}