from rest_framework import permissions
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView, RetrieveAPIView
from rest_framework.filters import SearchFilter
from .models import CityCatalog, LanguageCatalog, Relative, RelationshipCatalog, SupportAgent
from .serializers import CityListSerializer, LanguageSerializer, RelativeSerializer, RelationshipCatalogSerializer, SupportAgentSerializer


class CityListView(ListAPIView):
    queryset = CityCatalog.objects.all().order_by('name')
    serializer_class = CityListSerializer

    filter_backends = (SearchFilter,)
    search_fields = ('name',)
    pagination_class = None


class LanguageListView(ListAPIView):
    queryset = LanguageCatalog.objects.all()
    serializer_class = LanguageSerializer

    filter_backends = [SearchFilter]
    search_fields = ['name']


class RelationshipCatalogListView(ListAPIView):
    queryset = RelationshipCatalog.objects.all().order_by('name')
    serializer_class = RelationshipCatalogSerializer
    filter_backends = [SearchFilter]
    search_fields = ['name', 'description']


class RelativeListCreateView(ListCreateAPIView):
    serializer_class = RelativeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Relative.objects.all().order_by('-created_at')
        if getattr(user, 'is_admin', False):
            return qs
        return qs.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RelativeDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = RelativeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Relative.objects.all()
        if getattr(user, 'is_admin', False):
            return qs
        return qs.filter(user=user)


class SupportAgentListView(ListAPIView):
    queryset = SupportAgent.objects.all().order_by('name')
    serializer_class = SupportAgentSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class SupportAgentDetailView(RetrieveAPIView):
    queryset = SupportAgent.objects.all()
    serializer_class = SupportAgentSerializer
    permission_classes = [permissions.AllowAny]
