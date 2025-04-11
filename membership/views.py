from django.shortcuts import render
from membership.models import MembershipPlan, Suscription
from membership.serializers import MembershipPlanSerializer, SuscriptionSerializer
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from rest_framework import generics


class MembershipPlanView(generics.ListCreateAPIView):
    queryset = MembershipPlan.objects.all()
    serializer_class = MembershipPlanSerializer
    parser_classes = (CamelCaseJSONParser,)
    pagination_class = None


class MembershipPlanDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = MembershipPlan.objects.all()
    serializer_class = MembershipPlanSerializer
    parser_classes = (CamelCaseJSONParser,)
    pagination_class = None
    lookup_field = 'pk' 


class SuscriptionView(generics.ListCreateAPIView):
    queryset = Suscription.objects.all()
    serializer_class = SuscriptionSerializer
    parser_classes = (CamelCaseJSONParser,)
    # permission_classes = 


class SuscriptionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Suscription.objects.all()
    serializer_class = SuscriptionSerializer
    parser_classes = (CamelCaseJSONParser, )
    pagination_class = None
    lookup_field = 'pk'
