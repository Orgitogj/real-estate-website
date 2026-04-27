/* ═══════════════════════════════════════════════════════════════════
     1. MAIN          — navbar, lang switcher (base.html)
     2. WISHLIST CORE — localStorage (i përbashkët për të gjitha faqet)
     3. WISHLIST PAGE — lista e dëshirave 
     4. CONTACT       — forma e kontaktit
     5. KARRIERA      — forma e aplikimit
     6. ABOUT         — counter animacion
     7. BLOG          — list + detail + komente
     8. INDEX         — homepage (stats, filters)
     9. PROPERTY LIST — lista e pronave
    10. PROPERTY DETAIL — forma e vizitës
    11.TEAM
    12.MORTGAGE CALC — llogaritesi i interesit
    13. TESTIMONIALS 
    14. TESTIMONIAL FORM 
    15.VLERESIM PRONE JS
    16.AGENT DASHBOARD
   ═══════════════════════════════════════════════════════════════════ */

'use strict';
/* ═══════════════════════════════════════════════════════════════════
   1. MAIN — Kodi i përbashkët (base.html)
   ═══════════════════════════════════════════════════════════════════ */

window.addEventListener('scroll', function () {
    var navbar = document.querySelector('.custom-navbar');
    if (navbar) navbar.classList.toggle('scrolled', window.scrollY > 40);
});

/* Shënohet si 'active' linku që korrespondon me URL-në aktuale */
document.addEventListener('DOMContentLoaded', function () {
    var path = window.location.pathname;
    document.querySelectorAll('.navbar-nav .nav-link').forEach(function (link) {
        if (link.getAttribute('href') === path) link.classList.add('active');
    });
});

/* ── Language Switcher ── */
document.addEventListener('DOMContentLoaded', function () {
    var toggle = document.getElementById('langToggle');
    var menu   = document.getElementById('langDropdownMenu');
    var parent = toggle ? toggle.closest('.lang-switcher') : null;

    if (!toggle || !menu) return;

    toggle.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        var isOpen = menu.classList.contains('open');
        closeLangDropdown();
        if (!isOpen) {
            menu.classList.add('open');
            parent.classList.add('open');
            toggle.setAttribute('aria-expanded', 'true');
        }
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeLangDropdown();
    });

    document.addEventListener('click', function (e) {
        if (parent && !parent.contains(e.target)) closeLangDropdown();
    });

    /* Keyboard navigation brenda dropdown */
    menu.addEventListener('keydown', function (e) {
        var items = Array.from(menu.querySelectorAll('button.dropdown-item'));
        var idx   = items.indexOf(document.activeElement);
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            items[(idx + 1) % items.length].focus();
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            items[(idx - 1 + items.length) % items.length].focus();
        }
    });

    
    menu.querySelectorAll('.dropdown-item').forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            e.stopPropagation(); 
        });
    });

    function closeLangDropdown() {
        if (!menu || !parent) return;
        menu.classList.remove('open');
        parent.classList.remove('open');
        if (toggle) toggle.setAttribute('aria-expanded', 'false');
    }
});


/* ═══════════════════════════════════════════════════════════════════
   2. WISHLIST CORE 
   ═══════════════════════════════════════════════════════════════════ */

var WL_KEY = 'valorestate_wishlist';  // çelësi në localStorage
var WL_API = '/wishlist-data/';       // endpoint Django për të dhënat

function getWishlist() {
    try { return JSON.parse(localStorage.getItem(WL_KEY) || '[]'); }
    catch(e) { return []; }
}

function saveWishlist(ids) {
    localStorage.setItem(WL_KEY, JSON.stringify(ids));
}


function toggleWish(id) {
    var ids = getWishlist();
    var idx = ids.indexOf(String(id));
    var added;
    if (idx === -1) {
        ids.push(String(id));
        added = true;
        showWishToast('U shtua në listë ');
    } else {
        ids.splice(idx, 1);
        added = false;
        showWishToast('U hoq nga lista');
    }
    saveWishlist(ids);
    updateWishCount();
    return added;
}

/** Kontrollohet nëse një pronë është në wishlist */
function isWished(id) {
    return getWishlist().indexOf(String(id)) !== -1;
}


function initWishButtons() {
    document.querySelectorAll('.ve-card__wish').forEach(function(btn) {
        var id = btn.getAttribute('data-id');
        if (!id) return;
        btn.classList.toggle('active', isWished(id));
        // Largo event-in e vjetër para se të shtosh të riun (parandalon dublikat)
        btn.removeEventListener('click', btn._wishHandler);
        btn._wishHandler = function(e) {
            e.preventDefault();
            e.stopPropagation();
            var wished = toggleWish(id);
            btn.classList.toggle('active', wished);
            // Efekt vizual "bounce" i vogël
            btn.style.transform = 'scale(1.35)';
            setTimeout(function() { btn.style.transform = ''; }, 250);
        };
        btn.addEventListener('click', btn._wishHandler);
    });
}

/** Përditëson numrin e pronave në badge-in e navbar-it */
function updateWishCount() {
    var count = getWishlist().length;
    var badge = document.getElementById('wishNavBadge');
    if (badge) {
        badge.textContent   = count;
        badge.style.display = count > 0 ? 'flex' : 'none';
    }
}


var _wishToastTimer;
function showWishToast(msg) {
    var t = document.getElementById('wlToast');
    if (!t) {
        t = document.createElement('div');
        t.id        = 'wlToast';
        t.className = 'wl-toast';
        document.body.appendChild(t);
    }
    t.textContent = msg;
    t.classList.add('wl-toast--show');
    clearTimeout(_wishToastTimer);
    _wishToastTimer = setTimeout(function() {
        t.classList.remove('wl-toast--show');
    }, 2500);
}

/* Inicializon wishlist kur faqja ngarkohet */
document.addEventListener('DOMContentLoaded', function() {
    initWishButtons();
    updateWishCount();
});

/* ═══════════════════════════════════════════════════════════════════
   3. WISHLIST PAGE — Lista e Dëshirave (wishlist.html)
   ═══════════════════════════════════════════════════════════════════ */

/* IDs e pronave të zgjedhura për krahasim (max 3) */
var compareIds = [];

/**
 * Ngarkohen pronat nga API dhe shfaqen në grid.
 */
function loadWishlist() {
    var ids          = getWishlist();
    var heroCount    = document.getElementById('wlHeroCount');
    var toolbarCount = document.getElementById('wlToolbarCount');
    if (heroCount)    heroCount.textContent    = ids.length;
    if (toolbarCount) toolbarCount.textContent = ids.length;

    if (ids.length === 0) {
        document.getElementById('wlLoading').style.display = 'none';
        document.getElementById('wlEmpty').style.display   = 'flex';
        document.getElementById('wlGrid').style.display    = 'none';
        return;
    }

    /* Dërgohen ID tek Django si query string: /wishlist-data/?ids=1,2,3 */
    fetch(WL_API + '?ids=' + ids.join(','))
        .then(function(r) { return r.json(); })
        .then(function(data) {
            document.getElementById('wlLoading').style.display = 'none';
            if (!data.properties || data.properties.length === 0) {
                document.getElementById('wlEmpty').style.display = 'flex';
                return;
            }
            renderProperties(data.properties);
        })
        .catch(function() {
            document.getElementById('wlLoading').style.display = 'none';
            document.getElementById('wlEmpty').style.display   = 'flex';
        });
}

/**
 * Çdo kartë ka buton fshirje dhe checkbox krahasimi.
 */

function renderProperties(props) {
    const grid = document.getElementById('wlGrid');
    const template = document.getElementById('property-card-template');

    grid.innerHTML = '';

    props.forEach((p) => {
        const clone = template.content.cloneNode(true);

        const card = clone.querySelector('.wl-card');
        card.dataset.id = p.id;

        // IMAGE
        const img = clone.querySelector('.ve-card__img');
        if (p.image) {
            img.src = p.image;
            img.alt = p.title;
        } else {
            img.remove();
        }

        // BADGE
        const badge = clone.querySelector('.ve-card__badges');
        badge.innerHTML = (p.status === 'sale')
            ? '<span class="ve-badge ve-badge--sale">Shitje</span>'
            : '<span class="ve-badge ve-badge--rent">Qira</span>';

        // PRICE
        clone.querySelector('.ve-card__price').textContent =
            '€' + Number(p.price).toLocaleString('sq-AL');

        // TITLE + LINK
        const titleLink = clone.querySelector('.ve-card__title a');
        titleLink.textContent = p.title;
        titleLink.href = '/properties/' + p.slug + '/';

        // LOCATION
        clone.querySelector('.ve-card__location').innerHTML =
            `<i class="fas fa-map-marker-alt"></i> ${p.city}${p.address ? ', ' + p.address : ''}`;

        // SPECS
        const specs = clone.querySelector('.ve-card__specs');
        let specsHTML = '';

        if (p.bedrooms) specsHTML += `<span><i class="fas fa-bed"></i> ${p.bedrooms}</span>`;
        if (p.bathrooms) specsHTML += `<span><i class="fas fa-bath"></i> ${p.bathrooms}</span>`;
        if (p.area) specsHTML += `<span><i class="fas fa-ruler-combined"></i> ${p.area} m²</span>`;

        specs.innerHTML = specsHTML;

        // AGENT
        clone.querySelector('.ve-card__agent-name').textContent =
            p.agent_name || 'ValorEstate';

        const agentImg = clone.querySelector('.ve-card__agent-photo');
        if (p.agent_photo) {
            agentImg.src = p.agent_photo;
        } else {
            agentImg.remove();
        }

        // CTA
        clone.querySelector('.ve-card__cta').href =
            '/properties/' + p.slug + '/';

        // REMOVE BUTTON (FIX)
        const wishBtn = clone.querySelector('.wl-wish-btn');
        wishBtn.setAttribute('data-id', p.id);
        wishBtn.addEventListener('click', function () {
            removeFromWishlist(p.id, wishBtn);
        });

        // COMPARE (FIX)
        const checkbox = clone.querySelector('.wl-compare-input');
        checkbox.setAttribute('data-id', p.id);
        checkbox.addEventListener('change', function () {
            toggleCompare(p.id, checkbox);
        });

        grid.appendChild(clone);
    });

    grid.style.display = 'grid';
}

/** Kthen ikonen sipas llojit të pronës */
function getTypeIcon(type) {
    var icons = {
        'apartment': '', 'house': '', 'land': '',
        'commercial': '', 'villa': '', 'office': ''
    };
    return icons[type] || '';
}


function removeFromWishlist(id, btn) {
    toggleWish(id);
    var card = document.querySelector('.wl-card[data-id="' + id + '"]');
    if (card) {
        card.style.transition = 'all 0.4s ease';
        card.style.opacity    = '0';
        card.style.transform  = 'scale(0.9) translateY(-10px)';
        setTimeout(function() {
            card.remove();
            var remaining    = document.querySelectorAll('.wl-card').length;
            var heroCount    = document.getElementById('wlHeroCount');
            var toolbarCount = document.getElementById('wlToolbarCount');
            if (heroCount)    heroCount.textContent    = remaining;
            if (toolbarCount) toolbarCount.textContent = remaining;
            if (remaining === 0) {
                document.getElementById('wlGrid').style.display  = 'none';
                document.getElementById('wlEmpty').style.display = 'flex';
            }
            /* E heq edhe nga lista e krahasimit nëse ishte zgjedhur */
            var ci = compareIds.indexOf(String(id));
            if (ci !== -1) { compareIds.splice(ci, 1); updateCompareBtn(); }
        }, 400);
    }
}

