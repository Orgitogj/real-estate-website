from django.urls import path
from . import views

urlpatterns = [
    # ═══ FAQET KRYESORE ═══
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('team/', views.team, name='team'),
    path('karriera/', views.karriera, name='karriera'),

    # ═══ PRONAT ═══
    path('properties/', views.property_list, name='property_list'),
    path('properties/<slug:slug>/', views.property_detail, name='property_detail'),
    path('properties/<slug:slug>/visit/', views.visit_request, name='visit_request'),

    # ═══ URL PER SECILIN AGJENT ═══
    path('agent/<int:pk>/', views.agent_detail, name='agent_detail'),

    # ═══ AGENT  & DASHBOARD ═══
    path('agent/login/', views.agent_login, name='agent_login'),
    path('agent/logout/', views.agent_logout, name='agent_logout'),
    path('agent/dashboard/', views.agent_dashboard, name='agent_dashboard'),

    # ═══ VEPRIMET QE MUND TE BEJ AGJENTI ═══
    path('agent/dashboard/visit/<int:visit_id>/<str:action>/', views.visit_action, name='visit_action'),
    path('agent/dashboard/property/add/', views.agent_property_add, name='agent_property_add'),
    path('agent/dashboard/property/<int:pk>/edit/', views.agent_property_edit, name='agent_property_edit'),
    path('agent/dashboard/property/<int:pk>/delete/', views.agent_property_delete, name='agent_property_delete'),

    # ═══ WISHLIST ═══
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist-data/', views.wishlist_data, name='wishlist_data'),

    # ═══ BLOG & NEWS ═══
    path('news/', views.news, name='news'),
    path('blog/', views.blog, name='blog'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('blog/category/<slug:slug>/', views.blog_category, name='blog_category'),
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    path('terms/', views.terms_of_use, name='terms_of_use'),
    

    # ═══ FORMA TE TJERA ═══
    path('pershtypje/dergo/', views.testimonial_submit, name='testimonial_submit'),
    path('vleresim-prone/', views.vleresim_prone, name='vleresim_prone'),
    path('vleresim-prone/dergo/', views.vleresim_submit, name='vleresim_submit'),
]