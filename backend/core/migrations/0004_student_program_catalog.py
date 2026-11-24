from django.db import migrations


def add_program_catalog(apps, schema_editor):
    Institution = apps.get_model('core', 'Institution')
    Department = apps.get_model('core', 'Department')
    Programme = apps.get_model('core', 'Programme')

    institution, _ = Institution.objects.get_or_create(
        code='DBUU',
        defaults={
            'name': 'Dev Bhoomi Uttarakhand University',
            'address': 'Dehradun, Uttarakhand',
            'email': 'office@dbuu.ac.in',
            'website': 'https://dbuu.ac.in',
        },
    )
    department_specs = [
        ('MBA', 'Management Studies (MBA)'),
        ('BBA', 'Business Administration (BBA)'),
        ('BCA', 'Computer Applications (BCA)'),
        ('BHM', 'Hotel Management & Hospitality (BHM)'),
        ('PHARM', 'Pharmacy (B.Pharm)'),
        ('NURS', 'Nursing'),
    ]
    departments = {}
    for code, name in department_specs:
        department, created = Department.objects.get_or_create(
            institution=institution,
            code=code,
            defaults={'name': name},
        )
        if code == 'MBA' and not created and department.name == 'Management Studies':
            department.name = name
            department.save(update_fields=['name'])
        departments[code] = department

    programme_specs = [
        ('MBA', 'MBA', 'Master of Business Administration', 2),
        ('MBA', 'MBA-FIN', 'MBA - Finance', 2),
        ('MBA', 'MBA-MKT', 'MBA - Marketing', 2),
        ('MBA', 'MBA-HR', 'MBA - Human Resource Management', 2),
        ('MBA', 'MBA-BA', 'MBA - Business Analytics', 2),
        ('BBA', 'BBA-GEN', 'BBA - General Management', 3),
        ('BBA', 'BBA-FIN', 'BBA - Finance', 3),
        ('BBA', 'BBA-MKT', 'BBA - Marketing', 3),
        ('BBA', 'BBA-HR', 'BBA - Human Resource Management', 3),
        ('BCA', 'BCA-GEN', 'BCA - General', 3),
        ('BCA', 'BCA-AI-DS', 'BCA - Artificial Intelligence & Data Science', 3),
        ('BCA', 'BCA-CYBER', 'BCA - Cyber Security', 3),
        ('BCA', 'BCA-CLOUD', 'BCA - Cloud Computing', 3),
        ('BHM', 'BHM-GEN', 'BHM - Hotel Management', 4),
        ('BHM', 'BHM-CUL', 'BHM - Culinary Arts', 4),
        ('BHM', 'BHM-OPS', 'BHM - Hotel Operations', 4),
        ('PHARM', 'BPHARM', 'Bachelor of Pharmacy (B.Pharm)', 4),
        ('PHARM', 'DPHARM', 'Diploma in Pharmacy (D.Pharm)', 2),
        ('PHARM', 'PHARMD', 'Doctor of Pharmacy (Pharm.D)', 6),
        ('NURS', 'BSN', 'B.Sc Nursing', 4),
        ('NURS', 'GNM', 'General Nursing and Midwifery (GNM)', 3),
        ('NURS', 'PB-BSN', 'Post Basic B.Sc Nursing', 2),
    ]
    for department_code, code, name, duration in programme_specs:
        Programme.objects.get_or_create(
            department=departments[department_code],
            code=code,
            defaults={'name': name, 'duration_years': duration, 'is_active': True},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_student_user_alter_user_role'),
    ]

    operations = [
        migrations.RunPython(add_program_catalog, migrations.RunPython.noop),
    ]
