# ═══════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════
from django.http import JsonResponse
import re
import json
from django.shortcuts      import render, redirect, get_object_or_404
from django.contrib        import messages
from django.contrib.auth   import authenticate, login, logout
from django.core.paginator import Paginator
from django.core.mail      import send_mail, BadHeaderError
from django.http           import JsonResponse
from django.utils          import timezone
from django.utils.html     import escape
from django.conf           import settings
from django.db             import models
from django.db.models      import Count
from .models import PropertyValuation   
from django.http import HttpResponse
from django.utils import translation
from django.http import HttpResponseRedirect
from django.urls import translate_url
from .models import (
    Property, PropertyImage,
    Agent,
    ContactMessage,
    Post, PostCategory, Comment,
    JobApplication,
    VisitRequest,
    Testimonial,
)
from .forms import TestimonialForm


# ═══════════════════════════════════════════════════════════════════
# HOMEPAGE
# ═══════════════════════════════════════════════════════════════════

def home(request):
    # Pronat e zgjedhura — nëse nuk ka featured, merr 6 të fundit
    featured_properties = Property.objects.filter(is_featured=True)[:6]
    if not featured_properties:
        featured_properties = Property.objects.all()[:6]

   
    city_counts = {}
    for item in Property.objects.values('city').annotate(c=Count('id')):
        city_counts[item['city']] = item['c']

    # Vetëm testimoniale të aprovuara, të renditura sipas 'order'
    testimonials = (
        Testimonial.objects
        .filter(status=Testimonial.STATUS_APPROVED)
        .select_related('agent')       
        .order_by('order', '-approved_at')[:8]
    )

    context = {
        'featured_properties': featured_properties,
        'apartment_count':     Property.objects.filter(type='apartment').count(),
        'house_count':         Property.objects.filter(type='house').count(),
        'land_count':          Property.objects.filter(type='land').count(),
        'commercial_count':    Property.objects.filter(type='commercial').count(),
        'featured_agents':     Agent.objects.filter(is_active=True, is_featured=True)[:6],
        'partners':            [],
      # BEHET:
        'cities': Property.objects.values_list('city', flat=True).distinct().order_by('city'),
        'city_counts':         city_counts,
        'testimonials':        testimonials,
    }
    return render(request, 'properties/index.html', context)


# ═══════════════════════════════════════════════════════════════════
# FAQET STATIKE
# ═══════════════════════════════════════════════════════════════════

def about(request):
    return render(request, 'properties/about.html', {
        'team_members': Agent.objects.filter(
            is_active=True,
            show_on_about=True,
        ).order_by('-is_featured', 'full_name')[:8],
    })


def privacy_policy(request):
    return render(request, 'properties/privacy_policy.html')

def terms_of_use(request):
    return render(request, 'properties/terms_of_use.html')

def news(request):
    return render(request, 'properties/news.html')
def team(request):
    agents = list(Agent.objects.filter(is_active=True).order_by('-is_featured', 'full_name'))
    for agent in agents:
        r = float(agent.rating)
        agent.rating_display = f"{r:.1f}" if r != int(r) else str(int(r))
    return render(request, 'properties/team.html', {
        'agents': agents,
        'agents_count': Agent.objects.filter(is_active=True).count(),  
    })
# ═══════════════════════════════════════════════════════════════════
# PROPERTY LIST — Lista e pronave me filtrim
# ═══════════════════════════════════════════════════════════════════

def property_list(request):
    properties = Property.objects.filter(available=True)

    # Lexohen parametrat e filtrimit nga URL (?type=apartment&city=tirane...)
    prop_type    = request.GET.get('type',         '')
    transaction  = request.GET.get('transaction',  '')
    city         = request.GET.get('city',         '')
    neighborhood = request.GET.get('neighborhood', '')
    min_price    = request.GET.get('min_price',    '')
    max_price    = request.GET.get('max_price',    '')
    min_area     = request.GET.get('min_area',     '')
    max_area     = request.GET.get('max_area',     '')
    bedrooms     = request.GET.get('bedrooms',     '')
    elevator     = request.GET.get('elevator',     '')
    status       = request.GET.get('status',       '')
    q            = request.GET.get('q',            '')
    sort         = request.GET.get('sort', '-created_at')

    # Aplikohen filtrat një nga një (vetëm nëse janë dhënë)
    if prop_type:    properties = properties.filter(type=prop_type)
    if transaction:  properties = properties.filter(transaction=transaction)
    if city:         properties = properties.filter(city__icontains=city)
    if neighborhood: properties = properties.filter(neighborhood__icontains=neighborhood)
    if min_price:    properties = properties.filter(price__gte=min_price)
    if max_price:    properties = properties.filter(price__lte=max_price)
    if min_area:     properties = properties.filter(area_m2__gte=min_area)
    if max_area:     properties = properties.filter(area_m2__lte=max_area)
    if bedrooms:     properties = properties.filter(bedrooms__gte=bedrooms)
    if elevator == '1': properties = properties.filter(elevator=True)
    if elevator == '0': properties = properties.filter(elevator=False)
    if status:       properties = properties.filter(status=status)

    # Kërkimi me fjale kyce — gjet në titull, adresë, qytet ose ID
    if q:
        properties = properties.filter(
            models.Q(title__icontains=q)    |
            models.Q(location__icontains=q) |
            models.Q(city__icontains=q)     |
            models.Q(pk__icontains=q)
        )

    # Renditja — map nga vlerat e URL-së tek fusha e modelit
    sort_map = {
        'price_asc':  'price',
        'price_desc': '-price',
        'area_asc':   'area_m2',
    }
    properties = properties.order_by(sort_map.get(sort, '-created_at'))

    total_count = properties.count()
    paginator   = Paginator(properties, 6)
    page_obj    = paginator.get_page(request.GET.get('page', 1))

    cities = Property.objects.filter(
        available=True
    ).values_list('city', flat=True).distinct().order_by('city')

    return render(request, 'properties/property_list.html', {
        'properties':     page_obj,
        'cities':         cities,
        'property_types': Property.TYPE_CHOICES,
        'total_count':    total_count,
        
        # Kthehen filtrat aktive tek template (për të ruajtur vlerat e formës)
        
        'active_filters': {
            'type':         prop_type,
            'transaction':  transaction,
            'city':         city,
            'neighborhood': neighborhood,
            'min_price':    min_price,
            'max_price':    max_price,
            'min_area':     min_area,
            'max_area':     max_area,
            'bedrooms':     bedrooms,
            'elevator':     elevator,
            'status':       status,
            'q':            q,
            'sort':         sort,
        },
    })


