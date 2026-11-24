from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from reportlab.pdfgen import canvas

from core.models import (
    AcademicYear,
    Department,
    EvidenceDocument,
    Faculty,
    Institution,
    InstitutionalFacility,
    Parameter,
    Placement,
    Programme,
    Publication,
    ResearchProject,
    Student,
    Submission,
    User,
)


TARGET_COUNT = 15


class Command(BaseCommand):
    help = 'Add sample Dev Bhoomi data until each dashboard record type has at least 15 records'

    def handle(self, *args, **options):
        institution = Institution.objects.filter(code='DBUU').first()
        if institution is None:
            raise CommandError('Dev Bhoomi University (DBUU) was not found. Run seed_data first.')

        academic_year = AcademicYear.objects.order_by('-start_date').first()
        if academic_year is None:
            raise CommandError('No academic year exists. Create an academic year before populating demo data.')

        self.add_departments_and_programmes(institution)
        departments = list(Department.objects.filter(institution=institution).order_by('id'))
        self.add_students(institution, departments, academic_year)
        self.add_faculty(institution, departments)
        faculty = list(Faculty.objects.filter(department__institution=institution).order_by('id'))
        self.add_facilities(institution)
        self.add_research(institution, departments, faculty, academic_year)
        self.add_publications(institution, departments, academic_year)
        self.add_placements(institution, academic_year)

        submitter = User.objects.filter(username='faculty').first()
        if submitter is None:
            raise CommandError('Seeded faculty account was not found. Run seed_data first.')
        self.add_submissions(institution, academic_year, submitter)
        self.add_evidence(institution, academic_year, submitter, departments)

        self.stdout.write(self.style.SUCCESS('Dev Bhoomi dashboard demo data is ready.'))
        self.write_counts(institution)

    def add_departments_and_programmes(self, institution):
        catalog = [
            ('EE-DEMO', 'Electrical Engineering (Sample)', 'BTECH-EE-DEMO',
             'B.Tech Electrical Engineering (Sample)', 4),
            ('BIO-DEMO', 'Biotechnology (Sample)', 'BSC-BIO-DEMO',
             'B.Sc Biotechnology (Sample)', 3),
            ('AGRI-DEMO', 'Agriculture (Sample)', 'BSC-AGRI-DEMO',
             'B.Sc Agriculture (Sample)', 4),
            ('LAW-DEMO', 'Law (Sample)', 'LLB-DEMO', 'LL.B. (Sample)', 3),
            ('EDU-DEMO', 'Education (Sample)', 'BED-DEMO', 'B.Ed. (Sample)', 2),
        ]
        department_count = Department.objects.filter(institution=institution).count()
        for department_code, department_name, programme_code, programme_name, duration in catalog:
            if department_count >= TARGET_COUNT:
                break
            department, created = Department.objects.get_or_create(
                institution=institution,
                code=department_code,
                defaults={'name': department_name},
            )
            Programme.objects.get_or_create(
                department=department,
                code=programme_code,
                defaults={'name': programme_name, 'duration_years': duration, 'is_active': True},
            )
            if created:
                department_count += 1

    def add_students(self, institution, departments, academic_year):
        count = Student.objects.filter(department__institution=institution).count()
        if count >= TARGET_COUNT:
            return
        programmes = list(Programme.objects.filter(
            department__institution=institution,
            is_active=True,
        ).select_related('department').order_by('id'))
        if not programmes:
            raise CommandError('No programmes exist for DBUU. Add a department and programme first.')
        department_ids = {department.id for department in departments}
        programmes = [programme for programme in programmes if programme.department_id in department_ids]
        for number in range(1, TARGET_COUNT - count + 1):
            programme = programmes[(number - 1) % len(programmes)]
            Student.objects.get_or_create(
                student_id=f'DBUU-DEMO-STU-{number:03d}',
                defaults={
                    'roll_number': f'DBUU-DEMO-ROLL-{number:03d}',
                    'full_name': f'Demo Student {number:02d}',
                    'email': f'demo.student{number:03d}@dbuu.ac.in',
                    'department': programme.department,
                    'programme': programme,
                    'academic_year': academic_year,
                    'admission_year': academic_year.start_date.year,
                },
            )

    def add_faculty(self, institution, departments):
        count = Faculty.objects.filter(department__institution=institution).count()
        number = 1
        while count < TARGET_COUNT:
            department = departments[(number - 1) % len(departments)]
            faculty, created = Faculty.objects.get_or_create(
                faculty_id=f'DBUU-DEMO-FAC-{number:03d}',
                defaults={
                    'full_name': f'Demo Faculty {number:02d}',
                    'email': f'demo.faculty{number:03d}@dbuu.ac.in',
                    'department': department,
                    'designation': 'Assistant Professor',
                    'qualification': 'Ph.D.',
                    'experience_years': 5 + number % 12,
                    'joining_date': date(2015 + number % 8, 7, 1),
                    'specialization': 'Institutional research and academic development',
                    'research_interests': 'Sample dashboard data',
                },
            )
            if created:
                count += 1
            number += 1

    def add_facilities(self, institution):
        count = InstitutionalFacility.objects.filter(institution=institution).count()
        number = 1
        while count < TARGET_COUNT:
            facility, created = InstitutionalFacility.objects.get_or_create(
                institution=institution,
                name=f'Demo Facility {number:02d}',
                defaults={
                    'facility_type': 'Academic Facility',
                    'location': f'Demo Block {((number - 1) % 5) + 1}',
                    'capacity': 50 + number * 10,
                    'description': 'Sample facility record for dashboard demonstration.',
                },
            )
            if created:
                count += 1
            number += 1

    def add_research(self, institution, departments, faculty, academic_year):
        count = ResearchProject.objects.filter(department__institution=institution).count()
        number = 1
        while count < TARGET_COUNT:
            department = departments[(number - 1) % len(departments)]
            investigators = [member for member in faculty if member.department_id == department.id]
            investigator = investigators[0] if investigators else faculty[(number - 1) % len(faculty)]
            _, created = ResearchProject.objects.get_or_create(
                title=f'DBUU Demo Research Project {number:02d}',
                defaults={
                    'principal_investigator': investigator,
                    'department': department,
                    'academic_year': academic_year,
                    'funding_agency': 'Demonstration Grant',
                    'funding_amount': Decimal(number * 100000),
                    'status': 'ONGOING' if number % 2 else 'COMPLETED',
                    'start_date': academic_year.start_date,
                    'end_date': academic_year.end_date if number % 2 == 0 else None,
                },
            )
            if created:
                count += 1
            number += 1

    def add_publications(self, institution, departments, academic_year):
        count = Publication.objects.filter(department__institution=institution).count()
        number = 1
        while count < TARGET_COUNT:
            department = departments[(number - 1) % len(departments)]
            month = ((number - 1) % 12) + 1
            _, created = Publication.objects.get_or_create(
                title=f'DBUU Demo Publication {number:02d}',
                defaults={
                    'authors': 'Demo Faculty; Institutional Research Team',
                    'department': department,
                    'publication_type': 'Journal Article',
                    'publication_date': date(academic_year.start_date.year, month, 15),
                    'academic_year': academic_year,
                    'doi_or_reference': f'DEMO-DBUU-PUB-{number:03d}',
                },
            )
            if created:
                count += 1
            number += 1

    def add_placements(self, institution, academic_year):
        count = Placement.objects.filter(student__department__institution=institution).count()
        students = list(Student.objects.filter(
            department__institution=institution).order_by('student_id'))
        if count >= TARGET_COUNT:
            return
        if not students:
            raise CommandError('No DBUU students exist for sample placements.')
        number = 1
        while count < TARGET_COUNT:
            student = students[(number - 1) % len(students)]
            _, created = Placement.objects.get_or_create(
                student=student,
                company=f'Demo Employer {((number - 1) % 5) + 1}',
                position='Graduate Trainee',
                academic_year=academic_year,
                defaults={
                    'package_lpa': Decimal(f'{4 + number % 5}.0'),
                    'placement_date': academic_year.start_date + timedelta(days=number),
                },
            )
            if created:
                count += 1
            number += 1

    def add_submissions(self, institution, academic_year, submitter):
        count = Submission.objects.filter(department__institution=institution).count()
        parameters = list(Parameter.objects.filter(
            department__institution=institution).select_related('department', 'academic_year').order_by('id'))
        if count >= TARGET_COUNT:
            return
        if not parameters:
            raise CommandError('No DBUU accreditation parameters exist for sample submissions.')

        reviewer = User.objects.filter(role='REVIEWER_VERIFIER').first()
        approver = User.objects.filter(can_approve=True).exclude(id=submitter.id).first()
        statuses = ['DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'CORRECTION_REQUIRED', 'VERIFIED', 'APPROVED']
        number = 1
        while count < TARGET_COUNT:
            parameter = parameters[(number - 1) % len(parameters)]
            submission_status = statuses[(number - 1) % len(statuses)]
            _, created = Submission.objects.get_or_create(
                title=f'DBUU Demo Submission {number:02d}',
                parameter=parameter,
                defaults={
                    'department': parameter.department or Department.objects.filter(
                        institution=institution).first(),
                    'academic_year': parameter.academic_year or academic_year,
                    'narrative': 'Sample accreditation submission for dashboard demonstration.',
                    'status': submission_status,
                    'submitted_by': submitter,
                    'reviewed_by': reviewer if submission_status in (
                        'UNDER_REVIEW', 'CORRECTION_REQUIRED', 'VERIFIED', 'APPROVED') else None,
                    'approved_by': approver if submission_status == 'APPROVED' else None,
                },
            )
            if created:
                count += 1
            number += 1

    def add_evidence(self, institution, academic_year, submitter, departments):
        count = EvidenceDocument.objects.filter(department__institution=institution).count()
        parameters = list(Parameter.objects.filter(
            department__institution=institution).order_by('id'))
        number = 1
        while count < TARGET_COUNT:
            department = departments[(number - 1) % len(departments)]
            parameter = next(
                (item for item in parameters if item.department_id == department.id),
                None,
            )
            title = f'DBUU Demo Evidence {number:02d}'
            _, created = EvidenceDocument.objects.get_or_create(
                title=title,
                defaults={
                    'category': 'Demo Accreditation Evidence',
                    'department': department,
                    'academic_year': academic_year,
                    'parameter': parameter,
                    'file': ContentFile(
                        self.make_pdf(title), name=f'dbuu-demo-evidence-{number:03d}.pdf'),
                    'uploaded_by': submitter,
                },
            )
            if created:
                count += 1
            number += 1

    @staticmethod
    def make_pdf(title):
        buffer = BytesIO()
        document = canvas.Canvas(buffer)
        document.drawString(72, 740, title)
        document.drawString(72, 720, 'Sample evidence file for dashboard demonstration.')
        document.save()
        return buffer.getvalue()

    def write_counts(self, institution):
        counts = {
            'Departments': Department.objects.filter(institution=institution).count(),
            'Programmes': Programme.objects.filter(department__institution=institution).count(),
            'Students': Student.objects.filter(department__institution=institution).count(),
            'Faculty': Faculty.objects.filter(department__institution=institution).count(),
            'Facilities': InstitutionalFacility.objects.filter(institution=institution).count(),
            'Research': ResearchProject.objects.filter(department__institution=institution).count(),
            'Publications': Publication.objects.filter(department__institution=institution).count(),
            'Placements': Placement.objects.filter(student__department__institution=institution).count(),
            'Submissions': Submission.objects.filter(department__institution=institution).count(),
            'Evidence': EvidenceDocument.objects.filter(department__institution=institution).count(),
        }
        for label, count in counts.items():
            self.stdout.write(f'{label}: {count}')
