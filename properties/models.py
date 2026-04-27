# ═══════════════════════════════════════════════════════════════════
# Modelet e databazes
# ═══════════════════════════════════════════════════════════════════

from django.db                  import models
from django.contrib.auth.models import User
from django.utils.text          import slugify
from django.utils               import timezone
from django.utils.translation import gettext_lazy as _

# ═══════════════════════════════════════════════════════════════════
# AGENT — Agjentet e kompanise
# ═══════════════════════════════════════════════════════════════════

class Agent(models.Model):

    SPECIALIZATION_CHOICES = [
        ('buying and selling',_('Shitje dhe blerje pronash')),     
        ('rent management',  _ ('Menaxhim i pronave me qera')),
        ('property valuation',_('Vlerësim prone')),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='agent_profile',
        null=True, blank=True,
    )

    full_name        = models.CharField(max_length=100,  verbose_name="Emri i Plotë")
    email            = models.EmailField(                 verbose_name="Email")
    phone            = models.CharField(max_length=20,   verbose_name="Telefon")
    photo            = models.ImageField(
        upload_to='agents/photos/', null=True, blank=True, verbose_name="Foto"
    )
    
    specialization   = models.CharField(
        max_length=50, choices=SPECIALIZATION_CHOICES,
        default='residential', verbose_name="Specializimi"
    )
    bio              = models.TextField(blank=True,               verbose_name="Bio")
    experience_years = models.PositiveIntegerField(default=0,     verbose_name="Vitet e eksperiences")
    rating           = models.DecimalField(
        max_digits=3, decimal_places=1, default=5.0,              verbose_name="Rating"
    )
    sold_count       = models.PositiveIntegerField(default=0,     verbose_name="Prona të Shitura")
    linkedin         = models.URLField(blank=True,                verbose_name="LinkedIn")
    instagram        = models.URLField(blank=True,                verbose_name="Instagram")
    role             = models.CharField(
        max_length=100, default='Agjent Imobiliar',               verbose_name="Roli"
    )

    # Percakton se ku shfaqen agjentet
    is_active     = models.BooleanField(default=True,  verbose_name="Aktiv")
    is_featured   = models.BooleanField(default=False, verbose_name="I Zgjedhur")
    show_on_about = models.BooleanField(default=True,  verbose_name="Shfaq në about")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Agjent"
        verbose_name_plural = "Agjentë"
        ordering            = ['-is_featured', 'full_name']

    def __str__(self):
        return self.full_name

    def get_active_listings(self):
        """Kthen numrin e pronave aktive te ketij agjenti."""
        return self.property_set.filter(available=True).count()


# ═══════════════════════════════════════════════════════════════════
# PROPERTY — Pronat imobiliare
# ═══════════════════════════════════════════════════════════════════

