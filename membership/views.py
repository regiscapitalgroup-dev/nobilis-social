from django.shortcuts import render
from membership.models import MembershipPlan
from membership.serializers import MembershipPlanSerializer
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
