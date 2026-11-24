from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APIClient
from datetime import date
from io import BytesIO
import tempfile
from openpyxl import Workbook, load_workbook
from .models import *


class WorkflowTests(TestCase):
    def setUp(self):
        institution = Institution.objects.create(name='Test University', code='TU')
        department = Department.objects.create(institution=institution, name='CSE', code='CSE')
        year = AcademicYear.objects.create(name='2025-26', start_date=date(2025, 7, 1), end_date=date(2026, 6, 30))
        framework = AccreditationFramework.objects.create(name='Framework', code='FW1')
        criterion = Criterion.objects.create(framework=framework, code='C1', title='Criterion')
        parameter = Parameter.objects.create(criterion=criterion, code='P1', title='Parameter')
        User = get_user_model()
        self.submitter = User.objects.create_user(username='faculty', password='Password@123', role='FACULTY_STAFF')
        self.reviewer = User.objects.create_user(username='reviewer', password='Password@123', role='REVIEWER_VERIFIER')
        self.approver = User.objects.create_user(username='approver', password='Password@123', role='INSTITUTIONAL_ADMIN', can_approve=True)
        self.submission = Submission.objects.create(
            parameter=parameter, department=department, academic_year=year,
            title='Test Submission', submitted_by=self.submitter)
        self.client = APIClient()

    def test_self_approval_is_rejected(self):
        self.submission.status = 'VERIFIED'
        self.submission.save()
        self.client.force_authenticate(self.submitter)
        response = self.client.post(f'/api/submissions/{self.submission.id}/approve/')
        self.assertEqual(response.status_code, 403)

    def test_review_and_approval_workflow(self):
        self.client.force_authenticate(self.reviewer)
        response = self.client.post(f'/api/submissions/{self.submission.id}/review/',
                                    {'decision': 'VERIFIED', 'comments': 'Verified'})
        self.assertEqual(response.status_code, 200)
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, 'VERIFIED')
        self.client.force_authenticate(self.approver)
        response = self.client.post(f'/api/submissions/{self.submission.id}/approve/')
        self.assertEqual(response.status_code, 200)
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, 'APPROVED')


class ProfileTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='profile-user', password='OldPassword@123', role='FACULTY_STAFF')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_profile_update(self):
        response = self.client.patch('/api/auth/profile/', {
            'first_name': 'Updated',
            'email': 'updated@example.com',
        })
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')

    def test_password_change_rejects_wrong_password(self):
        response = self.client.post('/api/auth/change-password/', {
            'old_password': 'WrongPassword',
            'new_password': 'NewPassword@123',
        })
        self.assertEqual(response.status_code, 400)


class StudentRegistrationTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name='Student University', code='STU')
        self.department = Department.objects.create(
            institution=self.institution, name='Computer Science', code='CS')
        self.programme = Programme.objects.create(
            department=self.department, name='BSc Computer Science', code='BSCS')
        self.year = AcademicYear.objects.create(
            name='2026-27', start_date=date(2026, 7, 1), end_date=date(2027, 6, 30))
        self.client = APIClient()
        self.payload = {
            'username': 'student-account',
            'email': 'student@example.com',
            'password': 'StudentPass@123',
            'full_name': 'Test Student',
            'student_id': 'STU-001',
            'roll_number': 'ROLL-001',
            'institution': self.institution.id,
            'department': self.department.id,
            'programme': self.programme.id,
            'academic_year': self.year.id,
            'admission_year': 2026,
        }

    def test_registration_links_student_to_selected_university_and_login(self):
        response = self.client.post('/api/auth/student-register/', self.payload)
        self.assertEqual(response.status_code, 201)
        user = get_user_model().objects.get(username='student-account')
        student = Student.objects.get(user=user)
        self.assertEqual(user.role, 'STUDENT')
        self.assertEqual(student.department.institution, self.institution)
        self.assertEqual(student.programme, self.programme)

        login = self.client.post('/api/auth/login/', {
            'username': 'student-account',
            'password': 'StudentPass@123',
        })
        self.assertEqual(login.status_code, 200)
        self.client.force_authenticate(user)
        profile = self.client.get('/api/auth/student-profile/')
        self.assertEqual(profile.status_code, 200)
        self.assertEqual(profile.data['institution_name'], 'Student University')
        self.client.patch('/api/auth/profile/', {'role': 'SUPER_ADMIN'})
        user.refresh_from_db()
        self.assertEqual(user.role, 'STUDENT')
        self.assertEqual(self.client.get('/api/dashboard/').status_code, 403)
        self.assertEqual(self.client.get('/api/students/').status_code, 403)
        admin = get_user_model().objects.create_user(
            username='student-test-admin', password='Password@123', role='SUPER_ADMIN')
        self.client.force_authenticate(admin)
        dashboard = self.client.get('/api/dashboard/', {'institution': self.institution.id})
        self.assertEqual(dashboard.status_code, 200)
        self.assertEqual(dashboard.data['students'], 1)

    def test_registration_rejects_department_from_another_university(self):
        other_institution = Institution.objects.create(name='Other University', code='OTHER')
        other_department = Department.objects.create(
            institution=other_institution, name='Other Department', code='OD')
        self.payload['department'] = other_department.id
        response = self.client.post('/api/auth/student-register/', self.payload)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(get_user_model().objects.filter(username='student-account').exists())

    def test_registration_options_only_show_universities_with_programmes(self):
        incomplete = Institution.objects.create(name='Incomplete University', code='INC')
        Department.objects.create(institution=incomplete, name='No Programme', code='NP')
        response = self.client.get('/api/auth/student-options/')
        self.assertEqual(response.status_code, 200)
        institution_names = [item['name'] for item in response.data['institutions']]
        department_names = [item['name'] for item in response.data['departments']]
        programme_names = [item['name'] for item in response.data['programmes']]
        self.assertCountEqual(
            institution_names,
            ['Dev Bhoomi Uttarakhand University', 'Student University'],
        )
        self.assertIn('Computer Science', department_names)
        self.assertNotIn('No Programme', department_names)
        self.assertIn('BSc Computer Science', programme_names)
        self.assertNotIn('Incomplete University', institution_names)

    def test_requested_departments_have_multiple_programmes(self):
        response = self.client.get('/api/auth/student-options/')
        self.assertEqual(response.status_code, 200)
        department_names = {item['name'] for item in response.data['departments']}
        programme_names = {item['name'] for item in response.data['programmes']}
        for name in (
            'Business Administration (BBA)',
            'Computer Applications (BCA)',
            'Hotel Management & Hospitality (BHM)',
            'Pharmacy (B.Pharm)',
            'Nursing',
        ):
            self.assertIn(name, department_names)
        for name in (
            'BBA - Finance',
            'MBA - Business Analytics',
            'BCA - Cyber Security',
            'Bachelor of Pharmacy (B.Pharm)',
            'B.Sc Nursing',
            'General Nursing and Midwifery (GNM)',
        ):
            self.assertIn(name, programme_names)