/* Event listeners për butonat Clear dhe Compare */
document.addEventListener('DOMContentLoaded', function() {
    var clearBtn = document.getElementById('wlClearBtn');
    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            document.getElementById('wlConfirm').style.display = 'flex';
        });
    }
    var compareBtn = document.getElementById('wlCompareBtn');
    if (compareBtn) {
        compareBtn.addEventListener('click', function() { openCompare(); });
    }
    /* Ngarko wishlist vetëm nëse jemi në faqen wishlist */
    if (document.getElementById('wlGrid')) loadWishlist();
});

function closeConfirm() {
    document.getElementById('wlConfirm').style.display = 'none';
}

/** Pastro të gjitha pronat nga wishlist pas konfirmimit */
function confirmClear() {
    saveWishlist([]);
    compareIds = [];
    updateCompareBtn();
    document.getElementById('wlGrid').innerHTML       = '';
    document.getElementById('wlGrid').style.display   = 'none';
    document.getElementById('wlEmpty').style.display  = 'flex';
    document.getElementById('wlHeroCount').textContent    = '0';
    document.getElementById('wlToolbarCount').textContent = '0';
    closeConfirm();
    showWishToast('Lista u pastrua');
    document.querySelectorAll('.ve-card__wish').forEach(function(b) {
        b.classList.remove('active');
    });
}

/**
 * Shton/heq pronën nga lista e krahasimit.
 * Maksimumi 3 prona mund të krahasohen njëkohësisht.
 */
function toggleCompare(id, checkbox) {
    id = String(id);
    if (checkbox.checked) {
        if (compareIds.length >= 3) {
            checkbox.checked = false;
            showWishToast('Maksimumi 3 prona për krahasim');
            return;
        }
        compareIds.push(id);
    } else {
        var ci = compareIds.indexOf(id);
        if (ci !== -1) compareIds.splice(ci, 1);
    }
    updateCompareBtn();
}

/** Shfaq/fsheh butonin "Krahaso" sipas numrit të pronave të zgjedhura */
function updateCompareBtn() {
    var btn   = document.getElementById('wlCompareBtn');
    var count = document.getElementById('wlCompareCount');
    if (!btn || !count) return;
    count.textContent = compareIds.length;
    /* Butoni shfaqet vetëm kur zgjedhim 2 ose 3 prona */
    btn.style.display = compareIds.length >= 2 ? 'inline-flex' : 'none';
}

/**
 * Hap modalin e krahasimit dhe shfaq tabelën.
 * Merr të dhënat nga API dhe i shfaq rresht-për-rresht.
 */
function openCompare() {
    var modal = document.getElementById('wlCompareModal');
    var body  = document.getElementById('wlCompareBody');

    fetch(WL_API + '?ids=' + compareIds.join(','))
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (!data.properties) return;
            var props = data.properties;
            var html  = '<div class="wl-compare-grid wl-compare-grid--' + props.length + '">';

            /* Rreshtat e tabelës — çdo row ka label dhe vlerë për çdo pronë */
            var rows = [
                { lbl: 'Imazhi',    key: 'image',         type: 'img'    },
                { lbl: 'Titulli',   key: 'title',         type: 'text'   },
                { lbl: 'Çmimi',     key: 'price',         type: 'price'  },
                { lbl: 'Qyteti',    key: 'city',          type: 'text'   },
                { lbl: 'Tipi',      key: 'property_type', type: 'text'   },
                { lbl: 'Dhoma',     key: 'bedrooms',      type: 'text'   },
                { lbl: 'Banjo',     key: 'bathrooms',     type: 'text'   },
                { lbl: 'Sipërfaqe', key: 'area',          type: 'area'   },
                { lbl: 'Statusi',   key: 'status',        type: 'status' },
            ];

            /* Header me titujt e pronave */
            html += '<div class="wl-cmp-row wl-cmp-row--header">';
            html += '<div class="wl-cmp-lbl"></div>';
            props.forEach(function(p) {
                html += '<div class="wl-cmp-val wl-cmp-val--head">' + p.title + '</div>';
            });
            html += '</div>';

            /* Rreshtat e të dhënave */
            rows.forEach(function(row) {
                html += '<div class="wl-cmp-row">';
                html += '<div class="wl-cmp-lbl">' + row.lbl + '</div>';
                props.forEach(function(p) {
                    var val = p[row.key] || '—';
                    if (row.type === 'img') {
                        val = p.image
                            ? '<img src="' + p.image + '" alt="' + p.title + '" class="wl-cmp-img">'
                            : '<div class="wl-cmp-img wl-cmp-img--ph"><i class="fas fa-building"></i></div>';
                    } else if (row.type === 'price') {
                        val = '€' + Number(p.price).toLocaleString('sq-AL');
                    } else if (row.type === 'area') {
                        val = p.area ? p.area + ' m²' : '—';
                    } else if (row.type === 'status') {
                        val = p.status === 'sale' ? 'Shitje' : 'Qira';
                    }
                    html += '<div class="wl-cmp-val">' + val + '</div>';
                });
                html += '</div>';
            });

            /* Rreshti i fundit me butonin "Shiko Pronën" */
            html += '<div class="wl-cmp-row">';
            html += '<div class="wl-cmp-lbl"></div>';
            props.forEach(function(p) {
                html += '<div class="wl-cmp-val"><a href="/properties/' + p.slug + '/" class="wl-cmp-btn">Shiko Pronën</a></div>';
            });
            html += '</div></div>';

            body.innerHTML = html;
            modal.style.display = 'flex';
            /* setTimeout i vogël lejon CSS transition të funksionojë */
            setTimeout(function() { modal.classList.add('wl-compare-modal--open'); }, 10);
        });
}

function closeCompare() {
    var modal = document.getElementById('wlCompareModal');
    modal.classList.remove('wl-compare-modal--open');
    setTimeout(function() { modal.style.display = 'none'; }, 300);
}