# ═══════════════════════════════════════════════════════════════════
# PROPERTY DETAIL — Detajet e pronave
# ═══════════════════════════════════════════════════════════════════

def property_detail(request, slug):
    property = get_object_or_404(Property, slug=slug, available=True)

    # Rrit views_count me update direkt 
    Property.objects.filter(pk=property.pk).update(
        views_count=property.views_count + 1
    )

    # Prona të ngjashme — i njëjti lloj dhe qytet
    similar = Property.objects.filter(
        available=True,
        type=property.type,
        city=property.city,
    ).exclude(pk=property.pk).order_by('-is_featured', '-created_at')[:3]

    # Nëse nuk ka 3 të ngjashme, plotësohet me prona të tjera
    if similar.count() < 3:
        similar = Property.objects.filter(
            available=True
        ).exclude(pk=property.pk).order_by('-is_featured', '-created_at')[:3]

    return render(request, 'properties/property_detail.html', {
        'property': property,
        'images':   property.images.all(),
        'similar':  similar,
    })


# ═══════════════════════════════════════════════════════════════════
# CONTACT — Forma e kontaktit
# ═══════════════════════════════════════════════════════════════════

def contact(request):
    success       = False
    errors        = {}
    form_data     = {}
    server_error  = False
    email_warning = False

    if request.method == 'POST':

        # ── Merren të dhënat e formës nepermjet metodes get ────────────────────────────────
        name     = request.POST.get('name',    '').strip()
        email    = request.POST.get('email',   '').strip()
        phone    = request.POST.get('phone',   '').strip()
        subject  = request.POST.get('subject', '').strip()
        message  = request.POST.get('message', '').strip()
        privacy  = request.POST.get('privacy', '')
        honeypot = request.POST.get('website', '')   

        # Ruhen të dhënat dhe plotesohet serish nëse forma ka gabime
        form_data = {
            'name': name, 'email': email,
            'phone': phone, 'subject': subject, 'message': message,
        }

        if honeypot:
            return render(request, 'properties/contact.html', {
                'success': True, 'errors': {}, 'form_data': {},
                'server_error': False, 'email_warning': False,
            })

        # ── Validimi ──────────────────────────────────────────────

        # Emri
        if not name:
            errors['name'] = 'Emri është i detyrueshëm.'
        elif len(name) < 4:
            errors['name'] = 'Emri duhet të ketë të paktën 4 karaktere.'
        elif len(name) > 20:
            errors['name'] = 'Emri nuk mund të jetë më i gjatë se 20 karaktere.'
        elif re.search(r'[<>{}|\\^`]', name):
            errors['name'] = 'Emri përmban karaktere të pavlefshme.'

        # Email
        email_regex = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
        if not email:
            errors['email'] = 'Email-i është i detyrueshëm.'
        elif len(email) > 254:
            errors['email'] = 'Email-i është shumë i gjatë.'
        elif not re.match(email_regex, email):
            errors['email'] = 'Ju lutem vendosni një email të vlefshëm (p.sh. emri@gmail.com).'
        elif '..' in email:
            errors['email'] = 'Email-i nuk është valid.'

        # Validimi per numrin e teleonit
        if phone:
            phone_clean = re.sub(r'[\s\-\(\)\+\.]', '', phone)
            if not phone_clean.isdigit():
                errors['phone'] = 'Numri i telefonit duhet të përmbajë vetëm shifra.'
            elif len(phone_clean) < 10:
                errors['phone'] = 'Numri i telefonit është shumë i shkurtër (min. 10 shifra).'
            elif len(phone_clean) > 15:
                errors['phone'] = 'Numri i telefonit është shumë i gjatë (max. 15 shifra).'

        # Subjekti (opsional)
        if subject and len(subject) > 200:
            errors['subject'] = 'Subjekti nuk mund të jetë më i gjatë se 200 karaktere.'

        # Mesazhi
        if not message:
            errors['message'] = 'Mesazhi është i detyrueshëm.'
        elif len(message) < 10:
            errors['message'] = 'Mesazhi është shumë i shkurtër (min. 10 karaktere).'
        elif len(message) > 5000:
            errors['message'] = f'Mesazhi është shumë i gjatë ({len(message)}/5000 karaktere).'

        # Privacy checkbox
        if not privacy:
            errors['privacy'] = 'Duhet të pranoni politikën e privatësisë për të vazhduar.'

        # Nëse ka gabime → kthe formën me gabimet
        if errors:
            return render(request, 'properties/contact.html', {
                'success': False, 'errors': errors, 'form_data': form_data,
                'server_error': False, 'email_warning': False,
            })

        # ── Ruhen në databazë ──────────────────────────────────────
        subject_final = subject or 'Kontakt nga website'
        admin_email   = getattr(settings, 'CONTACT_EMAIL', 'info@valorestate.com')
        from_email    = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@valorestate.com')

        try:
            contact_msg = ContactMessage.objects.create(
                name       = escape(name),          
                email      = email.lower(),
                phone      = phone,
                subject    = escape(subject_final),
                message    = escape(message),
            )
        except Exception as e:
            print(f'[ValorEstate] DB error: {e}')
            return render(request, 'properties/contact.html', {
                'success': False, 'errors': {}, 'form_data': form_data,
                'server_error': True, 'email_warning': False,
            })

        # ── Dërgo email-et ────────────────────────────────────────
        admin_email_ok  = False
        client_email_ok = False

        admin_body = (
            f"ValorEstate\n{'='*52}\n"
            f"Emri:      {name}\n"
            f"Email:     {email}\n"
            f"Telefon:   {phone if phone else '—'}\n"
            f"Subjekti:  {subject_final}\n"
           # f"IP:        {client_ip}\n"
            f"Data/Ora:  {contact_msg.created_at.strftime('%d/%m/%Y %H:%M')}\n"
            f"{'─'*52}\nMESAZHI:\n{'─'*52}\n{message}\n{'='*52}\n"
            f"Shiko në admin: {request.build_absolute_uri('/admin/properties/contactmessage/')}"
        )

        client_body = (
            f"Përshëndetje {name},\n\n"
            f"Faleminderit që na kontaktuat! Mesazhi juaj u pranua.\n"
            f"Ekipi ynë do ju përgjigjet brenda 24 orëve në: {email}\n"
            f"{('Ose do ju kontaktojë në: ' + phone) if phone else ''}\n\n"
            f"─────────────────────────────────\n"
            f"Subjekti: {subject_final}\nMesazhi juaj:\n{message}\n"
            f"─────────────────────────────────\n\n"
            f"Me respekt,\nEkipi ValorEstate\n"
            f"📍 Rruga Myslym Shyri, Nr. 24, Tiranë\n"
            f"📞 +355 69 000 0000\n✉️  info@valorestate.com"
        )

        # Email tek admin
        try:
            send_mail(
                subject        = f'[ValorEstate] Mesazh i ri nga {name}',
                message        = admin_body,
                from_email     = from_email,
                recipient_list = [admin_email],
                fail_silently  = False,
            )
            admin_email_ok = True
        except BadHeaderError:
           
            contact_msg.status = 'spam'
            contact_msg.save()
        except (ConnectionRefusedError, Exception) as e:
            print(f'[ValorEstate] Admin email error: {e}')

        # Email konfirmimi tek klienti
        try:
            send_mail(
                subject        = 'ValorEstate — Mesazhi juaj u pranua!',
                message        = client_body,
                from_email     = from_email,
                recipient_list = [email],
                fail_silently  = False,
            )
            client_email_ok = True
        except (BadHeaderError, ConnectionRefusedError, Exception) as e:
            print(f'[ValorEstate] Client email error: {e}')

        # Nëse të dyja email-et dështojnë , warning (mesazhi u ruhet në DB)
        if not admin_email_ok and not client_email_ok:
            email_warning = True

        success   = True
        form_data = {}   # pastrohet forma pas suksesit

    return render(request, 'properties/contact.html', {
        'success':       success,
        'errors':        errors,
        'form_data':     form_data,
        'server_error':  server_error,
        'email_warning': email_warning,
    })


