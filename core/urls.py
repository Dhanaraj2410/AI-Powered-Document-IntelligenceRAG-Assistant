from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('rag_app.urls')),
    path('api/', include('rag_app.api.urls_api')),
    re_path(r'^data/sample_documents/(?P<path>.*)$', serve, {'document_root': settings.BASE_DIR / 'data' / 'sample_documents'}),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