class Property(models.Model):

    TRANSACTION_CHOICES = [
        ('sale', _('Shitje')),
        ('rent', _('Qira')),
    ]

    TYPE_CHOICES = [
        ('apartment', _('Apartament')),
        ('house', _('Shtëpi')),
        ('land', _('Tokë')),
        ('commercial', _('Komerciale')),
        ('villa', _('Vilë')),
        ('garage', _('Garazh')),
    ]

    STATUS_CHOICES = [
        ('available', _('E disponueshme')),
        ('sold', _('Shitur')),
        ('for_rent', _('Për Qira')),
        ('rented', _('Dhënë me qira')),
        ('reserved', _('Rezervuar')),
    ]

    FURNISHING_CHOICES = [
        ('furnished', _('E mobiluar')),
        ('unfurnished', _('Pa mobilje')),
        ('partial', _('Pjesërisht e mobiluar')),
    ]
    # ── Informacion baze rreth prones ──────────────────────────────────────────
    title       = models.CharField(max_length=200,  verbose_name="Titulli")
    slug        = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True,      verbose_name="Përshkrimi")
    transaction = models.CharField(
        max_length=10, choices=TRANSACTION_CHOICES,
        default='sale',                             verbose_name="Tipi"
    )
    type        = models.CharField(
        max_length=20, choices=TYPE_CHOICES,
        default='apartment',                        verbose_name="Lloji i prones"
    )
    status      = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default='available',                        verbose_name="Statusi"
    )

    # ── Çmimi ─────────────────────────────────────────────────────
    price         = models.DecimalField(
        max_digits=12, decimal_places=2,            verbose_name="Çmimi (€)"
    )
    is_negotiable = models.BooleanField(default=False, verbose_name="Çmim i negociueshëm")

    # ── Lokacioni ─────────────────────────────────────────────────
    location     = models.CharField(max_length=200,  verbose_name="Adresa")
    city         = models.CharField(max_length=100, default='Tiranë', verbose_name="Qyteti")
    neighborhood = models.CharField(max_length=100, blank=True,       verbose_name="Lagja/Zona")
    # Koordinatat për Google Maps (opsionale)
    latitude     = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude    = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # ── Karakteristikat ───────────────────────────────────────────
    area_m2      = models.PositiveIntegerField(default=0, verbose_name="Sipërfaqe (m²)")
    bedrooms     = models.PositiveIntegerField(null=True, blank=True, verbose_name="Dhoma gjumi")
    bathrooms    = models.PositiveIntegerField(null=True, blank=True, verbose_name="Banjo")
    floor        = models.IntegerField(null=True,         blank=True, verbose_name="Kati")
    total_floors = models.PositiveIntegerField(null=True, blank=True, verbose_name="Katet totale")
    year_built   = models.PositiveIntegerField(null=True, blank=True, verbose_name="Viti i ndërtimit")
    furnishing   = models.CharField(
        max_length=20, choices=FURNISHING_CHOICES,
        blank=True,                                      verbose_name="Mobilimi"
    )

    # ── Veçorite e prones ne vlere booleane ──────────────────────────────────
    parking          = models.BooleanField(default=False, verbose_name="Parking")
    balcony          = models.BooleanField(default=False, verbose_name="Ballkon")
    elevator         = models.BooleanField(default=False, verbose_name="Ashensor")
    pool             = models.BooleanField(default=False, verbose_name="Pishinë")
    garden           = models.BooleanField(default=False, verbose_name="Kopsht")
    storage          = models.BooleanField(default=False, verbose_name="Depo")
    air_conditioning = models.BooleanField(default=False, verbose_name="Kondicionim")
    heating          = models.BooleanField(default=False, verbose_name="Ngrohje")
    sea_view         = models.BooleanField(default=False, verbose_name="Pamje deti")
    mountain_view    = models.BooleanField(default=False, verbose_name="Pamje mali")

    # ── Foto kryesore  ──────────────────────────────────
    image = models.ImageField(
        upload_to='properties/', blank=True, null=True, verbose_name="Foto Kryesore"
    )

    # ── Lidhja e prones me agjentin qe e ka publikaur ─────────────────────────────────────
    # SET_NULL → nese fshihet agjenti, prones nuk i shfaqet nje agjent
    agent = models.ForeignKey(
        Agent, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name="Agjenti"
    )

    # ── Flags  qe shfaqen ne karten e pronave duke treguar statusin e tyre ─────────────────────────────────────────────────────
    available   = models.BooleanField(default=True,  verbose_name="E Disponueshme")
    is_featured = models.BooleanField(default=False, verbose_name="Featured")
    is_new      = models.BooleanField(default=False, verbose_name="I Ri")
    views_count = models.PositiveIntegerField(default=0, verbose_name="Vizita")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Pronë"
        verbose_name_plural = "Prona"
        ordering            = ['-is_featured', '-created_at']

    def __str__(self):
        return f"{self.title} — {self.city}"

    def save(self, *args, **kwargs):
        """
        Auto-gjenero slug nga titulli nese nuk ekziston.
        Nese slug baze ekziston, shton numer: 'titulli-1', 'titulli-2', ...
        """
        if not self.slug:
            base = slugify(self.title)
            slug = base
            n = 1
            while Property.objects.filter(slug=slug).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def address(self):
        """Adresa e seciles prones"""
        return self.location

    def get_main_image(self):
        """
        Kthen foton kryesore të pronës.
        Prioriteti: PropertyImage me is_main=True → PropertyImage e parë → None
        """
        img = self.images.filter(is_main=True).first()
        if not img:
            img = self.images.first()
        return img