# ═══════════════════════════════════════════════════════════════════
# BLOG
# ═══════════════════════════════════════════════════════════════════

def blog(request):
    posts      = Post.objects.filter(status='published').select_related('author', 'category')
    categories = PostCategory.objects.all()
    cat_slug   = request.GET.get('category', '')
    q          = request.GET.get('q', '')

    if cat_slug:
        posts = posts.filter(category__slug=cat_slug)
    if q:
        posts = posts.filter(
            models.Q(title__icontains=q)   |
            models.Q(body__icontains=q)    |
            models.Q(excerpt__icontains=q)
        )

    total     = posts.count()
    paginator = Paginator(posts, 6)
    page_obj  = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'properties/blog_list.html', {
        'posts':      page_obj,
        'categories': categories,
        'active_cat': cat_slug,
        'q':          q,
        'total':      total,
    })


def blog_category(request, slug):
    category   = get_object_or_404(PostCategory, slug=slug)
    posts      = Post.objects.filter(status='published', category=category)
    paginator  = Paginator(posts, 6)
    page_obj   = paginator.get_page(request.GET.get('page', 1))
    categories = PostCategory.objects.all()
    return render(request, 'properties/blog_list.html', {
        'posts':      page_obj,
        'categories': categories,
        'active_cat': slug,
        'category':   category,
        'total':      posts.count(),
    })


