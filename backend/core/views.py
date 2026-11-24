from zipfile import BadZipFile

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.http import FileResponse, Http404
from django.utils import timezone
from datetime import datetime
from rest_framework import serializers, viewsets, status, generics
from rest_framework.views import APIView
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView
import json
from openpyxl import Workbook, load_workbook
from openpyxl.utils.exceptions import InvalidFileException
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from io import BytesIO

from .models import *
from .serializers import *
from .permissions import CanManageRecords


@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    try:
        Institution.objects.count()
        return Response({'status': 'ok', 'database': 'connected'})
    except Exception as exc:
        return Response({'status': 'degraded', 'database': str(exc)}, status=503)


class LoginView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.filter(username=request.data.get('username')).first()
            if user:
                AuditLog.objects.create(
                    user=user,
                    action='LOGIN',
                    module='AUTHENTICATION',
                    record_reference=str(user.pk),
                    change_details={'username': user.username},
                    ip_address=request.META.get('REMOTE_ADDR'),
                )
        return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(UserSerializer(request.user).data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    serializer = ProfileSerializer(request.user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    old_password = request.data.get('old_password', '')
    new_password = request.data.get('new_password', '')
    if not request.user.check_password(old_password):
        return Response({'old_password': ['Current password is incorrect.']}, status=400)
    if len(new_password) < 8:
        return Response({'new_password': ['Password must be at least 8 characters.']}, status=400)
    request.user.set_password(new_password)
    request.user.save(update_fields=['password'])
    return Response({'detail': 'Password changed successfully.'})


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    if not request.user.is_authenticated:
        pass
    data = request.data.copy()
    data['role'] = 'FACULTY_STAFF'
    serializer = UserSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response(UserSerializer(user).data, status=201)


@api_view(['GET'])
@permission_classes([AllowAny])
def student_registration_options(request):
    return Response({
        'institutions': list(Institution.objects.filter(
            departments__is_active=True,
            departments__programmes__is_active=True,
        ).distinct().order_by('name').values('id', 'name')),
        'departments': list(Department.objects.filter(
            is_active=True,
            programmes__is_active=True,
        ).distinct().order_by('name').values(
            'id', 'name', 'institution_id')),
        'programmes': list(Programme.objects.filter(is_active=True).order_by('name').values(
            'id', 'name', 'department_id')),
        'academic_years': list(AcademicYear.objects.order_by('-start_date').values('id', 'name')),
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def student_register(request):
    serializer = StudentRegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    student = serializer.save()
    return Response({
        'detail': 'Student account created. You can now sign in.',
        'student': StudentPortalSerializer(student).data,
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_profile(request):
    if request.user.role != 'STUDENT':
        raise PermissionDenied('Student account required.')
    student = Student.objects.select_related(
        'department__institution', 'programme', 'academic_year',
    ).filter(user=request.user).first()
    if student is None:
        raise PermissionDenied('No student profile is linked to this account.')
    return Response(StudentPortalSerializer(student).data)


class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [CanManageRecords]


class BulkImportView(APIView):
    permission_classes = [IsAuthenticated]
    max_import_rows = 5000
    max_import_file_size = 10 * 1024 * 1024
    max_evidence_total_size = 50 * 1024 * 1024
    excluded_fields = {'id', 'user', 'created_at', 'updated_at'}
    resource_serializers = {
        'institutions': (Institution, InstitutionSerializer),
        'academic-years': (AcademicYear, AcademicYearSerializer),
        'facilities': (InstitutionalFacility, InstitutionalFacilitySerializer),
        'departments': (Department, DepartmentSerializer),
        'programmes': (Programme, ProgrammeSerializer),
        'courses': (Course, CourseSerializer),
        'faculty': (Faculty, FacultySerializer),
        'research-projects': (ResearchProject, ResearchProjectSerializer),
        'publications': (Publication, PublicationSerializer),
        'placements': (Placement, PlacementSerializer),
        'frameworks': (AccreditationFramework, FrameworkSerializer),
        'criteria': (Criterion, CriterionSerializer),
        'parameters': (Parameter, ParameterSerializer),
        'evidence': (EvidenceDocument, EvidenceDocumentSerializer),
        'submissions': (Submission, SubmissionSerializer),
    }

    def _resource(self, resource):
        config = self.resource_serializers.get(resource)
        if config is None:
            raise Http404
        if self.request.user.role not in ('SUPER_ADMIN', 'INSTITUTIONAL_ADMIN'):
            raise PermissionDenied('Only university administrators can import records.')
        if resource == 'institutions' and self.request.user.role != 'SUPER_ADMIN':
            raise PermissionDenied('Only super administrators can import institutions.')
        return config

    def _columns(self, resource, serializer):
        columns = [
            name for name, field in serializer.fields.items()
            if not field.read_only
            and name not in self.excluded_fields
            and not isinstance(field, serializers.FileField)
        ]
        if resource == 'evidence':
            columns.append('file_name')
        if resource == 'submissions':
            columns = [
                name for name in columns
                if name not in ('status', 'submitted_by', 'reviewed_by', 'approved_by')
            ]
        return columns

    def get(self, request, resource):
        model, serializer_class = self._resource(resource)
        serializer = serializer_class()
        columns = self._columns(resource, serializer)
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = 'Data'
        sheet.append(columns)

        instructions = workbook.create_sheet('Instructions')
        instructions.append([f'{model._meta.verbose_name.title()} Excel import'])
        instructions.append(['Add one record per row on the Data sheet.'])
        instructions.append(['Relationship columns must contain record IDs; see the reference sheets.'])
        instructions.append(['The full workbook is validated before any records are saved.'])
        instructions.append(['User accounts, audit history, and notifications are not imported from Excel.'])
        if resource == 'evidence':
            instructions.append(['Provide each document separately with the upload, using the exact file name in file_name.'])
            instructions.append(['Supported document types: PDF, JPG, JPEG, PNG, DOC, DOCX, XLS, XLSX.'])
        if resource == 'submissions':
            instructions.append(['Imported submissions are always created as DRAFT and must be submitted through the workflow.'])
        optional_file_fields = [
            name for name, field in serializer.fields.items()
            if isinstance(field, serializers.FileField) and name != 'file'
        ]
        if optional_file_fields:
            instructions.append([
                f'Optional file fields ({", ".join(optional_file_fields)}) are not included; attach files separately.'
            ])

        for name in columns:
            field = serializer.fields.get(name)
            queryset = getattr(field, 'queryset', None)
            if queryset is None:
                continue
            reference = workbook.create_sheet(f'{name[:21]}_reference')
            reference.append(['id', 'name', 'code'])
            for item in self._reference_queryset(queryset).order_by('pk')[:1000]:
                label = (
                    getattr(item, 'name', None)
                    or getattr(item, 'title', None)
                    or getattr(item, 'full_name', None)
                    or str(item)
                )
                reference.append([item.pk, label, getattr(item, 'code', '')])

        output = BytesIO()
        workbook.save(output)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="{resource}_import_template.xlsx"'
        return response

    def _reference_queryset(self, queryset):
        user = self.request.user
        if user.role == 'SUPER_ADMIN' or queryset.model in (AcademicYear, AccreditationFramework, Criterion):
            return queryset
        if user.department is None:
            return queryset.none()
        institution_id = user.department.institution_id
        model = queryset.model
        if model is Institution:
            return queryset.filter(pk=institution_id)
        if model is Department:
            return queryset.filter(institution_id=institution_id)
        if model in (Programme, Faculty, Student, ResearchProject, Publication):
            return queryset.filter(department__institution_id=institution_id)
        if model is Course:
            return queryset.filter(programme__department__institution_id=institution_id)
        if model is Placement:
            return queryset.filter(student__department__institution_id=institution_id)
        if model in (EvidenceDocument, Submission):
            return queryset.filter(department__institution_id=institution_id)
        if model is Parameter:
            return queryset.filter(
                Q(department__institution_id=institution_id) | Q(department__isnull=True))
        return queryset

    def post(self, request, resource):
        model, serializer_class = self._resource(resource)
        upload = request.FILES.get('file')
        if upload is None:
            raise ValidationError({'file': 'Choose an .xlsx workbook to import.'})
        if not upload.name.lower().endswith('.xlsx'):
            raise ValidationError({'file': 'Only .xlsx files are supported.'})
        if upload.size > self.max_import_file_size:
            raise ValidationError({'file': 'The workbook must be 10 MB or smaller.'})

        evidence_files = request.FILES.getlist('documents') if resource == 'evidence' else []
        if sum(item.size for item in evidence_files) > self.max_evidence_total_size:
            raise ValidationError({'documents': 'Evidence documents must total 50 MB or less.'})
        if any(item.size > self.max_import_file_size for item in evidence_files):
            raise ValidationError({'documents': 'Each evidence document must be 10 MB or smaller.'})

        try:
            workbook = load_workbook(upload, read_only=True, data_only=True)
        except (BadZipFile, InvalidFileException, OSError, ValueError):
            raise ValidationError({'file': 'The uploaded file is not a valid .xlsx workbook.'})
        if 'Data' not in workbook.sheetnames:
            workbook.close()
            raise ValidationError({'file': 'The workbook must contain a Data sheet.'})

        serializer = serializer_class()
        columns = self._columns(resource, serializer)
        rows = workbook['Data'].iter_rows(values_only=True)
        header_row = next(rows, None)
        if not header_row:
            workbook.close()
            raise ValidationError({'file': 'The workbook is empty.'})
        headers = [self._cell_text(value).lstrip('\ufeff').lower() for value in header_row]
        if len(headers) != len(set(headers)):
            workbook.close()
            raise ValidationError({'headers': 'Column headers must not be duplicated.'})
        missing = sorted({
            name for name, field in serializer.fields.items()
            if name in columns and field.required and name not in headers
        })
        if resource == 'evidence' and 'file_name' not in headers:
            missing.append('file_name')
        if missing:
            workbook.close()
            raise ValidationError({'headers': f'Missing required columns: {", ".join(missing)}.'})
        unknown = sorted(set(headers) - set(columns))
        if unknown:
            workbook.close()
            raise ValidationError({'headers': f'Unknown columns: {", ".join(unknown)}.'})

        document_map = {}
        for item in evidence_files:
            filename = item.name
            name_key = filename.casefold()
            if ('/' in filename or '\\' in filename or not filename or name_key in document_map):
                workbook.close()
                raise ValidationError({'documents': 'Document names must be unique file names without folder paths.'})
            document_map[name_key] = item

        errors = []
        valid_rows = []
        used_document_names = set()
        for row_number, values in enumerate(rows, start=2):
            if row_number > self.max_import_rows + 1:
                errors.append({
                    'row': row_number,
                    'errors': {'file': 'A maximum of 5,000 data rows is allowed.'},
                })
                break
            if not values or all(value is None or self._cell_text(value) == '' for value in values):
                continue
            row = {
                header: values[index] if index < len(values) else None
                for index, header in enumerate(headers)
                if header
            }
            data = {}
            for name in columns:
                if name == 'file_name':
                    continue
                if name not in row:
                    continue
                value = row[name]
                field = serializer.fields[name]
                if isinstance(value, str):
                    value = value.strip()
                if isinstance(value, datetime) and isinstance(field, serializers.DateField):
                    value = value.date()
                if value is None or value == '':
                    if field.allow_null:
                        data[name] = None
                    elif getattr(field, 'allow_blank', False):
                        data[name] = ''
                    elif field.required:
                        data[name] = None
                    continue
                data[name] = value

            row_errors = {}
            evidence_file = None
            if resource == 'evidence':
                filename = self._cell_text(row.get('file_name'))
                evidence_file = document_map.get(filename.casefold())
                if not filename or evidence_file is None:
                    row_errors['file_name'] = 'Upload the document whose name exactly matches this value.'
                elif filename.casefold() in used_document_names:
                    row_errors['file_name'] = 'Each uploaded document can be used for only one evidence row.'
                elif not filename.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx', '.xls', '.xlsx')):
                    row_errors['file_name'] = 'This document type is not supported.'
                else:
                    used_document_names.add(filename.casefold())
                    data['file'] = evidence_file

            row_serializer = serializer_class(data=data)
            if not row_serializer.is_valid():
                row_errors.update({
                    field: '; '.join(str(message) for message in messages)
                    for field, messages in row_serializer.errors.items()
                })
            if not row_errors:
                candidate_data = dict(row_serializer.validated_data)
                save_kwargs = {}
                if resource == 'submissions':
                    candidate_data['status'] = 'DRAFT'
                    candidate_data['submitted_by'] = request.user
                    save_kwargs = {'status': 'DRAFT', 'submitted_by': request.user}
                elif resource == 'evidence':
                    save_kwargs = {'uploaded_by': request.user}
                candidate_data.update(save_kwargs)
                candidate = model(**candidate_data)
                try:
                    self._validate_institution_scope(resource, candidate)
                except PermissionDenied as exc:
                    row_errors['institution'] = str(exc.detail)
                if not row_errors:
                    try:
                        candidate.full_clean()
                    except DjangoValidationError as exc:
                        validation_errors = getattr(
                            exc, 'message_dict', {'non_field_errors': exc.messages})
                        row_errors.update({
                            field: '; '.join(str(message) for message in messages)
                            for field, messages in validation_errors.items()
                        })
                    if not row_errors:
                        valid_rows.append((row_serializer, save_kwargs, evidence_file))
            if row_errors and len(errors) < 100:
                errors.append({'row': row_number, 'errors': row_errors})

        workbook.close()
        if resource == 'evidence' and set(document_map) != used_document_names:
            if len(errors) < 100:
                errors.append({
                    'row': 1,
                    'errors': {'documents': 'Upload exactly one document for each evidence row.'},
                })
        if errors:
            return Response({
                'detail': 'No records were imported. Correct the listed workbook errors and try again.',
                'errors': errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        if not valid_rows:
            raise ValidationError({'file': 'The workbook contains no data rows.'})

        created_files = []
        try:
            with transaction.atomic():
                for row_serializer, save_kwargs, _evidence_file in valid_rows:
                    instance = row_serializer.save(**save_kwargs)
                    if resource == 'evidence' and instance.file:
                        created_files.append((instance.file.storage, instance.file.name))
        except IntegrityError:
            for storage, name in created_files:
                storage.delete(name)
            raise ValidationError({
                'detail': 'No records were imported because one or more unique values already exist.',
            })
        except Exception:
            for storage, name in created_files:
                storage.delete(name)
            raise

        return Response({
            'detail': f'Imported {len(valid_rows)} {model._meta.verbose_name_plural}.',
            'imported': len(valid_rows),
        }, status=status.HTTP_201_CREATED)

    def _validate_institution_scope(self, resource, instance):
        user = self.request.user
        if user.role == 'SUPER_ADMIN':
            return
        if resource == 'institutions':
            raise PermissionDenied('Institutional administrators cannot create institutions.')
        if user.role != 'INSTITUTIONAL_ADMIN':
            raise PermissionDenied('Only university administrators can import records.')
        if user.department is None:
            raise PermissionDenied('Your account must be linked to a department before importing records.')
        institution_id = user.department.institution_id
        target_institution_id = None
        if isinstance(instance, (Department, InstitutionalFacility)):
            target_institution_id = instance.institution_id
        elif isinstance(instance, (Programme, Faculty, ResearchProject, Publication)):
            target_institution_id = instance.department.institution_id
        elif isinstance(instance, Course):
            target_institution_id = instance.programme.department.institution_id
        elif isinstance(instance, Student):
            target_institution_id = instance.department.institution_id
        elif isinstance(instance, Placement):
            target_institution_id = instance.student.department.institution_id
        elif isinstance(instance, EvidenceDocument):
            target_institution_id = instance.department.institution_id
        elif isinstance(instance, Submission):
            target_institution_id = instance.department.institution_id
        elif isinstance(instance, Parameter) and instance.department_id:
            target_institution_id = instance.department.institution_id
        if target_institution_id is not None and target_institution_id != institution_id:
            raise PermissionDenied('You can only import records for your own university.')

    @staticmethod
    def _cell_text(value):
        if value is None:
            return ''
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value).strip()


class UserViewSet(BaseViewSet):
    queryset = User.objects.select_related('department').all()
    serializer_class = UserSerializer
    search_fields = ['username', 'email', 'first_name', 'last_name']


class InstitutionViewSet(BaseViewSet):
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer


class DepartmentViewSet(BaseViewSet):
    queryset = Department.objects.select_related('institution').all().order_by('name')
    serializer_class = DepartmentSerializer
    filterset_fields = ['institution', 'is_active']
    search_fields = ['name', 'code', 'head']


class AcademicYearViewSet(BaseViewSet):
    queryset = AcademicYear.objects.all().order_by('-start_date')
    serializer_class = AcademicYearSerializer


class InstitutionalFacilityViewSet(BaseViewSet):
    queryset = InstitutionalFacility.objects.select_related('institution').all().order_by('name')
    serializer_class = InstitutionalFacilitySerializer
    filterset_fields = ['institution', 'facility_type']
    search_fields = ['name', 'location', 'facility_type']


class ProgrammeViewSet(BaseViewSet):
    queryset = Programme.objects.select_related('department').all().order_by('name')
    serializer_class = ProgrammeSerializer
    filterset_fields = ['department', 'is_active']
    filterset_fields = ['department', 'department__institution', 'is_active']
    search_fields = ['name', 'code']


class CourseViewSet(BaseViewSet):
    queryset = Course.objects.select_related('programme').all().order_by('name')
    serializer_class = CourseSerializer
    filterset_fields = ['programme']


class FacultyViewSet(BaseViewSet):
    queryset = Faculty.objects.select_related('department').all().order_by('full_name')
    serializer_class = FacultySerializer
    filterset_fields = ['department']
    filterset_fields = ['department', 'department__institution']
    search_fields = ['full_name', 'faculty_id', 'designation', 'email']


class StudentViewSet(BaseViewSet):
    queryset = Student.objects.select_related('department', 'programme', 'academic_year').all().order_by('student_id')
    serializer_class = StudentSerializer
    filterset_fields = ['department', 'programme', 'academic_year']
    filterset_fields = ['department', 'department__institution', 'programme', 'academic_year']
    search_fields = ['full_name', 'student_id', 'roll_number', 'email']

    import_headers = [
        'student_id', 'roll_number', 'full_name', 'email', 'department_code',
        'programme_code', 'academic_year', 'admission_year', 'achievements',
        'internship_details', 'project_details',
    ]
    max_import_rows = 5000
    max_import_file_size = 10 * 1024 * 1024

    def _require_import_role(self):
        if self.request.user.role not in ('SUPER_ADMIN', 'INSTITUTIONAL_ADMIN'):
            raise PermissionDenied('Only university administrators can import student records.')

    def _import_institution(self):
        self._require_import_role()
        institution_id = self.request.data.get('institution')
        if self.request.user.role == 'INSTITUTIONAL_ADMIN':
            department = self.request.user.department
            if department is None:
                raise PermissionDenied('Your account must be linked to a department before importing students.')
            institution = department.institution
            if institution_id and str(institution_id) != str(institution.id):
                raise PermissionDenied('You can only import students for your own university.')
            return institution
        if not institution_id:
            raise ValidationError({'institution': 'Select the university for these student records.'})
        institution = Institution.objects.filter(pk=institution_id).first()
        if institution is None:
            raise ValidationError({'institution': 'The selected university does not exist.'})
        return institution

    @action(detail=False, methods=['get'], url_path='import-template')
    def import_template(self, request):
        self._require_import_role()
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = 'Students'
        sheet.append(self.import_headers)
        instructions = workbook.create_sheet('Instructions')
        instructions.append(['Student Excel import template'])
        instructions.append(['Fill one student per row on the Students sheet.'])
        instructions.append(['Use department_code and programme_code from the selected university.'])
        instructions.append(['Use an existing academic year name, for example 2025-26.'])
        instructions.append(['Required columns: student_id, roll_number, full_name, email, department_code, programme_code, academic_year, admission_year.'])
        instructions.append(['Optional columns: achievements, internship_details, project_details.'])
        instructions.append(['This import creates student records only; it does not create login accounts.'])
        output = BytesIO()
        workbook.save(output)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = 'attachment; filename="student_import_template.xlsx"'
        return response

    @action(detail=False, methods=['post'], url_path='import-excel')
    def import_excel(self, request):
        institution = self._import_institution()
        upload = request.FILES.get('file')
        if upload is None:
            raise ValidationError({'file': 'Choose an .xlsx file to import.'})
        if not upload.name.lower().endswith('.xlsx'):
            raise ValidationError({'file': 'Only .xlsx files are supported.'})
        if upload.size > self.max_import_file_size:
            raise ValidationError({'file': 'The workbook must be 10 MB or smaller.'})

        try:
            workbook = load_workbook(upload, read_only=True, data_only=True)
        except (BadZipFile, InvalidFileException, OSError, ValueError):
            raise ValidationError({'file': 'The uploaded file is not a valid .xlsx workbook.'})

        sheet = workbook['Students'] if 'Students' in workbook.sheetnames else workbook.active
        rows = sheet.iter_rows(values_only=True)
        header_row = next(rows, None)
        if not header_row:
            workbook.close()
            raise ValidationError({'file': 'The workbook is empty.'})

        headers = [self._cell_text(value).lstrip('\ufeff').lower() for value in header_row]
        required_headers = set(self.import_headers[:8])
        missing_headers = sorted(required_headers - set(headers))
        if missing_headers:
            workbook.close()
            raise ValidationError({
                'headers': f'Missing required columns: {", ".join(missing_headers)}.',
            })
        if len(headers) != len(set(headers)):
            workbook.close()
            raise ValidationError({'headers': 'Column headers must not be duplicated.'})

        departments = {
            department.code.strip().upper(): department
            for department in Department.objects.filter(institution=institution, is_active=True)
        }
        programmes = {
            (programme.department.code.strip().upper(), programme.code.strip().upper()): programme
            for programme in Programme.objects.filter(
                department__institution=institution,
                department__is_active=True,
                is_active=True,
            ).select_related('department')
        }
        academic_years = {
            academic_year.name.strip().casefold(): academic_year
            for academic_year in AcademicYear.objects.all()
        }
        used_student_ids = set(Student.objects.values_list('student_id', flat=True))
        used_roll_numbers = set(Student.objects.values_list('roll_number', flat=True))
        used_emails = {email.casefold() for email in Student.objects.values_list('email', flat=True)}
        seen_student_ids = set()
        seen_roll_numbers = set()
        seen_emails = set()
        students = []
        errors = []

        for row_number, values in enumerate(rows, start=2):
            if row_number > self.max_import_rows + 1:
                errors.append({'row': row_number, 'errors': {'file': 'A maximum of 5,000 student rows is allowed.'}})
                break
            if not values or all(value is None or self._cell_text(value) == '' for value in values):
                continue
            row = {
                header: values[index] if index < len(values) else None
                for index, header in enumerate(headers)
                if header
            }
            fields = {name: self._cell_text(row.get(name)) for name in self.import_headers}
            row_errors = {}

            for field in self.import_headers[:8]:
                if not fields[field]:
                    row_errors[field] = 'This value is required.'

            for field, max_length in (
                ('student_id', 30), ('roll_number', 50), ('full_name', 200),
                ('email', 254), ('department_code', 30), ('programme_code', 30),
                ('academic_year', 30),
            ):
                if len(fields[field]) > max_length:
                    row_errors[field] = f'Must be {max_length} characters or fewer.'

            email = fields['email'].casefold()
            try:
                validate_email(fields['email'])
            except DjangoValidationError:
                if fields['email']:
                    row_errors['email'] = 'Enter a valid email address.'

            student_id = fields['student_id']
            roll_number = fields['roll_number']
            if student_id and (student_id in used_student_ids or student_id in seen_student_ids):
                row_errors['student_id'] = 'This student ID is already registered.'
            if roll_number and (roll_number in used_roll_numbers or roll_number in seen_roll_numbers):
                row_errors['roll_number'] = 'This roll number is already registered.'
            if email and (email in used_emails or email in seen_emails):
                row_errors['email'] = 'A student record already uses this email.'

            department = departments.get(fields['department_code'].upper())
            if fields['department_code'] and department is None:
                row_errors['department_code'] = 'This department code does not belong to the selected university.'
            programme = programmes.get((
                fields['department_code'].upper(),
                fields['programme_code'].upper(),
            ))
            if fields['programme_code'] and programme is None:
                row_errors['programme_code'] = 'This programme code does not belong to the selected department.'

            academic_year = academic_years.get(fields['academic_year'].casefold())
            if fields['academic_year'] and academic_year is None:
                row_errors['academic_year'] = 'This academic year does not exist.'
            try:
                admission_year = int(float(fields['admission_year']))
                if not 1900 <= admission_year <= 2200:
                    raise ValueError
            except (ValueError, OverflowError):
                if fields['admission_year']:
                    row_errors['admission_year'] = 'Enter a year between 1900 and 2200.'
                admission_year = None

            if row_errors:
                if len(errors) < 100:
                    errors.append({'row': row_number, 'errors': row_errors})
                continue

            seen_student_ids.add(student_id)
            seen_roll_numbers.add(roll_number)
            seen_emails.add(email)
            students.append(Student(
                student_id=student_id,
                roll_number=roll_number,
                full_name=fields['full_name'],
                email=fields['email'],
                department=department,
                programme=programme,
                academic_year=academic_year,
                admission_year=admission_year,
                achievements=fields['achievements'],
                internship_details=fields['internship_details'],
                project_details=fields['project_details'],
            ))

        workbook.close()
        if errors:
            return Response({
                'detail': 'No student records were imported. Correct the listed workbook errors and try again.',
                'errors': errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        if not students:
            raise ValidationError({'file': 'The workbook contains no student data rows.'})

        try:
            with transaction.atomic():
                Student.objects.bulk_create(students, batch_size=500)
        except IntegrityError:
            raise ValidationError({
                'detail': 'The import was not saved because one or more student IDs, roll numbers, or emails already exist.',
            })
        return Response({
            'detail': f'Imported {len(students)} student records into {institution.name}.',
            'imported': len(students),
        }, status=status.HTTP_201_CREATED)

    @staticmethod
    def _cell_text(value):
        if value is None:
            return ''
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value).strip()


class ResearchProjectViewSet(BaseViewSet):
    queryset = ResearchProject.objects.select_related('department', 'principal_investigator').all().order_by('-start_date')
    serializer_class = ResearchProjectSerializer
    filterset_fields = ['department', 'academic_year', 'status']


class PublicationViewSet(BaseViewSet):
    queryset = Publication.objects.select_related('department', 'academic_year').all().order_by('-publication_date')
    serializer_class = PublicationSerializer
    filterset_fields = ['department', 'academic_year', 'publication_type']


class PlacementViewSet(BaseViewSet):
    queryset = Placement.objects.select_related('student', 'academic_year').all().order_by('-placement_date')
    serializer_class = PlacementSerializer
    filterset_fields = ['academic_year', 'student']


class FrameworkViewSet(BaseViewSet):
    queryset = AccreditationFramework.objects.all()
    serializer_class = FrameworkSerializer
    search_fields = ['name', 'code']


class CriterionViewSet(BaseViewSet):
    queryset = Criterion.objects.select_related('framework').all()
    serializer_class = CriterionSerializer
    filterset_fields = ['framework']


class ParameterViewSet(BaseViewSet):
    queryset = Parameter.objects.select_related('criterion', 'department').all()
    serializer_class = ParameterSerializer
    filterset_fields = ['criterion', 'department', 'academic_year']


class EvidenceViewSet(BaseViewSet):
    queryset = EvidenceDocument.objects.select_related('department', 'academic_year', 'uploaded_by').all()
    serializer_class = EvidenceDocumentSerializer
    filterset_fields = ['department', 'academic_year', 'parameter', 'category']
    search_fields = ['title', 'category']

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        evidence = self.get_object()
        if not evidence.file:
            raise Http404
        try:
            return FileResponse(evidence.file.open('rb'), as_attachment=True,
                                filename=evidence.file.name.rsplit('/', 1)[-1])
        except FileNotFoundError:
            raise Http404


class SubmissionViewSet(BaseViewSet):
    queryset = Submission.objects.select_related(
        'parameter', 'department', 'academic_year', 'submitted_by').all()
    serializer_class = SubmissionSerializer
    filterset_fields = ['status', 'department', 'department__institution', 'academic_year', 'parameter']

    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        obj = self.get_object()
        if obj.submitted_by_id != request.user.id:
            raise PermissionDenied('Only the submitter can submit this record.')
        obj.status = 'SUBMITTED'
        obj.save()
        Review.objects.create(submission=obj, reviewer=request.user,
                              decision='SUBMITTED', comments=request.data.get('comments', ''))
        Notification.objects.create(
            user=request.user,
            title='Submission sent',
            message=f'{obj.title} was submitted for review.',
            link=f'/submissions/{obj.id}',
        )
        return Response(SubmissionSerializer(obj).data)

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        if request.user.role not in ('REVIEWER_VERIFIER', 'SUPER_ADMIN', 'INSTITUTIONAL_ADMIN'):
            raise PermissionDenied('Reviewer role required.')
        obj = self.get_object()
        decision = request.data.get('decision')
        if decision not in ('UNDER_REVIEW', 'CORRECTION_REQUIRED', 'VERIFIED'):
            raise PermissionDenied('Invalid review decision.')
        obj.status = decision
        obj.reviewed_by = request.user
        obj.save()
        Review.objects.create(submission=obj, reviewer=request.user, decision=decision,
                              comments=request.data.get('comments', ''))
        Notification.objects.create(
            user=obj.submitted_by,
            title=f'Submission {decision.replace("_", " ").title()}',
            message=request.data.get('comments', f'Submission status changed to {decision}.'),
            link=f'/submissions/{obj.id}',
        )
        return Response(SubmissionSerializer(obj).data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        if not request.user.can_approve and request.user.role not in ('SUPER_ADMIN', 'INSTITUTIONAL_ADMIN'):
            raise PermissionDenied('Approval authority required.')
        obj = self.get_object()
        if obj.submitted_by_id == request.user.id:
            raise PermissionDenied('Self approval is prohibited.')
        if obj.status != 'VERIFIED':
            raise PermissionDenied('Only verified submissions can be approved.')
        obj.status = 'APPROVED'
        obj.approved_by = request.user
        obj.save()
        Notification.objects.create(
            user=obj.submitted_by,
            title='Submission Approved',
            message=f'{obj.title} has been approved.',
            link=f'/submissions/{obj.id}',
        )
        return Response(SubmissionSerializer(obj).data)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response(NotificationSerializer(notification).data)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.select_related('user').all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['module', 'action']
    search_fields = ['module', 'action', 'record_reference']

    def get_queryset(self):
        if self.request.user.role not in ('SUPER_ADMIN', 'INSTITUTIONAL_ADMIN'):
            raise PermissionDenied('Audit logs are restricted.')
        return super().get_queryset()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request):
    if request.user.role == 'STUDENT':
        raise PermissionDenied('Student accounts cannot access the institutional dashboard.')
    institution_id = request.query_params.get('institution')
    institution_name = None
    departments = Department.objects.all()
    faculty = Faculty.objects.all()
    students = Student.objects.all()
    programmes = Programme.objects.all()
    projects = ResearchProject.objects.all()
    publications = Publication.objects.all()
    placements = Placement.objects.all()
    submissions = Submission.objects.all()
    evidence = EvidenceDocument.objects.all()
    parameters = Parameter.objects.all()
    criteria = Criterion.objects.all()

    if institution_id:
        institution = Institution.objects.filter(pk=institution_id).first()
        if institution:
            institution_name = institution.name
            departments = departments.filter(institution=institution)
            faculty = faculty.filter(department__institution=institution)
            students = students.filter(department__institution=institution)
            programmes = programmes.filter(department__institution=institution)
            projects = projects.filter(department__institution=institution)
            publications = publications.filter(department__institution=institution)
            placements = placements.filter(student__department__institution=institution)
            submissions = submissions.filter(department__institution=institution)
            evidence = evidence.filter(department__institution=institution)
            parameters = parameters.filter(department__institution=institution)
            criteria = criteria.filter(parameters__department__institution=institution).distinct()

    verified = submissions.filter(status='VERIFIED').count()
    approved = submissions.filter(status='APPROVED').count()
    pending = submissions.filter(status__in=('SUBMITTED', 'UNDER_REVIEW', 'CORRECTION_REQUIRED')).count()
    parameter_count = parameters.count()
    completed = submissions.filter(status='APPROVED').values('parameter').distinct().count()
    total_evidence = evidence.count()
    missing_evidence = max(parameter_count - total_evidence, 0)
    activity_logs = AuditLog.objects.all().values(
        'action', 'module', 'record_reference', 'timestamp')
    if institution_id:
        submission_ids = {str(pk) for pk in submissions.values_list('pk', flat=True)}
        evidence_ids = {str(pk) for pk in evidence.values_list('pk', flat=True)}
        activity_logs = [
            item for item in activity_logs
            if (item['module'] == 'SUBMISSIONS' and item['record_reference'] in submission_ids)
            or (item['module'] == 'EVIDENCE' and item['record_reference'] in evidence_ids)
        ][:8]
    else:
        activity_logs = list(activity_logs[:8])
    data = {
        'institution': institution_name,
        'departments': departments.count(),
        'faculty': faculty.count(),
        'students': students.count(),
        'programmes': programmes.count(),
        'research_projects': projects.count(),
        'publications': publications.count(),
        'placements': placements.count(),
        'criteria': criteria.count(),
        'parameters': parameter_count,
        'pending_submissions': pending,
        'verified_records': verified,
        'approved_records': approved,
        'missing_evidence': missing_evidence,
        'data_completeness': round((completed / parameter_count * 100), 1) if parameter_count else 0,
        'department_stats': list(departments.annotate(
            student_count=Count('students')).values('name', 'student_count')),
        'submission_stats': list(submissions.values('status').annotate(count=Count('id')).order_by('status')),
        'recent_activity': activity_logs,
    }
    return Response(data)


def report_download(request):
    try:
        authenticated = JWTAuthentication().authenticate(request)
    except Exception:
        authenticated = None
    if authenticated is None:
        return HttpResponse('Unauthorized', status=401)
    if authenticated[0].role == 'STUDENT':
        return HttpResponse('Forbidden', status=403)
    report_type = request.GET.get('type', 'institutional')
    export_format = request.GET.get('format', 'xlsx')
    department_id = request.GET.get('department')
    academic_year_id = request.GET.get('academic_year')
    status_filter = request.GET.get('status')
    if report_type == 'faculty':
        queryset = Faculty.objects.all()
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        rows = list(queryset.values('faculty_id', 'full_name', 'email', 'designation'))
    elif report_type == 'student':
        queryset = Student.objects.all()
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        rows = list(queryset.values('student_id', 'roll_number', 'full_name', 'email'))
    elif report_type == 'accreditation':
        queryset = Submission.objects.all()
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        rows = list(queryset.values('title', 'status', 'created_at'))
    elif report_type == 'placement':
        queryset = Placement.objects.select_related('student', 'academic_year').all()
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        rows = list(queryset.values(
            'student__full_name', 'company', 'position', 'package_lpa',
            'placement_date', 'academic_year__name'))
    elif report_type == 'research':
        queryset = ResearchProject.objects.select_related(
            'department', 'principal_investigator', 'academic_year').all()
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        rows = list(queryset.values(
            'title', 'principal_investigator__full_name', 'department__name',
            'funding_agency', 'funding_amount', 'status'))
    else:
        queryset = Department.objects.all()
        if department_id:
            queryset = queryset.filter(pk=department_id)
        rows = list(queryset.values('name', 'code', 'head'))

    if export_format == 'xlsx':
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = report_type[:31]
        if rows:
            sheet.append(list(rows[0].keys()))
            for row in rows:
                sheet.append(list(row.values()))
        output = BytesIO()
        workbook.save(output)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{report_type}-report.xlsx"'
        return response

    output = BytesIO()
    pdf = canvas.Canvas(output)
    pdf.setTitle(f'{report_type.title()} Report')
    pdf.drawString(40, 800, f'{report_type.title()} Report')
    y = 770
    for row in rows[:45]:
        pdf.drawString(40, y, str(row)[:110])
        y -= 16
        if y < 40:
            pdf.showPage()
            y = 770
    pdf.save()
    response = HttpResponse(output.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{report_type}-report.pdf"'
    return response