/* ═══════════════════════════════════════════════════════════════════
   4. CONTACT — Forma e Kontaktit
   ═══════════════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', function () {
    if (!document.getElementById('contactForm')) return;

    document.querySelectorAll('.ct-field__input').forEach(function (input) {
        input.addEventListener('focus', function () {
            this.closest('.ct-field').classList.add('ct-field--focused');
        });
        input.addEventListener('blur', function () {
            this.closest('.ct-field').classList.remove('ct-field--focused');
            if (this.value.trim()) this.closest('.ct-field').classList.add('ct-field--filled');
            else                   this.closest('.ct-field').classList.remove('ct-field--filled');
        });
    });

    var nameEl = document.getElementById('name');
    if (nameEl) {
        nameEl.addEventListener('keypress', function (e) {
            
            if (!/[\p{L}\s'\-]/u.test(e.key) && !isControlKey(e)) {
                e.preventDefault();
                shakefield(this);
            }
        });
        nameEl.addEventListener('paste', function (e) {
            var pasted = (e.clipboardData || window.clipboardData).getData('text');
            if (!/^[\p{L}\s'\-]+$/u.test(pasted)) {
                e.preventDefault();
                shakefield(this);
            }
        });
        nameEl.addEventListener('input', function () {
            
            this.value = this.value.replace(/[^\p{L}\s'\-]/gu, '');
            ctClearError(this);
        });
    }

    var emailEl = document.getElementById('email');
    if (emailEl) {
        emailEl.addEventListener('keypress', function (e) {
            if (!/[a-zA-Z0-9@.\-_+]/.test(e.key) && !isControlKey(e)) {
                e.preventDefault();
                shakefield(this);
            }
        });
        emailEl.addEventListener('paste', function (e) {
            var pasted = (e.clipboardData || window.clipboardData).getData('text');
            if (!/^[a-zA-Z0-9@.\-_+]+$/.test(pasted.trim())) {
                e.preventDefault();
                shakefield(this);
            }
        });
        emailEl.addEventListener('input', function () {
            
            this.value = this.value.replace(/[^a-zA-Z0-9@.\-_+]/g, '');
            ctClearError(this);
        });
    }

    var phoneEl = document.getElementById('phone');
    if (phoneEl) {
        phoneEl.addEventListener('keypress', function (e) {
            if (!/[+\d\s\-()\][]/.test(e.key) && !isControlKey(e)) {
                e.preventDefault();
                shakefield(this);
            }
        });
        phoneEl.addEventListener('paste', function (e) {
            var pasted = (e.clipboardData || window.clipboardData).getData('text');
            if (!/^[+\d\s\-()]+$/.test(pasted.trim())) {
                e.preventDefault();
                shakefield(this);
            }
        });
        phoneEl.addEventListener('input', function () {
            this.value = this.value.replace(/[^+\d\s\-()]/g, '');
            if (this.value.indexOf('+') > 0) {
                this.value = this.value.replace(/\+/g, '');
            }
            ctClearError(this);
        });
    }

    /* MESSAGE — pastrohet gabimi kur fillon të shkruajë perseri ne fushe */
    var msgEl = document.getElementById('message');
    if (msgEl) {
        msgEl.addEventListener('input', function () {
            ctClearError(this);
        });
    }

    var subjectEl = document.getElementById('subject');
    if (subjectEl) {
        subjectEl.addEventListener('change', function () {
            ctClearError(this);
        });
    }

    /* ── Submit — validim i plotë ────────────────────────────────── */
    var form = document.getElementById('contactForm');
    form.addEventListener('submit', function (e) {
        var hasError = false;

        /* ── 1. EMRI ──────────────────────────────────────────────── */
        if (nameEl) {
            ctClearError(nameEl);
            var nameVal = nameEl.value.trim();
            if (!nameVal) {
                ctSetError(nameEl, 'Emri është i detyrueshëm.'); hasError = true;
            } else if (nameVal.length < 2) {
                ctSetError(nameEl, 'Emri duhet të ketë të paktën 2 karaktere.'); hasError = true;
            } else if (nameVal.length > 100) {
                ctSetError(nameEl, 'Emri nuk mund të jetë më i gjatë se 100 karaktere.'); hasError = true;
            } else if (!/^[\p{L}\s'\-]+$/u.test(nameVal)) {
                ctSetError(nameEl, 'Emri mund të përmbajë vetëm shkronja, hapësira dhe vizë.'); hasError = true;
            } else if (/^\s+$/.test(nameVal)) {
                ctSetError(nameEl, 'Emri nuk mund të jetë vetëm hapësira.'); hasError = true;
            } else if (/[\-']{2,}/.test(nameVal)) {
                ctSetError(nameEl, 'Emri nuk mund të ketë dy viza ose apostrofa radhazi.'); hasError = true;
            }
        }

        /* ── 2. EMAIL ─────────────────────────────────────────────── */
        if (emailEl) {
            ctClearError(emailEl);
            var emailVal = emailEl.value.trim();
            if (!emailVal) {
                ctSetError(emailEl, 'Email-i është i detyrueshëm.'); hasError = true;
            } else if (emailVal.length > 254) {
                ctSetError(emailEl, 'Email-i nuk mund të jetë më i gjatë se 254 karaktere.'); hasError = true;
            } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailVal)) {
                ctSetError(emailEl, 'Email-i nuk është i vlefshëm. Shembull: emri@domain.com'); hasError = true;
            } else if ((emailVal.match(/@/g) || []).length > 1) {
                ctSetError(emailEl, 'Email-i mund të ketë vetëm një @ simbol.'); hasError = true;
            } else if (/\.{2,}/.test(emailVal)) {
                ctSetError(emailEl, 'Email-i nuk mund të ketë dy pika radhazi.'); hasError = true;
            } else if (emailVal.startsWith('.') || emailVal.endsWith('.')) {
                ctSetError(emailEl, 'Email-i nuk mund të fillojë ose mbarojë me pikë.'); hasError = true;
            } else {
               
                var parts   = emailVal.split('@');
                var domain  = parts[1] || '';
                var tldPart = domain.split('.');
                var tld     = tldPart[tldPart.length - 1];
                if (!domain.includes('.') || tld.length < 2) {
                    ctSetError(emailEl, 'Domain-i i email-it nuk është i vlefshëm.'); hasError = true;
                }
            }
        }

        /* ── 3. TELEFON ──────────────────────────────── */
if (phoneEl) {
    ctClearError(phoneEl);
    var phoneVal = phoneEl.value.trim();
    if (!phoneVal) {
        ctSetError(phoneEl, 'Numri i telefonit është i detyrueshëm.'); hasError = true;
    } else if (!/^[+\d\s\-()]+$/.test(phoneVal)) {
        ctSetError(phoneEl, 'Telefoni mund të përmbajë vetëm numra, +, hapësira dhe vizë.'); hasError = true;
    } else if (phoneVal.indexOf('+') > 0) {
        ctSetError(phoneEl, 'Simboli + mund të jetë vetëm në fillim të numrit.'); hasError = true;
    } else if ((phoneVal.match(/\+/g) || []).length > 1) {
        ctSetError(phoneEl, 'Numri i telefonit mund të ketë vetëm një + në fillim.'); hasError = true;
    } else if (phoneVal.replace(/\D/g, '').length < 6) {
        ctSetError(phoneEl, 'Numri i telefonit duhet të ketë të paktën 6 shifra.'); hasError = true;
    } else if (phoneVal.replace(/\D/g, '').length > 15) {
        ctSetError(phoneEl, 'Numri i telefonit nuk mund të ketë më shumë se 15 shifra.'); hasError = true;
    } else if (phoneVal.length > 20) {
        ctSetError(phoneEl, 'Numri i telefonit nuk mund të jetë më i gjatë se 20 karaktere.'); hasError = true;
    }
}

        /* ── 4. SUBJEKTI ──────────────────────────────────────────── */
        if (subjectEl) {
            ctClearError(subjectEl);
            if (!subjectEl.value) {
                ctSetError(subjectEl, 'Subjekti është i detyrueshëm. Zgjidhni një opsion.'); hasError = true;
            }
        }

        /* ── 5. MESAZHI ───────────────────────────────────────────── */
        if (msgEl) {
            ctClearError(msgEl);
            var msgVal = msgEl.value.trim();
            if (!msgVal) {
                ctSetError(msgEl, 'Mesazhi është i detyrueshëm.'); hasError = true;
            } else if (msgVal.length < 10) {
                ctSetError(msgEl, 'Mesazhi duhet të ketë të paktën 10 karaktere.'); hasError = true;
            } else if (msgVal.length > 5000) {
                ctSetError(msgEl, 'Mesazhi nuk mund të ketë më shumë se 5000 karaktere (aktualisht ' + msgVal.length + ').'); hasError = true;
            } else if (/^\s+$/.test(msgVal)) {
                ctSetError(msgEl, 'Mesazhi nuk mund të jetë vetëm hapësira.'); hasError = true;
            }
        }

        /* ── 6. PRIVACY CHECKBOX ──────────────────────────────────── */
        var privacy   = form.querySelector('[name="privacy"]');
        var privField = privacy ? privacy.closest('.ct-field') : null;
        if (privacy) {
            if (privField) {
                privField.classList.remove('ct-field--error');
                var privErr = privField.querySelector('.ct-field__error');
                if (privErr) privErr.remove();
            }
            if (!privacy.checked) {
                if (privField) {
                    privField.classList.add('ct-field--error');
                    var s = document.createElement('span');
                    s.className = 'ct-field__error';
                    s.innerHTML = '<i class="fas fa-times-circle"></i> Duhet të pranoni politikën e privatësisë.';
                    privField.appendChild(s);
                }
                hasError = true;
            }
        }

        /* ── 7. HONEYPOT  ─────────────────────────── */
        var honeypot = form.querySelector('[name="website"]');
        if (honeypot && honeypot.value.trim()) {
            e.preventDefault(); return;
        }

        /* ── Ndalohet submit nëse ka gabime ─────────────────────────── */
        if (hasError) {
            e.preventDefault();
            var firstErr = form.querySelector('.ct-field--error');
            if (firstErr) firstErr.scrollIntoView({ behavior: 'smooth', block: 'center' });
            return;
        }

        var btn = form.querySelector('.ct-submit');
        if (btn) {
            btn.innerHTML = '<span>Duke dërguar...</span> <i class="fas fa-spinner fa-spin"></i>';
            btn.disabled  = true;
        }
    });


    function ctSetError(el, msg) {
        var field = el.closest('.ct-field');
        if (!field) return;
        field.classList.add('ct-field--error');
        field.classList.remove('ct-field--focused');
        var existing = field.querySelector('.ct-field__error');
        if (existing) { existing.innerHTML = '<i class="fas fa-times-circle"></i> ' + msg; return; }
        var span = document.createElement('span');
        span.className = 'ct-field__error';
        span.innerHTML = '<i class="fas fa-times-circle"></i> ' + msg;
        field.appendChild(span);
    }

    function ctClearError(el) {
        var field = el.closest('.ct-field');
        if (!field) return;
        field.classList.remove('ct-field--error');
        var err = field.querySelector('.ct-field__error');
        if (err) err.remove();
    }

    function shakefield(el) {
        el.classList.remove('ct-field__shake');
        void el.offsetWidth;
        el.classList.add('ct-field__shake');
        setTimeout(function () { el.classList.remove('ct-field__shake'); }, 400);
    }

    function isControlKey(e) {
        return e.ctrlKey || e.metaKey || e.altKey ||
               ['Backspace', 'Delete', 'Tab', 'Enter', 'Escape',
                'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown',
                'Home', 'End', 'F1', 'F2', 'F3', 'F4', 'F5',
                'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12'].indexOf(e.key) !== -1;
    }

    var meta = document.getElementById('contactMeta');
    if (meta) {
        var hasErrors  = meta.dataset.errors  === 'true';
        var hasSuccess = meta.dataset.success === 'true';

        if (hasErrors && !hasSuccess) {
            var alertEl = document.querySelector('.contact-alert');
            if (alertEl) setTimeout(function () {
                alertEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 150);
        }
        if (hasSuccess) {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }
});
/* ═══════════════════════════════════════════════════════════════════
   5. KARRIERA — Forma e Aplikimit
   ═══════════════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', function() {
    if (!document.getElementById('applyForm')) return;

    AOS.init({ once: true, offset: 50, easing: 'ease-out-cubic', duration: 700 });

    /* ── Drag & Drop / File Upload për CV ─────────────────────── */
    var cvInput        = document.getElementById('cvInput');
    var uploadArea     = document.getElementById('uploadArea');
    var uploadContent  = document.getElementById('uploadContent');
    var uploadSelected = document.getElementById('uploadSelected');
    var uploadFileName = document.getElementById('uploadFileName');

    if (cvInput) {
        cvInput.addEventListener('change', function() {
            if (this.files && this.files[0]) showFile(this.files[0]);
        });
    }

    function showFile(file) {
        /* Validon tipin e skedarit */
        var allowed = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ];
        if (allowed.indexOf(file.type) === -1) {
            krSetError(cvInput, 'Vetëm PDF, DOC ose DOCX lejohen.');
            cvInput.value = '';
            return;
        }
        /* Valido madhësinë — max 5MB */
        if (file.size > 5 * 1024 * 1024) {
            krSetError(cvInput, 'Madhësia maksimale e skedarit është 5 MB.');
            cvInput.value = '';
            return;
        }
        krClearError(cvInput);
        uploadFileName.textContent   = file.name;
        uploadContent.style.display  = 'none';
        uploadSelected.style.display = 'flex';
        uploadArea.classList.add('kr-upload--selected');
    }

    /* Funksion global — thirret nga onclick="removeFile()" në template */
    window.removeFile = function() {
        cvInput.value                = '';
        uploadContent.style.display  = 'flex';
        uploadSelected.style.display = 'none';
        uploadArea.classList.remove('kr-upload--selected');
    };

    /*  Drag & Drop */
    if (uploadArea) {
        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('kr-upload--drag');
        });
        uploadArea.addEventListener('dragleave', function() {
            this.classList.remove('kr-upload--drag');
        });
        uploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('kr-upload--drag');
            var file = e.dataTransfer.files[0];
            if (file) { cvInput.files = e.dataTransfer.files; showFile(file); }
        });
    }

    /* ── Validim para submit-it ─────────────────────────────────── */
    var applyForm   = document.getElementById('applyForm');
    var applySubmit = document.getElementById('applySubmit');

    applyForm.addEventListener('submit', function(e) {
        var hasError = false;

        /* Emri: 2–50 karaktere, vetëm shkronja */
        var firstNameEl = applyForm.querySelector('[name="first_name"]');
        if (firstNameEl) {
            krClearError(firstNameEl);
            var fn = firstNameEl.value.trim();
            if (!fn)           { krSetError(firstNameEl, 'Emri është i detyrueshëm.'); hasError = true; }
            else if (fn.length < 2)  { krSetError(firstNameEl, 'Emri duhet të ketë të paktën 2 karaktere.'); hasError = true; }
            else if (fn.length > 50) { krSetError(firstNameEl, 'Emri nuk mund të jetë më i gjatë se 50 karaktere.'); hasError = true; }
            else if (!/^[\p{L}\s'\-]+$/u.test(fn)) { krSetError(firstNameEl, 'Emri mund të përmbajë vetëm shkronja.'); hasError = true; }
        }

        /* Mbiemri: 2–50 karaktere */
        var lastNameEl = applyForm.querySelector('[name="last_name"]');
        if (lastNameEl) {
            krClearError(lastNameEl);
            var ln = lastNameEl.value.trim();
            if (!ln)           { krSetError(lastNameEl, 'Mbiemri është i detyrueshëm.'); hasError = true; }
            else if (ln.length < 2)  { krSetError(lastNameEl, 'Mbiemri duhet të ketë të paktën 2 karaktere.'); hasError = true; }
            else if (ln.length > 50) { krSetError(lastNameEl, 'Mbiemri nuk mund të jetë më i gjatë se 50 karaktere.'); hasError = true; }
            else if (!/^[\p{L}\s'\-]+$/u.test(ln)) { krSetError(lastNameEl, 'Mbiemri mund të përmbajë vetëm shkronja.'); hasError = true; }
        }

        /* Email */
        var emailEl = applyForm.querySelector('[name="email"]');
        if (emailEl) {
            krClearError(emailEl);
            var ev = emailEl.value.trim();
            if (!ev)                                          { krSetError(emailEl, 'Email-i është i detyrueshëm.'); hasError = true; }
            else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(ev)) { krSetError(emailEl, 'Email-i nuk është i vlefshëm.'); hasError = true; }
            else if (ev.length > 254)                         { krSetError(emailEl, 'Email-i nuk mund të jetë më i gjatë se 254 karaktere.'); hasError = true; }
        }

        /* Telefon: 6–20 karaktere */
        var phoneEl = applyForm.querySelector('[name="phone"]');
        if (phoneEl) {
            krClearError(phoneEl);
            var pv = phoneEl.value.trim();
            if (!pv)                                        { krSetError(phoneEl, 'Telefoni është i detyrueshëm.'); hasError = true; }
            else if (!/^[+\d\s\-()]{6,20}$/.test(pv))      { krSetError(phoneEl, 'Numri i telefonit nuk është i vlefshëm (6–20 karaktere).'); hasError = true; }
        }

        /* Pozicioni: i detyrueshëm */
        var posEl = applyForm.querySelector('[name="position"]');
        if (posEl) {
            krClearError(posEl);
            if (!posEl.value) { krSetError(posEl, 'Zgjidhni një pozicion.'); hasError = true; }
        }

        /* CV: e detyrueshme */
        if (!cvInput || !cvInput.files || !cvInput.files[0]) {
            if (cvInput) krSetError(cvInput, 'Ju lutem ngarkoni CV-në tuaj (PDF/DOC/DOCX, max 5 MB).');
            hasError = true;
        }

        /* Leter motivimi: opsionale, max 2000 karaktere */
        var coverEl = applyForm.querySelector('[name="cover_letter"]');
        if (coverEl && coverEl.value.trim().length > 2000) {
            krClearError(coverEl);
            krSetError(coverEl, 'Letra motivuese nuk mund të ketë më shumë se 2000 karaktere.'); hasError = true;
        }

        /* Privacy: i detyrueshëm */
        var privacy = applyForm.querySelector('[name="privacy"]');
        if (privacy && !privacy.checked) {
            var pf = privacy.closest('.kr-field');
            if (pf) {
                pf.classList.add('kr-field--error');
                if (!pf.querySelector('.kr-field-error')) {
                    var s = document.createElement('span');
                    s.className = 'kr-field-error';
                    s.innerHTML = '<i class="fas fa-times-circle"></i> Duhet të pranoni kushtet.';
                    pf.appendChild(s);
                }
            }
            hasError = true;
        }

        if (hasError) {
            e.preventDefault();
            var firstErr = applyForm.querySelector('.kr-field--error');
            if (firstErr) firstErr.scrollIntoView({ behavior: 'smooth', block: 'center' });
            return;
        }

        /* Loading state gjatë dërgimit */
        if (applySubmit) {
            applySubmit.querySelector('.kr-submit__text').style.display    = 'none';
            applySubmit.querySelector('.kr-submit__loading').style.display = 'inline-flex';
            applySubmit.disabled = true;
        }
    });

    /* Pastrohet  gabimi sapo përdoruesi fillon të shkruajë */
    applyForm.querySelectorAll('.kr-input').forEach(function(el) {
        el.addEventListener('input', function() {
            if (this.value.trim()) krClearError(this);
        });
    });

    function krSetError(el, msg) {
        var field = el.closest('.kr-field');
        if (!field) return;
        field.classList.add('kr-field--error');
        if (!field.querySelector('.kr-field-error')) {
            var span = document.createElement('span');
            span.className = 'kr-field-error';
            span.innerHTML = '<i class="fas fa-times-circle"></i> ' + msg;
            field.appendChild(span);
        }
    }
    function krClearError(el) {
        var field = el.closest('.kr-field');
        if (!field) return;
        field.classList.remove('kr-field--error');
        var err = field.querySelector('.kr-field-error');
        if (err) err.remove();
    }

    var meta = document.getElementById('karrieraMeta');
    if (meta) {
        karrieraHandleSuccess(meta.dataset.success === 'true');
        karrieraHandleErrors(meta.dataset.errors   === 'true');
    }
});

/** Ndryshon pozicionin në dropdown kur klikohet një kartë pozicioni */
function setPosition(pos) {
    var sel = document.getElementById('positionSelect');
    if (sel) {
        sel.value = pos;
        sel.closest('.kr-field').classList.remove('kr-field--error');
    }
}

function karrieraHandleSuccess(applySuccess) {
    if (!applySuccess) return;
    var alertEl = document.getElementById('successAlert');
    var formEl  = document.getElementById('applyForm');
    setTimeout(function() { alertEl.scrollIntoView({ behavior: 'smooth', block: 'center' }); }, 150);
    setTimeout(function() {
        alertEl.style.transition = 'opacity 0.6s ease';
        alertEl.style.opacity    = '0';
        setTimeout(function() {
            alertEl.style.display   = 'none';
            formEl.reset();
            formEl.style.opacity    = '0';
            formEl.style.transition = 'opacity 0.6s ease';
            setTimeout(function() { formEl.style.opacity = '1'; }, 30);
        }, 600);
    }, 4000);
}

function karrieraHandleErrors(hasErrors) {
    if (!hasErrors) return;
    setTimeout(function() {
        var err = document.querySelector('.kr-alert--error');
        if (err) err.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 150);
}

/* Counter animacion për statistikat e karrierës (.kr-stat__num) */
document.addEventListener('DOMContentLoaded', function() {
    if (!document.querySelector('.kr-stat__num')) return;

    function animateCounter(el) {
        var raw    = el.textContent.trim();
        var target = parseInt(raw.replace(/\D/g, ''), 10);
        var suffix = raw.replace(/[\d\s]/g, '');
        if (isNaN(target)) return;
        var duration = 1800, step = 16;
        var increment = target / (duration / step);
        var current = 0;
        var timer = setInterval(function() {
            current += increment;
            if (current >= target) { current = target; clearInterval(timer); }
            el.textContent = Math.floor(current) + suffix;
        }, step);
    }

    /* Animacioni fillon vetëm kur elementi bëhet i dukshëm */
    var observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (!entry.isIntersecting) return;
            animateCounter(entry.target);
            observer.unobserve(entry.target);  
        });
    }, { threshold: 0.5 });

    document.querySelectorAll('.kr-stat__num').forEach(function(el) { observer.observe(el); });
});


