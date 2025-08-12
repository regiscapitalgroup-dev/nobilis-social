from rest_framework.generics import ListAPIView
from rest_framework.filters import SearchFilter
from .models import CityCatalog
from .serializers import CityListSerializer


class CityListView(ListAPIView):
    queryset = CityCatalog.objects.all().order_by('name')
    serializer_class = CityListSerializer

    filter_backends = (SearchFilter,)
    search_fields = ('name',)
    pagination_class = None