def blog_detail(request, slug):
    post     = get_object_or_404(Post, slug=slug, status='published')
    comments = post.comments.filter(approved=True)
    related  = Post.objects.filter(
        status='published', category=post.category
    ).exclude(pk=post.pk)[:3]

    # Rrit views me F() expression — sigurt ndaj race conditions
    Post.objects.filter(pk=post.pk).update(views=models.F('views') + 1)

    comment_success = False
    comment_errors  = {}
    form_data       = {}

    if request.method == 'POST':
        name     = request.POST.get('name',    '').strip()
        email    = request.POST.get('email',   '').strip()
        body     = request.POST.get('body',    '').strip()
        honeypot = request.POST.get('website', '')

        form_data = {'name': name, 'email': email, 'body': body}

        # Anti-spam honeypot
        if honeypot:
            comment_success = True
        else:
            email_regex = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'

            if not name:
                comment_errors['name'] = 'Emri është i detyrueshëm.'
            elif len(name) < 2:
                comment_errors['name'] = 'Emri duhet të jetë të paktën 2 karaktere.'

            if not email:
                comment_errors['email'] = 'Email-i është i detyrueshëm.'
            elif not re.match(email_regex, email):
                comment_errors['email'] = 'Email-i nuk është valid.'

            if not body:
                comment_errors['body'] = 'Komenti është i detyrueshëm.'
            elif len(body) < 5:
                comment_errors['body'] = 'Komenti është shumë i shkurtër.'
            elif len(body) > 1000:
                comment_errors['body'] = 'Komenti nuk mund të jetë më i gjatë se 1000 karaktere.'

            if not comment_errors:
                # Komentet ruhen me approved=False — duhen aprovuar nga admin
                Comment.objects.create(
                    post       = post,
                    name       = name,
                    email      = email,
                    body       = body,
                    approved   = False,
                    ip_address = request.META.get('REMOTE_ADDR'),
                )
                comment_success = True
                form_data       = {}

    return render(request, 'properties/blog_detail.html', {
        'post':            post,
        'comments':        comments,
        'comments_count':  comments.count(),
        'related':         related,
        'comment_success': comment_success,
        'comment_errors':  comment_errors,
        'form_data':       form_data,
    })


# ═══════════════════════════════════════════════════════════════════
# KARRIERA — Aplikime për punë
# ═══════════════════════════════════════════════════════════════════

def karriera(request):
    apply_success = False
    apply_errors  = {}
    apply_data    = {}

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name',  '').strip()
        email      = request.POST.get('email',      '').strip()
        phone      = request.POST.get('phone',      '').strip()
        position   = request.POST.get('position',   '').strip()
        privacy    = request.POST.get('privacy',    '')
        honeypot   = request.POST.get('website',    '')
        cv_file    = request.FILES.get('cv')

        # Ruhet për riplotësim nëse ka gabime
        apply_data = {
            'first_name': first_name, 'last_name': last_name,
            'email': email, 'phone': phone, 'position': position,
        }

        # Anti-spam
        if honeypot:
            apply_success = True
        else:
            email_regex = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'

            if not first_name:
                apply_errors['first_name'] = 'Emri është i detyrueshëm.'
            elif len(first_name) < 2:
                apply_errors['first_name'] = 'Emri duhet të ketë të paktën 2 karaktere.'

            if not last_name:
                apply_errors['last_name'] = 'Mbiemri është i detyrueshëm.'
            elif len(last_name) < 2:
                apply_errors['last_name'] = 'Mbiemri duhet të ketë të paktën 2 karaktere.'

            if not email:
                apply_errors['email'] = 'Email-i është i detyrueshëm.'
            elif not re.match(email_regex, email):
                apply_errors['email'] = 'Email-i nuk është valid.'

            if not phone:
                apply_errors['phone'] = 'Telefoni është i detyrueshëm.'
            else:
                phone_clean = re.sub(r'[\s\-\(\)\+\.]', '', phone)
                if not phone_clean.isdigit() or len(phone_clean) < 6:
                    apply_errors['phone'] = 'Numri i telefonit nuk është valid.'

            if not position:
                apply_errors['position'] = 'Zgjidhni një pozicion.'

            # Validimi i skedarit CV
            if not cv_file:
                apply_errors['cv'] = 'Ju lutem ngarkoni CV-në tuaj.'
            elif cv_file.size > 5 * 1024 * 1024:   # max 5MB
                apply_errors['cv'] = 'Fajlli nuk mund të jetë më i madh se 5MB.'
            elif not cv_file.name.lower().endswith(('.pdf', '.doc', '.docx', '.png', '.jpg', '.jpeg')):
                apply_errors['cv'] = 'Formati i fajllit nuk pranohet. Përdorni PDF, DOC ose imazh.'

            if not privacy:
                apply_errors['privacy'] = 'Duhet të pranoni kushtet e përdorimit.'

            if not apply_errors:
                # ── Ruhet aplikimi në databazë ────────────────────
                application = JobApplication.objects.create(
                    first_name = first_name,
                    last_name  = last_name,
                    email      = email,
                    phone      = phone,
                    position   = position,
                    cv         = cv_file,
                    ip_address = request.META.get('REMOTE_ADDR'),
                )

                # ── Email te HR ──────────────────────────────────
                try:
                    send_mail(
                        subject = (
                            f'[ValorEstate Karriera] Aplikim i ri — '
                            f'{position} nga {first_name} {last_name}'
                        ),
                        message = (
                            f'Aplikim i ri #{application.pk}\n\n'
                            f'Emri: {first_name} {last_name}\n'
                            f'Email: {email}\nTelefon: {phone}\nPozicioni: {position}\n\n'
                            f'Shiko në admin: http://127.0.0.1:8000/admin/'
                            f'properties/jobapplication/{application.pk}/'
                        ),
                        from_email     = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@valorestate.com'),
                        recipient_list = [getattr(settings, 'CAREERS_EMAIL',
                                          getattr(settings, 'CONTACT_EMAIL', 'info@valorestate.com'))],
                        fail_silently  = True,
                    )
                    # ── Email konfirmimi tek aplikanti ────────────
                    send_mail(
                        subject        = 'ValorEstate — Aplikimi juaj u pranua!',
                        message        = (
                            f'Përshëndetje {first_name},\n\n'
                            f'Faleminderit për interesin tuaj për pozicionin "{position}"!\n\n'
                            f'Ekipi ynë do ju kontaktojë brenda 48 orëve.\n\n'
                            f'Me respekt,\nEkipi ValorEstate'
                        ),
                        from_email     = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@valorestate.com'),
                        recipient_list = [email],
                        fail_silently  = True,
                    )
                except Exception as e:
                    print(f'[ValorEstate Karriera] Email error: {e}')

                apply_success = True
                apply_data    = {}

    return render(request, 'properties/karriera.html', {
        'apply_success': apply_success,
        'apply_errors':  apply_errors,
        'apply_data':    apply_data,
    })