/* ═══════════════════════════════════════════════════════════════════
   6. ABOUT 
   ═══════════════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', function() {
    if (!document.querySelector('.ab-stat__num')) return;

    AOS.init({ once: true, offset: 60, easing: 'ease-out-cubic' });

    /* Lexohet numri target nga data-count="" dhe behet animacioni  nga 0 deri ne ate numer */
    var observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(e) {
            if (!e.isIntersecting) return;
            var el     = e.target;
            var target = parseInt(el.dataset.count);
            var current = 0, steps = 60, inc = target / steps;
            var timer = setInterval(function() {
                current += inc;
                if (current >= target) { el.textContent = target; clearInterval(timer); }
                else                   { el.textContent = Math.floor(current); }
            }, 1800 / steps);
            observer.unobserve(el);
        });
    }, { threshold: 0.5 });

    document.querySelectorAll('.ab-stat__num').forEach(function(c) { observer.observe(c); });
});

/* ═══════════════════════════════════════════════════════════════════
   7. BLOG — List, Detail, Komente
   ═══════════════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', function() {
    /* Ekzekutohet vetëm nëse jemi në faqet e blogut */
    if (!document.getElementById('blPageInput') &&
        !document.querySelector('[name="body"]') &&
        !document.getElementById('blogMeta')) return;

    AOS.init({ once: true, offset: 40, easing: 'ease-out-cubic', duration: 600 });

    /* Navigim me keyboard tek input-i i faqes (blog list pagination) */
    var blPageInput = document.getElementById('blPageInput');
    if (blPageInput) {
        blPageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                var page = parseInt(this.value), max = parseInt(this.max);
                if (page >= 1 && page <= max) {
                    var p = new URLSearchParams(window.location.search);
                    p.set('page', page);
                    window.location.search = p.toString();
                }
            }
        });
    }

    /* ── Forma e komenteve (blog detail) ─────────────────────── */
    var commentForm = document.querySelector('.bd-comment-form, form[id*="comment"]');
    if (commentForm) {
        commentForm.addEventListener('submit', function(e) {
            var hasError = false;

            /* Emri: 2–100 karaktere */
            var authorEl = commentForm.querySelector('[name="author"], [name="name"]');
            if (authorEl) {
                bdClearError(authorEl);
                var av = authorEl.value.trim();
                if (!av)            { bdSetError(authorEl, 'Emri është i detyrueshëm.'); hasError = true; }
                else if (av.length < 2)   { bdSetError(authorEl, 'Emri duhet të ketë të paktën 2 karaktere.'); hasError = true; }
                else if (av.length > 100) { bdSetError(authorEl, 'Emri nuk mund të jetë më i gjatë se 100 karaktere.'); hasError = true; }
            }

            /* Email: opsional, por nëse plotësohet — format valid */
            var emailEl = commentForm.querySelector('[name="email"]');
            if (emailEl && emailEl.value.trim()) {
                bdClearError(emailEl);
                if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailEl.value.trim())) {
                    bdSetError(emailEl, 'Email-i nuk është i vlefshëm.'); hasError = true;
                }
            }

            /* Teksti: 5–1000 karaktere */
            var bodyEl = commentForm.querySelector('[name="body"]');
            if (bodyEl) {
                bdClearError(bodyEl);
                var bv = bodyEl.value.trim();
                if (!bv)            { bdSetError(bodyEl, 'Komenti është i detyrueshëm.'); hasError = true; }
                else if (bv.length < 5)    { bdSetError(bodyEl, 'Komenti duhet të ketë të paktën 5 karaktere.'); hasError = true; }
                else if (bv.length > 1000) { bdSetError(bodyEl, 'Komenti nuk mund të ketë më shumë se 1000 karaktere.'); hasError = true; }
            }

            if (hasError) {
                e.preventDefault();
                var firstErr = commentForm.querySelector('.bd-field--error');
                if (firstErr) firstErr.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        });

        /* Pastrohen gabimet sapo perdoruesi fillon të shkruajë */
        commentForm.querySelectorAll('input, textarea').forEach(function(el) {
            el.addEventListener('input', function() { bdClearError(this); });
        });
    }

    function bdSetError(el, msg) {
        var field = el.closest('.bd-field, .bd-comment-field, div');
        if (!field) return;
        field.classList.add('bd-field--error');
        if (!field.querySelector('.bd-field-error')) {
            var span = document.createElement('span');
            span.className = 'bd-field-error';
            span.style.cssText = 'display:block;margin-top:4px;font-size:.78rem;color:#e74c3c;';
            span.innerHTML = '<i class="fas fa-times-circle"></i> ' + msg;
            field.appendChild(span);
        }
    }
    function bdClearError(el) {
        var field = el.closest('.bd-field, .bd-comment-field, div');
        if (!field) return;
        field.classList.remove('bd-field--error');
        var err = field.querySelector('.bd-field-error');
        if (err) err.remove();
    }

    /* Counter karakteresh për komentin */
    var commentArea = document.querySelector('[name="body"]');
    var commentChar = document.getElementById('commentChar');
    if (commentArea && commentChar) {
        function updateCommentChar() {
            var len = commentArea.value.length;
            commentChar.textContent = len + ' / 1000';
            commentChar.style.color = len > 900 ? '#dc2626' : len > 800 ? '#e67e22' : '#b5afa7';
        }
        commentArea.addEventListener('input', updateCommentChar);
        updateCommentChar();
    }

    window.copyLink = function() {
        navigator.clipboard.writeText(window.location.href).then(function() {
            var btn = document.querySelector('.bd-share-btn--copy');
            btn.innerHTML = '<i class="fas fa-check"></i>';
            setTimeout(function() { btn.innerHTML = '<i class="fas fa-link"></i>'; }, 2000);
        });
    };

    var blogMeta = document.getElementById('blogMeta');
    if (blogMeta) blogScrollToComments(blogMeta.dataset.scroll === 'true');
});