class StudentExcelImportTests(TestCase):
    def setUp(self):
        self.institution, _ = Institution.objects.get_or_create(
            code='DBUU',
            defaults={'name': 'Dev Bhoomi Uttarakhand University'},
        )
        self.department, _ = Department.objects.get_or_create(
            institution=self.institution,
            code='CSE',
            defaults={'name': 'Computer Science & Engineering'},
        )
        self.programme, _ = Programme.objects.get_or_create(
            department=self.department,
            code='BTECH-CSE',
            defaults={'name': 'B.Tech Computer Science & Engineering'},
        )
        self.year = AcademicYear.objects.create(
            name='Excel Import Year',
            start_date=date(2026, 7, 1),
            end_date=date(2027, 6, 30),
        )
        self.admin = get_user_model().objects.create_user(
            username='excel-admin', password='Password@123', role='SUPER_ADMIN')
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def make_workbook(self, rows):
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = 'Students'
        sheet.append([
            'student_id', 'roll_number', 'full_name', 'email', 'department_code',
            'programme_code', 'academic_year', 'admission_year', 'achievements',
            'internship_details', 'project_details',
        ])
        for row in rows:
            sheet.append(row)
        output = BytesIO()
        workbook.save(output)
        return SimpleUploadedFile(
            'students.xlsx',
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

    def row(self, student_id, roll_number, email, programme_code='BTECH-CSE'):
        return [
            student_id, roll_number, f'{student_id} Name', email, 'CSE',
            programme_code, self.year.name, 2026, '', '', '',
        ]

    def test_import_adds_students_to_selected_university(self):
        upload = self.make_workbook([
            self.row('XLS-STU-1', 'XLS-ROLL-1', 'xls1@example.com'),
            self.row('XLS-STU-2', 'XLS-ROLL-2', 'xls2@example.com'),
        ])
        response = self.client.post('/api/students/import-excel/', {
            'institution': self.institution.id,
            'file': upload,
        }, format='multipart')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['imported'], 2)
        self.assertEqual(
            Student.objects.filter(department__institution=self.institution).count(),
            2,
        )

    def test_import_is_all_or_nothing_when_a_row_is_invalid(self):
        upload = self.make_workbook([
            self.row('XLS-VALID-1', 'XLS-VALID-ROLL-1', 'valid@example.com'),
            self.row('XLS-INVALID-2', 'XLS-INVALID-ROLL-2', 'invalid@example.com', 'NOT-A-PROGRAM'),
        ])
        response = self.client.post('/api/students/import-excel/', {
            'institution': self.institution.id,
            'file': upload,
        }, format='multipart')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Student.objects.filter(student_id='XLS-VALID-1').exists())

    def test_only_administrators_can_download_import_template(self):
        faculty = get_user_model().objects.create_user(
            username='excel-faculty', password='Password@123', role='FACULTY_STAFF')
        self.client.force_authenticate(faculty)
        response = self.client.get('/api/students/import-template/')
        self.assertEqual(response.status_code, 403)

        student = get_user_model().objects.create_user(
            username='excel-student', password='Password@123', role='STUDENT')
        self.client.force_authenticate(student)
        response = self.client.get('/api/students/import-template/')
        self.assertEqual(response.status_code, 403)

    def test_template_download_contains_student_headers(self):
        response = self.client.get('/api/students/import-template/')
        self.assertEqual(response.status_code, 200)
        workbook = load_workbook(BytesIO(response.content), read_only=True)
        self.assertEqual(workbook['Students'].cell(1, 1).value, 'student_id')
        self.assertEqual(workbook['Students'].cell(1, 6).value, 'programme_code')
        workbook.close()

    def test_institutional_admin_cannot_import_for_another_university(self):
        other_institution = Institution.objects.create(name='Other University', code='OTHER-IMPORT')
        admin = get_user_model().objects.create_user(
            username='institutional-excel-admin',
            password='Password@123',
            role='INSTITUTIONAL_ADMIN',
            department=self.department,
        )
        self.client.force_authenticate(admin)
        upload = self.make_workbook([
            self.row('XLS-OTHER-1', 'XLS-OTHER-ROLL-1', 'other@example.com'),
        ])
        response = self.client.post('/api/students/import-excel/', {
            'institution': other_institution.id,
            'file': upload,
        }, format='multipart')
        self.assertEqual(response.status_code, 403)


class BulkImportTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name='Bulk University', code='BULK')
        self.department = Department.objects.create(
            institution=self.institution, name='Computer Science', code='CS')
        self.year = AcademicYear.objects.create(
            name='2026-27', start_date=date(2026, 7, 1), end_date=date(2027, 6, 30))
        self.programme = Programme.objects.create(
            department=self.department, name='BSc Computer Science', code='BSCS')
        self.user = get_user_model().objects.create_user(
            username='bulk-admin', password='Password@123', role='SUPER_ADMIN')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def make_workbook(self, headers, rows):
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = 'Data'
        sheet.append(headers)
        for row in rows:
            sheet.append(row)
        output = BytesIO()
        workbook.save(output)
        return SimpleUploadedFile(
            'bulk-import.xlsx',
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

    def test_templates_cover_data_sections_and_include_relationship_references(self):
        for resource in (
            'institutions', 'academic-years', 'facilities', 'departments', 'programmes',
            'courses', 'faculty', 'research-projects', 'publications', 'placements',
            'frameworks', 'criteria', 'parameters', 'evidence', 'submissions',
        ):
            response = self.client.get(f'/api/bulk-import/{resource}/template/')
            self.assertEqual(response.status_code, 200, resource)
            workbook = load_workbook(BytesIO(response.content), read_only=True)
            self.assertIn('Data', workbook.sheetnames)
            self.assertIn('Instructions', workbook.sheetnames)
            workbook.close()

        response = self.client.get('/api/bulk-import/programmes/template/')
        workbook = load_workbook(BytesIO(response.content), read_only=True)
        self.assertIn('department_reference', workbook.sheetnames)
        reference_ids = [
            row[0] for row in workbook['department_reference'].iter_rows(min_row=2, values_only=True)
        ]
        self.assertIn(self.department.id, reference_ids)
        workbook.close()

    def test_import_adds_programmes_and_rolls_back_invalid_workbook(self):
        upload = self.make_workbook(
            ['department', 'name', 'code', 'duration_years'],
            [
                [self.department.id, 'BSc Data Science', 'BSDS', 3],
                [999999, 'BSc Cyber Security', 'BSCSCY', 3],
            ],
        )
        response = self.client.post(
            '/api/bulk-import/programmes/', {'file': upload}, format='multipart')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Programme.objects.filter(code='BSDS').exists())

        upload = self.make_workbook(
            ['department', 'name', 'code', 'duration_years'],
            [[self.department.id, 'BSc Data Science', 'BSDS', 3]],
        )
        response = self.client.post(
            '/api/bulk-import/programmes/', {'file': upload}, format='multipart')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['imported'], 1)

    def test_imports_academic_year_facility_research_and_publication_records(self):
        upload = self.make_workbook(
            ['name', 'start_date', 'end_date', 'is_current'],
            [['2027-28', date(2027, 7, 1), date(2028, 6, 30), True]],
        )
        response = self.client.post(
            '/api/bulk-import/academic-years/', {'file': upload}, format='multipart')
        self.assertEqual(response.status_code, 201, response.data)
        imported_year = AcademicYear.objects.get(name='2027-28')

        upload = self.make_workbook(
            ['institution', 'name', 'facility_type', 'location', 'capacity', 'description'],
            [[self.institution.id, 'Research Lab', 'Laboratory', 'North Campus', 40, 'Materials lab']],
        )
        response = self.client.post(
            '/api/bulk-import/facilities/', {'file': upload}, format='multipart')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertTrue(InstitutionalFacility.objects.filter(name='Research Lab').exists())

        faculty = Faculty.objects.create(
            faculty_id='BULK-FAC-1',
            full_name='Research Lead',
            email='research-lead@bulk.example',
            department=self.department,
            designation='Professor',
            qualification='PhD',
            joining_date=date(2020, 1, 1),
        )
        upload = self.make_workbook(
            [
                'title', 'principal_investigator', 'department', 'academic_year',
                'funding_agency', 'funding_amount', 'status', 'start_date', 'end_date',
            ],
            [[
                'Imported Research Project', faculty.id, self.department.id, imported_year.id,
                'Research Council', 250000.50, 'ONGOING', date(2027, 8, 1), None,
            ]],
        )
        response = self.client.post(
            '/api/bulk-import/research-projects/', {'file': upload}, format='multipart')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(ResearchProject.objects.filter(title='Imported Research Project').exists())

        upload = self.make_workbook(
            [
                'title', 'authors', 'department', 'publication_type', 'publication_date',
                'academic_year', 'doi_or_reference',
            ],
            [[
                'Imported Publication', 'Research Lead', self.department.id, 'Journal',
                date(2028, 1, 15), imported_year.id, 'doi:example',
            ]],
        )
        response = self.client.post(
            '/api/bulk-import/publications/', {'file': upload}, format='multipart')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Publication.objects.filter(title='Imported Publication').exists())

    def test_institutional_admin_cannot_import_for_another_university(self):
        other = Institution.objects.create(name='Other University', code='OTHER-BULK')
        other_department = Department.objects.create(
            institution=other, name='Other Department', code='OD')
        admin = get_user_model().objects.create_user(
            username='bulk-institution-admin',
            password='Password@123',
            role='INSTITUTIONAL_ADMIN',
            department=self.department,
        )
        self.client.force_authenticate(admin)
        template = self.client.get('/api/bulk-import/programmes/template/')
        self.assertEqual(template.status_code, 200)
        workbook = load_workbook(BytesIO(template.content), read_only=True)
        reference_ids = [
            row[0] for row in workbook['department_reference'].iter_rows(min_row=2, values_only=True)
        ]
        workbook.close()
        self.assertIn(self.department.id, reference_ids)
        self.assertNotIn(other_department.id, reference_ids)
        upload = self.make_workbook(
            ['department', 'name', 'code', 'duration_years'],
            [[other_department.id, 'Other Programme', 'OP', 4]],
        )
        response = self.client.post(
            '/api/bulk-import/programmes/', {'file': upload}, format='multipart')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Programme.objects.filter(code='OP').exists())

    def test_imported_submissions_are_drafts_owned_by_importing_admin(self):
        framework = AccreditationFramework.objects.create(name='Framework', code='BULK-FW')
        criterion = Criterion.objects.create(framework=framework, code='C1', title='Criterion')
        parameter = Parameter.objects.create(criterion=criterion, code='P1', title='Parameter')
        upload = self.make_workbook(
            ['parameter', 'department', 'academic_year', 'title', 'narrative'],
            [[parameter.id, self.department.id, self.year.id, 'Imported draft', 'Details']],
        )
        response = self.client.post(
            '/api/bulk-import/submissions/', {'file': upload}, format='multipart')
        self.assertEqual(response.status_code, 201)
        submission = Submission.objects.get(title='Imported draft')
        self.assertEqual(submission.status, 'DRAFT')
        self.assertEqual(submission.submitted_by, self.user)

    def test_evidence_import_saves_document_with_metadata_atomically(self):
        parameter = Parameter.objects.create(
            criterion=Criterion.objects.create(
                framework=AccreditationFramework.objects.create(
                    name='Evidence Framework', code='EVID-FW'),
                code='C1',
                title='Criterion',
            ),
            code='P1',
            title='Parameter',
        )
        media_dir = tempfile.TemporaryDirectory()
        self.addCleanup(media_dir.cleanup)
        settings_override = override_settings(MEDIA_ROOT=media_dir.name)
        settings_override.enable()
        self.addCleanup(settings_override.disable)
        upload = self.make_workbook(
            ['title', 'category', 'department', 'academic_year', 'parameter', 'file_name'],
            [['Evidence record', 'Accreditation', self.department.id, self.year.id, parameter.id, 'evidence.pdf']],
        )
        document = SimpleUploadedFile('evidence.pdf', b'%PDF-test')
        response = self.client.post('/api/bulk-import/evidence/', {
            'file': upload,
            'documents': [document],
        }, format='multipart')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertTrue(EvidenceDocument.objects.filter(title='Evidence record').exists())

    def test_non_administrator_cannot_download_bulk_templates(self):
        faculty = get_user_model().objects.create_user(
            username='bulk-faculty', password='Password@123', role='FACULTY_STAFF')
        self.client.force_authenticate(faculty)
        response = self.client.get('/api/bulk-import/academic-years/template/')
        self.assertEqual(response.status_code, 403)


class ReportAndRoleTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name='Report University', code='RU')
        department = Department.objects.create(institution=self.institution, name='CSE', code='CSE')
        year = AcademicYear.objects.create(name='2025-26', start_date=date(2025,7,1), end_date=date(2026,6,30))
        programme = Programme.objects.create(department=department, name='B.Tech CSE', code='BTECH')
        for index in range(3):
            Student.objects.create(
                student_id=f'RSTU-{index}', roll_number=f'R-{index}', full_name=f'Report Student {index}',
                email=f'report{index}@example.com', department=department, programme=programme,
                academic_year=year, admission_year=2024)
        User = get_user_model()
        self.admin = User.objects.create_user(username='report-admin', password='Password@123', role='SUPER_ADMIN')
        self.viewer = User.objects.create_user(username='report-viewer', password='Password@123', role='MANAGEMENT_VIEWER')
        self.client = APIClient()

    def test_faculty_report_download_returns_xlsx(self):
        login = self.client.post('/api/auth/login/', {
            'username': 'report-admin',
            'password': 'Password@123',
        })
        self.assertEqual(login.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        response = self.client.get('/api/report-download/', {'type':'faculty','format':'xlsx'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('spreadsheet', response['Content-Type'])
        self.assertGreater(len(response.content), 100)

    def test_management_viewer_cannot_edit_departments(self):
        self.client.force_authenticate(self.viewer)
        response = self.client.post('/api/departments/', {'name':'Forbidden','code':'FOR','institution':1})
        self.assertIn(response.status_code, (403, 404))

    def test_dashboard_filters_by_institution(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get('/api/dashboard/', {'institution': self.institution.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['institution'], 'Report University')
        self.assertEqual(response.data['students'], 3)

    def test_registration_creates_faculty_account(self):
        response = self.client.post('/api/auth/register/', {
            'username': 'new-member',
            'email': 'new-member@example.com',
            'password': 'Password@123',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(get_user_model().objects.get(username='new-member').role, 'FACULTY_STAFF')