# ═══════════════════════════════════════════════════════════════════
# WISHLIST — Lista e të preferuarave
# ═══════════════════════════════════════════════════════════════════

def wishlist(request):
    return render(request, 'properties/wishlist.html')


def wishlist_data(request):
   
    ids_param = request.GET.get('ids', '')
    if not ids_param:
        return JsonResponse({'properties': []})

    try:
        ids = [int(i.strip()) for i in ids_param.split(',') if i.strip().isdigit()]
    except (ValueError, AttributeError):
        return JsonResponse({'properties': []})

    if not ids:
        return JsonResponse({'properties': []})

    properties = Property.objects.filter(
        pk__in=ids
    ).select_related('agent').prefetch_related('images')[:20]

    data = []
    for prop in properties:
        image_url = None
        primary   = prop.images.filter(is_main=True).first()
        if primary:
            image_url = request.build_absolute_uri(primary.image.url)
        elif prop.images.exists():
            image_url = request.build_absolute_uri(prop.images.first().image.url)
        elif prop.image:
            image_url = request.build_absolute_uri(prop.image.url)

        agent_name  = None
        agent_photo = None
        if prop.agent:
            agent_name = prop.agent.full_name
            if prop.agent.photo:
                agent_photo = request.build_absolute_uri(prop.agent.photo.url)

        data.append({
            'id':            prop.pk,
            'title':         prop.title,
            'slug':          prop.slug,
            'price':         str(prop.price),
            'city':          prop.city,
            'address':       prop.location or '',
            'property_type': prop.type,
            'status':        prop.transaction,
            'bedrooms':      prop.bedrooms,
            'bathrooms':     prop.bathrooms,
            'area':          str(prop.area_m2) if prop.area_m2 else None,
            'image':         image_url,
            'agent_name':    agent_name,
            'agent_photo':   agent_photo,
        })

    return JsonResponse({'properties': data})


# ═══════════════════════════════════════════════════════════════════
# VISIT REQUEST — Kërkesë  per vizite prone
# ═══════════════════════════════════════════════════════════════════

def visit_request(request, slug):
    property_obj = get_object_or_404(Property, slug=slug)

    if request.method == 'POST':
        name       = request.POST.get('name',       '').strip()
        phone      = request.POST.get('phone',      '').strip()
        email      = request.POST.get('email',      '').strip()
        visit_date = request.POST.get('visit_date', '') or None
        message    = request.POST.get('message',    '').strip()

        # Kërkohen  emri dhe telefoni
        if name and phone:
            visit = VisitRequest.objects.create(
                property   = property_obj,
                agent      = property_obj.agent,
                name       = name,
                phone      = phone,
                email      = email,
                visit_date = visit_date,
                message    = message,
                ip_address = request.META.get('REMOTE_ADDR'),
            )

            # Njoftohet agjenti me email
            if property_obj.agent and property_obj.agent.email:
                send_mail(
                    subject        = f'[ValorEstate] Kërkesë vizite e re — {property_obj.title}',
                    message        = (
                        f'Kërkesë e re vizite #{visit.pk}\n\n'
                        f'Prona: {property_obj.title}\n'
                        f'Klienti: {name}\nTelefon: {phone}\n'
                        f'Email: {email or "—"}\nData: {visit_date or "—"}\n'
                        f'Mesazhi: {message or "—"}\n\n'
                        f'Menaxho nga dashboard: http://127.0.0.1:8000/dashboard/'
                    ),
                    from_email     = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@valorestate.com'),
                    recipient_list = [property_obj.agent.email],
                    fail_silently  = True,
                )

            # Konfirmo klientin me email
            if email:
                send_mail(
                    subject        = 'ValorEstate — Kërkesa juaj u pranua!',
                    message        = (
                        f'Përshëndetje {name},\n\n'
                        f'Kërkesa juaj për vizitën e pronës "{property_obj.title}" '
                        f'u pranua me sukses.\n'
                        f'Agjenti ynë do ju kontaktojë së shpejti.\n\n'
                        f'Me respekt,\nEkipi ValorEstate'
                    ),
                    from_email     = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@valorestate.com'),
                    recipient_list = [email],
                    fail_silently  = True,
                )
            messages.success(
                request,
                'Kërkesa juaj u dërgua me sukses! Agjenti do ju kontaktojë së shpejti.'
            )
        else:
            messages.error(request, 'Ju lutem plotësoni emrin dhe telefonin.')

    return redirect('property_detail', slug=slug)


