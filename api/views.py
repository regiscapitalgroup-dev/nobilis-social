from rest_framework.generics import ListAPIView
from rest_framework.filters import SearchFilter
from .models import CityCatalog, LanguageCatalog
from .serializers import CityListSerializer, LanguageSerializer


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
