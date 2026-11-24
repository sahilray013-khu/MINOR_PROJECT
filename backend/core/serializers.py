from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import *

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone',
                  'department', 'can_approve', 'password', 'is_active']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone']


class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Institution


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Department


class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = AcademicYear


class InstitutionalFacilitySerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = InstitutionalFacility


class ProgrammeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Programme


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Course


class FacultySerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Faculty


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Student


class StudentRegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=200)
    student_id = serializers.CharField(max_length=30)
    roll_number = serializers.CharField(max_length=50)
    institution = serializers.PrimaryKeyRelatedField(queryset=Institution.objects.all())
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.filter(is_active=True))
    programme = serializers.PrimaryKeyRelatedField(queryset=Programme.objects.filter(is_active=True))
    academic_year = serializers.PrimaryKeyRelatedField(queryset=AcademicYear.objects.all())
    admission_year = serializers.IntegerField(min_value=1900, max_value=2200)

    def validate(self, attrs):
        if attrs['department'].institution_id != attrs['institution'].id:
            raise serializers.ValidationError({
                'department': 'Choose a department belonging to the selected university.',
            })
        if attrs['programme'].department_id != attrs['department'].id:
            raise serializers.ValidationError({
                'programme': 'Choose a programme belonging to the selected department.',
            })
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({'username': 'This username is already in use.'})
        if Student.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({'email': 'A student account already uses this email.'})
        if Student.objects.filter(student_id=attrs['student_id']).exists():
            raise serializers.ValidationError({'student_id': 'This student ID is already registered.'})
        if Student.objects.filter(roll_number=attrs['roll_number']).exists():
            raise serializers.ValidationError({'roll_number': 'This roll number is already registered.'})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop('institution')
        username = validated_data.pop('username')
        email = validated_data.pop('email')
        full_name = validated_data.pop('full_name')
        password = validated_data.pop('password')
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=full_name[:150],
            role='STUDENT',
        )
        return Student.objects.create(user=user, email=email, full_name=full_name, **validated_data)


class StudentPortalSerializer(serializers.ModelSerializer):
    institution_name = serializers.CharField(source='department.institution.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    programme_name = serializers.CharField(source='programme.name', read_only=True)
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)

    class Meta:
        model = Student
        fields = [
            'student_id', 'roll_number', 'full_name', 'email', 'admission_year',
            'institution_name', 'department_name', 'programme_name', 'academic_year_name',
        ]


class ResearchProjectSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = ResearchProject


class PublicationSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Publication


class PlacementSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Placement


class FrameworkSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = AccreditationFramework


class CriterionSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Criterion


class ParameterSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Parameter


class EvidenceDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = EvidenceDocument
        read_only_fields = ['uploaded_by']

    def validate_file(self, file):
        if file.size > 10 * 1024 * 1024:
            raise serializers.ValidationError('File exceeds 10 MB limit.')
        return file


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Review


class SubmissionSerializer(serializers.ModelSerializer):
    evidence_count = serializers.SerializerMethodField()

    class Meta:
        fields = '__all__'
        model = Submission
        read_only_fields = ['submitted_by', 'reviewed_by', 'approved_by']

    def get_evidence_count(self, obj):
        return EvidenceDocument.objects.filter(parameter=obj.parameter).count()


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Notification
        read_only_fields = ['user']


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'user_name', 'action', 'module', 'record_reference',
            'change_details', 'ip_address', 'timestamp',
        ]
        read_only_fields = [
            'id', 'user', 'user_name', 'action', 'module', 'record_reference',
            'change_details', 'ip_address', 'timestamp',
        ]