function blogScrollToComments(hasSuccessOrErrors) {
    if (hasSuccessOrErrors) {
        setTimeout(function() {
            var el = document.getElementById('comments');
            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 200);
    }
}

/* ═══════════════════════════════════════════════════════════════════
   8. INDEX — Faqja Kryesore (Homepage)
   ═══════════════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', function() {
    if (!document.querySelector('.ve-stats__num') && !document.querySelector('.ve-filter')) return;
    AOS.init({ once: true, offset: 60, easing: 'ease-out-cubic' });

    var statsObserver = new IntersectionObserver(function(entries) {
        entries.forEach(function(e) {
            if (!e.isIntersecting) return;
            var el = e.target, target = parseInt(el.dataset.count);
            var current = 0, steps = 60, inc = target / steps;
            var timer = setInterval(function() {
                current += inc;
                if (current >= target) { el.textContent = target; clearInterval(timer); }
                else                   { el.textContent = Math.floor(current); }
            }, 1800 / steps);
            statsObserver.unobserve(el);
        });
    }, { threshold: 0.5 });

    document.querySelectorAll('.ve-stats__num').forEach(function(c) { statsObserver.observe(c); });

    /* Filter buttons — fsheh/shfaq kartat sipas tipit ose transaksionit */
    document.querySelectorAll('.ve-filter').forEach(function(btn) {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.ve-filter').forEach(function(b) { b.classList.remove('active'); });
            this.classList.add('active');
            var f = this.dataset.filter;
            document.querySelectorAll('.ve-card').forEach(function(card) {
                card.style.display =
                    (f === 'all' || card.dataset.transaction === f || card.dataset.type === f)
                    ? '' : 'none';
            });
        });
    });

    window.addEventListener('scroll', function() {
        var si = document.querySelector('.ve-hero__scroll');
        if (si) si.style.opacity = window.scrollY > 80 ? '0' : '1';
    });
});


/* ═══════════════════════════════════════════════════════════════════
   9. PROPERTY LIST — Lista e Pronave
   ═══════════════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', function() {
    if (!document.getElementById('fpWrap') && !document.getElementById('pageInput')) return;

    AOS.init({ once: true, offset: 40, easing: 'ease-out-cubic', duration: 600 });

    /* Inicializon butonat wish për kartat e reja */
    if (typeof initWishButtons === 'function') initWishButtons();

    window.addEventListener('scroll', function() {
        var fpWrap = document.getElementById('fpWrap');
        if (fpWrap) fpWrap.classList.toggle('fp-wrap--scrolled', window.scrollY > 300);
    });

    var pageInput = document.getElementById('pageInput');
    if (pageInput) {
        pageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                var page = parseInt(this.value), max = parseInt(this.max);
                if (page >= 1 && page <= max) {
                    var params = new URLSearchParams(window.location.search);
                    params.set('page', page);
                    window.location.search = params.toString();
                }
            }
        });
    }
});

function toggleFilter() {
    document.getElementById('fpWrap').classList.toggle('fp-wrap--open');
}


/* ═══════════════════════════════════════════════════════════════════
   10. PROPERTY DETAIL — Forma e Vizitës
   ═══════════════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', function() {
    if (!document.querySelector('.pd-visit-form')) return;

    AOS.init({ once: true, offset: 60, easing: 'ease-out-cubic' });

    var visitDate = document.querySelector('[name="visit_date"]');
    if (visitDate) {
        var today = new Date().toISOString().split('T')[0];
        var maxDt = new Date(); maxDt.setFullYear(maxDt.getFullYear() + 1);
        visitDate.min = today;
        visitDate.max = maxDt.toISOString().split('T')[0];
    }

    /* ── Validim i formës ─────────────────────────────────────── */
    var visitForm = document.querySelector('.pd-visit-form form');
    if (visitForm) {
        visitForm.addEventListener('submit', function(e) {
            var hasError = false;

            /* Emri: 2–100 karaktere */
            var nameEl = this.querySelector('[name="name"]');
            if (nameEl) {
                pdClearError(nameEl);
                var nv = nameEl.value.trim();
                if (!nv)            { pdSetError(nameEl, 'Emri është i detyrueshëm.'); hasError = true; }
                else if (nv.length < 2)   { pdSetError(nameEl, 'Emri duhet të ketë të paktën 2 karaktere.'); hasError = true; }
                else if (nv.length > 100) { pdSetError(nameEl, 'Emri nuk mund të jetë më i gjatë se 100 karaktere.'); hasError = true; }
            }

            /* Email: format valid, max 254 */
            var emailEl = this.querySelector('[name="email"]');
            if (emailEl) {
                pdClearError(emailEl);
                var ev = emailEl.value.trim();
                if (!ev)                                           { pdSetError(emailEl, 'Email-i është i detyrueshëm.'); hasError = true; }
                else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(ev))  { pdSetError(emailEl, 'Email-i nuk është i vlefshëm.'); hasError = true; }
                else if (ev.length > 254)                          { pdSetError(emailEl, 'Email-i nuk mund të jetë më i gjatë se 254 karaktere.'); hasError = true; }
            }

            /* Telefon: 6–20 karaktere */
            var phoneEl = this.querySelector('[name="phone"]');
            if (phoneEl) {
                pdClearError(phoneEl);
                var pv = phoneEl.value.trim();
                if (!pv)                                      { pdSetError(phoneEl, 'Numri i telefonit është i detyrueshëm.'); hasError = true; }
                else if (!/^[+\d\s\-()]{6,20}$/.test(pv))    { pdSetError(phoneEl, 'Numri i telefonit nuk është i vlefshëm (6–20 karaktere).'); hasError = true; }
            }

            /* Data e vizitës: opsionale, por nuk mund të jetë në të shkuarën */
            var vd = this.querySelector('[name="visit_date"]');
            if (vd && vd.value) {
                pdClearError(vd);
                var todayStr = new Date().toISOString().split('T')[0];
                if (vd.value < todayStr) { pdSetError(vd, 'Data nuk mund të jetë në të shkuarën.'); hasError = true; }
                else if (vd.value > vd.max) { pdSetError(vd, 'Data nuk mund të jetë më shumë se 1 vit përpara.'); hasError = true; }
            }

            /* Mesazhi: opsional, max 1000 karaktere */
            var msgEl = this.querySelector('[name="message"]');
            if (msgEl && msgEl.value.trim().length > 1000) {
                pdClearError(msgEl);
                pdSetError(msgEl, 'Mesazhi nuk mund të ketë më shumë se 1000 karaktere.'); hasError = true;
            }

            if (hasError) {
                e.preventDefault();
                var firstErr = visitForm.querySelector('.pd-vf-input--error');
                if (firstErr) firstErr.scrollIntoView({ behavior: 'smooth', block: 'center' });
                return;
            }

            /* Loading state */
            var btn      = document.getElementById('visitSubmitBtn');
            var textSpan = btn && btn.querySelector('.pd-vf-btn__text');
            var loadSpan = btn && btn.querySelector('.pd-vf-btn__loading');
            if (btn) {
                if (textSpan) textSpan.style.display = 'none';
                if (loadSpan) loadSpan.style.display = 'inline-flex';
                btn.disabled = true;
            }
        });

        /* Pastrohen  gabimet sapo ndryshon vlera */
        visitForm.querySelectorAll('.pd-vf-input').forEach(function(el) {
            el.addEventListener('input', function() { pdClearError(this); });
        });
    }

    function pdSetError(el, msg) {
        el.classList.add('pd-vf-input--error');
        var wrap = el.closest('.pd-vf-field');
        if (!wrap) return;
        if (!wrap.querySelector('.pd-vf-error')) {
            var span = document.createElement('span');
            span.className = 'pd-vf-error';
            span.innerHTML = '<i class="fas fa-times-circle"></i> ' + msg;
            wrap.appendChild(span);
        }
    }
    function pdClearError(el) {
        el.classList.remove('pd-vf-input--error');
        var wrap = el.closest('.pd-vf-field');
        if (!wrap) return;
        var err = wrap.querySelector('.pd-vf-error');
        if (err) err.remove();
    }
});


/* ═══════════════════════════════════════════════════════════════════
   11. TEAM 
   ═══════════════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', function() {
    if (!document.querySelector('.tm-stat__num')) return;

    AOS.init({ once: true, offset: 40, easing: 'ease-out-cubic', duration: 700 });

    function animateCounter(el) {
        var raw    = el.textContent.trim();
        var target = parseInt(raw.replace(/\D/g, ''), 10);
        var suffix = raw.replace(/[\d\s]/g, '');    // p.sh. '+' ose 'Vjet'
        if (isNaN(target)) return;
        var duration = 1800, step = 16;
        var increment = target / (duration / step);
        var current = 0;
        var timer = setInterval(function() {
            current += increment;
            if (current >= target) { current = target; clearInterval(timer); }
            el.textContent = Math.floor(current) + suffix;
        }, step);
    }

    var observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (!entry.isIntersecting) return;
            animateCounter(entry.target);
            observer.unobserve(entry.target);
        });
    }, { threshold: 0.5 });

    document.querySelectorAll('.tm-stat__num').forEach(function(el) { observer.observe(el); });
});


/* ═══════════════════════════════════════════════════════════════════
   12.MORTGAGE CALCULATOR — Kalkulatori i Kredisë
   ═══════════════════════════════════════════════════════════════════ */

function showErr(id, msg) {
  var el = document.getElementById(id);
  if (!el) return;
  el.querySelector('span').textContent = msg;
  el.style.display = 'flex';
  document.getElementById(id.replace('err-', '')).classList.add('mort-input--error');
}

function clearErrs() {
  ['mortPrice', 'mortDown', 'mortYears', 'mortRate'].forEach(function(id) {
    var inp = document.getElementById(id);
    if (inp) inp.classList.remove('mort-input--error');
    var err = document.getElementById('err-' + id);
    if (err) err.style.display = 'none';
  });
}

function fmt(n) {
  return '€' + Math.round(n).toLocaleString('sq-AL');
}