# ═══════════════════════════════════════════════════════════════════
# AGENT DASHBOARD — Autentikimi dhe paneli i agjentit
# ═══════════════════════════════════════════════════════════════════

def agent_login(request):
    if request.user.is_authenticated:
        return redirect('agent_dashboard')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user     = authenticate(request, username=username, password=password)

        if user is not None:
            # Kontrollo që ky user ka profil agjenti
            try:
                Agent.objects.get(user=user)
                login(request, user)
                return redirect('agent_dashboard')
            except Agent.DoesNotExist:
                return HttpResponse("Ky user nuk eshte agent")
        else:
            error = 'Username ose fjalëkalimi i pasaktë.'

    return render(request, 'properties/agent_login.html', {'error': error})


def agent_logout(request):
    logout(request)
    return redirect('agent_login')


def agent_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('agent_login')

    # Merr profilin e agjentit nga user-i i kyçur
    try:
        agent = Agent.objects.get(user=request.user)
    except Agent.DoesNotExist:
        return redirect('home')

    # Statistikat e dashboard-it
    total_properties = Property.objects.filter(agent=agent).count()
    total_visits     = VisitRequest.objects.filter(agent=agent).count()
    pending_visits   = VisitRequest.objects.filter(agent=agent, status='pending').count()
    confirmed_visits = VisitRequest.objects.filter(agent=agent, status='confirmed').count()

    visits     = VisitRequest.objects.filter(agent=agent).select_related('property')[:20]
    properties = Property.objects.filter(agent=agent).prefetch_related('images')[:10]

    return render(request, 'properties/agent_dashboard.html', {
        'agent':            agent,
        'total_properties': total_properties,
        'total_visits':     total_visits,
        'pending_visits':   pending_visits,
        'confirmed_visits': confirmed_visits,
        'visits':           visits,
        'properties':       properties,
    })


def visit_action(request, visit_id, action):
    if not request.user.is_authenticated:
        return redirect('agent_login')

    try:
        agent = Agent.objects.get(user=request.user)
    except Agent.DoesNotExist:
        return redirect('home')

    # Sigurohet që vizita i përket këtij agjenti
    visit = get_object_or_404(VisitRequest, pk=visit_id, agent=agent)

    if request.method == 'POST':
        reply = request.POST.get('reply', '').strip()

        if action == 'confirm':
            visit.status  = 'confirmed'
            default_reply = (
                f'Përshëndetje {visit.name},\n\n'
                f'Vizita juaj për pronën "{visit.property.title}" u konfirmua.\n'
                f'Data: {visit.visit_date or "Do ju njoftojmë"}\n\n'
                f'Me respekt,\n{agent.full_name}'
            )
        elif action == 'reject':
            visit.status  = 'rejected'
            default_reply = (
                f'Përshëndetje {visit.name},\n\n'
                f'Fatkeqësisht nuk mund të konfirmojmë vizitën në datën e kërkuar.\n'
                f'Ju lutem na kontaktoni për datë tjetër.\n\n'
                f'Me respekt,\n{agent.full_name}'
            )
        else:
            return redirect('agent_dashboard')

        # Nëse agjenti ka shkruar përgjigje tjeter,përdoret ajo, përndryshe default
        visit.reply      = reply or default_reply
        visit.replied_at = timezone.now()
        visit.save()

        if visit.email:
            send_mail(
                subject        = f'ValorEstate — Përgjigje për vizitën: {visit.property.title}',
                message        = visit.reply,
                from_email     = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@valorestate.com'),
                recipient_list = [visit.email],
                fail_silently  = True,
            )
        messages.success(request, 'Përgjigja u dërgua me sukses!')

    return redirect('agent_dashboard')


# ═══════════════════════════════════════════════════════════════════
# MENAXHIMI I PRONAVE
# ═══════════════════════════════════════════════════════════════════

def agent_property_add(request):
    if not request.user.is_authenticated:
        return redirect('agent_login')
    try:
        agent = Agent.objects.get(user=request.user)
    except Agent.DoesNotExist:
        return redirect('home')

    errors = []
    if request.method == 'POST':
        errors = _save_property(request, agent, None)
        if not errors:
            messages.success(request, 'Prona u shtua me sukses!')
            return redirect('agent_dashboard')

    return render(request, 'properties/agent_property_form.html', {
        'agent': agent, 'action': 'add', 'errors': errors,
    })


def agent_property_edit(request, pk):
    if not request.user.is_authenticated:
        return redirect('agent_login')
    try:
        agent = Agent.objects.get(user=request.user)
    except Agent.DoesNotExist:
        return redirect('home')

    # Sigurohet që prona i përket këtij agjenti
    prop   = get_object_or_404(Property, pk=pk, agent=agent)
    errors = []
    if request.method == 'POST':
        errors = _save_property(request, agent, prop)
        if not errors:
            messages.success(request, 'Ndryshimet u ruajtën me sukses!')
            return redirect('agent_dashboard')

    return render(request, 'properties/agent_property_form.html', {
        'agent': agent, 'action': 'edit', 'property': prop, 'errors': errors,
    })


