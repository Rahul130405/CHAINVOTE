from django.urls import path
from . import views

urlpatterns = [
    # ── Frontend Routes ──────────────────────────────
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('election/<int:election_id>/', views.election_detail, name='election_detail'),
    path('election/<int:election_id>/vote/', views.cast_vote, name='cast_vote'),
    path('election/<int:election_id>/results/', views.results_view, name='results'),
    path('election/<int:election_id>/blockchain/', views.blockchain_explorer, name='blockchain_explorer'),
    path('security/threat-dashboard/', views.threat_dashboard, name='threat_dashboard'),
    # ── REST API Routes ──────────────────────────────
    path('api/elections/', views.api_election_list, name='api_elections'),
    path('api/elections/<int:election_id>/', views.api_election_detail, name='api_election_detail'),
    path('api/elections/<int:election_id>/vote/', views.api_cast_vote, name='api_vote'),
    path('api/elections/<int:election_id>/results/', views.api_results, name='api_results'),
]
