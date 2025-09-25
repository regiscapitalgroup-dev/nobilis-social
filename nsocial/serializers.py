from rest_framework import serializers
from membership.serializers import SubscriptionStatusSerializer, MembershipSubscriptionSerializer
from nsocial.models import (
    CustomUser,
    UserProfile,
    SocialMediaProfile,
    PersonalDetail,
    Club,
    ProfessionalProfile,
    WorkPosition,
    Education,
    BoardPosition,
    NonProfitInvolvement,
    Recognition,
    Expertise,
    UserVideo,
    Experience,
    Author,
    Role
)
import stripe
import logging
from api.models import LanguageCatalog
import json
from django.contrib.auth.password_validation import validate_password

logger = logging.getLogger(__name__)


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'code', 'name', 'description', 'is_admin']
        read_only_fields = ['id']

class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    class Meta:
        model = CustomUser
        fields = ['email', 'password']
    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            validated_data['email'],
            validated_data['password']
        )
        return user


class CurrentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields =('first_name', 'last_name', 'email', 'id')


class SetNewPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)
    refresh_token = serializers.CharField(required=True)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class TokenSerializer(serializers.Serializer):
    token = serializers.TimeField(required=True)


class SocialMediaProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialMediaProfile
        fields = ['id', 'platform_name', 'profile_url']


class CommaSeparatedArrayField(serializers.CharField):
    def to_representation(self, value):
        if not value:
            return []
        return [item.strip() for item in value.split(',')]

    def to_internal_value(self, data):
        if not isinstance(data, list):
            self.fail('invalid', format='json')
        return ', '.join(str(item).strip() for item in data)


class UserProfileSerializer(serializers.ModelSerializer):
    languages = CommaSeparatedArrayField(required=False)
    social_media_profiles = SocialMediaProfileSerializer(many=True, read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'user',
            'introduction_headline',
            'alias_title',
            'profile_picture',
            'birthday',
            'phone_number',
            'city',
            'postal_code',
            'languages',
            'social_media_profiles',
        ]
        extra_kwargs = {
            'user': {'read_only': True}
        }


class PasswordResetConfirmSerializer(serializers.Serializer):
    user = serializers.CharField(write_only=True, required=True)
    token = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password], 
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        return attrs


class ClubSerializer(serializers.ModelSerializer):
    class Meta:
        model = Club
        fields = ['name', 'city']


class WorkPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkPosition
        fields = ['company', 'position', 'city', 'from_year', 'to_year']


class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = ['university_name', 'carreer', 'city', 'from_year', 'to_year']


class BoardPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoardPosition
        fields = ['company', 'position', 'city', 'from_year', 'to_year']


class NonProfitInvolvementSerializer(serializers.ModelSerializer):
    class Meta:
        model = NonProfitInvolvement
        fields = ['company', 'position', 'city', 'from_year', 'to_year']


class ExpertiseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expertise
        fields = ['title', 'content', 'rate']


# --- Serializadores para los modelos "intermedios" (objetos) ---

class PersonalDetailSerializer(serializers.ModelSerializer):
    clubs = ClubSerializer(many=True)
    hobbies = CommaSeparatedArrayField(required=False)
    interests = CommaSeparatedArrayField(required=False)

    class Meta:
        model = PersonalDetail
        fields = ['hobbies', 'interests', 'clubs']


class ProfessionalProfileSerializer(serializers.ModelSerializer):
    work_positions = WorkPositionSerializer(many=True)
    education = EducationSerializer(many=True)
    on_board = BoardPositionSerializer(many=True)
    non_profit_involvement = NonProfitInvolvementSerializer(many=True)
    industries = CommaSeparatedArrayField(required=False)
    professional_interest = CommaSeparatedArrayField(required=False)

    class Meta:
        model = ProfessionalProfile
        fields = ['industries', 'professional_interest', 'work_positions', 'education', 'on_board',
                  'non_profit_involvement']


class RecognitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recognition
        fields = ['top_accomplishments', 'additional_links']


class UserVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserVideo
        fields = ['id', 'video_link', 'title', 'description', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'name', 'photo_url']