def agent_property_delete(request, pk):
    if not request.user.is_authenticated:
        return redirect('agent_login')
    try:
        agent = Agent.objects.get(user=request.user)
    except Agent.DoesNotExist:
        return redirect('home')

    prop = get_object_or_404(Property, pk=pk, agent=agent)
    if request.method == 'POST':
        title = prop.title
        prop.delete()
        messages.success(request, f'Prona "{title}" u fshi me sukses.')
    return redirect('agent_dashboard')


def _save_property(request, agent, prop=None):
   
    POST   = request.POST
    FILES  = request.FILES
    errors = []

    # Validim bazë i fushave të detyrueshme
    if not POST.get('title',    '').strip(): errors.append('Titulli është i detyrueshëm.')
    if not POST.get('price',    '').strip(): errors.append('Çmimi është i detyrueshëm.')
    if not POST.get('area_m2',  '').strip(): errors.append('Sipërfaqja është e detyrueshme.')
    if not POST.get('location', '').strip(): errors.append('Adresa është e detyrueshme.')
    if not POST.get('city',     '').strip(): errors.append('Qyteti është i detyrueshëm.')

    if errors:
        return errors

    # Krijohet objekt i ri ose merret ai ekzistues
    is_new = prop is None
    if is_new:
        prop = Property()

    # Plotëso fushat
    prop.agent        = agent
    prop.title        = POST.get('title',       '').strip()
    prop.transaction  = POST.get('transaction', 'sale')
    prop.type         = POST.get('type',        'apartment')
    prop.status       = POST.get('status',      'available')
    prop.furnishing   = POST.get('furnishing',  '')
    prop.description  = POST.get('description', '').strip()
    prop.price        = POST.get('price', 0)
    prop.location     = POST.get('location',     '').strip()
    prop.city         = POST.get('city',         'Tiranë').strip()
    prop.neighborhood = POST.get('neighborhood', '').strip()

    
    def _int(val):
        try:    return int(val) if val else None
        except: return None

    def _dec(val):
        try:
            from decimal import Decimal
            return Decimal(val) if val else None
        except: return None

    prop.area_m2      = int(POST.get('area_m2', 0) or 0)
    prop.bedrooms     = _int(POST.get('bedrooms'))
    prop.bathrooms    = _int(POST.get('bathrooms'))
    prop.floor        = _int(POST.get('floor'))
    prop.total_floors = _int(POST.get('total_floors'))
    prop.year_built   = _int(POST.get('year_built'))
    prop.latitude     = _dec(POST.get('latitude'))
    prop.longitude    = _dec(POST.get('longitude'))

    # Boolean flags , kontrollon nëse checkbox-i është check-uar
    
    prop.is_negotiable    = 'is_negotiable'    in POST
    prop.available        = 'available'        in POST
    prop.is_featured      = 'is_featured'      in POST
    prop.is_new           = 'is_new'           in POST
    prop.parking          = 'parking'          in POST
    prop.balcony          = 'balcony'          in POST
    prop.elevator         = 'elevator'         in POST
    prop.pool             = 'pool'             in POST
    prop.garden           = 'garden'           in POST
    prop.storage          = 'storage'          in POST
    prop.air_conditioning = 'air_conditioning' in POST
    prop.heating          = 'heating'          in POST
    prop.sea_view         = 'sea_view'         in POST
    prop.mountain_view    = 'mountain_view'    in POST
 
   # Foto kryesore
    if 'image' in FILES:
        prop.image = FILES['image']

    prop.save()

    # Foto shtesë 
    if 'extra_images' in FILES:
        for img_file in FILES.getlist('extra_images'):
            PropertyImage.objects.create(
                property = prop,
                image    = img_file,
                is_main  = False,
            )

    return []   


# ═══════════════════════════════════════════════════════════════════
# AGENT DETAIL — Faqja publike e agjentit
# ═══════════════════════════════════════════════════════════════════

def agent_detail(request, pk):
    agent = get_object_or_404(Agent, pk=pk, is_active=True)

    # Filtron pronat e disponueshme të këtij agjenti
    properties = Property.objects.filter(agent=agent, available=True)

    q      = request.GET.get('q',    '').strip()
    type_f = request.GET.get('type', '')
    city_f = request.GET.get('city', '')
    zone_f = request.GET.get('zone', '').strip()

    if q:      properties = properties.filter(title__icontains=q)
    if type_f: properties = properties.filter(type=type_f)
    if city_f: properties = properties.filter(city__icontains=city_f)
    if zone_f: properties = properties.filter(neighborhood__icontains=zone_f)

    # Vlerat për dropdown-et e filtrimit (vetëm per pronat e këtij agjenti)
    all_props = Property.objects.filter(agent=agent, available=True)
    cities    = all_props.values_list('city', flat=True).distinct().order_by('city')
    zones     = (
        all_props.exclude(neighborhood='')
        .values_list('neighborhood', flat=True).distinct().order_by('neighborhood')
    )

    return render(request, 'properties/agent_detail.html', {
        'agent':      agent,
        'properties': properties,
        'cities':     cities,
        'zones':      zones,
        'q':          q,
        'type_f':     type_f,
        'city_f':     city_f,
        'zone_f':     zone_f,
        'total':      properties.count(),
    })


