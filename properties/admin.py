# ═══════════════════════════════════════════════════════════════════
# properties/admin.py
# ═══════════════════════════════════════════════════════════════════

from django.contrib    import admin
from django.utils      import timezone
from django.utils.html import format_html
from django.core.mail  import send_mail
from django.conf       import settings

from modeltranslation.admin import TranslationAdmin, TranslationTabularInline
import properties.translation
from .models import PropertyValuation
from .models import (
    Agent, Property, PropertyImage,
    ContactMessage,
    PostCategory, Post, Comment,
    JobApplication, VisitRequest, Testimonial,
)

admin.site.site_header = "ValorEstate Admin"
admin.site.site_title  = "ValorEstate"
admin.site.index_title = "Paneli i Administrimit"


# ═══════════════════════════════════════════════════════════════════
# AGENT
# ═══════════════════════════════════════════════════════════════════

@admin.register(Agent)
class AgentAdmin(TranslationAdmin):
    list_display  = ['full_name', 'phone', 'email', 'specialization', 'rating', 'sold_count', 'is_active', 'is_featured']
    list_filter   = ['is_active', 'is_featured', 'specialization']
    search_fields = ['full_name', 'email', 'phone']
    list_editable = ['is_active', 'is_featured', 'rating']

    fieldsets = (
        ('Info Personale', {'fields': ('user', 'full_name', 'email', 'phone', 'photo')}),
        ('Info Profesionale', {'fields': ('role', 'specialization', 'bio', 'experience_years', 'rating', 'sold_count')}),
        ('Social Media', {'fields': ('linkedin', 'instagram'), 'classes': ('collapse',)}),
        ('Statuset', {'fields': ('is_active', 'is_featured', 'show_on_about', 'created_at')}),
    )

    def photo_preview(self, obj):
        if obj.pk and obj.photo:
            return format_html('<img src="{}" style="width:80px;height:80px;border-radius:50%;object-fit:cover;border:2px solid #C9A227;">', obj.photo.url)
        return "— Nuk ka foto —"
    photo_preview.short_description = 'Preview Foto'

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['created_at', 'photo_preview']
        return ['created_at']


# ═══════════════════════════════════════════════════════════════════
# PROPERTY IMAGES — Inline
# ═══════════════════════════════════════════════════════════════════

class PropertyImageInline(TranslationTabularInline):
    model           = PropertyImage
    extra           = 3
    fields          = ['image', 'caption', 'is_main', 'order', 'image_preview']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:55px;border-radius:6px;object-fit:cover;">', obj.image.url)
        return "—"
    image_preview.short_description = 'Preview'


# ═══════════════════════════════════════════════════════════════════
# PROPERTY
# ═══════════════════════════════════════════════════════════════════
@admin.register(Property)
class PropertyAdmin(TranslationAdmin):
    list_display    = ['main_img', 'title', 'city', 'type', 'transaction',
                       'price_display', 'area_m2', 'status', 'is_featured', 'available']
    list_filter     = ['type', 'transaction', 'status', 'city',
                       'is_featured', 'available', 'is_new',
                       'parking', 'balcony', 'elevator']
    search_fields   = ['title', 'city', 'location', 'neighborhood']
    list_editable   = ['is_featured', 'available', 'status']
    readonly_fields = ['slug', 'views_count', 'created_at', 'updated_at']
    inlines         = [PropertyImageInline]
    ordering        = ['-created_at']

    class Media:
        js = ('properties/js/property_admin.js',)

    def price_display(self, obj):
        return format_html('<strong style="color:#C9A227;">€{}</strong>', f"{int(obj.price):,}")
    price_display.short_description = 'Çmimi'

    def main_img(self, obj):
        img = obj.get_main_image()
        src = img.image.url if img else (obj.image.url if obj.image else None)
        if src:
            return format_html('<img src="{}" style="width:60px;height:42px;object-fit:cover;border-radius:6px;">', src)
        return "—"
    main_img.short_description = 'Foto'
# ═══════════════════════════════════════════════════════════════════
# CONTACT MESSAGE
# ═══════════════════════════════════════════════════════════════════

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display    = ('name', 'email', 'phone', 'subject', 'status', 'created_at')
    list_filter     = ('status',)
    search_fields   = ('name', 'email', 'subject', 'message')
    readonly_fields = ('name', 'email', 'phone', 'subject', 'message', 'ip_address', 'created_at')
    list_editable   = ('status',)

    def has_add_permission(self, request):
        return False


# ═══════════════════════════════════════════════════════════════════
# BLOG
# ═══════════════════════════════════════════════════════════════════

@admin.register(PostCategory)
class PostCategoryAdmin(TranslationAdmin):
    list_display        = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Post)