class FullProfileSerializer(UserProfileSerializer):
    personal_detail = PersonalDetailSerializer(required=False)
    professional_profile = ProfessionalProfileSerializer(required=False)
    recognition = RecognitionSerializer(required=False)
    expertise = ExpertiseSerializer(many=True, required=False)
    videos = UserVideoSerializer(many=True, read_only=True)

    subscription = serializers.SerializerMethodField()
    current_subscription = MembershipSubscriptionSerializer(read_only=True)

    class Meta(UserProfileSerializer.Meta):
        model = UserProfile
        fields = UserProfileSerializer.Meta.fields + [
            'bio_presentation', 'biography', 'pic_footer', 'personal_detail', 'professional_profile',
            'recognition', 'expertise', 'videos', 'subscription', 'current_subscription'
        ]

    def get_subscription(self, obj: UserProfile):

        if not obj.stripe_subscription_id:
            return None

        fresh = bool(self.context.get('fresh_subscription', False))

        # Opción A: devolver datos cacheados del perfil (sin pegar a Stripe)
        if not fresh:
            return {
                'id': obj.stripe_subscription_id,
                'status': obj.subscription_status,
                'current_period_end': obj.subscription_current_period_end,
                'cancel_at_period_end': obj.cancel_at_period_end,
                'card': (
                    {'brand': obj.card_brand, 'last4': obj.card_last4}
                    if obj.card_last4 else None
                )
            }

        # Opción B: consultar Stripe y serializar con SubscriptionStatusSerializer
        try:
            stripe_sub = stripe.Subscription.retrieve(
                obj.stripe_subscription_id,
                expand=['plan.product', 'default_payment_method']
            )

            # Sincronización opcional de campos cacheados con lo que devuelve Stripe
            local_period_end_ts = int(
                obj.subscription_current_period_end.timestamp()) if obj.subscription_current_period_end else None
            stripe_period_end_ts = getattr(stripe_sub, 'current_period_end', None)
            stripe_status = getattr(stripe_sub, 'status', None)
            stripe_cancel_at_period_end = getattr(stripe_sub, 'cancel_at_period_end', False)

            if (
                    obj.subscription_status != stripe_status or
                    local_period_end_ts != stripe_period_end_ts or
                    obj.cancel_at_period_end != stripe_cancel_at_period_end
            ):
                logger.warning(
                    f"Desfase de datos de suscripción detectado para {obj.user_id}. Actualizando perfil."
                )
                obj.update_subscription_details(stripe_sub)

            return SubscriptionStatusSerializer(stripe_sub).data

        except stripe.error.InvalidRequestError as e:
            logger.warning(
                f"ID de suscripción inválido para user {obj.user_id} ({obj.stripe_subscription_id}): {e}. Limpiando campos locales."
            )
            obj.clear_subscription_details()
            return {"status": "inactive", "message": "Subscription reference invalid."}
        except stripe.error.StripeError as e:
            logger.error(
                f"Error de Stripe al recuperar suscripción para user {obj.user_id}: {e}",
                exc_info=True
            )
            return {"status": "error", "message": "Could not retrieve subscription details."}

    def update(self, instance, validated_data):
        # 1) Extraer bloques anidados para no interferir con campos simples
        personal_data = validated_data.pop('personal_detail', None)
        professional_data = validated_data.pop('professional_profile', None)
        recognition_data = validated_data.pop('recognition', None)
        expertise_data = validated_data.pop('expertise', None)

        # 2) Actualizar campos simples del UserProfile presentes en el payload
        simple_fields = [
            'introduction_headline', 'alias_title', 'birthday', 'phone_number', 'city',
            'postal_code', 'languages', 'bio_presentation', 'biography', 'pic_footer',
            'postal_address', 'guiding_principle',
            'often_in',
            'life_partner_name',
            'life_partner_lastname',
            'annual_limits_introduction',
            'receive_reports',
        ]
        for field in simple_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()

        def update_or_create_one_to_one(model, serializer, related_name, data):
            if data is None:
                return getattr(instance, related_name, None)
            obj, created = model.objects.update_or_create(
                user_profile=instance,
                defaults=data
            )
            return obj

        # Helper para manejar listas (borrar y recrear es lo más simple)
        def update_many_related(model, parent_instance, fk_field_name, related_name, data):
            if data is None:
                return
            # Borramos los objetos existentes
            getattr(parent_instance, related_name).all().delete()
            # Creamos los nuevos usando el nombre correcto del FK
            for item_data in data:
                model.objects.create(**{fk_field_name: parent_instance}, **item_data)

        # 3) Personal Details y Clubs
        if personal_data is not None:
            clubs_data = personal_data.pop('clubs', [])
            personal_detail_obj = update_or_create_one_to_one(
                PersonalDetail, PersonalDetailSerializer, 'personal_detail', personal_data
            )
            if personal_detail_obj:
                update_many_related(Club, personal_detail_obj, 'personal_detail', 'clubs', clubs_data)

        # 4) Professional Profile y sus listas
        if professional_data is not None:
            work_data = professional_data.pop('work_positions', [])
            edu_data = professional_data.pop('education', [])
            board_data = professional_data.pop('on_board', [])
            non_profit_data = professional_data.pop('non_profit_involvement', [])
            prof_profile_obj = update_or_create_one_to_one(
                ProfessionalProfile, ProfessionalProfileSerializer, 'professional_profile', professional_data
            )
            if prof_profile_obj:
                update_many_related(WorkPosition, prof_profile_obj, 'professional_profile', 'work_positions', work_data)
                update_many_related(Education, prof_profile_obj, 'professional_profile', 'education', edu_data)
                update_many_related(BoardPosition, prof_profile_obj, 'professional_profile', 'on_board', board_data)
                update_many_related(NonProfitInvolvement, prof_profile_obj, 'professional_profile', 'non_profit_involvement', non_profit_data)

        # 5) Recognition (1-1)
        if recognition_data is not None:
            update_or_create_one_to_one(Recognition, RecognitionSerializer, 'recognition', recognition_data)

        # 6) Expertise (FK directo a UserProfile)
        if expertise_data is not None:
            instance.expertise.all().delete()
            for item_data in expertise_data:
                Expertise.objects.create(user_profile=instance, **item_data)

        return instance