function calcMortgage() {
  clearErrs();

  var priceVal = document.getElementById('mortPrice').value.trim();
  var downVal  = document.getElementById('mortDown').value.trim();
  var yearsVal = document.getElementById('mortYears').value.trim();
  var rateVal  = document.getElementById('mortRate').value.trim();

  var price = parseFloat(priceVal) || 0;
  var down  = parseFloat(downVal)  || 0;
  var years = parseFloat(yearsVal) || 0;
  var rate  = parseFloat(rateVal);
  var hasErr = false;

  /* Validim */
  if (!priceVal || price <= 0)          { showErr('err-mortPrice', 'Shkruani çmimin e shitjes.'); hasErr = true; }
  else if (price > 50000000)            { showErr('err-mortPrice', 'Çmimi nuk mund të jetë mbi 50,000,000 €.'); hasErr = true; }

  if (down < 0)                         { showErr('err-mortDown', 'Parapagimi nuk mund të jetë negativ.'); hasErr = true; }
  else if (price > 0 && down >= price)  { showErr('err-mortDown', 'Parapagimi nuk mund të jetë më i madh se çmimi.'); hasErr = true; }

  if (!yearsVal || years < 1)           { showErr('err-mortYears', 'Afati minimal është 1 vit.'); hasErr = true; }
  else if (years > 40)                  { showErr('err-mortYears', 'Afati maksimal është 40 vite.'); hasErr = true; }
  else if (!Number.isInteger(years))    { showErr('err-mortYears', 'Afati duhet të jetë numër i plotë.'); hasErr = true; }

  if (rateVal === '' || isNaN(rate))    { showErr('err-mortRate', 'Shkruani normën e interesit.'); hasErr = true; }
  else if (rate < 0)                    { showErr('err-mortRate', 'Interesi nuk mund të jetë negativ.'); hasErr = true; }
  else if (rate > 30)                   { showErr('err-mortRate', 'Interesi nuk mund të jetë mbi 30%.'); hasErr = true; }

  /* Nëse ka gabime — fshih rezultatin  */
  if (hasErr) {
    document.getElementById('mortResult').style.display = 'none';
    return;
  }

  /* Llogaritja */
  var principal = price - down;
  var monthly, totalPayment, totalInterest;

  if (rate === 0) {
    monthly       = principal / (years * 12);
    totalPayment  = principal;
    totalInterest = 0;
  } else {
    var r = (rate / 100) / 12;
    var n = years * 12;
    monthly       = principal * (r * Math.pow(1 + r, n)) / (Math.pow(1 + r, n) - 1);
    totalPayment  = monthly * n;
    totalInterest = totalPayment - principal;
  }

  document.getElementById('mortMonthly').textContent       = fmt(monthly);
  document.getElementById('mortTotalInterest').textContent = fmt(totalInterest);
  document.getElementById('mortTotalPayment').textContent  = fmt(totalPayment);

  var result = document.getElementById('mortResult');
  result.style.display = 'block';
  result.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/* Enter key për të gjitha inputet */
document.addEventListener('DOMContentLoaded', function() {
  ['mortPrice', 'mortDown', 'mortYears', 'mortRate'].forEach(function(id) {
    var el = document.getElementById(id);
    if (el) {
      el.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') calcMortgage();
      });
    }
  });
});


/* ═══════════════════════════════════════════════════════════════════
   13. TESTIMONIALS 
   ═══════════════════════════════════════════════════════════════════ */

(function () {
    var current = 0; 

    var slides  = document.querySelectorAll('.ve-testi-slide');
    var navBtns = document.querySelectorAll('.ve-testi-nav-btn');
    var prevBtn = document.getElementById('vestiPrev');
    var nextBtn = document.getElementById('vestiNext');

    if (!slides.length) return;

    function goTo(idx) {

        slides[current].classList.remove('active');
        if (navBtns[current]) {
            navBtns[current].classList.remove('active');
            navBtns[current].setAttribute('aria-selected', 'false');
        }

        /* Mbyll "lexo më shumë" nëse ishte hapur */
        var extra = document.getElementById('extra-' + current);
        if (extra && extra.classList.contains('open')) {
            extra.classList.remove('open');
            var readBtn = slides[current].querySelector('.ve-testi-read-more');
            if (readBtn) {
                readBtn.innerHTML = 'Lexo më shumë <i class="fas fa-chevron-down" style="font-size:0.7rem"></i>';
            }
        }
        current = ((idx % slides.length) + slides.length) % slides.length;
        slides[current].classList.add('active');
        if (navBtns[current]) {
            navBtns[current].classList.add('active');
            navBtns[current].setAttribute('aria-selected', 'true');
            navBtns[current].scrollIntoView({
                behavior: 'smooth', block: 'nearest', inline: 'center'
            });
        }
    }
    navBtns.forEach(function (btn, i) {
        btn.addEventListener('click', function () { goTo(i); });
    });

    /* Shigjetat prev/next */
    if (prevBtn) prevBtn.addEventListener('click', function () { goTo(current - 1); });
    if (nextBtn) nextBtn.addEventListener('click', function () { goTo(current + 1); });

    /* Swipe  per mobile */
    var section = document.querySelector('.ve-testi-section');
    if (section) {
        var touchX = 0;
        section.addEventListener('touchstart', function (e) {
            touchX = e.touches[0].clientX;
        }, { passive: true });
        section.addEventListener('touchend', function (e) {
            var diff = touchX - e.changedTouches[0].clientX;
            if (Math.abs(diff) > 50) {
                goTo(diff > 0 ? current + 1 : current - 1);
            }
        });
    }

    /* Keyboard: ← → */
    document.addEventListener('keydown', function (e) {
        if (!document.querySelector('.ve-testi-section')) return;
        if (e.key === 'ArrowLeft')  goTo(current - 1);
        if (e.key === 'ArrowRight') goTo(current + 1);
    });

})();

/**
 * Hap/mbyll tekstin e plotë të testimonialit.
 * Thirret nga onclick="toggleExtra(idx, this)" në template.
 * @param {number} idx  - indeksi i slide-it
 * @param {HTMLElement} btn - butoni që u klikua
 */
function toggleExtra(idx, btn) {
    var extra = document.getElementById('extra-' + idx);
    if (!extra) return;
    var isOpen = extra.classList.toggle('open');
    btn.innerHTML = isOpen
        ? 'Lexo më pak <i class="fas fa-chevron-up" style="font-size:0.7rem"></i>'
        : 'Lexo më shumë <i class="fas fa-chevron-down" style="font-size:0.7rem"></i>';
}


