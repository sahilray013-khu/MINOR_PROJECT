from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class Role(models.Model):
    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    ROLE_CHOICES = [
        ('SUPER_ADMIN', 'Super Admin'), ('INSTITUTIONAL_ADMIN', 'Institutional Admin'),
        ('ACCREDITATION_COORDINATOR', 'Accreditation Coordinator'),
        ('DEPARTMENT_ADMIN', 'Department Admin'), ('FACULTY_STAFF', 'Faculty/Staff'),
        ('STUDENT', 'Student'),
        ('REVIEWER_VERIFIER', 'Reviewer/Verifier'), ('MANAGEMENT_VIEWER', 'Management Viewer'),
    ]
    role = models.CharField(max_length=32, choices=ROLE_CHOICES, default='FACULTY_STAFF')
    phone = models.CharField(max_length=20, blank=True)
    department = models.ForeignKey('Department', null=True, blank=True, on_delete=models.SET_NULL)
    can_approve = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Institution(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.name


class Department(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=30)
    head = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('institution', 'code')

    def __str__(self):
        return self.name


class AcademicYear(models.Model):
    name = models.CharField(max_length=30, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError('End date must be after start date.')

    def __str__(self):
        return self.name


class InstitutionalFacility(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='facilities')
    name = models.CharField(max_length=150)
    facility_type = models.CharField(max_length=100)
    location = models.CharField(max_length=150, blank=True)
    capacity = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ('institution', 'name')

    def __str__(self):
        return self.name


class Programme(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='programmes')
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=30)
    duration_years = models.PositiveSmallIntegerField(default=4)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('department', 'code')


class Course(models.Model):
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='courses')
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=30)
    credits = models.PositiveSmallIntegerField(default=3)
    semester = models.PositiveSmallIntegerField(default=1)

    class Meta:
        unique_together = ('programme', 'code')


class Faculty(models.Model):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.SET_NULL)
    faculty_id = models.CharField(max_length=30, unique=True)
    full_name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='faculty')
    designation = models.CharField(max_length=100)
    qualification = models.CharField(max_length=200)
    experience_years = models.PositiveSmallIntegerField(default=0)
    joining_date = models.DateField()
    specialization = models.CharField(max_length=200, blank=True)
    research_interests = models.TextField(blank=True)
    achievements = models.TextField(blank=True)
    document = models.FileField(upload_to='faculty/', blank=True)


class Student(models.Model):
    user = models.OneToOneField(
        'User', null=True, blank=True, on_delete=models.SET_NULL, related_name='student_profile')
    student_id = models.CharField(max_length=30, unique=True)
    roll_number = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='students')
    programme = models.ForeignKey(Programme, on_delete=models.PROTECT, related_name='students')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT)
    admission_year = models.PositiveSmallIntegerField()
    achievements = models.TextField(blank=True)
    internship_details = models.TextField(blank=True)
    project_details = models.TextField(blank=True)


class ResearchProject(models.Model):
    title = models.CharField(max_length=255)
    principal_investigator = models.ForeignKey(Faculty, on_delete=models.PROTECT)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT)
    funding_agency = models.CharField(max_length=150, blank=True)
    funding_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=30, default='ONGOING')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    document = models.FileField(upload_to='research/', blank=True)


class Publication(models.Model):
    title = models.CharField(max_length=255)
    authors = models.CharField(max_length=255)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    publication_type = models.CharField(max_length=50)
    publication_date = models.DateField()
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT)
    doi_or_reference = models.CharField(max_length=255, blank=True)
    document = models.FileField(upload_to='publications/', blank=True)


class Placement(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='placements')
    company = models.CharField(max_length=150)
    position = models.CharField(max_length=150)
    package_lpa = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    placement_date = models.DateField()
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT)


class AccreditationFramework(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    version = models.CharField(max_length=30, default='1.0')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Criterion(models.Model):
    framework = models.ForeignKey(AccreditationFramework, on_delete=models.CASCADE, related_name='criteria')
    code = models.CharField(max_length=30)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        unique_together = ('framework', 'code')


class Parameter(models.Model):
    criterion = models.ForeignKey(Criterion, on_delete=models.CASCADE, related_name='parameters')
    code = models.CharField(max_length=30)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    required_information = models.TextField(blank=True)
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL)
    academic_year = models.ForeignKey(AcademicYear, null=True, blank=True, on_delete=models.SET_NULL)
    deadline = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ('criterion', 'code')


class EvidenceDocument(models.Model):
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT)
    parameter = models.ForeignKey(Parameter, null=True, blank=True, on_delete=models.SET_NULL, related_name='documents')
    file = models.FileField(upload_to='evidence/%Y/%m/')
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        allowed = {'.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx', '.xls', '.xlsx'}
        name = self.file.name.lower()
        if not any(name.endswith(ext) for ext in allowed):
            raise ValidationError('Unsupported document type.')


class Submission(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'), ('SUBMITTED', 'Submitted'), ('UNDER_REVIEW', 'Under Review'),
        ('CORRECTION_REQUIRED', 'Correction Required'), ('VERIFIED', 'Verified'), ('APPROVED', 'Approved'),
    ]
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE, related_name='submissions')
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT)
    title = models.CharField(max_length=255)
    narrative = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='DRAFT')
    submitted_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='submissions')
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT, related_name='reviews')
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT, related_name='approvals')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.approved_by_id and self.approved_by_id == self.submitted_by_id:
            raise ValidationError('A submitter cannot approve their own submission.')


class Review(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='review_history')
    reviewer = models.ForeignKey(User, on_delete=models.PROTECT)
    decision = models.CharField(max_length=30)
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class AuditLog(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=100)
    module = models.CharField(max_length=100)
    record_reference = models.CharField(max_length=255, blank=True)
    change_details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