class ExperienceSerializer(serializers.ModelSerializer):
    # Pro-tip: Defino el precio como FloatField para que en el JSON
    # aparezca como un número (ej. 99.99) y no como una cadena ("99.99").
    price = serializers.FloatField()
    authors = AuthorSerializer(many=True)

    class Meta:
        model = Experience
        fields = [
            'id', 'title', 'authors', 'experience_photograph', 'description', 'city', 'price',
            'is_new', 'created_at'
        ]

    def create(self, validated_data):
        authors_data = validated_data.pop('authors', [])
        exp = Experience.objects.create(**validated_data)
        for a in authors_data:
            author_obj, _ = Author.objects.get_or_create(name=a.get('name'), defaults={'photo_url': a.get('photo_url')})
            # Si quieres actualizar photo_url cuando llegue una nueva
            if a.get('photo_url') and author_obj.photo_url != a['photo_url']:
                author_obj.photo_url = a['photo_url']
                author_obj.save()
            exp.authors.add(author_obj)
        return exp

    def update(self, instance, validated_data):
        authors_data = validated_data.pop('authors', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if authors_data is not None:
            author_objs = []
            for a in authors_data:
                author_obj, _ = Author.objects.get_or_create(name=a.get('name'),
                                                             defaults={'photo_url': a.get('photo_url')})
                if a.get('photo_url') and author_obj.photo_url != a['photo_url']:
                    author_obj.photo_url = a['photo_url']
                    author_obj.save()
                author_objs.append(author_obj)
            instance.authors.set(author_objs)
        return instance

class AdminProfileSerializer(FullProfileSerializer):
    """
    AdminProfile now includes the entire FullProfile plus a read-only list of the user's relatives.
    Allows full updates (PUT) using the same nested structure as FullProfileSerializer.
    """
    # Make often_in editable via AdminProfile (list of places stored as comma-separated text)
    often_in = CommaSeparatedArrayField(required=False)
    relatives = serializers.SerializerMethodField(read_only=True)

    class Meta(FullProfileSerializer.Meta):
        fields = FullProfileSerializer.Meta.fields + [
            'guiding_principle',
            'postal_address',
            'often_in',
            'life_partner_name',
            'life_partner_lastname',
            'annual_limits_introduction',
            'receive_reports',
            'relatives']

    def get_relatives(self, obj):
        # Import here to avoid circular import at module load
        from api.serializers import RelativeSerializer
        try:
            user = obj.user
            qs = getattr(user, 'relatives', None)
            if qs is None:
                return []
            return RelativeSerializer(qs.all().order_by('-created_at'), many=True).data
        except Exception:
            return []
