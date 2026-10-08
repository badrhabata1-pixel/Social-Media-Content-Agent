from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Social Media Content Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Sensors: data the Agent receives ─────────────────────────────────────────
class PostRequest(BaseModel):
    topic: str
    platform: str
    tone: str

# ── Intelligent Agent ─────────────────────────────────────────────────────────
class SocialMediaAgent:
    """
    A rule-based intelligent agent that applies the PEAS model:
      Performance  – quality and relevance of generated content
      Environment  – user input and selected social media platform
      Actuators    – caption, hashtags, visual concept
      Sensors      – topic, platform, tone
    """

    def __init__(self):
        # ── Knowledge Base: caption templates ────────────────────────────────
        self.templates = {
            "Facebook": {
                "funny": (
                    "Who else can totally relate to {topic}? 😂 Drop your funniest experience "
                    "in the comments — let's see who's been through the most! 👇"
                ),
                "professional": (
                    "{topic} is shaping the way we think and work today. "
                    "Understanding it isn't optional anymore — it's essential. "
                    "What's your take? Share your thoughts below. 💬"
                ),
            },
            "Twitter": {
                "funny": (
                    "Me pretending I understand {topic} while absolutely losing it internally 🤡\n"
                    "#{topic_tag} #RelatableContent #TrueStory"
                ),
                "professional": (
                    "Quick thought: {topic} is one of the most impactful trends right now.\n"
                    "Are you paying attention? #{topic_tag} #Innovation #FutureForward"
                ),
            },
            "Instagram": {
                "funny": (
                    "POV: You thought {topic} would be easy 😅✨\n"
                    "Swipe left to see the chaos ⬅️\n"
                    "Save this for anyone who needs a laugh today 💀"
                ),
                "professional": (
                    "The secret to mastering {topic} isn't talent — it's consistency. 💡\n"
                    "Read the caption for the full breakdown 👇\n"
                    "Follow for more insights like this ✨"
                ),
            },
        }

        # ── Knowledge Base: visual concept hints ─────────────────────────────
        self.visual_rules = {
            "Facebook": (
                "Designer tip: Use an engaging image with a bold question overlay to spark discussion. "
                "Warm, relatable visuals perform best on Facebook."
            ),
            "Twitter": (
                "Designer tip: A sharp meme, a data chart, or a short GIF works great. "
                "Keep it punchy and immediately understandable at a glance."
            ),
            "Instagram": (
                "Designer tip: Create a carousel (3–5 slides) with clean typography and a consistent color palette. "
                "The first slide should hook the viewer; the last should include a clear call-to-action."
            ),
        }

    # ── Reasoning: agent decision-making ─────────────────────────────────────
    def generate_post(self, topic: str, platform: str, tone: str) -> str:
        topic_tag = topic.strip().replace(" ", "")

        # Select the best template based on platform + tone
        if platform in self.templates and tone in self.templates[platform]:
            caption = self.templates[platform][tone].format(
                topic=topic,
                topic_tag=topic_tag,
            )
        else:
            caption = (
                f"Here's a post about {topic} crafted for {platform} "
                f"in a {tone} tone. Adapt and share!"
            )

        # Determine the visual concept
        visual = self.visual_rules.get(
            platform,
            "Use a clear, high-quality image that represents the topic visually."
        )

        # Generate contextual hashtags
        hashtags = f"#{topic_tag} #Trending #SocialMedia #{platform}"

        # ── Actuator: build final output ──────────────────────────────────────
        return (
            f"📝 Caption:\n{caption}\n\n"
            f"#️⃣ Hashtags:\n{hashtags}\n\n"
            f"🎨 Visual Concept:\n{visual}"
        )

# ── Instantiate the agent ─────────────────────────────────────────────────────
agent = SocialMediaAgent()

@app.post("/generate")
def generate_content(request: PostRequest):
    """
    Perception → Reasoning → Action
    Receives sensor inputs, runs the agent, and returns actuator outputs.
    """
    result = agent.generate_post(
        topic=request.topic,
        platform=request.platform,
        tone=request.tone,
    )
    return {"status": "success", "data": result}