# ═══════════════════════════════════════════════════════════════════
# PROPERTY IMAGE — Imazhet shtese te prones
# ═══════════════════════════════════════════════════════════════════

class PropertyImage(models.Model):
    # Nese fshihet prona, fshihen edhe te gjitha imazhet e saj
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE,
        related_name='images'
    )
    image   = models.ImageField(upload_to='properties/images/', verbose_name="Foto")
    caption = models.CharField(max_length=200, blank=True,      verbose_name="Titulli")
    is_main = models.BooleanField(default=False, verbose_name="Foto Kryesore")
    order   = models.PositiveSmallIntegerField(default=0,       verbose_name="Rendi")

    class Meta:
        verbose_name        = "Foto Prone"
        verbose_name_plural = "Foto Pronash"
        ordering            = ['order', '-is_main']

    def __str__(self):
        return f"Foto — {self.property.title}"

    def save(self, *args, **kwargs):
        """
        Nëse ky imazh shenohet si kryesor (is_main=True),
        hiqet statusi is_main nga te gjithe imazhet e tjera te kesaj prone.
        Keshtu sigurohet qe vetem 1 imazh te jete kryesor ne çdo moment.
        """
        if self.is_main:
            PropertyImage.objects.filter(
                property=self.property, is_main=True
            ).exclude(pk=self.pk).update(is_main=False)
        super().save(*args, **kwargs)


# ═══════════════════════════════════════════════════════════════════
# CONTACT MESSAGE — Mesazhet nga faqja e kontaktit
# ═══════════════════════════════════════════════════════════════════

class ContactMessage(models.Model):
    STATUS_CHOICES = [
        ('new',     'Mesazh i ri'),
        ('read',    'Lexuar'),
        ('replied', 'Pergjigjur'),
        ('spam',    'Spam'),
    ]

    name       = models.CharField(max_length=100)
    email      = models.EmailField()
    phone      = models.CharField(max_length=20, blank=True)
    subject    = models.CharField(max_length=200, blank=True)
    message    = models.TextField()
    status     = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='new'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ['-created_at']
        verbose_name        = 'Mesazh Kontakti'
        verbose_name_plural = 'Mesazhe Kontakti'

    def __str__(self):
        return f'{self.name} — {self.subject or "Pa subjekt"}'


# ═══════════════════════════════════════════════════════════════════
# BLOG — Kategorite, Artikujt, Komentet
# ═══════════════════════════════════════════════════════════════════

class PostCategory(models.Model):
    name       = models.CharField(max_length=100, verbose_name='Emri')
    slug       = models.SlugField(unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Kategori Blogu'
        verbose_name_plural = 'Kategori Blogu'
        ordering            = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Auto-gjenero slug nga emri nese nuk ekziston."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Post(models.Model):
    STATUS_CHOICES = [
        ('draft',     _('Draft')),
        ('published', _('Publiko')),
    ]

    title    = models.CharField(max_length=200, verbose_name='Titulli')
    slug     = models.SlugField(unique=True, blank=True, max_length=220)
    category = models.ForeignKey(
        PostCategory, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='posts', verbose_name='Kategoria'
    )
    
    # Autori eshte nje agjent — SET_NULL nese fshihet agjenti
    author = models.ForeignKey(
        Agent, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='posts', verbose_name='Autori'
    )
    image        = models.ImageField(
        upload_to='blog/', blank=True, null=True, verbose_name='Imazhi kryesor'
    )
    body         = models.TextField(verbose_name='Teksti')
    excerpt      = models.TextField(
        max_length=300, blank=True, verbose_name='Pershkrim i shkurter'
    )
    status       = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default='draft', verbose_name='Statusi'
    )
    views        = models.PositiveIntegerField(default=0, editable=False)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering            = ['-created_at']
        verbose_name        = 'Artikull'
        verbose_name_plural = 'Artikuj'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """
        Auto-gjenero slug nga titulli.
        Auto-gjenero excerpt nga body (250 karakteret e para) nese lihet bosh.
        """
        if not self.slug:
            self.slug = slugify(self.title)
        if not self.excerpt and self.body:
            self.excerpt = self.body[:250] + ('...' if len(self.body) > 250 else '')
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('blog_detail', kwargs={'slug': self.slug})