class PostAdmin(TranslationAdmin):
    list_display        = ('title', 'category', 'author', 'status', 'views', 'created_at')
    list_filter         = ('status', 'category', 'author')
    search_fields       = ('title', 'body')
    prepopulated_fields = {'slug': ('title',)}
    list_editable       = ('status',)
    date_hierarchy      = 'created_at'
    readonly_fields     = ('views', 'created_at', 'updated_at')

    fieldsets = (
        ('Përmbajtja', {'fields': ('title', 'slug', 'category', 'author', 'image', 'excerpt', 'body')}),
        ('Publikimi', {'fields': ('status', 'published_at')}),
        ('Meta', {'fields': ('views', 'created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display    = ('name', 'email', 'post', 'approved', 'created_at')
    list_filter     = ('approved',)
    list_editable   = ('approved',)
    search_fields   = ('name', 'email', 'body')
    readonly_fields = ('ip_address', 'created_at')
    actions         = ['approve_comments']

    def approve_comments(self, request, queryset):
        queryset.update(approved=True)
    approve_comments.short_description = 'Aprovo komentet e zgjedhura'


# ═══════════════════════════════════════════════════════════════════
# JOB APPLICATION
# ═══════════════════════════════════════════════════════════════════

@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display    = ('full_name', 'position', 'email', 'phone', 'status', 'created_at')
    list_filter     = ('status', 'position')
    search_fields   = ('first_name', 'last_name', 'email', 'phone')
    list_editable   = ('status',)
    readonly_fields = ('first_name', 'last_name', 'email', 'phone', 'position', 'cv', 'ip_address', 'created_at')
    actions         = ['send_acceptance_email', 'send_rejection_email']

    fieldsets = (
        ('Aplikanti', {'fields': ('first_name', 'last_name', 'email', 'phone', 'position', 'cv')}),
        ('Statusi & Shënime', {'fields': ('status', 'notes')}),
        ('Meta', {'fields': ('ip_address', 'created_at'), 'classes': ('collapse',)}),
    )

    def full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'
    full_name.short_description = 'Emri i Plotë'

    def send_acceptance_email(self, request, queryset):
        for app in queryset:
            send_mail(
                subject='ValorEstate — Ftesë për Intervistë',
                message=(f'Përshëndetje {app.first_name},\n\nJu njoftojmë se aplikimi juaj për pozicionin "{app.position}" u shqyrtua me sukses dhe jeni ftuar për intervistë pranë zyrave të ValorEstate.\n\nEkipi ynë do ju kontaktojë së shpejti.\n\nMe respekt,\nEkipi ValorEstate'),
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@valorestate.com'),
                recipient_list=[app.email], fail_silently=True,
            )
            app.status = 'interview'
            app.save()
        self.message_user(request, f'{queryset.count()} email u dërgua me sukses.')
    send_acceptance_email.short_description = 'Dërgo ftesë për intervistë'

    def send_rejection_email(self, request, queryset):
        for app in queryset:
            send_mail(
                subject='ValorEstate — Përgjigje për aplikimin tuaj',
                message=(f'Përshëndetje {app.first_name},\n\nFaleminderit për interesin tuaj për pozicionin "{app.position}".\n\nPas shqyrtimit, ju njoftojmë se nuk mund të vazhdojmë me hapat e mëtejshëm.\n\nJu urojmë suksese!\n\nMe respekt,\nEkipi ValorEstate'),
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@valorestate.com'),
                recipient_list=[app.email], fail_silently=True,
            )
            app.status = 'rejected'
            app.save()
        self.message_user(request, f'{queryset.count()} email u dërgua me sukses.')
    send_rejection_email.short_description = 'Dërgo mesazh refuzimi'


# ═══════════════════════════════════════════════════════════════════
# VISIT REQUEST
# ═══════════════════════════════════════════════════════════════════

@admin.register(VisitRequest)
class VisitRequestAdmin(admin.ModelAdmin):
    list_display    = ('name', 'property', 'agent', 'visit_date', 'status', 'created_at')
    list_filter     = ('status', 'agent')
    search_fields   = ('name', 'phone', 'email', 'property__title')
    list_editable   = ('status',)
    readonly_fields = ('name', 'phone', 'email', 'property', 'agent', 'visit_date', 'message', 'ip_address', 'created_at', 'replied_at')
    actions         = ['confirm_visit', 'reject_visit']

    fieldsets = (
        ('Klienti', {'fields': ('name', 'phone', 'email', 'visit_date', 'message')}),
        ('Prona & Agjenti', {'fields': ('property', 'agent')}),
        ('Statusi & Përgjigja', {'fields': ('status', 'reply', 'replied_at')}),
        ('Meta', {'fields': ('ip_address', 'created_at'), 'classes': ('collapse',)}),
    )

    def save_model(self, request, obj, form, change):
        if change and obj.reply and not obj.replied_at:
            obj.replied_at = timezone.now()
            if obj.email:
                send_mail(
                    subject=f'ValorEstate — Përgjigje për vizitën tuaj: {obj.property.title}',
                    message=(f'Përshëndetje {obj.name},\n\n{obj.reply}\n\nProna: {obj.property.title}\nData: {obj.visit_date or "E papërcaktuar"}\n\nMe respekt,\n{obj.agent.full_name if obj.agent else "Ekipi ValorEstate"}'),
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@valorestate.com'),
                    recipient_list=[obj.email], fail_silently=True,
                )
        super().save_model(request, obj, form, change)

    def confirm_visit(self, request, queryset):
        for visit in queryset:
            visit.status = 'confirmed'
            visit.save()
            if visit.email:
                send_mail(
                    subject='ValorEstate — Vizita juaj u konfirmua!',
                    message=(f'Përshëndetje {visit.name},\n\nVizita juaj për pronën "{visit.property.title}" u konfirmua.\nData: {visit.visit_date or "Do ju njoftojmë"}\nAgjenti: {visit.agent.full_name if visit.agent else "Ekipi ValorEstate"}\n\nMe respekt,\nEkipi ValorEstate'),
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@valorestate.com'),
                    recipient_list=[visit.email], fail_silently=True,
                )
        self.message_user(request, f'{queryset.count()} vizitë/a u konfirmua.')
    confirm_visit.short_description = 'Konfirmo vizitën'

    def reject_visit(self, request, queryset):
        for visit in queryset:
            visit.status = 'rejected'
            visit.save()
            if visit.email:
                send_mail(
                    subject='ValorEstate — Përgjigje për kërkesën tuaj',
                    message=(f'Përshëndetje {visit.name},\n\nFatkeqësisht nuk mund të konfirmojmë vizitën për pronën "{visit.property.title}".\n\nJu lutem na kontaktoni për datë tjetër.\n\nMe respekt,\nEkipi ValorEstate'),
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@valorestate.com'),
                    recipient_list=[visit.email], fail_silently=True,
                )
        self.message_user(request, f'{queryset.count()} vizitë/a u refuzua.')
    reject_visit.short_description = 'Refuzo vizitën'


# ═══════════════════════════════════════════════════════════════════
# TESTIMONIAL
# ═══════════════════════════════════════════════════════════════════

@admin.register(Testimonial)
class TestimonialAdmin(TranslationAdmin):
    list_display    = ('client_name', 'client_city', 'agent_display_col', 'rating_stars', 'status_badge', 'is_featured', 'order', 'created_at')
    list_editable   = ('is_featured', 'order')
    list_filter     = ('status', 'rating', 'is_featured', 'agent')
    search_fields   = ('client_name', 'message', 'agent_label', 'client_email')
    ordering        = ('-created_at',)
    readonly_fields = ('created_at', 'approved_at', 'ip_address')
    actions         = ['approve_selected', 'reject_selected']

    fieldsets = (
        ('Klienti', {'fields': (('client_name', 'client_city'), ('client_email', 'client_phone'))}),
        ('Agjenti', {'fields': ('agent', 'agent_label')}),
        ('Mesazhi', {'fields': ('message', 'message_short', 'rating')}),
        ('Publikimi', {'fields': (('status', 'is_featured', 'order'), ('created_at', 'approved_at', 'ip_address'))}),
    )

    @admin.display(description='Agjenti')
    def agent_display_col(self, obj):
        return obj.agent_display

    @admin.display(description='★')
    def rating_stars(self, obj):
        return '★' * obj.rating + '☆' * (5 - obj.rating)

    @admin.display(description='Statusi')
    def status_badge(self, obj):
        colors = {'pending': '#f59e0b', 'approved': '#10b981', 'rejected': '#ef4444'}
        labels = {'pending': 'Në pritje', 'approved': 'Aprovuar', 'rejected': 'Refuzuar'}
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;border-radius:100px;font-size:0.78rem;font-weight:700">{}</span>',
            colors.get(obj.status, '#999'), labels.get(obj.status, obj.status),
        )

    @admin.action(description='✅ Aprovo të zgjedhurat')
    def approve_selected(self, request, queryset):
        count = 0
        for t in queryset:
            if t.status != Testimonial.STATUS_APPROVED:
                t.approve()
                count += 1
        self.message_user(request, f'{count} testimoniale u aprovuan.')

    @admin.action(description='❌ Refuzo të zgjedhurat')
    def reject_selected(self, request, queryset):
        count = queryset.update(status=Testimonial.STATUS_REJECTED)
        self.message_user(request, f'{count} testimoniale u refuzuan.')


# ═══════════════════════════════════════════════════════════════════
# PROPERTY VALUATION
# ═══════════════════════════════════════════════════════════════════

@admin.register(PropertyValuation)
class PropertyValuationAdmin(admin.ModelAdmin):
    list_display    = ('full_name', 'prop_type', 'area', 'address', 'email', 'phone', 'status', 'created_at')
    list_filter     = ('status', 'prop_type', 'condition')
    search_fields   = ('first_name', 'last_name', 'email', 'address', 'phone')
    list_editable   = ('status',)
    ordering        = ('-created_at',)
    readonly_fields = ('first_name', 'last_name', 'email', 'phone', 'prop_type', 'rooms', 'area', 'period', 'condition', 'parking', 'address', 'ip_address', 'created_at')

    fieldsets = (
        ('Klienti', {'fields': (('first_name', 'last_name'), ('email', 'phone'))}),
        ('Prona', {'fields': ('prop_type', ('rooms', 'area'), ('period', 'condition'), 'parking', 'address')}),
        ('Statusi', {'fields': ('status', 'notes')}),
        ('Meta', {'fields': ('ip_address', 'created_at'), 'classes': ('collapse',)}),
    )

    def has_add_permission(self, request):
        return False