# ═══════════════════════════════════════════════════════════════════
# TESTIMONIALS — Forma publike e dërgimit
# ═══════════════════════════════════════════════════════════════════

def testimonial_submit(request):
    
    form = TestimonialForm(request.POST or None)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        if form.is_valid():
            t            = form.save(commit=False)
            t.status     = Testimonial.STATUS_PENDING
            t.ip_address = request.META.get('REMOTE_ADDR')
            t.save()

            # Njofto adminin me email
            _notify_admin_new_testimonial(t)

            if is_ajax:
                return JsonResponse({'success': True})
            return redirect('testimonial_thanks')

        else:
            # Nese Forma ka gabime
            if is_ajax:
                # Kthehen gabimet si dict {field_name: error_message}
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = error_list[0]   # merr gabimin e parë për çdo fushë
                return JsonResponse({'success': False, 'errors': errors})

            # POST normal me gabime — jep perseri  formën
            return render(request, 'properties/testimonial_form.html', {'form': form})

    # GET — shfaq formën bosh
    return render(request, 'properties/testimonial_form.html', {'form': form})


def _notify_admin_new_testimonial(t):

    try:
        send_mail(
            subject = f'[ValorEstate] Testimonial i ri nga {t.client_name}',
            message = (
                f'Emri: {t.client_name}\n'
                f'Qyteti: {t.client_city}\n'
                f'Agjenti: {t.agent_display}\n'
                f'Vlerësimi: {"★" * t.rating}\n\n'
                f'Mesazhi:\n{t.message}\n\n'
                f'Aprovo ose refuzo nga: /admin/properties/testimonial/'
            ),
            from_email     = settings.DEFAULT_FROM_EMAIL,
            recipient_list = [settings.DEFAULT_FROM_EMAIL],
            fail_silently  = True,
        )
    except Exception:
        pass 
    

def vleresim_prone(request):

    return render(request, 'properties/vleresim_prone.html')
 
 
def vleresim_submit(request):
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Metoda jo e lejuar'}, status=405)
 
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Të dhëna të pavlefshme'}, status=400)
 
    # Validim minimal i fushave të detyrueshme
    required = ['prop_type', 'area', 'address', 'fn', 'ln', 'email', 'phone']
    for field in required:
        if not data.get(field, '').strip():
            return JsonResponse({'success': False, 'error': f'Fusha "{field}" mungon'}, status=400)
 
    try:
        valuation = PropertyValuation.objects.create(
            prop_type  = data.get('prop_type', ''),
            rooms      = data.get('rooms', ''),
            area       = data.get('area', ''),
            period     = data.get('period', ''),
            condition  = data.get('condition', ''),
            parking    = data.get('parking', ''),
            address    = data.get('address', ''),
            first_name = data.get('fn', '').strip(),
            last_name  = data.get('ln', '').strip(),
            email      = data.get('email', '').strip().lower(),
            phone      = data.get('phone', '').strip(),
            ip_address = request.META.get('REMOTE_ADDR'),
        )
 
        # Njoftim tek admin me email
        _notify_admin_valuation(request, valuation)
 
        return JsonResponse({'success': True})
 
    except Exception as e:
        print(f'[ValorEstate Vlerësim] DB error: {e}')
        return JsonResponse({'success': False, 'error': 'Gabim i brendshëm'}, status=500)
 
 
def _notify_admin_valuation(request, v):
    '''Dërgon email tek admin kur vjen kërkesë e re vlerësimi.'''
    try:
        send_mail(
            subject    = f'[ValorEstate] Kërkesë vlerësimi e re — {v.full_name}',
            message    = (
                f'Kërkesë e re vlerësimi #{v.pk}\\n\\n'
                f'Klienti: {v.full_name}\\n'
                f'Email: {v.email}\\n'
                f'Telefon: {v.phone}\\n\\n'
                f'Prona:\\n'
                f'  Lloji: {v.get_prop_type_display()}\\n'
                f'  Dhoma: {v.rooms or "—"}\\n'
                f'  Sipërfaqja: {v.area} m²\\n'
                f'  Periudha: {v.get_period_display() if v.period else "—"}\\n'
                f'  Gjendja: {v.get_condition_display() if v.condition else "—"}\\n'
                f'  Parkimi: {v.get_parking_display() if v.parking else "—"}\\n'
                f'  Adresa: {v.address}\\n\\n'
                f'Shiko në admin: {request.build_absolute_uri("/admin/properties/propertyvaluation/" + str(v.pk) + "/")}'
            ),
            from_email     = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@valorestate.com'),
            recipient_list = [getattr(settings, 'CONTACT_EMAIL', 'info@valorestate.com')],
            fail_silently  = True,
        )
    except Exception:
        pass



def set_language_view(request):
    if request.method == 'POST':
        lang = request.POST.get('language', 'sq')
        next_url = request.POST.get('next', '/')
        for code, _ in [('sq',''), ('en',''), ('it',''), ('el',''), ('fr',''), ('de','')]:
            if next_url.startswith('/' + code + '/'):
                next_url = next_url[len('/' + code):]
                break
        
        if lang != 'sq':
            next_url = '/' + lang + next_url
        
        translation.activate(lang)
        response = HttpResponseRedirect(next_url if next_url else '/')
        response.set_cookie(
            'django_language',
            lang,
            max_age=31536000,
            samesite='Lax'
        )
        request.session['_language'] = lang
        request.session.save()
        return response
    return HttpResponseRedirect('/')