class Comment(models.Model):
    # Nese fshihet post-i, fshihen edhe komentet e tij
    post       = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='comments'
    )
    name       = models.CharField(max_length=100,  verbose_name='Emri')
    email      = models.EmailField(                verbose_name='Email')
    body       = models.TextField(max_length=1000, verbose_name='Komenti')
    # Komentet jane te fshehura deri sa aprovohne nga admin
    approved   = models.BooleanField(default=False, verbose_name='Aprovuar')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ['created_at']
        verbose_name        = 'Koment'
        verbose_name_plural = 'Komente'

    def __str__(self):
        return f'{self.name} — {self.post.title[:40]}'


# ═══════════════════════════════════════════════════════════════════
# JOB APPLICATION — Aplikime për pozicione pune (Karriera)
# ═══════════════════════════════════════════════════════════════════

class JobApplication(models.Model):
    POSITION_CHOICES = [
        ('Office manager',          'Office Manager'),
        ('Office asistant',         'Office Assistant'),
        ('Real Estate consultant',  'Real Estate Consultant'),
        ('Graphic Designer',        'Graphic Designer'),
        ('Marketing Specialist',    'Marketing Specialist'),
        ('Social media specialist', 'Social Media Specialist'),
    ]
    STATUS_CHOICES = [
        ('new',       'I Ri'),
        ('reviewing', 'Duke Shqyrtuar'),
        ('interview', 'Intervistë'),
        ('accepted',  'Pranuar'),
        ('rejected',  'Refuzuar'),
    ]

    first_name = models.CharField(max_length=100, verbose_name='Emri')
    last_name  = models.CharField(max_length=100, verbose_name='Mbiemri')
    email      = models.EmailField(               verbose_name='Email')
    phone      = models.CharField(max_length=20,  verbose_name='Telefoni')
    position   = models.CharField(
        max_length=50, choices=POSITION_CHOICES,  verbose_name='Pozicioni'
    )
    cv         = models.FileField(upload_to='karriera/cv/', verbose_name='CV')
    status     = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default='new',                            verbose_name='Statusi'
    )
    # Shenime private — vetem per admin, nuk i shfaqen aplikantit
    notes      = models.TextField(blank=True,     verbose_name='Shenime (Admin)')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ['-created_at']
        verbose_name        = 'Aplikim karriere'
        verbose_name_plural = 'Aplikimet e karrierës'

    def __str__(self):
        return f'{self.first_name} {self.last_name} — {self.position}'

    @property
    def full_name(self):
        """Kombinon emrin dhe mbiemrin — perdoret ne admin dhe email."""
        return f'{self.first_name} {self.last_name}'


# ═══════════════════════════════════════════════════════════════════
# VISIT REQUEST — Kerkesa per vizite prone
# ═══════════════════════════════════════════════════════════════════

class VisitRequest(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Ne pritje'),
        ('confirmed', 'Konfirmuar'),
        ('rejected',  'Refuzuar'),
        ('completed', 'Perfunduar'),
    ]

    # Nese fshihet prona, fshihen edhe kerkesat e vizites
    property = models.ForeignKey(
        'Property', on_delete=models.CASCADE,
        related_name='visit_requests', verbose_name='Prona'
    )
    # SET_NULL → nese fshihet agjenti, kerkesa mbetet
    agent    = models.ForeignKey(
        'Agent', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='visit_requests', verbose_name='Agjenti'
    )

    # Te dhënat e klientit
    name       = models.CharField(max_length=100,         verbose_name='Emri')
    phone      = models.CharField(max_length=20,          verbose_name='Telefoni')
    email      = models.EmailField(blank=True,            verbose_name='Email')
    visit_date = models.DateField(null=True, blank=True,  verbose_name='Data e vizitës')
    message    = models.TextField(blank=True,             verbose_name='Mesazhi')

    # Statusi dhe pergjigja e agjentit
    status     = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default='pending',                               verbose_name='Statusi'
    )
    reply      = models.TextField(blank=True,            verbose_name='Përgjigja e agjentit')
    # replied_at vendoset automatikisht kur agjenti dergon pergjigje 
    replied_at = models.DateTimeField(null=True, blank=True, verbose_name='Koha e përgjigjes')

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Krijuar')

    class Meta:
        ordering            = ['-created_at']
        verbose_name        = 'Kërkesë Vizite'
        verbose_name_plural = 'Kërkesat e Vizitave'

    def __str__(self):
        return f'{self.name} → {self.property.title} ({self.get_status_display()})'


