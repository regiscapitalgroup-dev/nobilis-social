from rest_framework import permissions, status, generics
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView, RetrieveAPIView
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import (
    CityCatalog,
    LanguageCatalog,
    Relative,
    RelationshipCatalog,
    SupportAgent,
    IndustryCatalog,
    ProfessionalInterestCatalog,
    HobbyCatalog,
    ClubCatalog,
    RateExpertise
)
from .serializers import (
    CityListSerializer,
    LanguageSerializer,
    RelativeSerializer,
    RelationshipCatalogSerializer,
    SupportAgentSerializer,
    IndustryCatalogSerializer,
    ProfessionalInterestCatalogSerializer,
    HobbyCatalogSerializer,
    ProfileIndustriesUpdateSerializer,
    ProfileInterestsUpdateSerializer,
    ProfileHobbiesUpdateSerializer,
    TokenWithSubscriptionSerializer,
    ClubCatalogSerializer,
    InviteUserSerializer
)
from nsocial.models import ProfessionalProfile, UserProfile, PersonalDetail, Role, CustomUser
from moderation.models import (
    TeamMembership, Team, ModeratorInvitation, ModeratorProfile
)
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db import transaction
from django.conf import settings
from django.core.mail import send_mail


class TokenObtainPairWithSubscriptionView(TokenObtainPairView):
    serializer_class = TokenWithSubscriptionSerializer


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


class IndustryCatalogListView(ListAPIView):
    queryset = IndustryCatalog.objects.filter(active=True).order_by('name')
    serializer_class = IndustryCatalogSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [SearchFilter]
    search_fields = ['name']
    pagination_class = None

    def list(self, request, *args, **kwargs):
        # Use DRF filtering to respect search params, then return only the names as a plain array
        queryset = self.filter_queryset(self.get_queryset())
        names = list(queryset.values_list('name', flat=True))
        return Response(names)


class ProfessionalInterestCatalogListView(ListAPIView):
    queryset = ProfessionalInterestCatalog.objects.filter(active=True).order_by('name')
    serializer_class = ProfessionalInterestCatalogSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [SearchFilter]
    search_fields = ['name']
    pagination_class = None


class HobbyCatalogListView(ListAPIView):
    queryset = HobbyCatalog.objects.filter(active=True).order_by('name')
    serializer_class = HobbyCatalogSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [SearchFilter]
    search_fields = ['name']
    pagination_class = None

    def list(self, request, *args, **kwargs):
        # Return only hobby names as a plain array of strings (with search applied)
        queryset = self.filter_queryset(self.get_queryset())
        names = list(queryset.values_list('name', flat=True))
        return Response(names)


class ClubCatalogListView(ListAPIView):
    queryset = ClubCatalog.objects.filter(active=True).order_by('name')
    serializer_class = ClubCatalogSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [SearchFilter]
    search_fields = ['name', 'city']
    pagination_class = None

    def list(self, request, *args, **kwargs):
        # Return concatenated "name - city" for each active club (with search applied)
        queryset = self.filter_queryset(self.get_queryset())
        items = [f"{c.name} - {c.city}" if c.city else c.name for c in queryset]
        return Response(items)


class UpdateProfileIndustriesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        serializer = ProfileIndustriesUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data.get('industry_ids', [])
        names = list(IndustryCatalog.objects.filter(id__in=ids, active=True).values_list('name', flat=True))

        # Obtener o crear ProfessionalProfile del usuario
        profile = UserProfile.objects.get(user=request.user)
        prof, _ = ProfessionalProfile.objects.get_or_create(user_profile=profile)
        # Guardar como CSV en el campo existente (compatibilidad mínima)
        prof.industries = ", ".join(names)
        prof.save(update_fields=['industries'])
        return Response({
            'industries': names,
            'count': len(names)
        })


class UpdateProfileInterestsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        serializer = ProfileInterestsUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data.get('interest_ids', [])
        names = list(ProfessionalInterestCatalog.objects.filter(id__in=ids, active=True).values_list('name', flat=True))

        profile = UserProfile.objects.get(user=request.user)
        prof, _ = ProfessionalProfile.objects.get_or_create(user_profile=profile)
        prof.professional_interest = ", ".join(names)
        prof.save(update_fields=['professional_interest'])
        return Response({
            'professional_interest': names,
            'count': len(names)
        })


class UpdateProfileHobbiesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        serializer = ProfileHobbiesUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data.get('hobby_ids', [])
        names = list(HobbyCatalog.objects.filter(id__in=ids, active=True).values_list('name', flat=True))

        profile = UserProfile.objects.get(user=request.user)
        # Obtener o crear PersonalDetail
        personal, _ = PersonalDetail.objects.get_or_create(user_profile=profile)
        personal.hobbies = ", ".join(names)
        personal.save(update_fields=['hobbies'])
        return Response({
            'hobbies': names,
            'count': len(names)
        })


class HeltChechView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class RateExpertiseView(APIView):
    """GET-only endpoint that returns the available expertise rate types from the model."""
    permission_classes = [permissions.AllowAny]
    http_method_names = ['get']

    def get(self, request):
        # Read from the model; if empty, provide sensible defaults without enforcing auth.
        names = list(RateExpertise.objects.filter(active=True).order_by('name').values_list('name', flat=True))
        if not names:
            names = ["hour", "project"]
        return Response(names)


class InviteUserView(generics.GenericAPIView):
    serializer_class = InviteUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        # Solo los administradores pueden invitar a otros moderadores
        if not getattr(request.user, 'is_admin', False):
            return Response({'error': 'No tienes permiso para realizar esta acción.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        email = validated_data['email']
        first_name = validated_data['first_name']
        last_name = validated_data['last_name']

        organization = validated_data.get('organization')
        relation = validated_data.get('relation')

        # Creamos al usuario colaborador
        assigned_role = serializer.validated_data['role']

        user = CustomUser.objects.create_user(
            email=email,
            password=None,  # Sin contraseña inicial
            first_name=first_name,
            last_name=last_name,
            is_active=False,  # Inactivo hasta que acepte
            invited_by=request.user,
            role=assigned_role
        )
        ModeratorProfile.objects.create(
            user=user,
            organization=organization,
            relation=relation
        )
        # Creación del equipo automático
        admin_user = request.user
        team_name = f"Team of {admin_user.first_name} {admin_user.last_name}".strip()
        team, _ = Team.objects.get_or_create(
            name=team_name,
            defaults={'description': f'Self-generated team for {admin_user.email}.'}
        )
        TeamMembership.objects.create(user=user, team=team, role=assigned_role)

        # --- LÓGICA CORREGIDA: Usamos el nuevo token ---
        invitation = ModeratorInvitation.objects.create(
            email=email,
            invited_by=request.user
        )

        # Generamos un enlace de activación específico para moderadores
        # IMPORTANTE: El frontend necesitará una ruta como /activate-moderator/<token>
        activation_url = f"https://main.d1rykkcgalxqn2.amplifyapp.com/activate-moderator/{invitation.token}/"
        subject = "Nobilis Invitation"
        message = f"""
                            You're invited to being my team

                            {activation_url}
                            
                            This is a development email sample, please don't reply
                        """
        from_email = settings.EMAIL_HOST_USER

        send_mail(subject=subject,
                  message=message,
                  from_email=from_email,
                  recipient_list=[email],
                  fail_silently=False,
                  )

        return Response({
            'success': 'Ok',
            'activation_url': activation_url  # Devolvemos la URL para facilitar las pruebas
        }, status=status.HTTP_201_CREATED)