/* ═══════════════════════════════════════════════════════════════════
   14. TESTIMONIAL FORM 
   ═══════════════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', function () {

    if (!document.getElementById('testiForm')) return;

    /* ── Referencat e elementeve ──────────────────────────────────── */
    var form       = document.getElementById('testiForm');
    var submitBtn  = document.getElementById('testiSubmit');
    var consent    = document.getElementById('consentCheck');
    var consentWrap= document.getElementById('consentWrap');
    var overlay    = document.getElementById('tfModalOverlay');
    var closeBtn   = document.getElementById('tfModalClose');
    var modalStars = document.getElementById('modalStars');
    var modalName  = document.getElementById('modalName');
    var hintEl     = document.getElementById('ratingHint');
    var msgEl      = document.getElementById(form.querySelector('[name$="message"]') ?
                       form.querySelector('[name$="message"]').id : 'id_message');
    var countEl    = document.getElementById('msgChar');

    var nameEl    = form.querySelector('[name$="client_name"]');
    var cityEl    = form.querySelector('[name$="client_city"]');
    var emailEl   = form.querySelector('[name$="client_email"]');
    var agentEl   = form.querySelector('[name$="agent"]');
    var ratingEls = form.querySelectorAll('[name$="rating"]');

    /* ── Rating hints ─────────────────────────────────────────────── */
    var hints = { '1':'Keq', '2':'Mesatar', '3':'Mirë', '4':'Shumë Mirë', '5':'Shkëlqyeshëm' };
    var rLabels = Array.from(form.querySelectorAll('.tf-rating label'));
    var rInputs = Array.from(form.querySelectorAll('.tf-rating input[type="radio"]'));

    function paintStars(upTo) {
        rLabels.forEach(function (l, i) { l.classList.toggle('active', i <= upTo); });
    }

    function resetToSelected() {
        var checked = form.querySelector('.tf-rating input:checked');
        if (checked) {
            paintStars(parseInt(checked.value, 10) - 1);
            if (hintEl) hintEl.textContent = hints[checked.value] || '';
        } else {
            rLabels.forEach(function (l) { l.classList.remove('active'); });
            if (hintEl) hintEl.textContent = '';
        }
    }

    rLabels.forEach(function (lbl, idx) {
        lbl.addEventListener('mouseenter', function () {
            paintStars(idx);
            if (hintEl) hintEl.textContent = hints[String(idx + 1)] || '';
        });
    });

    var rWrap = document.querySelector('.tf-rating-wrap');
    if (rWrap) rWrap.addEventListener('mouseleave', resetToSelected);
    rInputs.forEach(function (r) { r.addEventListener('change', resetToSelected); });
    resetToSelected();

    /* ── Char counter për mesazhin ──────────────────────────────────── */
    if (msgEl && countEl) {
        function updateCount() {
            var n = msgEl.value.length;
            countEl.textContent = n + ' karaktere';
            countEl.className   = 'tf-char' + (n > 0 && n < 20 ? ' tf-char--warn' : '');
        }
        msgEl.addEventListener('input', updateCount);
        updateCount();
    }

    if (nameEl) {
        nameEl.addEventListener('keypress', function (e) {
            if (!/[\p{L}\s'\-]/u.test(e.key) && !isControlKey(e)) {
                e.preventDefault();
                shakeField(this);
            }
        });
        nameEl.addEventListener('paste', function (e) {
            var pasted = (e.clipboardData || window.clipboardData).getData('text');
            if (!/^[\p{L}\s'\-]+$/u.test(pasted)) {
                e.preventDefault();
                shakeField(this);
            }
        });
        nameEl.addEventListener('input', function () {
            this.value = this.value.replace(/[^\p{L}\s'\-]/gu, '');
            tfClearError(this);
        });
    }

    if (cityEl) {
        cityEl.addEventListener('keypress', function (e) {
            if (!/[\p{L}\s'\-]/u.test(e.key) && !isControlKey(e)) {
                e.preventDefault();
                shakeField(this);
            }
        });
        cityEl.addEventListener('paste', function (e) {
            var pasted = (e.clipboardData || window.clipboardData).getData('text');
            if (!/^[\p{L}\s'\-]+$/u.test(pasted)) {
                e.preventDefault();
                shakeField(this);
            }
        });
        cityEl.addEventListener('input', function () {
            this.value = this.value.replace(/[^\p{L}\s'\-]/gu, '');
            tfClearError(this);
        });
    }

    if (emailEl) {
        emailEl.addEventListener('keypress', function (e) {
            if (!/[a-zA-Z0-9@.\-_+]/.test(e.key) && !isControlKey(e)) {
                e.preventDefault();
                shakeField(this);
            }
        });
        emailEl.addEventListener('paste', function (e) {
            var pasted = (e.clipboardData || window.clipboardData).getData('text');
            if (!/^[a-zA-Z0-9@.\-_+]+$/.test(pasted.trim())) {
                e.preventDefault();
                shakeField(this);
            }
        });
        emailEl.addEventListener('input', function () {
            this.value = this.value.replace(/[^a-zA-Z0-9@.\-_+]/g, '');
            tfClearError(this);
        });
    }

    if (msgEl) {
        msgEl.addEventListener('input', function () {
            tfClearError(this);
        });
    }

    if (agentEl) {
        agentEl.addEventListener('change', function () {
            tfClearError(this);
        });
    }

    rInputs.forEach(function (r) {
        r.addEventListener('change', function () {
            var ratingField = form.querySelector('.tf-field:has(.tf-rating)') ||
                              (rWrap ? rWrap.closest('.tf-field') : null);
            if (ratingField) {
                ratingField.classList.remove('tf-field--error');
                var err = ratingField.querySelector('.tf-error');
                if (err) err.remove();
            }
        });
    });

    /* ── Submit — validim i plotë ────────────────────────────────── */
    form.addEventListener('submit', function (e) {
        e.preventDefault();
        var hasError = false;

        /* ── 1. EMRI ──────────────────────────────────────────────── */
        if (nameEl) {
            tfClearError(nameEl);
            var nameVal = nameEl.value.trim();
            if (!nameVal) {
                tfSetError(nameEl, 'Emri është i detyrueshëm.'); hasError = true;
            } else if (nameVal.length < 2) {
                tfSetError(nameEl, 'Emri duhet të ketë të paktën 2 karaktere.'); hasError = true;
            } else if (nameVal.length > 100) {
                tfSetError(nameEl, 'Emri nuk mund të jetë më i gjatë se 100 karaktere.'); hasError = true;
            } else if (!/^[\p{L}\s'\-]+$/u.test(nameVal)) {
                tfSetError(nameEl, 'Emri mund të përmbajë vetëm shkronja, hapësira dhe vizë.'); hasError = true;
            } else if (/^\s+$/.test(nameVal)) {
                tfSetError(nameEl, 'Emri nuk mund të jetë vetëm hapësira.'); hasError = true;
            } else if (/[\-']{2,}/.test(nameVal)) {
                tfSetError(nameEl, 'Emri nuk mund të ketë dy viza ose apostrofa radhazi.'); hasError = true;
            }
        }

        /* ── 2. QYTETI  ─────────────────────────────────── */
        if (cityEl && cityEl.value.trim()) {
            tfClearError(cityEl);
            var cityVal = cityEl.value.trim();
            if (cityVal.length < 2) {
                tfSetError(cityEl, 'Qyteti duhet të ketë të paktën 2 karaktere.'); hasError = true;
            } else if (cityVal.length > 100) {
                tfSetError(cityEl, 'Qyteti nuk mund të jetë më i gjatë se 100 karaktere.'); hasError = true;
            } else if (!/^[\p{L}\s'\-]+$/u.test(cityVal)) {
                tfSetError(cityEl, 'Qyteti mund të përmbajë vetëm shkronja.'); hasError = true;
            }
        }

        /* ── 3. EMAIL  ──────────────────────────────────── */
        if (emailEl && emailEl.value.trim()) {
            tfClearError(emailEl);
            var emailVal = emailEl.value.trim();
            if (emailVal.length > 254) {
                tfSetError(emailEl, 'Email-i nuk mund të jetë më i gjatë se 254 karaktere.'); hasError = true;
            } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailVal)) {
                tfSetError(emailEl, 'Email-i nuk është i vlefshëm. Shembull: emri@domain.com'); hasError = true;
            } else if ((emailVal.match(/@/g) || []).length > 1) {
                tfSetError(emailEl, 'Email-i mund të ketë vetëm një @ simbol.'); hasError = true;
            } else if (/\.{2,}/.test(emailVal)) {
                tfSetError(emailEl, 'Email-i nuk mund të ketë dy pika radhazi.'); hasError = true;
            } else if (emailVal.startsWith('.') || emailVal.endsWith('.')) {
                tfSetError(emailEl, 'Email-i nuk mund të fillojë ose mbarojë me pikë.'); hasError = true;
            } else {
                var parts  = emailVal.split('@');
                var domain = parts[1] || '';
                var tldArr = domain.split('.');
                var tld    = tldArr[tldArr.length - 1];
                if (!domain.includes('.') || tld.length < 2) {
                    tfSetError(emailEl, 'Domain-i i email-it nuk është i vlefshëm.'); hasError = true;
                }
            }
        }

        /* ── 4. AGJENTI ───────────────────────────────────────────── */
        if (agentEl) {
            tfClearError(agentEl);
            if (!agentEl.value) {
                tfSetError(agentEl, 'Ju lutem zgjidhni agjentin.'); hasError = true;
            }
        }

        /* ── 5. RATING ────────────────────────────────────────────── */
        var checkedRating = form.querySelector('.tf-rating input:checked');
        if (!checkedRating) {
            /* Gjej kontejnerin e fushës së rating-ut */
            var ratingField = rWrap ? rWrap.closest('.tf-field') : null;
            if (ratingField) {
                ratingField.classList.add('tf-field--error');
                if (!ratingField.querySelector('.tf-error')) {
                    var rSpan = document.createElement('span');
                    rSpan.className = 'tf-error';
                    rSpan.innerHTML = '<i class="fas fa-exclamation-circle"></i> Ju lutem zgjidhni një vlerësim.';
                    ratingField.appendChild(rSpan);
                }
            }
            hasError = true;
        }

        /* ── 6. MESAZHI ───────────────────────────────────────────── */
        if (msgEl) {
            tfClearError(msgEl);
            var msgVal = msgEl.value.trim();
            if (!msgVal) {
                tfSetError(msgEl, 'Mesazhi është i detyrueshëm.'); hasError = true;
            } else if (msgVal.length < 20) {
                tfSetError(msgEl, 'Mesazhi duhet të ketë të paktën 20 karaktere.'); hasError = true;
            } else if (msgVal.length > 1000) {
                tfSetError(msgEl, 'Mesazhi nuk mund të ketë më shumë se 1000 karaktere (aktualisht ' + msgVal.length + ').'); hasError = true;
            } else if (/^\s+$/.test(msgVal)) {
                tfSetError(msgEl, 'Mesazhi nuk mund të jetë vetëm hapësira.'); hasError = true;
            }
        }

        /* ── 7. CONSENT CHECKBOX ──────────────────────────────────── */
        if (consent) {
            if (consentWrap) consentWrap.classList.remove('tf-consent--error');
            var cErr = consentWrap ? consentWrap.querySelector('.tf-error') : null;
            if (cErr) cErr.remove();
            if (!consent.checked) {
                if (consentWrap) {
                    consentWrap.classList.add('tf-consent--error');
                    var cs = document.createElement('span');
                    cs.className = 'tf-error';
                    cs.innerHTML = '<i class="fas fa-exclamation-circle"></i> Duhet të pranoni kushtet për të dërguar.';
                    consentWrap.appendChild(cs);
                }
                hasError = true;
            }
        }

        /* ── Honeypot ─────────────────────────────────────────────── */
        var honeypot = form.querySelector('[name="honeypot"]');
        if (honeypot && honeypot.value.trim()) { return; }

        /* ── Ndalon submit nëse ka gabime ──────────────────────────── */
        if (hasError) {
            var firstErr = form.querySelector('.tf-input--error, .tf-field--error');
            if (firstErr) firstErr.scrollIntoView({ behavior: 'smooth', block: 'center' });
            return;
        }
        /* ── Loading state ────────────────────────────────────────── */
        submitBtn.disabled  = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Duke dërguar...';
        var formData = new FormData(form);

        fetch(form.getAttribute('action') || window.location.href, {
            method : 'POST',
            body   : formData,
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.success) {
                var name   = formData.get('client_name') || '';
                var rating = parseInt(formData.get('rating') || '5', 10);
                openModal(name, rating);
                form.reset();
                rLabels.forEach(function (l) { l.classList.remove('active'); });
                if (hintEl)  hintEl.textContent  = '';
                if (countEl) countEl.textContent = '0 karaktere';
            } else if (data.errors) {
                showServerErrors(data.errors);
            } else {
                alert('Ndodhi një gabim. Ju lutem provoni përsëri.');
            }
            submitBtn.disabled  = false;
            submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i><span>Dërgo Testimonialin</span>';
        })
        .catch(function () {
            submitBtn.disabled  = false;
            submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i><span>Dërgo Testimonialin</span>';
            alert('Gabim lidhjeje. Kontrolloni internetin dhe provoni përsëri.');
        });
    });

    function openModal(name, rating) {
        if (modalStars) modalStars.textContent = '★'.repeat(rating) + '☆'.repeat(5 - rating);
        if (modalName && name) modalName.textContent = '— ' + name;
        if (overlay) {
            overlay.classList.add('open');
            document.body.style.overflow = 'hidden';
        }
    }

    function closeModal() {
        if (overlay) overlay.classList.remove('open');
        document.body.style.overflow = '';
    }

    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (overlay) {
        overlay.addEventListener('click', function (e) {
            if (e.target === overlay) closeModal();
        });
    }
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && overlay && overlay.classList.contains('open')) closeModal();
    });

    /* ── Shfaqen gabimet nga serveri ────────────────────────────────── */
    function showServerErrors(errors) {
        form.querySelectorAll('.tf-input--error').forEach(function (el) {
            el.classList.remove('tf-input--error');
        });
        form.querySelectorAll('.tf-error').forEach(function (el) { el.remove(); });

        Object.keys(errors).forEach(function (field) {
            var input = form.querySelector('[name$="' + field + '"]');
            if (!input) return;
            input.classList.add('tf-input--error');
            var span = document.createElement('span');
            span.className = 'tf-error';
            span.innerHTML = '<i class="fas fa-exclamation-circle"></i> ' + errors[field];
            input.parentNode.insertBefore(span, input.nextSibling);
        });

        var firstErr = form.querySelector('.tf-input--error');
        if (firstErr) firstErr.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    function tfSetError(el, msg) {
        el.classList.add('tf-input--error');
        var field = el.closest('.tf-field');
        if (!field) return;
        field.classList.add('tf-field--error');
        var existing = field.querySelector('.tf-error');
        if (existing) { existing.innerHTML = '<i class="fas fa-exclamation-circle"></i> ' + msg; return; }
        var span = document.createElement('span');
        span.className = 'tf-error';
        span.innerHTML = '<i class="fas fa-exclamation-circle"></i> ' + msg;
        field.appendChild(span);
    }

    function tfClearError(el) {
        el.classList.remove('tf-input--error');
        var field = el.closest('.tf-field');
        if (!field) return;
        field.classList.remove('tf-field--error');
        var err = field.querySelector('.tf-error');
        if (err) err.remove();
    }

    function shakeField(el) {
        el.classList.remove('tf-field__shake');
        void el.offsetWidth;
        el.classList.add('tf-field__shake');
        setTimeout(function () { el.classList.remove('tf-field__shake'); }, 400);
    }

    function isControlKey(e) {
        return e.ctrlKey || e.metaKey || e.altKey ||
               ['Backspace', 'Delete', 'Tab', 'Enter', 'Escape',
                'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown',
                'Home', 'End', 'F1','F2','F3','F4','F5',
                'F6','F7','F8','F9','F10','F11','F12'].indexOf(e.key) !== -1;
    }

});

/* ═══════════════════════════════════════════════════════════════════
     15.VLERESIM PRONE JS
   ═══════════════════════════════════════════════════════════════════ */

(function () {

  var cur   = 1;   
  var total = 5;

  /* Të dhënat e mbledhura gjatë hapave */
  var fd = {
    prop_type : '',
    rooms     : '',
    area      : '',
    period    : '',
    condition : '',
    parking   : '',
    address   : '',
    fn        : '',
    ln        : '',
    email     : '',
    phone     : '',
  };

  /* Teksti i sidebar-it i cili ndryshon me çdo hap */
  var sbc = {
    1: 'Zgjidhni llojin e pronës për të filluar procesin e vlerësimit.',
    2: 'Numri i dhomave dhe sipërfaqja ndikojnë drejtpërdrejt në vlerën e pronës.',
    3: 'Viti i ndërtimit dhe gjendja aktuale janë faktorë kyç në vlerësim.',
    4: 'Adresa dhe parkimi janë të rëndësishëm për analizën e tregut.',
    5: 'Plotësoni të dhënat tuaja dhe do ju kontaktojmë brenda 24 orëve.',
  };

  /* ── Drejton te hapi i ri ────────────────────────────────────────── */
  function goTo(n) {
    document.getElementById('step' + cur).classList.remove('active');
    cur = n;
    document.getElementById('step' + cur).classList.add('active');

    /* Progress bar */
    document.getElementById('vpProgFill').style.width = (cur / total * 100) + '%';
    document.getElementById('vpProgLbl').textContent  = 'Hapi ' + cur + '/' + total;

    /* Butoni "Pas" — fshihet vetëm në hapin 1 */
    document.getElementById('vpBack').style.display = cur > 1 ? 'inline-flex' : 'none';

    /* Përditëson përshkrimin e sidebar-it */
    var descEl = document.getElementById('sbDesc');
    if (descEl && sbc[cur]) descEl.textContent = sbc[cur];

    var panel = document.getElementById('vpPanel');
    if (panel) panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function showErr(id, show) {
    var el = document.getElementById(id);
    if (!el) return;
    if (show) el.classList.add('on');
    else      el.classList.remove('on');
  }

  /* ══════════════════════════════════════════════════════
     HAPI 1 — Lloji i pronës
  ══════════════════════════════════════════════════════ */
  document.querySelectorAll('[name="prop_type"]').forEach(function (r) {
    r.addEventListener('change', function () {
      fd.prop_type = this.value;
      document.getElementById('n1').disabled = false;

      var rw = document.getElementById('roomsWrap');
      if (rw) {
        rw.style.display =
          (this.value === 'land' || this.value === 'commercial') ? 'none' : 'block';
      }
    });
  });

  document.getElementById('n1').addEventListener('click', function () {
    if (fd.prop_type) goTo(2);
  });

  /* ══════════════════════════════════════════════════════
     HAPI 2 — Dhomat + Sipërfaqe
  ══════════════════════════════════════════════════════ */
  document.querySelectorAll('[name="rooms"]').forEach(function (r) {
    r.addEventListener('change', function () { fd.rooms = this.value; });
  });

  document.getElementById('n2').addEventListener('click', function () {
    var areaEl = document.getElementById('vpArea');
    var a      = areaEl.value.trim();

    if (!a || parseInt(a) < 5) {
      areaEl.style.borderColor = '#dc2626';
      areaEl.focus();
      return;
    }
    areaEl.style.borderColor = '';
    fd.area = a;
    goTo(3);
  });

  var areaEl = document.getElementById('vpArea');
  if (areaEl) {
    areaEl.addEventListener('input', function () {
      this.style.borderColor = '';
    });
  }

  /* ══════════════════════════════════════════════════════
     HAPI 3 — Periudha + Gjendja e prones
  ══════════════════════════════════════════════════════ */
  document.querySelectorAll('[name="period"]').forEach(function (r) {
    r.addEventListener('change', function () { fd.period = this.value; });
  });
  document.querySelectorAll('[name="condition"]').forEach(function (r) {
    r.addEventListener('change', function () { fd.condition = this.value; });
  });

  document.getElementById('n3').addEventListener('click', function () {
    goTo(4);
  });

  /* ══════════════════════════════════════════════════════
     HAPI 4 — Parkimi + Adresa
  ══════════════════════════════════════════════════════ */
  document.querySelectorAll('[name="parking"]').forEach(function (r) {
    r.addEventListener('change', function () { fd.parking = this.value; });
  });

  document.getElementById('n4').addEventListener('click', function () {
    var addr  = document.getElementById('vpAddr').value.trim();
    if (!addr) {
      showErr('addrErr', true);
      document.getElementById('vpAddr').focus();
      return;
    }
    showErr('addrErr', false);
    fd.address = addr;
    goTo(5);
  });

  var addrEl = document.getElementById('vpAddr');
  if (addrEl) {
    addrEl.addEventListener('input', function () { showErr('addrErr', false); });
  }

  /* ══════════════════════════════════════════════════════
     HAPI 5 — Kontakti + Submit
  ══════════════════════════════════════════════════════ */
  document.getElementById('vpSub').addEventListener('click', function () {
    var fn    = document.getElementById('vpFn').value.trim();
    var ln    = document.getElementById('vpLn').value.trim();
    var email = document.getElementById('vpEm').value.trim();
    var phone = document.getElementById('vpPh').value.trim();
    var re    = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    var ok    = true;

    showErr('fnErr', !fn);           if (!fn)             ok = false;
    showErr('lnErr', !ln);           if (!ln)             ok = false;
    showErr('emErr', !re.test(email)); if (!re.test(email)) ok = false;
    showErr('phErr', !phone);        if (!phone)          ok = false;

    if (!ok) return;

    fd.fn    = fn;
    fd.ln    = ln;
    fd.email = email;
    fd.phone = phone;

    /* Loading state — e ben disable butonin gjatë dërgimit */
    var btn     = document.getElementById('vpSub');
    btn.disabled  = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Duke dërguar...';

    var csrfEl = document.querySelector('[name=csrfmiddlewaretoken]');
    var csrf   = csrfEl ? csrfEl.value : '';

    /* Dërgohet te endpoint-i Django */
    fetch(window.VP_SUBMIT_URL || '/vleresim-prone/dergo/', {
      method  : 'POST',
      headers : {
        'Content-Type' : 'application/json',
        'X-CSRFToken'  : csrf,
      },
      body: JSON.stringify(fd),
    })
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (d.success) {
        /* Fsheh formën dhe shfaq mesazhin e suksesit */
        document.getElementById('vpProg').style.display   = 'none';
        document.getElementById('vpBack').style.display   = 'none';
        document.getElementById('step5').style.display    = 'none';
        var ok = document.getElementById('vpOk');
        ok.style.display        = 'flex';
        ok.style.flexDirection  = 'column';
        ok.style.alignItems     = 'center';
      } else {
        /* Riaktivizo butonin nëse ka gabime */
        btn.disabled  = false;
        btn.innerHTML = '<i class="fas fa-paper-plane"></i> Dërgoni Mesazhin Tuaj';
      }
    })
    .catch(function () {
      btn.disabled  = false;
      btn.innerHTML = '<i class="fas fa-paper-plane"></i> Dërgoni Mesazhin Tuaj';
    });
  });

  document.getElementById('vpBack').addEventListener('click', function () {
    if (cur > 1) goTo(cur - 1);
  });

  [
    ['vpFn', 'fnErr'],
    ['vpLn', 'lnErr'],
    ['vpEm', 'emErr'],
    ['vpPh', 'phErr'],
  ].forEach(function (pair) {
    var inp = document.getElementById(pair[0]);
    if (inp) {
      inp.addEventListener('input', function () {
        showErr(pair[1], false);
        this.classList.remove('vp-inp--e');
      });
    }
  });

})();

/* ══════════════════════════════════════════════════════
    16.AGENT DASHBOARD
  ══════════════════════════════════════════════════════ */


function switchTab(tab, btn) {
    document.querySelectorAll('.dash-tab-content').forEach(function(t) {
        t.classList.remove('active');
    });
    document.querySelectorAll('.dash-topbar__tab').forEach(function(b) {
        b.classList.remove('active');
    });
    document.getElementById('tab-' + tab).classList.add('active');
    btn.classList.add('active');
}

function openReplyModal(visitId, action, clientName, propertyTitle) {
    var modal    = document.getElementById('replyModal');
    var title    = document.getElementById('modalTitle');
    var sub      = document.getElementById('modalSub');
    var sendBtn  = document.getElementById('modalSendBtn');
    var textarea = document.getElementById('replyText');
    var form     = document.getElementById('replyForm');
    var agentName = document.getElementById('dashMeta').dataset.agentName || '';

    form.action = '/agent/dashboard/visit/' + visitId + '/' + action + '/';

    if (action === 'confirm') {
        title.textContent = 'Konfirmo Vizitën';
        sendBtn.className = 'dash-modal__send dash-modal__send--confirm';
        textarea.value    =
            'Përshëndetje ' + clientName + ',\n\n' +
            'Vizita juaj për pronën "' + propertyTitle + '" u konfirmua me sukses!\n\n' +
            'Agjenti do ju kontaktojë për detajet.\n\n' +
            'Me respekt,\n' + agentName;
    } else {
        title.textContent = 'Refuzo Vizitën';
        sendBtn.className = 'dash-modal__send dash-modal__send--reject';
        textarea.value    =
            'Përshëndetje ' + clientName + ',\n\n' +
            'Fatkeqësisht nuk mund të konfirmojmë vizitën e kërkuar.\n\n' +
            'Ju lutem na kontaktoni për të caktuar një datë tjetër.\n\n' +
            'Me respekt,\n' + agentName;
    }

    sub.textContent = 'Klienti: ' + clientName + ' · Prona: ' + propertyTitle;
    modal.classList.add('active');
}

function closeDashModal() {
    document.getElementById('replyModal').classList.remove('active');
}

function confirmDelete(propId, propTitle) {
    var modal = document.getElementById('deleteModal');
    var sub   = document.getElementById('deleteModalSub');
    var form  = document.getElementById('deleteForm');
    sub.textContent = 'A jeni i sigurt që dëshironi të fshini "' + propTitle + '"? Ky veprim nuk mund të kthehet.';
    form.action = '/agent/dashboard/property/' + propId + '/delete/';
    modal.classList.add('active');
}

function closeDeleteModal() {
    document.getElementById('deleteModal').classList.remove('active');
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.dash-modal').forEach(function(modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.remove('active');
            }
        });
    });
});


/* ══════════════════════════════════════════════════════
    16.AGENT PROPERTY FORM
  ══════════════════════════════════════════════════════ */
function previewMainImg(input) {
    var preview = document.getElementById('mainImgPreview');
    if (input.files && input.files[0]) {
        var reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
        };
        reader.readAsDataURL(input.files[0]);
    }
}

function previewExtraImgs(input) {
    var container = document.getElementById('extraImgsPreview');
    container.innerHTML = '';
    if (input.files) {
        Array.from(input.files).forEach(function(file) {
            var reader = new FileReader();
            reader.onload = function(e) {
                var img = document.createElement('img');
                img.src = e.target.result;
                img.style.cssText = 'width:70px;height:70px;object-fit:cover;border-radius:8px;border:2px solid #e5e7eb;';
                container.appendChild(img);
            };
            reader.readAsDataURL(file);
        });
    }
}
