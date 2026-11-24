from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import *
from datetime import date, timedelta
from decimal import Decimal
import random


class Command(BaseCommand):
    help = 'Seed realistic demonstration data'

    def handle(self, *args, **options):
        random.seed(2026)
        institution, _ = Institution.objects.get_or_create(code='DBUU', defaults={
            'name': 'Dev Bhoomi Uttarakhand University',
            'address': 'Dehradun, Uttarakhand',
            'email': 'office@dbuu.ac.in',
            'website': 'https://dbuu.ac.in',
        })
        for name, facility_type, location, capacity in [
            ('Central Library', 'Library', 'Main Block', 600),
            ('Digital Learning Centre', 'Laboratory', 'Academic Block A', 120),
            ('Central Auditorium', 'Auditorium', 'Administrative Block', 800),
            ('Sports Complex', 'Sports', 'Campus South', 500),
        ]:
            InstitutionalFacility.objects.get_or_create(
                institution=institution, name=name,
                defaults={'facility_type': facility_type, 'location': location, 'capacity': capacity},
            )

        department_specs = [
            ('CSE', 'Computer Science & Engineering', 'Dr. Arvind Kumar'),
            ('ECE', 'Electronics & Communication', 'Dr. Neha Sharma'),
            ('ME', 'Mechanical Engineering', 'Dr. Rahul Verma'),
            ('CE', 'Civil Engineering', 'Dr. Priya Singh'),
            ('MBA', 'Management Studies (MBA)', 'Dr. Aman Joshi'),
        ]
        additional_department_specs = [
            ('BBA', 'Business Administration (BBA)', 'Dr. Aman Joshi'),
            ('BCA', 'Computer Applications (BCA)', 'Dr. Arvind Kumar'),
            ('BHM', 'Hotel Management & Hospitality (BHM)', 'Dr. Kavita Rawat'),
            ('PHARM', 'Pharmacy (B.Pharm)', 'Dr. Meera Bhandari'),
            ('NURS', 'Nursing', 'Dr. Priya Singh'),
            ('EE-DEMO', 'Electrical Engineering (Sample)', 'Dr. Neha Sharma'),
            ('BIO-DEMO', 'Biotechnology (Sample)', 'Dr. Meera Bhandari'),
            ('AGRI-DEMO', 'Agriculture (Sample)', 'Dr. Priya Singh'),
            ('LAW-DEMO', 'Law (Sample)', 'Dr. Aman Joshi'),
            ('EDU-DEMO', 'Education (Sample)', 'Dr. Kavita Rawat'),
        ]
        departments = {}
        for code, name, head in department_specs + additional_department_specs:
            department, _ = Department.objects.update_or_create(
                institution=institution, code=code,
                defaults={'name': name, 'head': head, 'is_active': True})
            departments[code] = department

        year, _ = AcademicYear.objects.update_or_create(name='2025-26', defaults={
            'start_date': date(2025, 7, 1),
            'end_date': date(2026, 6, 30),
            'is_current': True,
        })
        year2, _ = AcademicYear.objects.get_or_create(name='2024-25', defaults={
            'start_date': date(2024, 7, 1),
            'end_date': date(2025, 6, 30),
            'is_current': False,
        })

        programme_specs = [
            ('CSE', 'BTECH-CSE', 'B.Tech Computer Science & Engineering'),
            ('ECE', 'BTECH-ECE', 'B.Tech Electronics & Communication'),
            ('ME', 'BTECH-ME', 'B.Tech Mechanical Engineering'),
            ('CE', 'BTECH-CE', 'B.Tech Civil Engineering'),
            ('MBA', 'MBA', 'Master of Business Administration'),
            ('MBA', 'MBA-FIN', 'MBA - Finance'),
            ('MBA', 'MBA-MKT', 'MBA - Marketing'),
            ('MBA', 'MBA-HR', 'MBA - Human Resource Management'),
            ('MBA', 'MBA-BA', 'MBA - Business Analytics'),
            ('BBA', 'BBA-GEN', 'BBA - General Management'),
            ('BBA', 'BBA-FIN', 'BBA - Finance'),
            ('BBA', 'BBA-MKT', 'BBA - Marketing'),
            ('BBA', 'BBA-HR', 'BBA - Human Resource Management'),
            ('BCA', 'BCA-GEN', 'BCA - General'),
            ('BCA', 'BCA-AI-DS', 'BCA - Artificial Intelligence & Data Science'),
            ('BCA', 'BCA-CYBER', 'BCA - Cyber Security'),
            ('BCA', 'BCA-CLOUD', 'BCA - Cloud Computing'),
            ('BHM', 'BHM-GEN', 'BHM - Hotel Management'),
            ('BHM', 'BHM-CUL', 'BHM - Culinary Arts'),
            ('BHM', 'BHM-OPS', 'BHM - Hotel Operations'),
            ('PHARM', 'BPHARM', 'Bachelor of Pharmacy (B.Pharm)'),
            ('PHARM', 'DPHARM', 'Diploma in Pharmacy (D.Pharm)'),
            ('PHARM', 'PHARMD', 'Doctor of Pharmacy (Pharm.D)'),
            ('NURS', 'BSN', 'B.Sc Nursing'),
            ('NURS', 'GNM', 'General Nursing and Midwifery (GNM)'),
            ('NURS', 'PB-BSN', 'Post Basic B.Sc Nursing'),
            ('EE-DEMO', 'BTECH-EE-DEMO', 'B.Tech Electrical Engineering (Sample)'),
            ('BIO-DEMO', 'BSC-BIO-DEMO', 'B.Sc Biotechnology (Sample)'),
            ('AGRI-DEMO', 'BSC-AGRI-DEMO', 'B.Sc Agriculture (Sample)'),
            ('LAW-DEMO', 'LLB-DEMO', 'LL.B. (Sample)'),
            ('EDU-DEMO', 'BED-DEMO', 'B.Ed. (Sample)'),
        ]
        programmes = {}
        for department_code, code, name in programme_specs:
            programme, _ = Programme.objects.update_or_create(
                department=departments[department_code], code=code,
                defaults={
                    'name': name,
                    'duration_years': 2 if code.startswith('MBA') else 3 if code.startswith(('BBA', 'BCA')) else 4,
                    'is_active': True,
                })
            programmes.setdefault(department_code, programme)

        framework, _ = AccreditationFramework.objects.update_or_create(code='NAAC-2026', defaults={
            'name': 'NAAC Institutional Accreditation Framework',
            'description': 'Configurable institution-wide accreditation framework',
            'version': '2.0',
            'is_active': True,
        })
        parameter_codes = [
            ('1', 'Curricular Aspects', 'Curriculum Design and Development'),
            ('2', 'Teaching-Learning and Evaluation', 'Student Performance and Learning Outcomes'),
            ('3', 'Research, Innovations and Extension', 'Research Projects and Innovation'),
            ('4', 'Infrastructure and Learning Resources', 'Learning Resource Utilization'),
            ('5', 'Student Support and Progression', 'Student Progression and Support'),
            ('6', 'Governance, Leadership and Management', 'Institutional Governance'),
            ('7', 'Institutional Values and Best Practices', 'Quality Assurance Practices'),
        ]
        parameters = []
        for criterion_code, criterion_title, parameter_title in parameter_codes:
            criterion, _ = Criterion.objects.update_or_create(
                framework=framework, code=f'CR{criterion_code}',
                defaults={'title': criterion_title, 'description': f'{criterion_title} documentation and evidence'})
            parameter, _ = Parameter.objects.update_or_create(
                criterion=criterion, code=f'{criterion_code}.1',
                defaults={
                    'title': parameter_title,
                    'required_information': 'Narrative, supporting records, evidence documents and annual data',
                    'department': departments['CSE'],
                    'academic_year': year,
                    'deadline': date(2026, 12, 31),
                })
            parameters.append(parameter)

        User = get_user_model()
        users = [
            ('admin', 'SUPER_ADMIN', True, 'Administrator'),
            ('institution', 'INSTITUTIONAL_ADMIN', True, 'Institution'),
            ('coordinator', 'ACCREDITATION_COORDINATOR', True, 'Coordinator'),
            ('department', 'DEPARTMENT_ADMIN', False, 'Department'),
            ('faculty', 'FACULTY_STAFF', False, 'Faculty'),
            ('reviewer', 'REVIEWER_VERIFIER', True, 'Reviewer'),
            ('viewer', 'MANAGEMENT_VIEWER', False, 'Management'),
        ]
        seeded_users = {}
        for username, role, can_approve, first_name in users:
            user, created = User.objects.get_or_create(username=username, defaults={
                'email': f'{username}@dbuu.ac.in',
                'role': role,
                'department': departments['CSE'],
                'can_approve': can_approve,
                'first_name': first_name,
            })
            if created:
                user.set_password('Password@123')
                user.save()
            seeded_users[role] = user

        faculty_names = [
            'Dr. Arvind Kumar', 'Dr. Neha Sharma', 'Prof. Rahul Verma', 'Dr. Priya Singh',
            'Prof. Aman Joshi', 'Dr. Kavita Rawat', 'Prof. Vivek Chauhan', 'Dr. Meera Bhandari',
            'Dr. Sanjay Gupta', 'Prof. Pooja Negi', 'Dr. Nitin Bisht', 'Prof. Riya Pandey',
        ]
        faculty_records = []
        for index, name in enumerate(faculty_names, 1):
            department_code = department_specs[(index - 1) % len(department_specs)][0]
            faculty, _ = Faculty.objects.update_or_create(faculty_id=f'FAC-{index:03}', defaults={
                'full_name': name,
                'email': f'faculty{index}@dbuu.ac.in',
                'phone': f'987650{index:04}',
                'department': departments[department_code],
                'designation': 'Professor' if index % 4 == 0 else 'Assistant Professor',
                'qualification': 'Ph.D.',
                'experience_years': 5 + (index % 12),
                'joining_date': date(2012 + (index % 10), 7, 1),
                'specialization': ['Artificial Intelligence', 'Data Science', 'Embedded Systems', 'Thermal Engineering'][index % 4],
                'research_interests': 'Research, publications and funded projects',
            })
            faculty_records.append(faculty)

        students = []
        for index in range(1, 61):
            department_code = department_specs[(index - 1) % len(department_specs)][0]
            student, _ = Student.objects.update_or_create(
                student_id=f'STU-{index:03}',
                defaults={
                    'roll_number': f'24{department_code}{index:04}',
                    'full_name': f'Student {index:02}',
                    'email': f'student{index}@dbuu.ac.in',
                    'department': departments[department_code],
                    'programme': programmes[department_code],
                    'academic_year': year if index <= 48 else year2,
                    'admission_year': 2024 if index <= 48 else 2023,
                    'achievements': 'Academic and extracurricular achievements' if index % 5 == 0 else '',
                    'internship_details': 'Industry internship completed' if index % 4 == 0 else '',
                    'project_details': 'Capstone project completed' if index % 3 == 0 else '',
                })
            students.append(student)

        for index in range(1, 11):
            department = departments[department_specs[(index - 1) % len(department_specs)][0]]
            ResearchProject.objects.update_or_create(
                title=f'Research and Innovation Project {index}',
                defaults={
                    'principal_investigator': faculty_records[(index - 1) % len(faculty_records)],
                    'department': department,
                    'academic_year': year,
                    'funding_agency': ['DST', 'UGC', 'AICTE', 'ISRO'][index % 4],
                    'funding_amount': Decimal(index * 750000),
                    'status': 'ONGOING' if index % 3 else 'COMPLETED',
                    'start_date': date(2024, index if index <= 12 else 1, 1),
                    'end_date': date(2026, 6, 30) if index % 3 else None,
                })

        publication_types = ['Journal Article', 'Conference Paper', 'Book Chapter']
        for index in range(1, 19):
            department = departments[department_specs[(index - 1) % len(department_specs)][0]]
            Publication.objects.update_or_create(
                title=f'Research Publication {index}',
                defaults={
                    'authors': f'{faculty_records[(index - 1) % len(faculty_records)].full_name}; Research Team',
                    'department': department,
                    'publication_type': publication_types[index % len(publication_types)],
                    'publication_date': date(2025, (index % 12) + 1, 15),
                    'academic_year': year,
                    'doi_or_reference': f'10.1000/dbuu.2025.{index:04}',
                })

        companies = ['TCS', 'Infosys', 'Wipro', 'Accenture', 'Amazon', 'Microsoft', 'Cognizant']
        for index in range(1, 25):
            student = students[index - 1]
            Placement.objects.update_or_create(
                student=student,
                defaults={
                    'company': companies[(index - 1) % len(companies)],
                    'position': ['Software Engineer', 'Analyst', 'Graduate Engineer Trainee'][index % 3],
                    'package_lpa': Decimal(f'{4 + (index % 8)}.{index % 10}'),
                    'placement_date': date(2025, (index % 12) + 1, 10),
                    'academic_year': year,
                })

        statuses = ['DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'CORRECTION_REQUIRED', 'VERIFIED', 'APPROVED']
        submitter = seeded_users['FACULTY_STAFF']
        reviewer = seeded_users['REVIEWER_VERIFIER']
        approver = seeded_users['INSTITUTIONAL_ADMIN']
        Submission.objects.exclude(title__startswith='2025-26').delete()
        for index, parameter in enumerate(parameters, 1):
            status = statuses[(index - 1) % len(statuses)]
            submission, _ = Submission.objects.update_or_create(
                title=f'2025-26 {parameter.title}',
                parameter=parameter,
                defaults={
                    'department': departments['CSE'],
                    'academic_year': year,
                    'narrative': f'Documented data and supporting evidence for {parameter.title}.',
                    'status': status,
                    'submitted_by': submitter,
                    'reviewed_by': reviewer if status not in ('DRAFT', 'SUBMITTED') else None,
                    'approved_by': approver if status == 'APPROVED' else None,
                })

        for index, parameter in enumerate(parameters[:5], 1):
            EvidenceDocument.objects.update_or_create(
                title=f'Evidence Record {index}',
                defaults={
                    'category': 'Accreditation',
                    'department': departments['CSE'],
                    'academic_year': year,
                    'parameter': parameter,
                    'uploaded_by': submitter,
                    'version': index,
                })

        for username, role, can_approve, first_name in users:
            Notification.objects.get_or_create(
                user=seeded_users[role],
                title='Accreditation submission requires attention',
                defaults={
                    'message': 'One or more accreditation submissions need review or supporting evidence.',
                    'link': '/submissions',
                })

        self.stdout.write(self.style.SUCCESS(
            f'Seeded 5 departments, 12 faculty, 60 students, 10 projects, 18 publications, '
            f'24 placements and 7 accreditation submissions.'
        ))
