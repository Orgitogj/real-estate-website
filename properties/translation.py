from modeltranslation.translator import register, TranslationOptions
from .models import (
    Agent,
    Property,
    PropertyImage,
    PostCategory,
    Post,
    Testimonial,
)


# ───────────────────────────────────────────────────────────────────
# AGENT — bio dhe rolet ndryshojnë sipas gjuhës
# ───────────────────────────────────────────────────────────────────
@register(Agent)
class AgentTranslationOptions(TranslationOptions):
    fields = ('bio', 'role')


# ───────────────────────────────────────────────────────────────────
# PROPERTY — fushat kryesore të pronës
# title është i detyrueshëm vetëm në shqip
# ───────────────────────────────────────────────────────────────────
@register(Property)
class PropertyTranslationOptions(TranslationOptions):
    fields = ('title', 'description', 'location', 'neighborhood')
    required_languages = {'sq': ('title',)}


# ───────────────────────────────────────────────────────────────────
# PROPERTY IMAGE — vetëm caption ndryshon sipas gjuhës
# ───────────────────────────────────────────────────────────────────
@register(PropertyImage)
class PropertyImageTranslationOptions(TranslationOptions):
    fields = ('caption',)


# ───────────────────────────────────────────────────────────────────
# POST CATEGORY — emri i kategorisë ndryshon sipas gjuhës
# ───────────────────────────────────────────────────────────────────
@register(PostCategory)
class PostCategoryTranslationOptions(TranslationOptions):
    fields = ('name',)


# ───────────────────────────────────────────────────────────────────
# POST (Blog) — fushat kryesore të artikullit
# title dhe body janë të detyrueshme vetëm në shqip
# ───────────────────────────────────────────────────────────────────
@register(Post)
class PostTranslationOptions(TranslationOptions):
    fields = ('title', 'body', 'excerpt')
    required_languages = {'sq': ('title', 'body')}


# ───────────────────────────────────────────────────────────────────
# TESTIMONIAL — mesazhi dhe preview ndryshojnë sipas gjuhës
# message_short ekziston në modelin Testimonial si fushë opsionale
# ───────────────────────────────────────────────────────────────────
@register(Testimonial)
class TestimonialTranslationOptions(TranslationOptions):
    fields = ('message', 'message_short')