# ═══════════════════════════════════════════════════════════════════
# TESTIMONIAL — Përshtypjet e klientëve
# ═══════════════════════════════════════════════════════════════════

class Testimonial(models.Model):

    STATUS_PENDING  = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    RATING_CHOICES = [(i, '★' * i) for i in range(1, 6)]
    STATUS_CHOICES = [
        (STATUS_PENDING,  'Ne pritje'),
        (STATUS_APPROVED, 'Aprovuar'),
        (STATUS_REJECTED, 'Refuzuar'),
    ]

    # ── Te dhenat e klientit ──────────────────────────────────────
    client_name  = models.CharField('Emri', max_length=120)
    client_city  = models.CharField('Qyteti', max_length=80, blank=True)
    # Email dhe telefon ruhen vetem per kontakt — nuk shfaqen publikisht
    client_email = models.EmailField(
        'Email', blank=True, help_text='Nuk shfaqet publikisht'
    )
    client_phone = models.CharField(
        'Telefon', max_length=30, blank=True, help_text='Nuk shfaqet publikisht'
    )

    # ── Agjenti ───────────────────────────────────────────────────
    # SET_NULL → Nese fshihet agjenti, testimoniali mbetet
    agent = models.ForeignKey(
        'Agent',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='testimonials',
        verbose_name='Agjenti',
    )
    # agent_label perdoret kur klienti shkruan emrin manualisht
    # (kur agjenti i tij nuk eshte ne listen dropdown)
    agent_label = models.CharField(
        'Emri Agjentit (manual)', max_length=120, blank=True,
        help_text='Plotësohet nga klienti nëse agjenti nuk është në listë',
    )

    # ── Mesazhi ───────────────────────────────────────────────────
    message = models.TextField('Mesazhi')
    # message_short — preview i shkurter qe shfaqet para "Lexo me shume"
    # nese lihet bosh, merren automatikisht 220 karakteret e para
    message_short = models.TextField(
        'Preview (opsional)', blank=True,
        help_text='Nëse lihet bosh, merren 220 karakteret e para',
    )

    # ── Meta ──────────────────────────────────────────────────────
    rating = models.PositiveSmallIntegerField(
        'Vlerësimi', choices=RATING_CHOICES, default=5
    )
    status = models.CharField(
        'Statusi', max_length=10,
        choices=STATUS_CHOICES, default=STATUS_PENDING,
    )
    is_featured = models.BooleanField('I Zgjedhur', default=False)
    # order — numer i vogel = shfaqet i pari ne homepage
    order       = models.PositiveSmallIntegerField('Rendi', default=0)
    created_at  = models.DateTimeField('Derguar', default=timezone.now)
    # approved_at vendoset nga metoda .approve() ose nga admin
    approved_at = models.DateTimeField('Aprovuar', null=True, blank=True)

    # IP ruhet per kontroll anti-spam (nuk shfaqet publikisht)
    ip_address  = models.GenericIPAddressField(null=True, blank=True, editable=False)

    class Meta:
        verbose_name        = 'Testimonial'
        verbose_name_plural = 'Testimoniale'
        # Renditja: sipas order → i aprovuari i fundit → i krijuari i fundit
        ordering            = ['order', '-approved_at', '-created_at']

    def __str__(self):
        return f'{self.client_name} → {self.agent_display} [{self.get_status_display()}]'

    # ── Properties ────────────────────────────────────────────────

    @property
    def agent_display(self):
        """Emri i agjentit: nga FK nese ekziston, ose nga fusha manuale."""
        if self.agent:
            return self.agent.full_name
        return self.agent_label or '—'

    @property
    def is_approved(self):
        """Kontrollo  nese testimoniali eshte aprovuar."""
        return self.status == self.STATUS_APPROVED

    @property
    def preview(self):
        """
        Teksti i shkurter qe shfaqet para "Lexo me shume".
        Nese message_short është plotesuar ,perdoret ai.
        Nese jo , merren 220 karakteret e para te message.
        """
        if self.message_short:
            return self.message_short
        return self.message[:220] + ('…' if len(self.message) > 220 else '')

    @property
    def has_more(self):
        """A ka tekst shtese pas preview-t (per butonin "Lexo me shume")?"""
        if self.message_short:
            return len(self.message) > len(self.message_short)
        return len(self.message) > 220

    @property
    def remainder(self):
        """Pjesa e mesazhit qe fshihet fillimisht (pas preview-t)."""
        if self.message_short:
            return self.message[len(self.message_short):]
        return self.message[220:]

    def stars_range(self):
        """Per template: {% for star in t.stars_range %}★{% endfor %}"""
        return range(self.rating)

    def empty_stars_range(self):
        """Per template: yjet bosh (☆) deri ne 5."""
        return range(5 - self.rating)

    # ── Metodat e veprimit ────────────────────────────────────────

    def approve(self):
        """
        Aprovo testimonialin dhe regjistro kohen e aprovimit.
        update_fields → perditeson vetem 2 fusha (me efikas se .save() i plote).
        """
        self.status      = self.STATUS_APPROVED
        self.approved_at = timezone.now()
        self.save(update_fields=['status', 'approved_at'])

    def reject(self):
        """Refuzo testimonialin."""
        self.status = self.STATUS_REJECTED
        self.save(update_fields=['status'])
        
        

