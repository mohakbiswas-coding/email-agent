from django.urls import path
from . import views

urlpatterns = [
    path('', views.inbox_view, name='inbox'),
    path('prompts/', views.prompts_view, name='prompts'),
    path('drafts/', views.drafts_view, name='drafts'),
    path('agent/<email_id>/', views.agent_view, name='agent'),
]