#Modeli per vleresimin e prones
class PropertyValuation(models.Model):

 
    PROP_TYPE_CHOICES = [
        ('vila',       'Vila Luksoze'),
        ('apartment',  'Apartament'),
        ('land',       'Tokë'),
        ('commercial', 'Dyqan/Komerciale'),
    ]
    PERIOD_CHOICES = [
        ('para_1970',  'Para vitit 1970'),
        ('1971_1990',  'Midis 1971 dhe 1990'),
        ('1991_2010',  'Midis 1991 dhe 2010'),
        ('pas_2010',   'Pas vitit 2010'),
    ]
    CONDITION_CHOICES = [
        ('rinovim',  'Për të rinovuar'),
        ('mesatare', 'Gjendje mesatare'),
        ('mire',     'Gjendje e mirë'),
        ('perfekte', 'Në gjendje perfekte'),
    ]
    PARKING_CHOICES = [
        ('Nuk ka parkim',  'Nuk ka parkim'),
        ('garazh', 'Garazh'),
        ('Parkim publik',  'Parkim publik'),
    ]
    STATUS_CHOICES = [
        ('new',        'E re'),
        ('reviewing',  'Duke u shqyrtuar'),
        ('sent',       'Vlerësim i dërguar'),
        ('closed',     'Mbyllur'),
    ]
 
    # Te dhenat e prones
    prop_type   = models.CharField(max_length=20, choices=PROP_TYPE_CHOICES, verbose_name='Lloji')
    rooms       = models.CharField(max_length=5, blank=True,  verbose_name='Dhoma')
    area        = models.CharField(max_length=20,             verbose_name='Sipërfaqja (m²)')
    period      = models.CharField(max_length=20, choices=PERIOD_CHOICES, blank=True, verbose_name='Periudha')
    condition   = models.CharField(max_length=20, choices=CONDITION_CHOICES, blank=True, verbose_name='Gjendja')
    parking     = models.CharField(max_length=20, choices=PARKING_CHOICES, blank=True, verbose_name='Parkimi')
    address     = models.CharField(max_length=250,            verbose_name='Adresa')
 
    # Te dhenat e klientit
    first_name  = models.CharField(max_length=100, verbose_name='Emri')
    last_name   = models.CharField(max_length=100, verbose_name='Mbiemri')
    email       = models.EmailField(               verbose_name='Email')
    phone       = models.CharField(max_length=30,  verbose_name='Telefon')
 
    # Admin
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name='Statusi')
    notes       = models.TextField(blank=True, verbose_name='Shënime (Admin)')
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering            = ['-created_at']
        verbose_name        = 'Kërkesë Vlerësimi'
        verbose_name_plural = 'Kërkesat e Vlerësimit'
 
    def __str__(self):
        return f'{self.first_name} {self.last_name} — {self.get_prop_type_display()} ({self.address[:40]})'
 
    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'
